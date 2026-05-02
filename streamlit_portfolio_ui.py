"""Charts + CSS for the Streamlit Portfolio dashboard (USD demo).

Portfolio charts avoid Plotly/st.plotly_chart because that path embeds Plotly in an
iframe; many browsers, VPNs, and CSP setups block or strip those embeds, which
produces empty chart areas even when data is valid. Native Streamlit charts and
Altair/Vega-Lite render reliably in the same environments.
"""

from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

NAVY = "#1a2b4b"
BLUE = "#1e3a5f"
ACCENT = "#2563eb"
GREEN = "#0f766e"
RED = "#b91c1c"
MUTED = "#64748b"

ALLOC_COLORS = ["#1e3a5f", "#0f766e", "#457b9d", "#a8dadc", "#e9c46a", "#bc6c25"]


def render_performance_chart(perf_df: pd.DataFrame) -> None:
    """Line chart via Streamlit (no Plotly iframe). Theme primaryColor matches portfolio navy."""
    work = perf_df[["Month", "Value"]].copy()
    st.line_chart(
        work,
        x="Month",
        y="Value",
        height=400,
        width="stretch",
    )


def render_allocation_chart(adf: pd.DataFrame) -> None:
    """Donut via Altair (Vega-Lite); matches navy / teal palette."""
    df = adf.copy()
    total = float(df["value"].sum()) or 1.0
    df["pct"] = df["value"] / total * 100.0
    n = len(df)
    colors = (ALLOC_COLORS * (1 + n // len(ALLOC_COLORS)))[:n]
    chart = (
        alt.Chart(df)
        .mark_arc(innerRadius=70, outerRadius=110, stroke="#ffffff", strokeWidth=2)
        .encode(
            theta=alt.Theta("value:Q", stack=True),
            color=alt.Color(
                "label:N",
                scale=alt.Scale(domain=df["label"].tolist(), range=colors),
                legend=alt.Legend(orient="left", title=None, labelLimit=220),
            ),
            tooltip=[
                alt.Tooltip("label:N", title="Holding"),
                alt.Tooltip("value:Q", format="$,.0f", title="Value (USD)"),
                alt.Tooltip("pct:Q", format=".1f", title="Weight %"),
            ],
        )
        .properties(height=380, background="white")
    )
    st.altair_chart(chart, use_container_width=True)


def render_transactions_chart(tx: pd.DataFrame) -> None:
    st.bar_chart(
        tx,
        x="Year",
        y="Net invested",
        height=340,
        width="stretch",
    )


def render_unrealized_chart(lt: float, st_pl: float) -> None:
    df = pd.DataFrame(
        {
            "bucket": ["Short-term unrealized", "Long-term unrealized"],
            "amount": [st_pl, lt],
        }
    )
    c_st = RED if st_pl < 0 else BLUE
    c_lt = GREEN if lt >= 0 else RED
    df["fill"] = [c_st, c_lt]
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("amount:Q", axis=alt.Axis(format="$,.0f", title=None)),
            y=alt.Y("bucket:N", sort=None, title=None),
            color=alt.Color("fill:N", scale=None, legend=None),
            tooltip=[
                alt.Tooltip("bucket:N", title="Bucket"),
                alt.Tooltip("amount:Q", format="$,.0f", title="Amount (USD)"),
            ],
        )
        .properties(height=300, background="white")
    )
    st.altair_chart(chart, use_container_width=True)


def inject_portfolio_dashboard_css() -> None:
    st.markdown(
        f"""
        <style>
        /* Native + Vega charts: reserve vertical space inside bordered cards */
        [data-testid="stVegaLiteChart"],
        [data-testid="stArrowVegaLiteChart"] {{
            min-height: 320px !important;
        }}
        div[data-testid="stBarChart"],
        div[data-testid="stLineChart"] {{
            min-height: 320px;
        }}
        .pf-wrap {{
            font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
            color: {NAVY};
            max-width: 1280px;
            margin: 0 auto;
            background: #ffffff;
        }}
        .pf-serif {{
            font-family: Georgia, "Times New Roman", serif;
            font-weight: 600;
            color: {NAVY};
            margin: 0 0 4px 0;
            font-size: 1.35rem;
        }}
        .pf-sub {{
            font-size: 0.88rem;
            color: {MUTED};
            margin: 0 0 16px 0;
        }}
        .pf-metric-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 28px;
            margin-bottom: 28px;
            padding: 20px 24px;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 2px 16px rgba(26, 43, 75, 0.08);
            border: 1px solid #e2e8f0;
        }}
        .pf-metric-block {{
            flex: 1;
            min-width: 200px;
        }}
        .pf-metric-label {{
            font-size: 0.68rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: {MUTED};
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .pf-metric-main {{
            font-size: 1.85rem;
            font-weight: 700;
            color: {NAVY};
            line-height: 1.15;
        }}
        .pf-metric-side {{
            font-size: 0.95rem;
            color: {MUTED};
            margin-top: 6px;
        }}
        .pf-pos {{ color: {GREEN}; font-weight: 600; }}
        .pf-neg {{ color: {RED}; font-weight: 600; }}
        .pf-card {{
            background: #ffffff;
            border-radius: 16px;
            padding: 20px 22px;
            box-shadow: 0 2px 14px rgba(26, 43, 75, 0.06);
            border: 1px solid #e2e8f0;
            height: 100%;
        }}
        .pf-footlink {{
            font-size: 0.88rem;
            color: {ACCENT};
            margin-top: 12px;
        }}
        .pf-disclaimer {{
            font-size: 0.75rem;
            color: {MUTED};
            line-height: 1.45;
            margin-top: 24px;
            max-width: 900px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
