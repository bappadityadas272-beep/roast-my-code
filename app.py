"""Roast My Code: Streamlit UI (look and feel lives in style.css).

Run with:  streamlit run app.py
"""

import difflib
import html
import uuid
from pathlib import Path

import streamlit as st

import demo_data
import history
import labtools
import languages
import llm
import prompts
import samples

MAX_LINES = 500
MAX_CHAT_TURNS = 20  # messages (not pairs) resent to the model per question
AUTO = "Auto-detect"
VIEWS = ["🔥 Roast", "🐛 Bugs", "✅ Fix", "💬 Ask", "📈 History", "🏛 OOP", "🧪 Tests", "⏱ Big-O", "📊 Report", "🎤 Interview"]
(V_ROAST, V_BUGS, V_FIX, V_ASK, V_HIST, V_OOP, V_TESTS, V_BIGO, V_REPORT, V_INT) = VIEWS
PANEL_HEIGHT = 330  # px: results panel scrolls inside itself, so the page does not

LANG_ALIASES = {"c++": "cpp", "c#": "csharp", "js": "javascript", "golang": "go", "shell": "bash"}
LEVEL_CAPTIONS = {
    "Gentle Mentor": "kind and encouraging",
    "Sarcastic Senior": "dry and witty",
    "Brutal": "dramatic, code-only",
}

st.set_page_config(
    page_title="Roast My Code",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# Small helpers: icons, escaping, HTML snippets
# --------------------------------------------------------------------------
_ICONS = {
    "flame": '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
    "code": '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
    "chat": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "trend": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
    "brain": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
    "bug": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
    "check": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
}


def icon(name: str, size: int = 22) -> str:
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
        f'stroke-linejoin="round">{_ICONS[name]}</svg>'
    )


def esc(text) -> str:
    """Escape model/user text before it goes into HTML. Never skip this."""
    return html.escape(str(text)).replace("\n", "<br>")


def build_report(result, code: str, lab: dict, level: str) -> str:
    """The whole review as one Markdown file the student can keep or hand in."""
    fence = lambda text, lang="": f"```{lang}\n{text.rstrip()}\n```"
    key = LANG_ALIASES.get(result.language.lower().strip(), result.language.lower().strip())
    out = [f"# Roast My Code report", "", f"- Language: {result.language}", f"- Score: {result.score}/10", f"- Roast level: {level}", "",
           "## The roast", "", result.roast, "", "## Bugs", ""]
    out += [f"{i}. **Line {b.line}**: {b.issue}  \n   Fix: {b.fix}" for i, b in enumerate(result.bugs, 1)] or ["No bugs found."]
    out += ["", "## Your code", "", fence(code, key), "", "## Fixed code", "", fence(result.fixed_code, key) if result.fixed_code.strip() else "Nothing to fix."]
    if "report" in lab:
        out += ["", "## Quality report card", ""] + [f"- {m.name}: {m.score}/10, {m.comment}" for m in lab["report"].metrics]
        out += ["", lab["report"].verdict]
    if "bigo" in lab:
        d = lab["bigo"]
        out += ["", "## Complexity", "", f"Time {d.overall_time}, space {d.overall_space}. {d.summary}"]
        out += [f"- {f.name}: time {f.time}, space {f.space}. {f.reason}" for f in d.functions]
    if "oop" in lab:
        out += ["", "## OOP refactor", "", lab["oop"].summary, "", fence(lab["oop"].refactored_code, key)]
    if "tests" in lab:
        out += ["", "## Unit tests", "", fence(lab["tests"].test_code, key), "", "How to run:", "", fence(lab["tests"].how_to_run)]
    if "interview" in lab:
        out += ["", "## Viva questions", ""]
        for i, q in enumerate(lab["interview"].questions, 1):
            out += [f"{i}. **{q.question}** ({q.level})", f"   - Answer: {q.model_answer}"]
    out += ["", "_AI can be wrong. Test every fix before you trust it._", ""]
    return "\n".join(out)


def md(snippet: str) -> None:
    # One flat line per tag, no indentation: indented HTML turns into a code
    # block in Markdown.
    st.markdown(" ".join(line.strip() for line in snippet.splitlines() if line.strip()), unsafe_allow_html=True)


def tone(score: int) -> str:
    return "good" if score >= 8 else "mid" if score >= 5 else "bad"


