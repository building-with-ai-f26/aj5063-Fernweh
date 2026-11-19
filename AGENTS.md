# AGENTS.md — Coding Agent Operating Manual

> Give this file to your coding agent and check that it is using these instructions. Keep the stack, commands, and ground rules current.

## 1. Project Overview
- **What this repo builds:** Fernweh, a virtual travel agent for friend groups that turns trip details and each friend's profile into restaurant and activity suggestions the group can vote on.
- **Primary user & core workflow:** The friend who organizes group trips, plus the friends who fill in profiles. See the living PRD in `docs/index.html`.
- **Tech stack:** Python standard library (`http.server`, `urllib`) for the backend, plain HTML/CSS/JavaScript for the frontend, OpenRouter for the AI model, GitHub Pages for the product page.
- **Project structure:**
  - `app.py` — backend server (Python standard library), serves the page and calls OpenRouter with the key from `.env`
  - `static/index.html` — app frontend (trip form + results page), served by `app.py`
  - `docs/` — public product page (GitHub Pages)
  - `trip_prototype.py`, `prototype.py` — earlier terminal throwaway prototypes (Fernweh and Mise), kept for reference

## 2. Commands
- **Install dependencies:** None — uses Python's standard library only.
- **Run locally:** Copy `.env.example` to `.env` and add your OpenRouter API key, then run `python3 app.py`. Open `http://localhost:8000` in your browser. Press Ctrl+C in the terminal to stop the server.
- **Run deterministic tests:** `[e.g., pytest / npm test]`
- **Run model evals:** `[e.g., python tests/eval.py]`

## 3. Non-Negotiable Engineering Rules
1. **Plan before coding:** Before touching multiple files, propose a brief plan and wait for approval.
2. **Small batches:** Make small, focused changes that can be reviewed and explained by a human in a single Pull Request.
3. **Explainability:** Avoid unnecessary abstractions or dependencies. Help the human builder understand the main components, what changed, why it matters, what could break, and how it was checked.
4. **Verify changes:** Run relevant checks. For a reproducible logic bug, use a failing test to demonstrate the fix when practical. Record manual checks and known limitations; follow the selected Build 4 evaluation track.
5. **Zero secrets in code:** Never hardcode API keys, tokens, or credentials. Always read from environment variables (`.env`) and update `.env.example` when new variables are needed.
6. **Stop when looping:** If a fix fails twice in a row, stop, summarize what failed, and ask the human before trying a third approach.

## 4. Shipping (Deploying to Render)

Fernweh deploys as a single Render **Web Service** on the Beginner lane — no Dockerfile, no `requirements.txt`, since it only uses Python's standard library.

1. Push your latest commits to GitHub (Render deploys from the repo).
2. Go to [render.com](https://render.com) and sign up / log in (GitHub login is fastest).
3. Click **New +** → **Web Service**, then connect your GitHub account and pick this repo (`aj5063-Fernweh`).
4. Fill in the service settings:
   - **Language/Runtime:** Python 3
   - **Build Command:** leave blank (there's nothing to install)
   - **Start Command:** `python3 app.py`
   - **Instance Type:** the free/Beginner tier
5. Under the **Environment** tab, add two environment variables (never commit these — they live only in Render's dashboard):
   - `OPENROUTER_API_KEY` — your real OpenRouter key
   - `OPENROUTER_MODEL` — the model you're using (e.g. the same value as in your local `.env`)
6. Click **Create Web Service**. Render builds and starts the app automatically, and sets its own `PORT` environment variable — `app.py` already reads `PORT` (defaulting to 8000 locally) and binds to `0.0.0.0`, so no code changes are needed per deploy.
7. Once it's live, Render gives you a public URL like `https://fernweh-xxxx.onrender.com`. Open it and run through the trip-planning flow once to confirm it works end to end.
8. **Beginner-lane heads-up:** the free tier spins the service down after a period of inactivity. The first request after it's been idle can take up to ~30–60 seconds to "wake up" — that's expected, not a bug.
9. To redeploy after future changes, just push to GitHub — Render auto-deploys on new commits to the connected branch.
