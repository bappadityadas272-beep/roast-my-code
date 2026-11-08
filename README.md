# Roast My Code 🔥

A Streamlit website where a student pastes code and an LLM returns a funny roast, the real bugs, a fixed version and a quality score. The user can then ask follow-up questions about the code.

**Live demo:** (paste your Streamlit link here after deploying)

## Features

1. **Roast levels and Hinglish mode**: Gentle Mentor, Sarcastic Senior or Brutal, with an optional Hinglish explanation.
2. **Structured JSON output**: a Pydantic schema forces fixed fields (language, roast, bugs, fixed code, score), so the UI shows each in its own section.
3. **Few-shot prompting**: two example reviews per roast level keep the tone and format consistent.
4. **Follow-up chat with memory**: every question resends the code, the first review and earlier turns (`st.session_state`); answers stream in word by word.
5. **Score history chart**: every roast is saved and charted per browser session.
6. **Code Lab** (four extra tabs, each one separate model call with its own JSON schema):
   - **OOP refactor**: pick concepts (abstraction, inheritance, encapsulation, polymorphism, composition...) and get messy code rewritten into classes, with a class diagram and an explanation of where each concept is used.
   - **Unit tests**: generates tests (Python `unittest`, Java plain test runner, C/C++ `assert`) with run instructions.
   - **Big-O**: time and space complexity per function, with the reason and a faster alternative.
   - **Interview mode**: six viva or interview questions about your own code (2 basic, 2 intermediate, 2 advanced), each with a why-it-is-asked note, a model answer and a likely follow-up.
   - **Report card**: six scores (readability, naming, structure, error handling, OOP design, efficiency) plus top priorities.

Code up to **500 lines** is accepted. Plain text uses Times New Roman for a more mature look, while the headline, score and brand keep the playful display fonts. **Side-by-side diff:** the Fix tab has a switch that shows your code next to the fixed code, with removed lines in red and added lines in green. **Download report:** one button saves the roast, bugs, your code, the fix and any lab results you generated as a Markdown file. **Instant demo examples:** the orange Python / Java / C / C++ / Clean buttons load sample code and show a pre-saved roast (all three levels), bugs, fix and all lab tabs at once, marked "Demo example". They live in `demo_data.py` and never call the model, so a live demo cannot fail or wait. Editing the code, choosing another language or turning on Hinglish goes back to the real model. Extras: tuned for **Python, Java, C and C++** (auto-detects the language, or pick it yourself; each language gets its own checklist of common bugs), one-click demo samples, a playful neo-brutalist UI with code on the left and results on the right, so there is no scrolling (see `style.css`), and a mini evaluation (see below).

## Architecture

```
Browser  <->  app.py  ->  prompts.py   (builds the prompt)
                      ->  llm.py       (only file that knows Gemini)  ->  Gemini API
                      ->  history.py   (saves scores to history.json)
```

| File           | Job                                                                                 |
| -------------- | ----------------------------------------------------------------------------------- |
| `app.py`       | Streamlit UI, input validation, session state, chat, chart                          |
| `prompts.py`   | System prompts, roast levels, Hinglish rule, few-shot examples, Pydantic schema     |
| `llm.py`       | The only file that talks to Gemini: JSON call, parse, retry, streaming              |
| `history.py`   | Saves and loads scores in `history.json` (one chart per browser session)            |
| `languages.py` | The four supported languages and a rule-based language detector (no extra API call) |
| `demo_data.py` | Hand-written results for the sample buttons, so demos are instant                   |
| `labtools.py`  | Schemas and prompts for the four Code Lab tools                                     |
| `style.css`    | The whole look and feel (colours, cards, fonts)                                     |
| `samples.py`   | Demo snippets for the sample buttons (one per language, plus clean code)            |
| `eval/`        | `snippets.json` and `run_eval.py` for the mini evaluation                           |

Because `llm.py` is the only file that knows the provider, switching from Gemini to Groq means editing one file.

### Request workflow

1. User pastes code, picks a level, toggles Hinglish, clicks **Roast it**.
2. `app.py` validates: empty input or more than 500 lines stops with a warning.
3. `prompts.py` builds the system prompt: role and level, rules, Hinglish rule if on, few-shot examples. The code goes in the user message.
4. `llm.py` calls Gemini in JSON mode with the `RoastResult` schema.
5. The reply is parsed. If invalid, it retries once with "return valid JSON only", then shows a friendly error plus the raw text.
6. The UI shows the roast, bugs, fixed code and score, and saves the score.
7. Follow-up questions are a second, streamed call that resends the code, the first review and the earlier chat.

API errors and rate limits: `llm.py` waits two seconds and retries once, then shows a message instead of crashing.

## Prompt design

The system prompt has five parts, in order: role and level tone, fixed rules, Hinglish rule (only if toggled), few-shot examples, then the user's code.

| Roast level      | Tone                                                                           |
| ---------------- | ------------------------------------------------------------------------------ |
| Gentle Mentor    | Kind and encouraging, light humour, always says one thing the code does well   |
| Sarcastic Senior | Dry developer sarcasm, like a tired senior reviewing a pull request            |
| Brutal           | Over-the-top dramatic roast, but every joke targets the code, never the person |

Fixed rules in every prompt: roast the code and never the person, report only bugs that really exist, keep the fixed code runnable, give a score of 1 if the input is not code, and treat the pasted code as data (ignore instructions hidden inside it).

