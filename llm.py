"""The only file that knows about model providers.

Three providers are supported, chosen with LLM_PROVIDER in secrets.toml:

    gemini  Google Gemini (default). Needs GEMINI_API_KEY.
    groq    Groq's free hosted API. Needs GROQ_API_KEY.
    ollama  A model running on your own computer. No key, no quota.

app.py and prompts.py never change when you switch provider. Messages are kept
in one neutral format ({"role": "user" | "assistant", "content": str}) and
converted to each provider's format only inside this file.

Secrets: keys are read from the environment or st.secrets only. They are never
written to disk by this code, never shown in the UI, and are stripped from
every error message by _redact().
"""

import json
import os
import re
import time
from dataclasses import dataclass
from typing import Iterator, Optional

from google import genai
from google.genai import types
from pydantic import ValidationError

import labtools
import languages
import prompts
from prompts import RoastResult

# Newest first. If a name is retired or not available to your key, the next
# one is tried automatically, and the one that works is remembered.
GEMINI_MODEL_CHAIN = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

PROVIDERS = {
    "gemini": {
        "short": "Gemini",
        "label": "Google's Gemini API",
        "model": GEMINI_MODEL_CHAIN[0],
        "timeout": 90,
    },
    "groq": {
        "short": "Groq",
        "label": "Groq's API",
        "model": "llama-3.3-70b-versatile",
        "base_url": "https://api.groq.com/openai/v1",
        "key_name": "GROQ_API_KEY",
        "timeout": 90,
    },
    "ollama": {
        "short": "Ollama",
        "label": "Ollama on your own computer (nothing leaves it)",
        "model": "llama3.2",
        "base_url": "http://localhost:11434/v1",
        "key_name": None,
        "timeout": 240,  # small local models on a laptop CPU can be slow
    },
}
RETRY_WAIT_SECONDS = 2
TOTAL_BUDGET_SECONDS = 200  # stop trying more models after this long

# What worked last time, so a failing name is not retried on every request.
_STATE: dict = {"backend": None, "model": None}


class LLMConfigError(Exception):
    """Missing key or unusable setup. Shown to the user with setup steps."""


class LLMError(Exception):
    """The provider failed even after retries."""


@dataclass
class RoastOutcome:
    ok: bool
    result: Optional[RoastResult] = None
    raw: str = ""  # raw model text, shown if parsing failed
    error: str = ""


# --------------------------------------------------------------------------
# Settings and secrets
# --------------------------------------------------------------------------
def _setting(name: str) -> Optional[str]:
    """Read a setting from the environment, then from Streamlit secrets."""
    value = os.environ.get(name)
    if value:
        return value
    try:
        import streamlit as st

        value = st.secrets.get(name)  # raises if no secrets file exists
        return str(value) if value else None
    except Exception:
        return None


_KEY_SHAPES = re.compile(
    r"(AIza[0-9A-Za-z_\-]{20,}|AQ\.[0-9A-Za-z_\-]{20,}|gsk_[0-9A-Za-z]{20,})"
)


def _redact(text: str) -> str:
    """Remove any API key from text before it can reach the screen or a log."""
    for name in ("GEMINI_API_KEY", "GROQ_API_KEY"):
        key = _setting(name)
        if key and len(key) > 8:
            text = text.replace(key, "[hidden]")
    return _KEY_SHAPES.sub("[hidden]", text)


def get_provider() -> str:
    name = (_setting("LLM_PROVIDER") or "gemini").strip().lower()
    return name if name in PROVIDERS else "gemini"


def provider_label() -> str:
    return PROVIDERS[get_provider()]["label"]


def provider_short() -> str:
    return PROVIDERS[get_provider()]["short"]


def get_model_name() -> str:
    provider = get_provider()
    old_gemini_name = _setting("GEMINI_MODEL") if provider == "gemini" else None
    return _setting("LLM_MODEL") or old_gemini_name or PROVIDERS[provider]["model"]


def _model_sequence() -> list[str]:
    """Models to try, in order. The first one gets a single retry."""
    main = get_model_name()
    if get_provider() != "gemini":
        return [main, main]
    chain = [main]
    extra = _setting("GEMINI_FALLBACK_MODEL")
    for name in ([extra] if extra else []) + GEMINI_MODEL_CHAIN:
        if name not in chain:
            chain.append(name)
    good = _STATE.get("model")
    if good in chain and good != chain[0]:
        chain.remove(good)
        chain.insert(0, good)
    return [chain[0]] + chain