def verdict(score: int) -> str:
    if score >= 9:
        return "Chef's kiss."
    if score >= 7:
        return "Pretty solid."
    if score >= 4:
        return "Needs some love."
    return "Send help."


# --------------------------------------------------------------------------
# Theme + session state
# --------------------------------------------------------------------------
css = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def init_state() -> None:
    defaults = {
        "session_id": uuid.uuid4().hex,
        "result": None,  # RoastResult of the latest roast
        "code": "",  # the code that was roasted
        "messages": [],  # follow-up chat: {"role", "content"}
        "lab": {},  # lab tool results for the current roast, by tool name
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


init_state()


def show_demo(name: str, level: str) -> None:
    """Show the pre-saved result for a sample: instant, no model call."""
    result = demo_data.demo_roast(name, level)
    st.session_state.result = result
    st.session_state.code = samples.SAMPLES[name]
    st.session_state.messages = []
    st.session_state.lab = {}
    st.session_state.view = V_ROAST
    st.session_state.is_demo = True
    st.session_state.scroll_to_results = True
    history.add_entry(st.session_state.session_id, result.language, level, result.score)


def load_sample(name: str) -> None:
    """Sample button: fill the code box and, unless Hinglish is on, show the saved roast."""
    st.session_state.code_input = samples.SAMPLES[name]
    if st.session_state.get("hinglish"):
        st.session_state.demo_note = True  # saved roasts are English only
    else:
        st.session_state.demo_note = False
        show_demo(name, st.session_state.get("level", prompts.LEVELS[1]))


# --------------------------------------------------------------------------
# Header bar
# --------------------------------------------------------------------------
md(
    f"""
    <div class="rmc-header">
      <div class="rmc-brand">
        <div class="rmc-logo">{icon("flame", 26)}</div>
        <div><div class="rmc-name">Roast My Code</div><div class="rmc-tag">BUGS &amp; BRAGGING RIGHTS</div></div>
      </div>
      <div class="rmc-pills">
        <span class="pill yellow">v1.0 “Extra Crispy”</span>
        <span class="pill teal">{esc(llm.provider_short())} inside</span>
      </div>
    </div>
    """
)


def render_verdict(result) -> None:
    t = tone(result.score)
    md(
        f"""
        <div class="result-head">
          <div class="score-badge {t}"><span class="score-num">{result.score}</span><span class="score-den">/10</span></div>
          <div class="result-meta">
            <span class="pill yellow">{esc(result.language)}</span>
            {'<span class="pill demo">Demo example</span>' if st.session_state.get("is_demo") else ""}
            <span class="verdict">{verdict(result.score)}</span>
            <div class="bar"><div class="bar-fill {t}" style="width:{result.score * 10}%"></div></div>
          </div>
        </div>
        """
    )


def render_roast_view(result) -> None:
    md(
        f"""
        <div class="roast-card">
          <div class="kicker">{icon("flame", 18)} THE ROAST</div>
          <p>{esc(result.roast)}</p>
        </div>
        """
    )


def render_bugs_view(result) -> None:
    md(f'<div class="section-label">{len(result.bugs)} bug(s) found</div>')
    if not result.bugs:
        md(f'<div class="good-card">{icon("check", 20)} No real bugs found. Suspiciously good.</div>')
    for i, bug in enumerate(result.bugs, start=1):
        where = f"LINE {bug.line}" if bug.line else "GENERAL"
        md(
            f"""
            <div class="bug-card">
              <div class="bug-num">{i}</div>
              <div class="bug-body">
                <div class="kicker">{where}</div>
                <p>{esc(bug.issue)}</p>
                <span class="fix-chip"><b>Fix:</b> {esc(bug.fix)}</span>
              </div>
            </div>
            """
        )


def diff_html(old_code: str, new_code: str) -> str:
    """Two columns, original on the left and fixed on the right, changed lines highlighted."""
    a, b = old_code.splitlines(), new_code.splitlines()
    rows = []

    def cell(n, text, kind):
        body = html.escape(text) if text is not None else ""
        return f'<td class="dn">{n or ""}</td><td class="dc {kind}">{body}</td>'

    ia = ib = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        left, right = a[i1:i2], b[j1:j2]
        for k in range(max(len(left), len(right))):
            has_l, has_r = k < len(left), k < len(right)
            kind_l = "same" if tag == "equal" else ("del" if has_l else "empty")
            kind_r = "same" if tag == "equal" else ("add" if has_r else "empty")
            rows.append(
                "<tr>" + cell(i1 + k + 1 if has_l else "", left[k] if has_l else None, kind_l)
                + cell(j1 + k + 1 if has_r else "", right[k] if has_r else None, kind_r) + "</tr>"
            )
    return (
        '<div class="diff-wrap"><table class="diff"><thead><tr><th colspan="2">Your code</th>'
        '<th colspan="2">Fixed code</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>"
    )


def render_fixed_view(result) -> None:
    if result.fixed_code.strip():
        lang_key = result.language.lower().strip()
        compare = st.toggle("Compare with my code", key="fix_compare", help="Your code on the left, the fix on the right, changes highlighted.")
        if compare:
            st.markdown(diff_html(st.session_state.code, result.fixed_code), unsafe_allow_html=True)
        else:
            st.code(result.fixed_code, language=LANG_ALIASES.get(lang_key, lang_key) or None)
        st.caption("AI can be wrong. Read and test the fix before you trust it.")
    else:
        md('<div class="good-card">Nothing to fix here.</div>')


def render_chat_view(result, level: str, hinglish: bool) -> None:
    st.caption('Try "explain bug 2", "why this score?" or "rewrite it in Java".')
    msg_box = st.container(border=False, key="chat_msgs")  # messages appear above the input
    with msg_box:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    question = st.chat_input("Ask about your code...")
    if question:
        prior = st.session_state.messages[-MAX_CHAT_TURNS:]
        with msg_box:
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                answer = st.write_stream(
                    llm.stream_followup(
                        st.session_state.code, result, prior, question, level, hinglish
                    )
                )
        st.session_state.messages.append({"role": "user", "content": question})
        st.session_state.messages.append({"role": "assistant", "content": answer})


def render_history_view() -> None:
    sid = st.session_state.session_id
    if st.button("Clear history", key="clear_history"):
        history.clear_history(sid)
    df = history.history_frame(sid)
    if df.empty:
        st.caption("Roast some code to start your chart.")
        return
    latest = int(df["Score"].iloc[-1])
    delta = latest - int(df["Score"].iloc[-2]) if len(df) > 1 else None
    st.metric("Latest score", f"{latest}/10", delta=delta)
    if len(df) > 1:
        st.line_chart(df, color="#3D5AFE", height=150)
    st.caption("Saved on the server for this session. It may reset when the app restarts.")



# --------------------------------------------------------------------------
# Lab views: OOP refactor, unit tests, Big-O, report card
# --------------------------------------------------------------------------
def code_lang(name: str):
    key = (name or "").lower().strip()
    return LANG_ALIASES.get(key, key) or None


def info_card(title: str, body: str = "", chip: str = "", extra: str = "") -> None:
    chip_html = f'<span class="pill white">{esc(chip)}</span>' if chip else ""
    body_html = f"<p>{esc(body)}</p>" if body else ""
    md(f'<div class="info-card"><div class="info-title">{esc(title)} {chip_html}</div>{body_html}{extra}</div>')


def sub_label(text: str) -> None:
    md(f'<div class="section-label sub">{esc(text)}</div>')


def render_oop(data, language: str) -> None:
    md(f'<div class="roast-card"><div class="kicker">{icon("code", 18)} DESIGN SUMMARY</div><p>{esc(data.summary)}</p></div>')
    if data.concepts:
        sub_label("OOP concepts applied")
        for c in data.concepts:
            info_card(c.concept, c.why, chip=c.where)
    if data.classes:
        sub_label("Classes")
        for c in data.classes:
            rel = f'<div class="info-rel">{esc(c.relationships)}</div>' if c.relationships.strip() else ""
            info_card(c.name, c.responsibility, chip=c.kind, extra=rel)
    if data.diagram.strip():
        sub_label("Class diagram")
        st.code(data.diagram, language=None)
    sub_label("Refactored code")
    st.code(data.refactored_code, language=code_lang(language))
    if data.notes.strip():
        st.caption(data.notes)


def render_tests(data, language: str) -> None:
    md(f'<span class="pill yellow">{esc(data.framework)}</span>')
    sub_label("How to run")
    st.code(data.how_to_run, language=None)
    if data.covers:
        sub_label("What the tests check")
        items = "".join(f"<li>{esc(c)}</li>" for c in data.covers)
        md(f'<ul class="covers">{items}</ul>')
    sub_label("Test code")
    st.code(data.test_code, language=code_lang(language))
    st.caption("Run these yourself. A test only proves what it checks.")


def render_bigo(data, language: str) -> None:
    md(
        f"""
        <div class="bigo-top">
          <div class="bigo-box"><span>TIME</span><b>{esc(data.overall_time)}</b></div>
          <div class="bigo-box"><span>SPACE</span><b>{esc(data.overall_space)}</b></div>
        </div>
        """
    )
    md(f'<div class="roast-card"><p>{esc(data.summary)}</p></div>')
    if data.functions:
        sub_label("Function by function")
    for f in data.functions:
        fast = (
            f'<span class="fix-chip"><b>Faster:</b> {esc(f.improvement)}</span>'
            if f.improvement.strip() else ""
        )
        chips = f'<span class="pill white">time {esc(f.time)}</span> <span class="pill white">space {esc(f.space)}</span>'
        md(
            f'<div class="info-card"><div class="info-title">{esc(f.name)} {chips}</div>'
            f"<p>{esc(f.reason)}</p>{fast}</div>"
        )


def render_report(data, language: str) -> None:
    for m in data.metrics:
        t = tone(m.score)
        md(
            f"""
            <div class="metric">
              <div class="metric-top"><span class="metric-name">{esc(m.name)}</span><span class="metric-score {t}">{m.score}/10</span></div>
              <div class="bar"><div class="bar-fill {t}" style="width:{m.score * 10}%"></div></div>
              <div class="metric-comment">{esc(m.comment)}</div>
            </div>
            """
        )
    info_card("Verdict", data.verdict)
    if data.priorities:
        sub_label("Fix these first")
        for i, p in enumerate(data.priorities, start=1):
            md(f'<div class="bug-card"><div class="bug-num">{i}</div><div class="bug-body"><p>{esc(p)}</p></div></div>')


def render_interview(data, language: str) -> None:
    md(f'<div class="roast-card"><div class="kicker">{icon("code", 18)} YOUR VIVA</div><p>{esc(data.intro)}</p></div>')
    for i, q in enumerate(data.questions, start=1):
        level = esc(q.level)
        md(
            f"""
            <div class="qa-card"><div class="qa-top"><span class="qa-num">Q{i}</span>
            <span class="pill {'yellow' if q.level == 'Basic' else 'white'}">{level}</span></div>
            <p class="qa-q">{esc(q.question)}</p>
            <p class="qa-why">{esc(q.why_asked)}</p></div>
            """
        )
        with st.expander("Model answer"):
            st.write(q.model_answer)
            if q.follow_up:
                st.markdown(f"**Likely follow-up:** {q.follow_up}")
    if data.tips:
        sub_label("How to answer well")
        for t in data.tips:
            md(f'<div class="info-card"><p>{esc(t)}</p></div>')


LAB_VIEWS = {
    V_OOP: ("oop", "Turn the code into a clean class design. Pick the OOP ideas to apply.", "Refactor with OOP", "Designing the classes...", render_oop),
    V_TESTS: ("tests", "Writes unit tests for the fixed code, using only the standard library.", "Generate unit tests", "Writing tests...", render_tests),
    V_BIGO: ("bigo", "Time and space complexity of your code, function by function.", "Analyse complexity", "Counting loops...", render_bigo),
    V_INT: ("interview", "Likely viva questions about your code, with model answers you can practise.", "Generate questions", "Preparing the examiner...", render_interview),
    V_REPORT: ("report", "Separate scores for readability, naming, structure, errors, OOP design and efficiency.", "Build report card", "Grading the code...", render_report),
}


def run_lab(kind: str, result, hinglish: bool):
    code = st.session_state.code
    if st.session_state.get("is_demo"):  # saved results for the sample code: instant
        name = demo_data.find_sample(code)
        saved = demo_data.demo_lab(name, kind) if name else None
        if saved is not None:
            return llm.ToolOutcome(ok=True, data=saved)
    if kind == "oop":
        concepts = st.session_state.get("oop_concepts") or labtools.OOP_CONCEPTS
        return llm.oop_refactor(code, result.language, concepts, hinglish)
    if kind == "tests":  # test the fixed version when there is one
        target = result.fixed_code if result.fixed_code.strip() else code
        return llm.generate_tests(target, result.language, hinglish)
    if kind == "bigo":
        return llm.analyze_complexity(code, result.language, hinglish)
    if kind == "interview":
        return llm.interview_questions(code, result.language, hinglish)
    return llm.quality_report(code, result.language, hinglish)


def render_lab_view(view: str, result, hinglish: bool) -> None:
    kind, blurb, button, spinner, renderer = LAB_VIEWS[view]
    st.caption(blurb)
    if kind == "oop":
        st.multiselect(
            "OOP concepts to apply", labtools.OOP_CONCEPTS, default=labtools.OOP_CONCEPTS,
            key="oop_concepts", label_visibility="collapsed",
            help="; ".join(f"{k}: {v}" for k, v in labtools.CONCEPT_HELP.items()),
        )
    if st.button(button, key=f"gen_{kind}", type="primary"):
        with st.spinner(spinner):
            outcome = run_lab(kind, result, hinglish)
        if outcome.ok:
            st.session_state.lab[kind] = outcome.data
        else:
            st.error(outcome.error)
            if outcome.raw:
                with st.expander("Raw model output"):
                    st.text(outcome.raw)
    data = st.session_state.lab.get(kind)
    if data is not None:
        renderer(data, result.language)


with st.container(key="page"):
    rail, main = st.columns([0.85, 3.6], gap="large")

    # ----------------------------------------------------------------------
    # Left rail: roast level cards, language, Hinglish, privacy note
    # ----------------------------------------------------------------------
    with rail:
        md('<div class="rail-label">Roast level</div>')
        with st.container(key="level_nav"):
            level = st.radio(
                "Roast level",
                prompts.LEVELS,
                index=1,
                captions=[LEVEL_CAPTIONS[l] for l in prompts.LEVELS],
                key="level",
                label_visibility="collapsed",
            )
        md('<div class="rail-label rail-gap">Language</div>')
        language_choice = st.selectbox(
            "Language", [AUTO] + languages.SUPPORTED,
            key="language_choice", label_visibility="collapsed",
        )
        md('<div class="rail-label rail-gap">Hinglish mode</div>')
        hinglish = st.toggle(
            "Turn on", key="hinglish",
            help="Roast and explanations in Hinglish. Code stays in English.",
        )
        md(
            f"""
            <div class="tip-card"><b>Privacy + honesty</b>
            <span>Your code goes to {esc(llm.provider_label())}. No passwords or keys.
            Roast = jokes, bugs = real.</span></div>
            """
        )
        mini_slot = st.empty()  # filled at the end of the run so it always shows the newest score

    # ----------------------------------------------------------------------
    # Main column: slim hero, then code (left) and results (right)
    # ----------------------------------------------------------------------
    with main:
        md(
            """
            <div class="eyebrow">AI code review · C · C++ · Java · Python</div>
            <div class="hero-row"><span class="hero-title">ROAST IT</span>
            <span class="hero-sub">Paste code. Get a roast, the real bugs, a fix and a score, then ask follow-ups.</span></div>
            """
        )
        code_col = st.container()  # code on top ...
        out_col = st.container()  # ... roast below it

        # --- code card -------------------------------------------------------
        with code_col:
            md('<div class="section-label">Your code</div>')
            with st.container(key="code_card"):
                md(f'<div class="examples-label">{icon("flame", 18)} Use examples <span>instant demo, no waiting</span></div>')
                sample_cols = st.columns(len(samples.SAMPLES))
                for col, name in zip(sample_cols, samples.SAMPLES):
                    col.button(
                        name, key=f"sample_{name}", on_click=load_sample, args=(name,)
                    )
                if st.session_state.get("demo_note"):
                    st.caption("Hinglish needs a live roast: the code is loaded, now press Roast it.")
                code_input = st.text_area(
                    "Your code",
                    key="code_input",
                    height=300,
                    placeholder="Paste up to 500 lines of C, C++, Java or Python here...",
                    label_visibility="collapsed",
                )
                guess_col, btn_col = st.columns([1, 1], vertical_alignment="center")
                with guess_col:
                    if code_input.strip() and language_choice == AUTO:
                        guess = languages.detect_language(code_input)
                        md(f'<span class="pill white">Looks like: {esc(guess or "not sure yet")}</span>')
                with btn_col:
                    roast_clicked = st.button("Roast it 🔥", type="primary", key="roast_btn")

        # --- results card ------------------------------------------------------
        with out_col:
            md('<div id="results-anchor" class="section-label">Your roast</div>')
            with st.container(key="result_card"):
                if roast_clicked:
                    lines = len(code_input.splitlines())
                    if not code_input.strip():
                        st.warning("Paste some code first.")
                    elif lines > MAX_LINES:
                        st.warning(
                            f"That is {lines} lines. Please keep it under {MAX_LINES} so the "
                            "roast stays fast."
                        )
                    elif (
                        (demo_name := demo_data.find_sample(code_input))
                        and not hinglish
                        and language_choice in (AUTO, demo_data.demo_roast(demo_name, level).language)
                    ):
                        show_demo(demo_name, level)  # same sample, so no model call is needed
                    else:
                        chosen = None if language_choice == AUTO else language_choice
                        with st.spinner("Heating up the roast..."):
                            outcome = llm.roast_code(code_input, level, hinglish, language=chosen)
                        if outcome.ok:
                            st.session_state.result = outcome.result
                            st.session_state.code = code_input
                            st.session_state.messages = []  # new code, new chat
                            st.session_state.lab = {}  # lab results belong to one roast
                            st.session_state.view = V_ROAST  # jump to the roast
                            st.session_state.scroll_to_results = True
                            st.session_state.is_demo = False
                            history.add_entry(
                                st.session_state.session_id,
                                outcome.result.language,
                                level,
                                outcome.result.score,
                            )
                        else:
                            st.error(outcome.error)
                            if outcome.raw:
                                with st.expander("Raw model output"):
                                    st.text(outcome.raw)

                result = st.session_state.result
                if result is None:
                    md(
                        f"""
                        <div class="empty-state">
                          <div class="empty-flame">{icon("flame", 40)}</div>
                          <div class="empty-title">Your roast lands here</div>
                          <div class="empty-sub">Pick a sample or paste your own code, then hit <b>Roast it</b>.
                          The score, bugs, fix and chat all show up right in this box.</div>
                        </div>
                        """
                    )
                else:
                    render_verdict(result)
                    st.session_state.setdefault("view", V_ROAST)
                    with st.container(key="view_nav"):
                        view = st.radio(
                            "View", VIEWS, key="view", horizontal=True,
                            label_visibility="collapsed",
                        )
                    if view == V_ASK:  # chat has its own fixed-height message area
                        render_chat_view(result, level, hinglish)
                    else:
                        with st.container(border=False, key="panel"):
                            if view == V_ROAST:
                                render_roast_view(result)
                            elif view == V_BUGS:
                                render_bugs_view(result)
                            elif view == V_FIX:
                                render_fixed_view(result)
                            elif view == V_HIST:
                                render_history_view()
                            else:
                                render_lab_view(view, result, hinglish)
                    st.download_button(
                        "⬇ Download report", key="dl_report", mime="text/markdown",
                        data=build_report(result, st.session_state.code, st.session_state.lab, level),
                        file_name=f"roast-report-{result.language.lower().replace('+', 'p')}.md",
                        help="Saves the roast, bugs, fixed code and any lab results you generated.",
                    )

# --------------------------------------------------------------------------
# After the page is drawn: scroll to the roast, and fill the score summary in the left panel
# --------------------------------------------------------------------------
if st.session_state.pop("scroll_to_results", False):
    scroll_js = """<script>
    const el = window.parent.document.getElementById('results-anchor');
    if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
    </script>"""
    if hasattr(st, "iframe"):  # newer Streamlit
        st.iframe(scroll_js, height=1)
    else:  # older Streamlit
        import streamlit.components.v1 as components

        components.html(scroll_js, height=0)

scores = history.history_frame(st.session_state.session_id)["Score"].tolist()
with mini_slot.container():
    if scores:
        md(
            f"""
            <div class="mini-card"><b>Your scores</b>
            <span>Last {scores[-1]}/10 · Best {max(scores)}/10 · {len(scores)} roast{"s" if len(scores) != 1 else ""}</span></div>
            """
        )