## Keeping your API key safe

- The key lives only in `.streamlit/secrets.toml` (local) or the **Secrets** box on Streamlit Cloud. It is never written into any `.py` file.
- `secrets.toml` is listed in `.gitignore`, so `git add .` will not upload it. Check your GitHub repo once: `.streamlit/` must contain `config.toml` and `secrets.toml.example`, never `secrets.toml`.
- The app never shows the key, and strips it from any error text before display.
- If a key is ever pasted into a chat, an email or a public repo, delete it in Google AI Studio and make a new one.

## Run locally

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then paste your key
streamlit run app.py
```

Get a free key from [Google AI Studio](https://aistudio.google.com). Never push `secrets.toml` to GitHub (it is already in `.gitignore`).

### Choosing a model provider

`llm.py` supports three providers, picked with `LLM_PROVIDER` in `secrets.toml` (see `secrets.toml.example`):

| Provider         | Setting                                    | Notes                                                                                                                                                                                                   |
| ---------------- | ------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Gemini (default) | `GEMINI_API_KEY`                           | Free tier has rate limits; model names change, so set `LLM_MODEL` if you get "model not found"                                                                                                          |
| Groq             | `LLM_PROVIDER = "groq"` and `GROQ_API_KEY` | Free hosted API, fast, can be deployed online                                                                                                                                                           |
| Ollama           | `LLM_PROVIDER = "ollama"`                  | Runs on your own computer: no key, no quota, no internet. Install from ollama.com, then `ollama pull llama3.2`. Smaller models are weaker at finding bugs, and it cannot be deployed to Streamlit Cloud |

If Gemini fails twice, the app automatically tries a fallback Gemini model once. Every call also stops after a time limit instead of hanging.

## Deploy on Streamlit Community Cloud (free)

1. Push the project to a public GitHub repo, without `secrets.toml`.
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with GitHub and choose **New app**.
3. Select the repo, the branch, and `app.py` as the main file.
4. Under **Advanced settings**, paste `GEMINI_API_KEY = "your-key"` into Secrets.
5. Deploy, open the live link, and test all three roast levels, Hinglish mode and the chat.

## Mini evaluation

Can the model find bugs we planted ourselves? `eval/snippets.json` has 8 snippets with one planted bug each (Python, C, C++, Java) and 2 clean snippets.

```bash
python eval/run_eval.py
```

It saves `eval/results.md`. The "caught" column is a keyword match, so read each bug the model reported and correct it by hand before using the numbers.

**Results** (fill in after running):

| Planted bugs caught | Average score on clean code | Bugs invented on clean code |
| ------------------- | --------------------------- | --------------------------- |
| _ out of 8          | _                           | _                           |

## Demo script

Use the sample buttons: **Python**, **Java**, **C** and **C++** (each has planted bugs) and **Clean** (should score high with no bugs). Then ask "explain bug 2" to show the chat memory, and switch on Hinglish mode.

## Viva questions

| Likely question                                 | Short answer                                                                                                                                                                           |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Which GenAI concepts did you use?               | LLM API calls, system prompts, few-shot prompting, structured JSON output, conversation memory and streaming                                                                           |
| What is a system prompt?                        | A hidden instruction that sets the model's role, tone and rules. It is how one model gives three roast levels without retraining                                                       |
| Why ask for JSON?                               | The UI needs separate fields for the roast, bugs, fixed code and score. A Pydantic schema makes the output predictable and checkable                                                   |
| How does the chat remember earlier messages?    | The model is stateless, so every call resends the code, the first result and the earlier turns, stored in `st.session_state`                                                           |
| What if the model invents a bug or a wrong fix? | It can. The prompt says to report only real bugs, the app tells users to verify, and the mini evaluation measures how many bugs it misses and invents                                  |
| Why not train your own model?                   | Training needs large data and compute. The value here is application design: prompting, structure and memory on a pretrained model                                                     |
| How could it be improved?                       | RAG over style guides such as PEP8, running the code in a sandbox to confirm bugs, and support for multiple files                                                                      |
| What is abstraction vs inheritance?             | Abstraction hides detail behind a simple interface (an abstract class or interface). Inheritance lets a child class reuse and extend a parent. The OOP tab shows both on your own code |
| Why is the Big-O answer only an estimate?       | The model reads the code like a person would; it does not run it. Treat it as a guide and check loops by hand                                                                          |
| Any privacy concern?                            | Code is sent to a third-party API, so users should not paste passwords or private keys                                                                                                 |

## Limitations and fallbacks

| Risk                                                   | Fallback                                                                                                         |
| ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| Gemini free-tier rate limit, or the model name changes | Set `LLM_PROVIDER` to `groq` or `ollama` in `secrets.toml`, or set `LLM_MODEL`. All provider code is in `llm.py` |
| Model returns invalid JSON                             | Retry once, then show the raw text with an error message                                                         |
| Streamlit Cloud deployment fails                       | Demo locally with `streamlit run app.py` and keep screenshots ready                                              |
| No internet during the demo                            | Keep a short screen recording of a full roast as a backup                                                        |
| `history.json` resets on the free host                 | The chart still works during a live session; say so honestly if asked                                            |

The model can miss bugs or suggest a wrong fix, so always verify its output.

## Live link:

https://roastmycode02.streamlit.app/