# --------------------------------------------------------------------------
# Error classification
# --------------------------------------------------------------------------
def _is_auth_error(exc: Exception) -> bool:
    t = str(exc).lower()
    return any(
        s in t
        for s in (
            "api key not valid", "api_key_invalid", "401", "403",
            "unauthenticated", "permission_denied", "permission denied",
            "forbidden", "unregistered caller", "invalid api key",
        )
    )


def _is_not_found(exc: Exception) -> bool:
    t = str(exc).lower()
    return "404" in t or "not found" in t or "is not supported" in t


def _pick_error(errors: list[Exception]) -> Exception:
    """The most useful error to show: prefer anything over 'model not found',
    because a not-found on a fallback name hides the real problem."""
    for exc in errors:
        if not _is_not_found(exc):
            return exc
    return errors[0]


def _friendly(exc: Exception) -> str:
    text = str(exc).lower()
    provider = get_provider()
    if provider == "ollama" and (
        "connection" in text or "connect" in text or "refused" in text
    ):
        msg = (
            "Could not reach Ollama. Open the Ollama app (or run 'ollama "
            "serve'), then try again."
        )
    elif "429" in text or "quota" in text or "resource_exhausted" in text or "rate limit" in text:
        msg = "The free quota or rate limit is used up for now. Wait a minute and try again."
    elif _is_auth_error(exc):
        msg = "The API key was rejected. Check the key in secrets.toml."
    elif "timeout" in text or "timed out" in text or "deadline" in text:
        msg = "The model took too long to answer. Try again, or use shorter code."
    elif "503" in text or "overloaded" in text or "unavailable" in text:
        msg = "The provider is overloaded right now. Wait a moment and try again."
    elif _is_not_found(exc):
        hint = (
            f" Run: ollama pull {get_model_name()}"
            if provider == "ollama"
            else " Set LLM_MODEL in secrets.toml to a current model name."
        )
        msg = f"No working model was found.{hint}"
    else:
        msg = "The model API had a problem. Please try again in a moment."
    detail = _redact(" ".join(str(exc).split()))[:200]
    return f"{msg} (Technical detail: {detail})"


# --------------------------------------------------------------------------
# Clients
# --------------------------------------------------------------------------
class _GeminiBackends:
    """Wraps the Gemini clients that could accept the key.

    Google issues two key styles: classic AI Studio keys (start with AIza) work
    with the Gemini Developer API; keys that start with "AQ." are Vertex AI
    express-mode keys. For an AQ. key both are tried, and the one that works is
    remembered. Exposes .models so it can stand in for a genai.Client.
    """

    def __init__(self, key: str, timeout_ms: int):
        http = types.HttpOptions(timeout=timeout_ms)
        self.names = ["developer"]
        self.clients = [genai.Client(api_key=key, http_options=http)]
        if not key.startswith("AIza"):
            self.names.append("vertex")
            self.clients.append(
                genai.Client(vertexai=True, api_key=key, http_options=http)
            )
        self.models = self

    def _order(self) -> list[int]:
        order = list(range(len(self.clients)))
        pref = _STATE.get("backend")
        if pref in self.names:
            i = self.names.index(pref)
            order.remove(i)
            order.insert(0, i)
        return order

    def generate_content(self, **kwargs):
        last: Optional[Exception] = None
        for i in self._order():
            try:
                out = self.clients[i].models.generate_content(**kwargs)
                _STATE["backend"] = self.names[i]
                return out
            except Exception as exc:
                last = exc
                if not _is_auth_error(exc):
                    raise
        raise last  # type: ignore[misc]

    def generate_content_stream(self, **kwargs):
        last: Optional[Exception] = None
        for i in self._order():
            started = False
            try:
                for chunk in self.clients[i].models.generate_content_stream(**kwargs):
                    started = True
                    yield chunk
                _STATE["backend"] = self.names[i]
                return
            except Exception as exc:
                last = exc
                if started or not _is_auth_error(exc):
                    raise
        if last:
            raise last


