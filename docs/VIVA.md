# Demo script (3 minutes)
1. Say what it is: "A web app where you paste C, C++, Java or Python code and Gemini roasts it, lists real bugs, fixes it, scores it, and answers follow-up questions."
2. Click an orange example (for example **C**, it has `gets()`). The result appears instantly (it is a saved demo example, so say so). Switch level to **Brutal** and press Roast to show the tone change. Show Bugs, Fix and the OOP, Tests, Big-O and Report tabs, all instant.
   Then paste your own code to show the real live model (takes a few seconds).
3. Switch on **Hinglish**, roast again, show the language change.
4. **Ask** tab: "why is gets dangerous?" then "and bug 2?" (shows memory).
5. Paste `docs/messy_demo.py` → **OOP** tab → pick Abstraction + Inheritance + Polymorphism → show the refactor and class diagram.
6. **Tests**, **Big-O**, **Report** tabs, one click each.
6b. **Fix** tab, switch on *Compare with my code* to show the side-by-side diff. **Interview** tab: show the viva questions it makes about your own code. Press **Download report** at the end.
7. **History** tab: the score chart.
8. End with the evaluation table and the limitations slide.

# Extra viva answers
| Question | Answer |
| --- | --- |
| How does the app talk to the model? | `llm.py` is the only file that knows the provider. It sends a system prompt plus the code and asks for JSON that must match a Pydantic schema |
| Why separate prompts for each tool? | Each tool has its own job and its own schema (OOP result, tests, complexity, report card), so each output is predictable |
| How do you stop prompt injection in pasted code? | The code is wrapped in `<code_to_review>` delimiters, the prompt says to treat it as data, and the closing tag inside user code is neutralised |
| How is the API key protected? | It lives only in `.streamlit/secrets.toml` (git-ignored) or the Streamlit Cloud Secrets box, and error messages are scrubbed of anything that looks like a key |
| What if the model is overloaded? | It retries, then falls back through a chain of models, and shows a friendly message instead of a crash |
| What are the OOP concepts the tool applies? | Abstraction, encapsulation, inheritance, polymorphism and composition |
| How does Interview mode work? | Same pattern as the other lab tools: a system prompt, the code wrapped in delimiters, and a JSON schema (question, level, why asked, model answer, follow-up) that Pydantic validates |
| How is the diff made? | Python's difflib compares the two codes line by line, and the app draws two columns with removed lines in red and added lines in green. No model call |
| Limits of the report card scores? | They are the model's opinion, not a measured metric, so they can differ between runs |
