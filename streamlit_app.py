"""
AIChemist — Streamlit Cloud entrypoint (Python).

Deploy: push this repo to GitHub → https://share.streamlit.io → New app →
select branch, main file `streamlit_app.py`.

Secrets (Streamlit Cloud → App settings → Secrets):
  ANTHROPIC_API_KEY = "sk-ant-..."

Optional:
  ANTHROPIC_MODEL = "claude-3-5-sonnet-20241022"

Without a key, AI Rebalance uses the built-in simulation only.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

import pandas as pd
import streamlit as st

from streamlit_claude_client import goal_coach_reply, whatif_reply
from streamlit_rebalance import SCENARIO_PROMPTS, run_rebalance, sum_by_type

st.set_page_config(
    page_title="AIChemist",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- session defaults
for k, v in [
    ("logged_in", False),
    ("goal_step", 0),
    ("goal_main", ""),
    ("goal_years", 15),
    ("goal_comfort", "hold"),
    ("agent_messages", []),
    ("goal_claude_summary", None),
    ("goal_claude_source", None),
]:
    if k not in st.session_state:
        st.session_state[k] = v

FINANCIAL_RE = re.compile(
    r"\b(portfolio|rebalanc|market|stock|mutual|fund|invest|withdraw|inflation|bond|equity|"
    r"risk|allocat|tax|scenario|what\s*if|drop|crash|yield|dividend|sip|etf|cash|retire|goal|"
    r"macro|interest|recess|volatil|loss|gain|percent|apy|return|asset|diversif|bear|bull|"
    r"correction|expense|capital\s*gain|savings|debt|pension|nominee|lumpsum|index|sector|"
    r"gold|commod|rupee|inr)\b",
    re.I,
)
OFF_TOPIC_RE = re.compile(
    r"\b(recipe|cook|weather|joke|poem|python|javascript|code|debug|movie|game|sports|"
    r"football|cricket)\b",
    re.I,
)

SAMPLE_ROWS = [
    {
        "name": "Sample stock A (placeholder)",
        "type": "stock",
        "value": 42000,
        "risk": "high",
    },
    {
        "name": "Sample stock B (placeholder)",
        "type": "stock",
        "value": 18000,
        "risk": "medium",
    },
    {
        "name": "Diversified equity mutual fund (placeholder)",
        "type": "mutual_fund",
        "value": 68000,
        "risk": "medium",
    },
    {
        "name": "Balanced mutual fund (placeholder)",
        "type": "mutual_fund",
        "value": 32000,
        "risk": "low",
    },
    {
        "name": "Liquid / cash-style mutual fund (placeholder)",
        "type": "cash_or_liquid",
        "value": 22000,
        "risk": "low",
    },
]

SCENARIO_OPTIONS = [
    ("market-drop", "Market drop (~20%)"),
    ("high-inflation", "High inflation"),
    ("planned-withdrawal", "Withdraw ~20% next year"),
    ("income-risk", "Lose income ~6 months"),
    ("timeline-sooner", "Need money sooner"),
]


def get_api_key() -> str | None:
    try:
        return st.secrets.get("ANTHROPIC_API_KEY") or None
    except Exception:
        return None


def sync_anthropic_env_from_secrets() -> None:
    """So streamlit_claude_client picks up ANTHROPIC_MODEL from Cloud secrets."""
    try:
        m = st.secrets.get("ANTHROPIC_MODEL")
        if m:
            os.environ["ANTHROPIC_MODEL"] = str(m)
    except Exception:
        pass


def get_goal_profile() -> dict[str, Any] | None:
    raw = st.session_state.get("goal_saved")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def login_screen() -> None:
    st.title("AIChemist")
    st.caption("Educational simulation — not financial advice.")
    u = st.text_input("Username", key="login_u")
    p = st.text_input("Password", type="password", key="login_p")
    if st.button("Log in", type="primary"):
        if u.strip().lower() == "admin" and p == "admin":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Use username **admin** and password **admin** for this demo.")


def page_portfolio() -> None:
    st.header("Portfolio")
    st.write("Illustrative dashboard — same spirit as the web demo.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Current value (demo)", "₹1.68 L")
    c2.metric("1 day change", "₹-1,529", delta="-0.9%")
    c3.metric("All-time return (demo)", "+₹36,239", delta="8.7% p.a.")
    chart = pd.DataFrame(
        {
            "Month": pd.date_range("2021-01-01", periods=24, freq="ME"),
            "Value": [42 + i * 2.1 + (i % 3) for i in range(24)],
        }
    )
    st.subheader("Performance (sample)")
    st.line_chart(chart.set_index("Month"))


def _guardrail_bullets() -> str:
    return (
        "- I only answer **money and portfolio** questions in simple language.\n"
        "- Try a **what if** about markets, inflation, withdrawals, or saving for a goal.\n"
        "- Example: *What if the market drops by 20%?*"
    )


def _greeting_bullets() -> str:
    return (
        "- Ask any **what-if** about investing in plain words.\n"
        "- Answers show as **bullet points** so they’re easy to scan.\n"
        "- For a full practice rebalance, open **AI Rebalance**.\n"
        "- Switch to **Guided goal-setting** for a short questionnaire + AI summary."
    )


def _append_whatif_response(user_text: str, prior_history: list[tuple[str, str]]) -> None:
    """Append assistant reply; prior_history = messages before this user turn (excludes current user)."""
    if OFF_TOPIC_RE.search(user_text) or (
        len(user_text.strip()) > 2 and not FINANCIAL_RE.search(user_text)
    ):
        st.session_state.agent_messages.append(("assistant", _guardrail_bullets()))
        st.session_state["_last_whatif_source"] = "guardrail"
        return
    if re.match(r"^(hi|hello|hey)\b", user_text, re.I) and len(user_text) < 40:
        st.session_state.agent_messages.append(("assistant", _greeting_bullets()))
        st.session_state["_last_whatif_source"] = "greeting"
        return

    key = get_api_key()
    sync_anthropic_env_from_secrets()
    reply, src = whatif_reply(key, user_text, prior_history)
    st.session_state.agent_messages.append(("assistant", reply))
    st.session_state["_last_whatif_source"] = src


def render_guided_goal_setting() -> None:
    """Wizard + Claude bullet summary (second tab on Agent page)."""
    st.subheader("Guided goal-setting")
    st.write("A few questions — then an **AI summary in bullet points** (Claude when configured).")

    step = st.session_state.goal_step
    if step == 0:
        st.write("We clarify **when** you need money and **how bumpy** a ride you can handle.")
        if st.button("Begin", key="g_begin"):
            st.session_state.goal_step = 1
            st.session_state.goal_claude_summary = None
            st.session_state.goal_claude_source = None
            st.rerun()
        return

    if step == 1:
        goal_labels = {
            "retirement": "Long-term / retirement",
            "home": "A large purchase",
            "emergency": "Safety net / emergency",
            "growth": "General long-term growth",
        }
        st.session_state.goal_main = st.radio(
            "What is this money mainly for?",
            list(goal_labels.keys()),
            format_func=lambda k: goal_labels[k],
            horizontal=False,
            key="g_main",
        )
        col1, col2 = st.columns(2)
        if col1.button("Back", key="g_b1"):
            st.session_state.goal_step = 0
            st.rerun()
        if col2.button("Next", key="g_n1"):
            st.session_state.goal_step = 2
            st.rerun()
        return

    if step == 2:
        years = st.slider(
            "Roughly when will you need most of this money? (years)",
            1,
            40,
            st.session_state.goal_years,
            key="g_years",
        )
        st.session_state.goal_years = years
        col1, col2 = st.columns(2)
        if col1.button("Back", key="g_b2"):
            st.session_state.goal_step = 1
            st.rerun()
        if col2.button("Next", key="g_n2"):
            st.session_state.goal_step = 3
            st.rerun()
        return

    if step == 3:
        comfort_labels = {
            "sell": "Move mostly to safer options — sleep matters most.",
            "hold": "Hold steady and stick to the plan.",
            "buy": "Try to add a little if I can — I accept more bumpiness.",
        }
        st.session_state.goal_comfort = st.radio(
            "If your portfolio dropped about 20% in a tough year, you would…",
            list(comfort_labels.keys()),
            format_func=lambda k: comfort_labels[k],
            key="g_comfort",
        )
        col1, col2 = st.columns(2)
        if col1.button("Back", key="g_b3"):
            st.session_state.goal_step = 2
            st.rerun()
        if col2.button("Get my summary", type="primary", key="g_save"):
            c = st.session_state.goal_comfort
            risk = "Cautious" if c == "sell" else "Balanced" if c == "hold" else "Growth-minded"
            profile = {
                "mainGoal": st.session_state.goal_main,
                "years": st.session_state.goal_years,
                "comfort": c,
                "riskLabel": risk,
            }
            st.session_state.goal_saved = json.dumps(profile)
            sync_anthropic_env_from_secrets()
            key = get_api_key()
            with st.spinner("Generating your summary…"):
                summary, src = goal_coach_reply(key, profile)
            st.session_state.goal_claude_summary = summary
            st.session_state.goal_claude_source = src
            st.session_state.goal_step = 4
            st.rerun()
        return

    st.success("Here’s your saved profile and AI summary.")
    st.json(json.loads(st.session_state.goal_saved))
    src = st.session_state.get("goal_claude_source") or "fallback"
    st.caption(f"Summary source: **{'Claude API' if src == 'claude' else 'Built-in template'}**")
    st.markdown(st.session_state.get("goal_claude_summary") or "")
    if st.button("Start over", key="g_reset"):
        st.session_state.goal_step = 0
        st.session_state.goal_claude_summary = None
        st.session_state.goal_claude_source = None
        st.rerun()


def page_agent() -> None:
    st.header("Agent")
    st.caption(
        "Both areas use the **Claude API** when `ANTHROPIC_API_KEY` is set in Streamlit secrets; "
        "otherwise you get clear bullet templates."
    )
    sync_anthropic_env_from_secrets()

    tab_chat, tab_goals = st.tabs(["What-if chat", "Guided goal-setting"])

    with tab_chat:
        st.subheader("What-if chat")
        st.write("Ask portfolio **what-if** questions. Replies are **bullet points** for quick reading.")

        presets = [
            "What if the market drops by 20%?",
            "What if inflation stays high?",
            "What if I need to withdraw 20% next year?",
        ]
        st.write("**Quick prompts**")
        pc = st.columns(3)
        for i, p in enumerate(presets):
            if pc[i].button(p, key=f"preset_{i}"):
                prior = [
                    (r, c)
                    for r, c in st.session_state.agent_messages
                    if r in ("user", "assistant")
                ]
                st.session_state.agent_messages.append(("user", p))
                _append_whatif_response(p, prior)
                st.rerun()

        for role, content in st.session_state.agent_messages:
            with st.chat_message(role):
                st.markdown(content)

        src = st.session_state.get("_last_whatif_source")
        if src in ("claude", "fallback"):
            st.caption(
                f"Last AI reply: **{'Claude API' if src == 'claude' else 'Built-in template (add API key for Claude)'}**"
            )

        if prompt := st.chat_input("Ask a what-if question…"):
            prior = [
                (r, c)
                for r, c in st.session_state.agent_messages
                if r in ("user", "assistant")
            ]
            st.session_state.agent_messages.append(("user", prompt))
            _append_whatif_response(prompt, prior)
            st.rerun()

        if st.button("Clear chat history"):
            st.session_state.agent_messages = []
            st.session_state.pop("_last_whatif_source", None)
            st.rerun()

    with tab_goals:
        render_guided_goal_setting()


def page_rebalance() -> None:
    st.header("AI Rebalance (simulation)")
    st.warning("**Educational simulation — not financial advice.** No real trades.")

    if "rebalance_df" not in st.session_state:
        st.session_state.rebalance_df = pd.DataFrame(SAMPLE_ROWS)

    col_a, col_b = st.columns([3, 1])
    with col_b:
        if st.button("Load sample portfolio"):
            st.session_state.rebalance_df = pd.DataFrame(SAMPLE_ROWS)
            st.rerun()

    edited = st.data_editor(
        st.session_state.rebalance_df,
        num_rows="dynamic",
        column_config={
            "name": st.column_config.TextColumn("Asset name"),
            "type": st.column_config.SelectboxColumn(
                "Type",
                options=["stock", "mutual_fund", "cash_or_liquid"],
                required=True,
            ),
            "value": st.column_config.NumberColumn("Value (₹)", min_value=0, format="%d"),
            "risk": st.column_config.SelectboxColumn(
                "Risk",
                options=["low", "medium", "high"],
                required=True,
            ),
        },
        hide_index=True,
        key="holdings_editor",
    )
    st.session_state.rebalance_df = edited

    scenario_labels = dict(SCENARIO_OPTIONS)
    scenario_id = st.selectbox(
        "What-if scenario",
        [x[0] for x in SCENARIO_OPTIONS],
        format_func=lambda x: scenario_labels[x],
    )
    st.caption(SCENARIO_PROMPTS.get(scenario_id, ""))

    rows = edited.dropna(how="all")
    rows = rows[rows["name"].astype(str).str.strip() != ""]
    rows = rows[rows["value"].fillna(0) > 0]

    portfolio: list[dict[str, Any]] = []
    for _, r in rows.iterrows():
        portfolio.append(
            {
                "name": str(r["name"]).strip(),
                "type": str(r["type"]),
                "value": float(r["value"]),
                "risk": str(r["risk"]),
            }
        )

    cur = sum_by_type(portfolio) if portfolio else None
    if cur:
        st.subheader("Current allocation (by type)")
        st.bar_chart(
            pd.DataFrame(
                {
                    "bucket": ["Stocks", "Mutual funds", "Cash / liquid"],
                    "percent": [
                        cur["stocks"],
                        cur["mutualFunds"],
                        cur["cashOrLiquidFunds"],
                    ],
                }
            ).set_index("bucket")
        )

    if st.button("Get AI recommendation", type="primary"):
        if not portfolio:
            st.error("Add at least one holding with a name and positive value.")
        else:
            with st.spinner("Thinking…"):
                try:
                    key = get_api_key()
                    goal = get_goal_profile()
                    result = run_rebalance(portfolio, scenario_id, goal, key)
                    st.session_state.rebalance_result = result
                except Exception as e:
                    st.error(str(e))
            st.rerun()

    res = st.session_state.get("rebalance_result")
    if res:
        src = res.get("_source", "")
        st.info(f"Source: **{'Claude API' if src == 'claude' else 'Built-in simulation'}**")
        if res.get("_warning"):
            st.warning(res["_warning"])

        st.subheader(res.get("summary", ""))
        c1, c2 = st.columns(2)
        c1.write(f"**Health:** {res.get('portfolioHealth', '')}")
        c1.write(f"**Risk feel before:** {res.get('riskLevelBefore', '')}")
        c1.write(f"**Risk feel after:** {res.get('riskLevelAfter', '')}")

        ra = res.get("recommendedAllocation", {})
        c2.write("**Suggested mix (%)**")
        c2.bar_chart(
            pd.DataFrame(
                {
                    "bucket": ["Stocks", "Mutual funds", "Cash / liquid"],
                    "percent": [
                        ra.get("stocks", 0),
                        ra.get("mutualFunds", 0),
                        ra.get("cashOrLiquidFunds", 0),
                    ],
                }
            ).set_index("bucket")
        )

        st.subheader("Simulated moves")
        for a in res.get("actions", []):
            with st.expander(f"{a.get('action', '')} — {a.get('amountOrPercent', '')}"):
                st.write(f"**From** {a.get('fromAsset', '')} → **To** {a.get('toAsset', '')}")
                st.write(a.get("reason", ""))

        tn = res.get("transparencyNotes", {})
        st.subheader("Transparency (non-advisory)")
        st.write(f"**Costs:** {tn.get('costs', '')}")
        st.write(f"**Taxes:** {tn.get('taxes', '')}")
        st.write(f"**Risk in plain words:** {tn.get('riskExplanation', '')}")
        st.write(f"**Goals:** {tn.get('goalAlignment', '')}")
        st.write(res.get("beginnerExplanation", ""))
        st.error("This is an educational simulation, not financial advice.")


def main() -> None:
    if not st.session_state.logged_in:
        login_screen()
        return

    sync_anthropic_env_from_secrets()

    with st.sidebar:
        st.markdown("### Workspace")
        page = st.radio(
            "Navigate",
            ["Portfolio", "Agent", "AI Rebalance"],
            label_visibility="collapsed",
        )
        st.divider()
        if st.button("Log out"):
            st.session_state.logged_in = False
            st.rerun()
        st.caption("Demo login: admin / admin")

    if page == "Portfolio":
        page_portfolio()
    elif page == "Agent":
        page_agent()
    else:
        page_rebalance()


if __name__ == "__main__":
    main()
