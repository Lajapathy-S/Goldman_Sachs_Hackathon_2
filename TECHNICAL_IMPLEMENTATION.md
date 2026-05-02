# AIChemist Technical Implementation Document

## 1) Overview

AIChemist is a portfolio-learning application with two implementations in the same repository:

- **Primary runtime (active):** Streamlit app (`streamlit_app.py`)
- **Secondary runtime (optional):** React + Express stack (`src/` + `server/`)

The Streamlit app is the currently deployed path and contains:

- Login-gated workspace shell
- Portfolio dashboard with synthetic metrics and visualizations
- REBA finance-only chat assistant
- Goal Coach guided questionnaire and AI summary

## 2) High-Level Architecture

### 2.1 Streamlit (Primary)

- **Entrypoint:** `streamlit_app.py`
- **UI helpers/charts:** `streamlit_portfolio_ui.py`
- **AI client + prompts:** `streamlit_claude_client.py`
- **Portfolio demo data + scoring:** `utils/portfolio_demo_metrics.py`
- **(Legacy in repo):** `streamlit_rebalance.py` (no longer exposed in current sidebar flow)

### 2.2 Optional React + API

- **Frontend app:** `src/` (React + Vite)
- **Backend API:** `server/index.js` (Express + Anthropic SDK + schema validation)
- This stack remains for future/polish use, but Streamlit is the active user path.

## 3) Technology Stack

### 3.1 Python / Streamlit

- `streamlit` (app framework)
- `anthropic` (Claude API)
- `pandas`, `numpy` (data shaping and synthetic series generation)
- `altair` (selected charts)
- Native Streamlit charts (`st.line_chart`, `st.bar_chart`) are used heavily for reliability.

### 3.2 TypeScript / React (optional)

- `react`, `react-router-dom`
- `recharts` (dashboard charts)
- `express`, `@anthropic-ai/sdk`, `zod` (API + validation)

## 4) Core Application Flows (Streamlit)

## 4.1 Authentication and Workspace Routing

- Login is session-based (`st.session_state.logged_in`).
- Demo credentials: `admin / admin`.
- Main sidebar navigation currently includes:
  - `portfolio`
  - `Agents`

Routing is handled in `main()` inside `streamlit_app.py`.

## 4.2 Portfolio Page

Implemented in `page_portfolio()`:

- Uses synthetic portfolio holdings and performance from `utils/portfolio_demo_metrics.py`
- Key sections:
  - Headline metrics (current value, 1-day move, all-time return/CAGR)
  - Performance chart (line chart)
  - Allocation chart (Altair donut; fallback available)
  - Transactions chart
  - Unrealized gain context
  - Returns by investment type
  - Portfolio health score meter (custom semicircle gauge)

### Portfolio Health Score

`portfolio_health_score()` computes score `0–100` based on:

- Diversification factor
- Allocation balance vs target stock mix
- Concentration penalty
- Growth trend component (CAGR-based)

Label bands:

- `<35`: Bad
- `35–54`: Needs work
- `55–74`: Fair
- `>=75`: Good

## 4.3 REBA (Finance-Only Chat)

REBA behavior is enforced in two layers:

1. **Input guardrails** in `streamlit_app.py` using regex:
   - `FINANCIAL_RE` for in-scope finance intents
   - `OFF_TOPIC_RE` for disallowed categories
2. **Claude system prompt** in `streamlit_claude_client.py` (`WHATIF_SYSTEM`)
   - Finance-only scope
   - Bullet-point response structure
   - Transparency requirements (costs, tax implications, goal alignment, simple logic)

If Claude fails/unavailable, deterministic fallback bullets are returned.

## 4.4 Goal Coach

Goal Coach is a step-based conversation state machine (`goal_step`):

1. Goal selection
2. Horizon (years)
3. Risk comfort reaction
4. Summary + follow-up

Summary generation:

- Primary: `goal_coach_reply()` via Claude (`GOAL_COACH_SYSTEM`)
- Fallback: `_fallback_goal_bullets()`

Current design includes:

- Suggested now section
- Real market examples
- **US-oriented stock/fund examples by default**

## 5) AI Integration Details

## 5.1 Model Configuration

In `streamlit_claude_client.py`:

- Default model: `claude-sonnet-4-6`
- Overridable by `ANTHROPIC_MODEL`

## 5.2 Secrets and Environment

Expected secrets:

- `ANTHROPIC_API_KEY`
- optional `ANTHROPIC_MODEL`

`sync_anthropic_env_from_secrets()` mirrors secret model value into process env so helper clients use consistent model selection.

## 6) Visualization Implementation Notes

The project intentionally moved away from direct Plotly rendering due to intermittent blank-chart behavior in some environments.

Current approach:

- Prefer native Streamlit charts where possible
- Use Altair where needed
- For custom gauge, use `streamlit.components.v1.html(...)` with SVG
- Provide fallback behavior when Altair is unavailable (`alt = None`)

This improves Cloud/runtime robustness while preserving visual fidelity.

## 7) Optional React + Express Path

The optional stack contains:

- Protected routes for dashboard, agents, goals, rebalance (`src/App.tsx`)
- Express endpoint `/api/rebalance` that:
  - validates request payload
  - calls Claude for JSON response
  - parses/validates output schema
  - falls back to deterministic mock output on failures

This path is not the primary deployed flow right now.

## 8) Data Model Summary

### Portfolio Demo Metrics (`utils/portfolio_demo_metrics.py`)

Key outputs:

- `snapshot()`: invested/current/day change/CAGR/unrealized splits
- `performance_monthly()`: synthetic monthly series
- `allocation_by_asset()`, `allocation_by_investment_type()`
- `transactions_annual()`
- `returns_by_type(duration_key)`
- `portfolio_health_score()`

### Rebalance (legacy streamlit module + optional Node API)

Canonical rebalance response fields include:

- `recommendedAllocation`
- `actions`
- `transparencyNotes`
- `beginnerExplanation`

## 9) Guardrails and Safety

- Finance-only topic enforcement in REBA
- Off-topic refusal template
- "No guaranteed returns" language in prompts
- Educational/simulation framing retained in multiple user-visible messages
- No execution of real trades

## 10) Deployment

### Streamlit Cloud (recommended)

1. Connect repo in Streamlit Cloud
2. Main file: `streamlit_app.py`
3. Add secrets:
   - `ANTHROPIC_API_KEY`
   - optional `ANTHROPIC_MODEL`

### Local Streamlit

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### Local Optional React/API

```bash
npm install
npm run dev
```

## 11) Known Constraints / Trade-offs

- Portfolio data is synthetic and static (not live market feed)
- Goal and chat recommendations are advisory-style examples, not suitability-checked recommendations
- Custom gauge is rendered via embedded SVG component; visual behavior depends on browser rendering support
- Two app stacks in one repo can create drift if both are evolved simultaneously

## 12) Suggested Next Engineering Steps

- Add automated tests for:
  - REBA guardrail routing
  - Goal Coach step transitions
  - Portfolio health scoring outputs
- Externalize constants (regex, scoring weights, copy) into config modules
- Add live market data abstraction layer (with caching + provider fallback)
- Add observability for AI failures and fallback frequency
- Introduce typed response schemas for Streamlit-side AI responses similar to Node-side validation

