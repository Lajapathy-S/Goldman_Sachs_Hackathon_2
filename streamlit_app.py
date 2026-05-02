"""
AIChemist — Streamlit Cloud entrypoint (Python).

Deploy: push this repo to GitHub → https://share.streamlit.io → New app →
select branch, main file `streamlit_app.py`.

Secrets (Streamlit Cloud → App settings → Secrets):
  ANTHROPIC_API_KEY = "sk-ant-..."

Optional:
  ANTHROPIC_MODEL = "claude-sonnet-4-6"

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
    ("show_member_login", False),
    ("goal_step", 0),
    ("goal_main", "retirement"),
    ("goal_years", 15),
    ("goal_comfort", "hold"),
    ("agent_messages", []),
    ("goal_chat_messages", []),
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
    r"gold|commod|rupee|inr|budget|mortgage|401k|\bira\b|roth|forex|crypto|bitcoin|insurance|"
    r"financial|broker|trade|trading|fee|401\b|emergency\s*fund|refinance|loan|credit\s*score|"
    r"income|salary|net\s*worth|\bsave\b|saving|vacation|travel|trip|holiday|wedding|tuition|"
    r"529|college|university|rainy\s*day|nest\s*egg|piggybank|allowance)\b",
    re.I,
)
OFF_TOPIC_RE = re.compile(
    r"\b(recipe|cook|weather|joke|poem|python|javascript|code|debug|movie|game|sports|"
    r"football|cricket|homework|essay|chatgpt|politics|election|religion|medical|diagnose|"
    r"dating|porn|hack\s*into|malware)\b",
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



def _inject_login_page_css() -> None:
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
        header[data-testid="stHeader"] { display: none !important; }
        div[data-testid="stToolbar"] { display: none !important; }
        footer { visibility: hidden !important; height: 0 !important; }
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            max-width: 100% !important;
        }
        .main .block-container { padding-left: 0 !important; padding-right: 0 !important; }
        [data-testid="stSidebar"] { display: none !important; }
        [data-testid="collapsedControl"] { display: none !important; }
        .stApp, [data-testid="stAppViewContainer"] {
            background-color: #ffffff !important;
        }
        .gs-login-strip {
            background: #ffffff;
            padding: 28px 6vw 40px 6vw;
            margin: 0;
            border-top: 1px solid #e2e8f0;
        }
        .gs-member-card-title {
            font-family: "Source Sans 3", system-ui, sans-serif;
            font-size: 0.72rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #64748b;
            margin: 0 0 14px 0;
            font-weight: 600;
        }
        .gs-login-hint {
            font-family: "Source Sans 3", system-ui, sans-serif;
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 14px;
            line-height: 1.45;
        }
        .gs-login-nav details {
            display: inline-block;
            margin-right: 10px;
            vertical-align: top;
            position: relative;
        }
        /* Open panel stacks above siblings (named <details> closes others in group). */
        .gs-login-nav details[open] { z-index: 40; }
        .gs-login-nav details > summary {
            cursor: pointer;
            list-style: none;
            font-weight: 600;
            color: #1e293b;
        }
        .gs-login-nav details > summary::-webkit-details-marker { display: none; }
        .gs-login-nav .gs-dd-body {
            position: absolute;
            left: 0;
            top: 100%;
            z-index: 20;
            margin-top: 6px;
            padding: 10px 12px;
            min-width: 220px;
            max-width: 280px;
            background: #ffffff;
            border: 1px solid rgba(26, 26, 26, 0.15);
            border-radius: 4px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
            font-weight: 500;
            font-size: 0.82rem;
            line-height: 1.5;
            color: #334155;
        }
        .gs-login-nav .gs-plain {
            display: inline-block;
            margin-right: 12px;
            padding-top: 2px;
            font-weight: 600;
            color: #1e293b;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _login_hero_white_html() -> str:
    """Light hero — white background, navy typography (landing before member sign-in)."""
    return """
