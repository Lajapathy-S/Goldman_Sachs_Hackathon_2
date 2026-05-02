# AIChemist — Goldman Sachs Hackathon 2

Beginner-friendly portfolio demo: guided goals, AI rebalance simulation, and a financial chat-style agent. **Primary app for now: Streamlit** (easy local run and [Streamlit Community Cloud](https://share.streamlit.io)). The **React + Express** stack remains in the repo if you want a higher-polish UI later.

---

## Streamlit (recommended path)

**Local**

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Log in with **admin** / **admin**. **Tax Planning** (no login): U.S. federal demo for stocks & mutual funds—snapshots, opportunities, scenario slider, and ELI5 expanders.

Under **Agent**: *What-if chat* (bullet answers via Claude) and *Guided goal-setting* (questionnaire + Claude bullet summary). Optional: add `.streamlit/secrets.toml`:

```toml
ANTHROPIC_API_KEY = "your-key"
# ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"
```

Without a key, **AI Rebalance** uses the built-in simulation only.

**Streamlit Cloud:** connect this repo, main file `streamlit_app.py`, add the same secrets in the app settings.

---

## React + API (optional, later)

**Full stack dev** (Vite + Express proxy):

```bash
npm install
npm run dev
```

Set `ANTHROPIC_API_KEY` in `.env` at the project root for live Claude on `/api/rebalance`.

**Build frontend only:** `npm run build`

---

## Disclaimer

Educational simulation only — not financial advice. No real trades.
