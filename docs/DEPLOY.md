# Deploy checklist (Windows, about 20 minutes)

## A. Test locally first
1. Open Command Prompt in the project folder (the one containing `app.py`).
2. `python -m pip install -r requirements.txt`
3. `python -m streamlit run app.py`
4. Paste `docs/messy_demo.py` and press **Roast it**. Then open each tab: Bugs, Fix, Ask, OOP, Tests, Big-O, Report. If a tab shows an error, copy the message (it never contains your key).

## B. Run the evaluation
1. `python eval\run_eval.py --delay 8`
2. Keep the printed table for the report and slides.

## C. Put the code on GitHub (the key must NOT go)
1. Check `.gitignore` lists `.streamlit/secrets.toml` (it does).
2. Create a new **public** repo on github.com named `roast-my-code`, with no README.
3. In the project folder:
   ```
   git init
   git add .
   git status
   ```
   Read the `git status` list: `secrets.toml` must NOT appear (`secrets.toml.example` is fine).
   ```
   git commit -m "Roast My Code"
   git branch -M main
   git remote add origin https://github.com/<your-username>/roast-my-code.git
   git push -u origin main
   ```
4. Open the repo on GitHub and confirm there is no `secrets.toml` file.

## D. Streamlit Community Cloud
1. Go to share.streamlit.io, sign in with GitHub, press **Create app**.
2. Repository `roast-my-code`, branch `main`, main file `app.py`.
3. Open **Advanced settings → Secrets** and paste:
   ```
   LLM_PROVIDER = "gemini"
   GEMINI_API_KEY = "your key here"
   ```
4. Deploy. The first build takes a few minutes. Paste the live link into `README.md`.

## E. Before you submit
- Take screenshots: home page, a roast, Bugs, Fix, Ask, History, OOP, Tests, Big-O, Report.
- Record a 2 minute backup video in case the internet or the quota fails during the demo.
- **Rotate your API key** (create a new one, delete the old one) because the old one was shared in chat.