<div style="position:relative;margin:0;font-family:'Source Sans 3',system-ui,sans-serif;
  background:#ffffff;padding:48px 6vw 56px 6vw;min-height:42vh;border-bottom:1px solid #e2e8f0;">
  <div style="position:relative;z-index:2;max-width:min(640px,92vw);">
    <h1 style="
      font-family:'Libre Baskerville',Georgia,serif;
      font-size:clamp(1.75rem, 4vw, 2.65rem);
      font-weight:700;line-height:1.2;color:#0f172a;margin:0 0 20px 0;
      letter-spacing:-0.02em;
    ">
      Navigate markets, goals, and portfolio decisions with clarity
    </h1>
    <p style="
      font-family:'Source Sans 3',system-ui,sans-serif;
      font-size:1.05rem;line-height:1.65;color:#475569;
      margin:0 0 28px 0;max-width:540px;
    ">
      Educational tools for stocks and mutual funds — AI chat with guardrails, goal coaching, and rebalance simulations.
      Not investment advice.
    </p>
    <div style="
      display:inline-block;padding:12px 26px;
      background:#0f172a;color:#ffffff;
      font-size:0.9rem;font-weight:700;
      letter-spacing:0.04em;border-radius:2px;
    ">
      EXPLORE WORKSPACE
    </div>
  </div>
  <div aria-hidden="true" style="
    position:absolute;right:4vw;top:42%;transform:translateY(-50%);
    font-family:'Libre Baskerville',Georgia,serif;
    font-size:clamp(3.5rem, 14vw, 8rem);
    font-weight:700;color:rgba(15,23,42,0.06);
    line-height:0.85;user-select:none;
  ">AI</div>