def _client():
    provider = get_provider()
    cfg = PROVIDERS[provider]

    if provider == "gemini":
        key = _setting("GEMINI_API_KEY")
        if not key or key == "your-key-here":
            raise LLMConfigError(
                "No Gemini API key found. Add GEMINI_API_KEY to "
                ".streamlit/secrets.toml (or set it as an environment variable)."
            )
        return _GeminiBackends(key.strip(), cfg["timeout"] * 1000)

    # groq and ollama both speak the OpenAI protocol
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMConfigError(
            "The 'openai' package is missing. Run: python -m pip install openai"
        ) from exc

    key = "ollama"  # Ollama ignores the key but the library needs something
    if cfg["key_name"]:
        key = _setting(cfg["key_name"])
        if not key or key.startswith("your-"):
            raise LLMConfigError(
                f"No {cfg['key_name']} found. Add it to .streamlit/secrets.toml."
            )
    base_url = _setting("LLM_BASE_URL") or cfg["base_url"]
    return OpenAI(
        base_url=base_url, api_key=key.strip(), timeout=cfg["timeout"], max_retries=0
    )


# --------------------------------------------------------------------------
# Message format conversion
# --------------------------------------------------------------------------
def _schema_hint(schema) -> str:
    """Gemini enforces the schema itself. Other providers are told in text."""
    return (
        "\n\nReturn one JSON object with exactly these fields (JSON schema):\n"
        + json.dumps(schema.model_json_schema())
    )


def _to_gemini(messages: list[dict]) -> list[types.Content]:
    return [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in messages
    ]


# --------------------------------------------------------------------------
# One call to the provider
# --------------------------------------------------------------------------
def _call_once(client, model: str, system: str, messages: list[dict], schema=None) -> str:
    if get_provider() == "gemini":
        kwargs = {"system_instruction": system}
        if schema is not None:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_schema"] = schema
        resp = client.models.generate_content(
            model=model,
            contents=_to_gemini(messages),
            config=types.GenerateContentConfig(**kwargs),
        )
        return resp.text or ""

    sys_text = system + (_schema_hint(schema) if schema is not None else "")
    kwargs = {}
    if schema is not None:
        kwargs["response_format"] = {"type": "json_object"}
        kwargs["max_tokens"] = 8000  # a 500-line refactor is a long answer; the default can cut JSON off
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": sys_text}] + messages,
        **kwargs,
    )
    return resp.choices[0].message.content or ""


def _remember_model(model: str) -> None:
    if get_provider() == "gemini":
        _STATE["model"] = model


def _complete(system: str, messages: list[dict], schema=None) -> str:
    """Non-streaming call with retries and model fallback."""
    client = _client()  # may raise LLMConfigError
    errors: list[Exception] = []
    dead: set[str] = set()  # model names that returned "not found"
    deadline = time.monotonic() + TOTAL_BUDGET_SECONDS
    for attempt, model in enumerate(_model_sequence()):
        if model in dead:
            continue
        if attempt > 0 and time.monotonic() > deadline:
            break
        try:
            out = _call_once(client, model, system, messages, schema)
            _remember_model(model)
            return out
        except Exception as exc:  # network, 429, 5xx, timeout ...
            errors.append(exc)
            if _is_not_found(exc):
                dead.add(model)
            elif attempt == 0:
                time.sleep(RETRY_WAIT_SECONDS)
    err = _pick_error(errors)
    raise LLMError(_friendly(err)) from err


def _parse(text: str, schema=RoastResult):
    cleaned = text.strip()
    # Safety nets for chattier models: strip ```json fences, then keep only
    # the part between the first "{" and the last "}".
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return schema.model_validate_json(cleaned)


@dataclass
class ToolOutcome:
    ok: bool
    data: object = None  # a parsed Pydantic object when ok
    raw: str = ""
    error: str = ""


_INVALID_JSON = (
    "The model did not return valid JSON, even after a retry. "
    "Try again, or shorten the code."
)


def _structured(system: str, user_for, schema) -> ToolOutcome:
    """Call the model for a JSON answer matching `schema`. One re-ask with a
    stricter prompt if the JSON is invalid. Never raises for model problems."""
    raw = ""
    try:
        for strict in (False, True):
            raw = _complete(system, [{"role": "user", "content": user_for(strict)}], schema)
            try:
                return ToolOutcome(ok=True, data=_parse(raw, schema), raw=raw)
            except (ValidationError, ValueError):
                continue
    except LLMConfigError as exc:
        return ToolOutcome(ok=False, error=str(exc))
    except LLMError as exc:
        return ToolOutcome(ok=False, raw=raw, error=str(exc))
    return ToolOutcome(ok=False, raw=raw, error=_INVALID_JSON)


def roast_code(
    code: str, level: str, hinglish: bool, language: Optional[str] = None
) -> RoastOutcome:
    """Review `code`. Never raises for model problems; returns an outcome.

    `language` is the user's choice (one of languages.SUPPORTED) or None to
    auto-detect."""
    lang = language if language in languages.SUPPORTED else languages.detect_language(code)
    out = _structured(
        prompts.build_system_prompt(level, hinglish, lang),
        lambda strict: prompts.build_user_prompt(code, strict=strict),
        RoastResult,
    )
    return RoastOutcome(ok=out.ok, result=out.data, raw=out.raw, error=out.error)


