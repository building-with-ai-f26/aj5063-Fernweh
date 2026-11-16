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