</div>
"""


def login_screen() -> None:
    """Landing (white) first; member login form only after 'Member sign-in'."""
    _inject_login_page_css()

    st.markdown(
        '<div style="background:#a2b9d6;padding:28px 7vw 30px 7vw;border-bottom:1px solid rgba(26,26,26,0.1);">',
        unsafe_allow_html=True,
    )
    c_brand, c_nav, c_demo, c_btn = st.columns([1.5, 3.4, 0.65, 1.25], gap="small")
    with c_brand:
        st.markdown(
            '<p style="font-family:Georgia,serif;font-size:1.35rem;font-weight:700;color:#0f172a;margin:0;padding-top:4px;">AIChemist</p>',
            unsafe_allow_html=True,
        )
    with c_nav:
        st.markdown(
            """
            <div class="gs-login-nav" style="padding-top:4px;font-size:0.88rem;font-family:'Source Sans 3',system-ui,sans-serif;">
            <details name="aichemist-landing-nav">
              <summary>portfolio ▾</summary>
              <div class="gs-dd-body">
                <strong>Stocks</strong> — Demo equity positions, performance, and how they move the mix.<br/><br/>
                <strong>Mutual funds</strong> — Demo fund holdings and diversification in the sample portfolio.
              </div>
            </details>
            <details name="aichemist-landing-nav">
              <summary>agents ▾</summary>
              <div class="gs-dd-body">
                <strong>Guided goal setting</strong> — A short, chat-style flow that captures your goal, timeline,
                and comfort with risk, then summarizes trade-offs in plain language (educational only).
              </div>
            </details>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_demo:
        st.markdown(
            '<p style="margin:0;padding-top:10px;font-size:0.82rem;color:#334155;">Demo</p>',
            unsafe_allow_html=True,
        )
    with c_btn:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        if st.button("Member sign-in", key="login_open_member_panel", use_container_width=True):
            st.session_state.show_member_login = True
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state.show_member_login:
        st.markdown(_login_hero_white_html(), unsafe_allow_html=True)
        st.caption("Click **Member sign-in** above to open the demo login. Educational only — not financial advice.")
        return

    st.markdown('<div class="gs-login-strip">', unsafe_allow_html=True)
    b1, b2 = st.columns([1, 5])
    with b1:
        if st.button("← Back", key="login_back_landing"):
            st.session_state.show_member_login = False
            st.rerun()
    with b2:
        st.markdown("")
    c_left, c_right = st.columns([1.35, 1.0], gap="large")
    with c_left:
        st.markdown(
            """
            <p style="font-family:'Source Sans 3',system-ui,sans-serif;font-size:1rem;line-height:1.65;
            color:#334155;max-width:520px;margin:8px 0 0 0;">
            <strong style="color:#1e293b;">What you get after sign-in</strong><br/>
            Portfolio-style metrics, what-if chat with guardrails, goal coaching,
            and AI rebalance simulations — built for learning, not live trading.
            </p>
            """,
            unsafe_allow_html=True,
        )
    with c_right:
        st.markdown(
            '<p class="gs-member-card-title">Member access</p>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            with st.form("login_form", clear_on_submit=False):
                u = st.text_input("Username", key="login_u", placeholder="Username")
                p = st.text_input("Password", type="password", key="login_p", placeholder="Password")
                submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
                if submitted:
                    if u.strip().lower() == "admin" and p == "admin":
                        st.session_state.logged_in = True
                        st.session_state.show_member_login = False
                        st.rerun()
                    else:
                        st.error("Demo account: **admin** / **admin**.")
            st.markdown(
                '<p class="gs-login-hint">Educational simulation only — not financial or tax advice.</p>',
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def page_portfolio() -> None:
    from streamlit_portfolio_ui import (
        chart_donut,
        chart_lt_st,
        chart_performance,
        chart_transactions,
        inject_portfolio_dashboard_css,
        show_plotly_chart,
    )
    from utils.portfolio_demo_metrics import (
        allocation_by_asset,
        allocation_by_investment_type,
        filter_performance,
        performance_monthly,
        returns_by_type,
        snapshot,
        transactions_annual,
    )

    inject_portfolio_dashboard_css()
    snap = snapshot()
    invested = snap["invested"]
    current = snap["current"]
    day = snap["one_day_change"]
    day_pct = snap["one_day_pct"]
    gain = snap["all_time_gain"]
    cagr = snap["cagr_pct"]
    day_cls = "pf-neg" if day < 0 else "pf-pos"
    gain_cls = "pf-pos" if gain >= 0 else "pf-neg"

    st.markdown(
        f"""
        <div class="pf-wrap">
        <h1 style="font-family:Georgia,serif;color:#1a2b4b;font-size:2rem;margin:0 0 8px 0;">Portfolio</h1>
        <p class="pf-sub">All holdings (stocks + mutual funds), USD — illustrative sample only.</p>
        <div class="pf-metric-row">
          <div class="pf-metric-block">
            <div class="pf-metric-label">Current value</div>
            <div class="pf-metric-main">${current:,.0f}</div>
            <div class="pf-metric-side">${invested:,.0f} invested</div>
          </div>
          <div class="pf-metric-block">
            <div class="pf-metric-label">1 day</div>
            <div class="pf-metric-main {day_cls}">${day:,.0f} &nbsp; ({day_pct:+.2f}%)</div>
            <div class="pf-metric-side">Illustrative 1-day move — not live quotes</div>
          </div>
          <div class="pf-metric-block">
            <div class="pf-metric-label">All-time returns</div>
            <div class="pf-metric-main {gain_cls}">${gain:+,.0f}</div>
            <div class="pf-metric-side {gain_cls}">{cagr:.1f}% p.a. (sample CAGR)</div>
          </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    perf_full = performance_monthly()
    range_options = ["ALL", "YTD", "1M", "3M", "6M", "1Y", "3Y", "5Y"]
    col_left, col_right = st.columns([1.2, 1.0])

    with col_left:
        with st.container(border=True):
            st.markdown('<p class="pf-serif">Performance</p>', unsafe_allow_html=True)
            if hasattr(st, "segmented_control"):
                sel_range = st.segmented_control(
                    "Range",
                    range_options,
                    default="ALL",
                    key="pf_perf_range",
                    label_visibility="collapsed",
                )
            else:
                sel_range = st.selectbox("Range", range_options, index=0, key="pf_perf_range_sb")
            perf_df = filter_performance(perf_full, sel_range)
            if perf_df.empty or len(perf_df) < 2:
                perf_df = perf_full
            show_plotly_chart(chart_performance(perf_df), key="pf_perf_chart")
            st.caption("Sample performance path for the **combined** portfolio above (illustrative).")
            st.markdown(
                '<p class="pf-footlink">See performance details — explore scenarios in <strong>AI Rebalance</strong> →</p>',
                unsafe_allow_html=True,
            )

    with col_right:
        with st.container(border=True):
            st.markdown('<p class="pf-serif">Allocation</p>', unsafe_allow_html=True)
            alloc_mode = st.radio(
                "View",
                ["By holding", "By investment type"],
                horizontal=True,
                key="pf_alloc_unified",
                label_visibility="collapsed",
            )
            if alloc_mode == "By holding":
                st.caption("Each **ticker / fund symbol** in the sample book.")
                adf = allocation_by_asset()
            else:
                st.caption("**Stocks** vs **mutual funds** in the combined portfolio.")
                adf = allocation_by_investment_type()
            labels = adf["label"].tolist()
            values = [float(x) for x in adf["value"].tolist()]
            if not labels or not values or sum(abs(v) for v in values) < 1e-9:
                st.warning("No allocation data to chart.")
            else:
                show_plotly_chart(chart_donut(labels, values, title=None), key="pf_alloc_chart")
            st.markdown(
                '<p class="pf-footlink">See detailed breakdown — same demo holdings as portfolio metrics</p>',
                unsafe_allow_html=True,
            )

    t1, t2, t3 = st.columns(3)

    with t1:
        with st.container(border=True):
            st.markdown('<p class="pf-serif">Transactions</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="pf-sub" style="margin-top:-8px;">Amount invested annually, net of withdrawals (sample)</p>',
                unsafe_allow_html=True,
            )
            tx = transactions_annual()
            show_plotly_chart(chart_transactions(tx), key="pf_tx_chart")
            st.markdown(
                '<p class="pf-footlink">See all transactions — not available in this prototype</p>',
                unsafe_allow_html=True,
            )

    with t2:
        with st.container(border=True):
            st.markdown('<p class="pf-serif">Unrealized gains context</p>', unsafe_allow_html=True)
            ty = snap["as_of"].year
            st.markdown(
                f'<p class="pf-sub" style="margin-top:-8px;">CY {ty}: unrealized buckets (educational)</p>',
                unsafe_allow_html=True,
            )
            show_plotly_chart(
                chart_lt_st(snap["lt_unrealized_pl"], snap["st_unrealized_pl"], f"CY {ty}"),
                key="pf_ltst_chart",
            )
            st.caption(
                "Bars show **unrealized** long-term vs short-term P/L on holdings (educational split only)."
            )
            st.markdown(
                '<p class="pf-footlink">For practice moves, open <strong>AI Rebalance</strong> in the sidebar</p>',
                unsafe_allow_html=True,
            )

    with t3:
        with st.container(border=True):
            st.markdown('<p class="pf-serif">Returns by investment type</p>', unsafe_allow_html=True)
            dur = st.selectbox(
                "Duration",
                ["1 Day", "1 Week", "1 Month", "3 Month", "YTD"],
                index=0,
                key="pf_ret_dur",
                label_visibility="collapsed",
            )
            st.caption(f"Window: **{dur}** (illustrative move on sample weights)")
            ret_rows = returns_by_type(dur)
            for row in ret_rows:
                if row["in_portfolio"]:
                    chg = float(row["change"] or 0)
                    pct = float(row["pct"] or 0)
                    cls = "pf-neg" if chg < 0 else "pf-pos"
                    st.markdown(
                        f'<p style="margin:12px 0 4px 0;font-weight:600;color:#1a2b4b;">{row["name"]}</p>'
                        f'<p class="{cls}" style="margin:0;font-size:1.05rem;">'
                        f"${chg:,.0f} ({pct:+.2f}%) </p>"
                        f'<p style="margin:4px 0 0 0;font-size:0.82rem;color:#64748b;">'
                        f'Value ~ ${float(row["value"]):,.0f}</p>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<p style="margin:14px 0 4px 0;font-weight:600;color:#1a2b4b;">{row["name"]}</p>'
                        f'<p style="margin:0;color:#94a3b8;font-size:0.9rem;">Not in this sample portfolio</p>',
                        unsafe_allow_html=True,
                    )

    st.markdown(
        """
        <div class="pf-wrap pf-disclaimer">
        Illustrative data only — not financial, tax, or investment advice. Figures are tied to the hardcoded
        demo portfolio, include synthetic performance history and contributions, and are not live market prices.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _guardrail_bullets() -> str:
    return (
        "- **REBA** only answers **finance and investing** questions (money, markets, goals, risk, taxes at a high level).\n"
        "- I can’t help with coding, homework, sports, recipes, health, politics, or general chat.\n"
        "- Try a **what if** about markets, inflation, withdrawals, or saving for a goal.\n"
        "- Example: *What if the market drops by 20%?*"
    )


def _greeting_bullets() -> str:
    return (
        "- I’m **REBA** — ask any **finance or investing** question in plain words.\n"
        "- Replies are **bullet points** so they’re easy to scan.\n"
        "- For a full practice rebalance, open **AI Rebalance** in the sidebar.\n"
        "- Switch to **Goal coach (chat)** for a short questionnaire + summary."
    )


def _inject_gs_workspace_css() -> None:
    """Goldman-style steel-blue sidebar + institutional grays (logged-in shell)."""
    st.markdown(
        """
        <link href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@700&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #a2b9d6 0%, #98b0cd 100%) !important;
            border-right: 1px solid rgba(26, 26, 26, 0.12) !important;
            min-width: 300px !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown { color: #1a1a1a !important; }
        [data-testid="stSidebar"] .stRadio label { font-weight: 600 !important; font-family: 'Source Sans 3', system-ui, sans-serif !important; }
        [data-testid="stSidebar"] button {
            border: 1px solid #1a1a1a !important;
            color: #1a1a1a !important;
            background: rgba(255,255,255,0.35) !important;
        }
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > div,
        section.main, section.main > div {
            background-color: #ffffff !important;
        }
        .main .block-container {
            font-family: 'Source Sans 3', system-ui, sans-serif !important;
            background: #ffffff !important;
            color: #1a2b4b !important;
        }
        section.main p, section.main label, section.main span, section.main .stMarkdown p {
            color: #334155 !important;
        }
        section.main h1, section.main h2, section.main h3 {
            color: #1a1a1a !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important;
            border-color: #e2e8f0 !important;
        }
        [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
            color: #1a2b4b !important;
        }
        h1, h2, h3 { font-family: 'Libre Baskerville', Georgia, serif !important; color: #1a1a1a !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _inject_gs_messaging_css() -> None:
    """Chat + tabs on Agent page — same palette as GS header (#a2b9d6) and navy text."""
    st.markdown(
        """
        <style>
        .goal-coach-frame {
            max-width: 760px;
            margin: 0 auto;
            padding: 0 8px 12px 8px;
        }
        .goal-coach-frame [data-testid="stVerticalBlock"] > div { gap: 0.35rem; }
        .goal-composer {
            max-width: 760px;
            margin: 12px auto 0 auto;
            padding: 12px 14px;
            background: #f8fafc;
            border: 1px solid #a2b9d6;
            border-radius: 12px;
            box-shadow: 0 1px 8px rgba(26, 26, 26, 0.05);
        }
        .goal-coach-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #1a1a1a;
            margin-bottom: 8px;
            font-weight: 700;
        }
        [data-testid="stChatMessage"] {
            background-color: #ffffff !important;
            border: 1px solid #c5d4e8 !important;
            border-radius: 14px !important;
            box-shadow: 0 1px 4px rgba(162, 185, 214, 0.35) !important;
        }
        [data-testid="stChatInput"] textarea {
            border: 1px solid #a2b9d6 !important;
            border-radius: 10px !important;
            font-family: 'Source Sans 3', system-ui, sans-serif !important;
        }
        [data-testid="stTabs"] [aria-selected="true"] {
            color: #1a1a1a !important;
            font-weight: 700 !important;
            border-bottom-color: #1a1a1a !important;
        }
        [data-testid="stTabs"] button { font-family: 'Source Sans 3', system-ui, sans-serif !important; color: #4a5568 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


GOAL_COACH_WELCOME = (
    "Hi — I’m your **Goal coach**.\n\n"
    "I’ll ask **three short questions** about what you’re investing for, your **time horizon**, and how you’d react "
    "if markets got rough. Then I’ll give you a **plain-English summary** (bullet points).\n\n"
    "This is **educational only** — not personal financial advice.\n\n"
    "When you’re ready, tap **Start conversation** below."
)


def _goal_chat_guardrail() -> str:
    return (
        "- I stay in **money and goal** territory — investing, saving, risk, and time horizon.\n"
        "- I can’t help with general chit-chat, coding, recipes, or unrelated topics here.\n"
        "- Tap **Start conversation** to begin the questionnaire, or open **REBA** for market “what if” questions.\n"
        "- Everything here is **educational**, not a recommendation to buy or sell anything."
    )


def _goal_chat_finish_questionnaire_hint() -> str:
    return (
        "- I’m in the middle of your **goal questionnaire** — use the **options and buttons** just above to continue.\n"
        "- After your summary, you can use the **follow-up** field (finance topics only).\n"
        "- For open-ended “what if” questions, **REBA** works great too."
    )


def _goal_begin_conversation() -> None:
    st.session_state.goal_chat_messages.append(("user", "Let’s start the goal questionnaire."))
    st.session_state.goal_chat_messages.append(
        (
            "assistant",
            "**Question 1 of 3:** What is **this money mainly for**?\n\n"
            "Choose one option below, then tap **Next**.",
        )
    )
    st.session_state.goal_step = 1


def _goal_append_user_assistant(user_text: str, assistant_text: str) -> None:
    st.session_state.goal_chat_messages.append(("user", user_text))
    st.session_state.goal_chat_messages.append(("assistant", assistant_text))


def _goal_followup_reply(user_text: str) -> None:
    """After summary: money-only follow-ups using same guardrails as what-if."""
    prior = [
        (r, c)
        for r, c in st.session_state.goal_chat_messages[:-1]
        if r in ("user", "assistant")
    ]
    if OFF_TOPIC_RE.search(user_text) or (
        len(user_text.strip()) > 2 and not FINANCIAL_RE.search(user_text)
    ):
        st.session_state.goal_chat_messages.append(("assistant", _goal_chat_guardrail()))
        return
    if re.match(r"^(hi|hello|hey)\b", user_text, re.I) and len(user_text) < 40:
        st.session_state.goal_chat_messages.append(
            (
                "assistant",
                "- You’ve finished the goal questionnaire — nice work.\n"
                "- Ask a **what-if** about markets, inflation, or withdrawals in plain words.\n"
                "- I’ll answer in **bullet points** so it’s easy to scan.\n"
                "- Or switch to **REBA** for the same style without the goal recap.",
            )
        )
        return
    key = get_api_key()
    sync_anthropic_env_from_secrets()
    reply, _src, _err = whatif_reply(key, user_text, prior)
    st.session_state.goal_chat_messages.append(("assistant", reply))
    if _err:
        st.session_state["_goal_followup_api_error"] = _err
    else:
        st.session_state.pop("_goal_followup_api_error", None)


def _append_whatif_response(user_text: str, prior_history: list[tuple[str, str]]) -> None:
    """Append assistant reply; prior_history = messages before this user turn (excludes current user)."""
    t = user_text.strip()
    if not t:
        return
    if OFF_TOPIC_RE.search(user_text) or (
        len(t) > 2 and not FINANCIAL_RE.search(user_text)
    ):
        st.session_state.agent_messages.append(("assistant", _guardrail_bullets()))
        st.session_state["_last_whatif_source"] = "guardrail"
        st.session_state.pop("_last_whatif_api_error", None)
        return
    if re.match(r"^(hi|hello|hey)\b", user_text, re.I) and len(user_text) < 40:
        st.session_state.agent_messages.append(("assistant", _greeting_bullets()))
        st.session_state["_last_whatif_source"] = "greeting"
        st.session_state.pop("_last_whatif_api_error", None)
        return

    key = get_api_key()
    sync_anthropic_env_from_secrets()
    reply, src, api_err = whatif_reply(key, user_text, prior_history)
    st.session_state.agent_messages.append(("assistant", reply))
    st.session_state["_last_whatif_source"] = src
    if src == "claude":
        st.session_state.pop("_last_whatif_api_error", None)
    else:
        st.session_state["_last_whatif_api_error"] = api_err


def _goal_chat_pop_last_turn() -> None:
    for _ in range(2):
        if st.session_state.goal_chat_messages:
            st.session_state.goal_chat_messages.pop()


def render_guided_goal_setting() -> None:
    """ChatGPT-style goal coach with financial guardrails (Agent tab)."""
    if not st.session_state.goal_chat_messages:
        st.session_state.goal_chat_messages = [("assistant", GOAL_COACH_WELCOME)]

    goal_labels = {
        "retirement": "Retirement",
        "education": "Education",
        "home": "Home",
        "emergency": "Emergency fund",
    }
    comfort_labels = {
        "sell": "Move mostly to safer options — sleep matters most.",
        "hold": "Hold steady and stick to the plan.",
        "buy": "Try to add a little if I can — I accept more bumpiness.",
    }

    st.markdown('<div class="goal-coach-frame">', unsafe_allow_html=True)
    st.markdown(
        '<div class="goal-coach-badge">Goal coach · Educational only</div>',
        unsafe_allow_html=True,
    )
    st.caption("Chat-style flow with **money-only** guardrails — like a focused research assistant for goals.")

    for role, content in st.session_state.goal_chat_messages:
        with st.chat_message(role):
            st.markdown(content)

    step = st.session_state.goal_step

    st.markdown('<div class="goal-composer">', unsafe_allow_html=True)
    if step == 0:
        if st.button("Start conversation", type="primary", key="g_begin"):
            st.session_state.goal_claude_summary = None
            st.session_state.goal_claude_source = None
            st.session_state.pop("_gc_main_goal", None)
            st.session_state.pop("_gc_years", None)
            st.session_state.pop("g_comfort", None)
            _goal_begin_conversation()
            st.rerun()

    elif step == 1:
        keys = list(goal_labels.keys())
        if st.session_state.goal_main not in keys:
            st.session_state.goal_main = keys[0]
        st.radio(
            "What is this money mainly for?",
            keys,
            format_func=lambda k: goal_labels[k],
            horizontal=False,
            key="goal_main",
            label_visibility="visible",
        )
        col1, col2 = st.columns(2)
        if col1.button("Back", key="g_b1"):
            _goal_chat_pop_last_turn()
            st.session_state.pop("_gc_main_goal", None)
            st.session_state.goal_step = 0
            st.rerun()
        if col2.button("Next", key="g_n1"):
            # Lock choice: step-1 radio is unmounted on later steps; `goal_main` can revert to default.
            main_key = st.session_state.goal_main
            st.session_state["_gc_main_goal"] = main_key
            lbl = goal_labels[main_key]
            _goal_append_user_assistant(
                f"I’m mainly investing for: **{lbl}**.",
                "**Question 2 of 3:** Roughly **when** will you need most of this money?\n\n"
                "Set the **years** on the slider, then tap **Next**.",
            )
            st.session_state.goal_step = 2
            st.rerun()

    elif step == 2:
        years = st.slider(
            "Years until you need most of this money",
            1,
            40,
            st.session_state.goal_years,
            key="g_years",
        )
        st.session_state.goal_years = years
        col1, col2 = st.columns(2)
        if col1.button("Back", key="g_b2"):
            _goal_chat_pop_last_turn()
            st.session_state.pop("_gc_years", None)
            st.session_state.goal_step = 1
            st.rerun()
        if col2.button("Next", key="g_n2"):
            y = int(st.session_state.goal_years)
            st.session_state["_gc_years"] = y
            _goal_append_user_assistant(
                f"I’m thinking about a horizon of about **{y} years**.",
                "**Question 3 of 3:** If your portfolio dropped about **20%** in a tough year, what would you lean toward?\n\n"
                "Choose an option, then tap **Get my summary**.",
            )
            st.session_state.goal_step = 3
            st.rerun()

    elif step == 3:
        if "g_comfort" not in st.session_state:
            st.session_state.g_comfort = st.session_state.get("goal_comfort", "hold")
        st.radio(
            "Your reaction if markets dropped ~20%",
            list(comfort_labels.keys()),
            format_func=lambda k: comfort_labels[k],
            key="g_comfort",
            label_visibility="visible",
        )
        col1, col2 = st.columns(2)
        if col1.button("Back", key="g_b3"):
            _goal_chat_pop_last_turn()
            st.session_state.goal_step = 2
            st.rerun()
        if col2.button("Get my summary", type="primary", key="g_save"):
            main_key = st.session_state.get("_gc_main_goal")
            if not main_key or main_key not in goal_labels:
                main_key = st.session_state.get("goal_main", "retirement")
            y = int(st.session_state.get("_gc_years", st.session_state.goal_years))
            c = st.session_state.get("g_comfort", "hold")
            risk = "Cautious" if c == "sell" else "Balanced" if c == "hold" else "Growth-minded"
            profile = {
                "mainGoal": main_key,
                "mainGoalLabel": goal_labels[main_key],
                "years": y,
                "comfort": c,
                "riskLabel": risk,
            }
            main_lbl = goal_labels[main_key]
            comfort_lbl = comfort_labels[c]
            user_recap = (
                f"**My answers:** Goal — {main_lbl}; horizon — **{y} years**; "
                f"if the market dropped ~20% — *{comfort_lbl}*"
            )
            st.session_state.goal_saved = json.dumps(profile)
            sync_anthropic_env_from_secrets()
            key = get_api_key()
            with st.spinner("Generating your summary…"):
                summary, src, g_err = goal_coach_reply(key, profile)
            st.session_state.goal_claude_summary = summary
            st.session_state.goal_claude_source = src
            if g_err:
                st.session_state["_goal_coach_api_error"] = g_err
            else:
                st.session_state.pop("_goal_coach_api_error", None)
            st.session_state.goal_chat_messages.append(("user", user_recap))
            st.session_state.goal_chat_messages.append(
                (
                    "assistant",
                    "Here’s your **Goal coach summary** (bullets):\n\n" + summary,
                )
            )
            st.session_state.goal_step = 4
            st.rerun()

    else:
        st.success("Profile saved — scroll up to see the full chat.")
        if st.session_state.get("_goal_coach_api_error"):
            st.warning(
                "Claude couldn’t generate the summary — showing the built-in template. "
                + str(st.session_state["_goal_coach_api_error"])
            )
        src = st.session_state.get("goal_claude_source") or "fallback"
        st.caption(f"Summary source: **{'Claude API' if src == 'claude' else 'Built-in template'}**")
        if st.session_state.get("_goal_followup_api_error"):
            st.warning(
                "Follow-up Claude call failed — last reply is the built-in template. "
                + str(st.session_state["_goal_followup_api_error"])
            )
        with st.form("goal_followup_form", clear_on_submit=True):
            fu = st.text_input(
                "Optional follow-up (finance topics only)",
                placeholder="e.g. Should I tilt more conservative for a shorter horizon?",
                key="goal_followup_text",
            )
            send_fu = st.form_submit_button("Send follow-up")
            if send_fu and fu.strip():
                st.session_state.goal_chat_messages.append(("user", fu.strip()))
                _goal_followup_reply(fu.strip())
                st.rerun()
        if st.button("Start over", key="g_reset"):
            st.session_state.goal_step = 0
            st.session_state.goal_claude_summary = None
            st.session_state.goal_claude_source = None
            st.session_state.pop("_gc_main_goal", None)
            st.session_state.pop("_gc_years", None)
            st.session_state.pop("g_comfort", None)
            st.session_state.goal_chat_messages = [("assistant", GOAL_COACH_WELCOME)]
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def page_agent() -> None:
    _inject_gs_messaging_css()
    st.header("Agents")
    st.caption(
        "**REBA** (finance-only chat) plus **Goal coach** for a structured questionnaire."
    )
    sync_anthropic_env_from_secrets()

    tab_chat, tab_goals = st.tabs(["REBA", "Goal coach (chat)"])

    with tab_chat:
        st.subheader("REBA")
        st.write(
            "Chat about **money and investing** only. Replies are **bullet points**. "
            "Off-topic questions get a short reminder — REBA won’t answer non-finance topics."
        )

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
                f"Last reply source: **{'Claude API' if src == 'claude' else 'Built-in template'}**"
            )
        _api_err = st.session_state.get("_last_whatif_api_error")
        if get_api_key() and src == "fallback" and _api_err:
            st.warning(
                "The last question used the **built-in template** because the Claude request failed:\n\n"
                f"`{_api_err}`\n\n"
                "Check your API key, billing, and that **`ANTHROPIC_MODEL`** (if set) is a current model ID."
            )

        if prompt := st.chat_input("Ask REBA a finance question…"):
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
            st.session_state.pop("_last_whatif_api_error", None)
            st.rerun()

    with tab_goals:
        render_guided_goal_setting()


def page_rebalance() -> None:
    st.header("AI Rebalance (simulation)")
    st.caption("Practice scenarios on the demo portfolio — open from the sidebar.")
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

    with st.sidebar:
        st.markdown("### Workspace")
        nav_main = st.radio(
            "Navigate",
            ["portfolio", "Agents", "AI Rebalance"],
            label_visibility="collapsed",
        )
        if nav_main == "Agents":
            st.markdown(
                "<small><strong>REBA</strong> — Finance-only what-if chat. "
                "<strong>Goal coach</strong> — questionnaire + summary. Educational only.</small>",
                unsafe_allow_html=True,
            )
        elif nav_main == "AI Rebalance":
            st.caption("What-if scenarios on the demo portfolio (practice only).")

        st.divider()
        if st.button("Log out"):
            st.session_state.logged_in = False
            st.session_state.show_member_login = False
            st.rerun()
        st.caption("Signed in (demo: **admin** / **admin**).")

    sync_anthropic_env_from_secrets()
    _inject_gs_workspace_css()

    if nav_main == "portfolio":
        page_portfolio()
    elif nav_main == "Agents":
        page_agent()
    else:
        page_rebalance()


if __name__ == "__main__":
    main()