# --------------------------------------------------------------------------
# Lab tools (see labtools.py)
# --------------------------------------------------------------------------
def oop_refactor(code: str, language: Optional[str], concepts: list[str], hinglish: bool = False) -> ToolOutcome:
    return _structured(
        labtools.oop_system_prompt(language, concepts, hinglish),
        lambda strict: labtools.user_prompt("Refactor this code using object-oriented design.", code, strict),
        labtools.OOPResult,
    )


def generate_tests(code: str, language: Optional[str], hinglish: bool = False) -> ToolOutcome:
    return _structured(
        labtools.tests_system_prompt(language, hinglish),
        lambda strict: labtools.user_prompt("Write unit tests for this code.", code, strict),
        labtools.UnitTestsResult,
    )


def analyze_complexity(code: str, language: Optional[str], hinglish: bool = False) -> ToolOutcome:
    return _structured(
        labtools.complexity_system_prompt(language, hinglish),
        lambda strict: labtools.user_prompt("Analyse the time and space complexity of this code.", code, strict),
        labtools.ComplexityResult,
    )


def interview_questions(code: str, language: Optional[str], hinglish: bool = False) -> ToolOutcome:
    return _structured(
        labtools.interview_system_prompt(language, hinglish),
        lambda strict: labtools.user_prompt("Write the viva questions for this code.", code, strict),
        labtools.InterviewResult,
    )


def quality_report(code: str, language: Optional[str], hinglish: bool = False) -> ToolOutcome:
    return _structured(
        labtools.report_system_prompt(language, hinglish),
        lambda strict: labtools.user_prompt("Write a quality report card for this code.", code, strict),
        labtools.ReportCard,
    )


# --------------------------------------------------------------------------
# Follow-up chat (streaming, with memory)
# --------------------------------------------------------------------------
def build_followup_messages(
    code: str, result: RoastResult, history: list[dict], question: str
) -> list[dict]:
    """The model is stateless, so every call resends the code, the first
    review and all earlier turns. `history` is a list of
    {"role": "user" | "assistant", "content": str} from st.session_state."""
    messages = [
        {"role": "user", "content": prompts.format_review_for_context(code, result)},
        {"role": "assistant", "content": "Got it. Ask me anything about this code or my review."},
    ]
    messages += [{"role": t["role"], "content": t["content"]} for t in history]
    messages.append({"role": "user", "content": question})
    return messages


def build_followup_contents(code, result, history, question) -> list[types.Content]:
    """Same messages, in Gemini's format (kept for tests)."""
    return _to_gemini(build_followup_messages(code, result, history, question))


def _stream_once(client, model: str, system: str, messages: list[dict]) -> Iterator[str]:
    if get_provider() == "gemini":
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=_to_gemini(messages),
            config=types.GenerateContentConfig(system_instruction=system),
        ):
            if chunk.text:
                yield chunk.text
        return

    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": system}] + messages,
        stream=True,
    )
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


def stream_followup(
    code: str,
    result: RoastResult,
    history: list[dict],
    question: str,
    level: str,
    hinglish: bool,
) -> Iterator[str]:
    """Yield the answer in chunks, for st.write_stream. Never raises."""
    try:
        client = _client()
    except LLMConfigError as exc:
        yield str(exc)
        return

    system = prompts.build_followup_system_prompt(level, hinglish)
    messages = build_followup_messages(code, result, history, question)

    errors: list[Exception] = []
    dead: set[str] = set()
    deadline = time.monotonic() + TOTAL_BUDGET_SECONDS
    for attempt, model in enumerate(_model_sequence()):
        if model in dead:
            continue
        if attempt > 0 and time.monotonic() > deadline:
            break
        yielded = False
        try:
            for piece in _stream_once(client, model, system, messages):
                yielded = True
                yield piece
            _remember_model(model)
            return
        except Exception as exc:
            errors.append(exc)
            if yielded:  # already showed partial text, don't restart mid-answer
                yield "\n\n(The reply was cut off. Please ask again.)"
                return
            if _is_not_found(exc):
                dead.add(model)
            elif attempt == 0:
                time.sleep(RETRY_WAIT_SECONDS)
    yield _friendly(_pick_error(errors))
