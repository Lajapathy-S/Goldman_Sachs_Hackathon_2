"""Charts + CSS for the Streamlit Portfolio dashboard (USD demo)."""

from __future__ import annotations

import streamlit as st

NAVY = "#1a2b4b"
BLUE = "#1e3a5f"
ACCENT = "#2563eb"
GREEN = "#0f766e"
RED = "#b91c1c"
MUTED = "#64748b"
BG = "#faf8f5"


def inject_portfolio_dashboard_css() -> None:
    st.markdown(
        f"""
        <style>
        .pf-wrap {{
            font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
            color: {NAVY};
            max-width: 1280px;
            margin: 0 auto;
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
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(26, 43, 75, 0.08);
            border: 1px solid #e8e4df;
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
            background: #fff;
            border-radius: 16px;
            padding: 20px 22px;
            box-shadow: 0 4px 24px rgba(26, 43, 75, 0.07);
            border: 1px solid #e8e4df;
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


def chart_performance(df, title: str = "Performance"):
    import plotly.graph_objects as go

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["Month"],
            y=df["Value"],
            mode="lines",
            line=dict(color=BLUE, width=2.5),
            fill="tozeroy",
            fillcolor="rgba(30, 58, 95, 0.08)",
            name="Value",
        )
    )
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=NAVY, family="Georgia, serif")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=16, r=16, t=48, b=16),
        height=340,
        xaxis=dict(showgrid=True, gridcolor="#eee", zeroline=False),
        yaxis=dict(
            showgrid=True,
            gridcolor="#eee",
            tickprefix="$",
            tickformat=",.0f",
        ),
        showlegend=False,
    )
    return fig


def chart_donut(labels: list[str], values: list[float], title: str | None = None):
    import plotly.graph_objects as go

    colors = ["#1e3a5f", "#2d6a4f", "#457b9d", "#a8dadc", "#e9c46a", "#bc6c25"]
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(colors=colors[: len(labels)]),
                textinfo="label+percent",
                textposition="outside",
                sort=False,
            )
        ]
    )
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=16, r=16, t=24 if not title else 48, b=16),
        height=340,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, x=0.02),
    )
    if title:
        layout["title"] = dict(text=title, font=dict(size=18, color=NAVY, family="Georgia, serif"))
    fig.update_layout(**layout)
    return fig


def chart_transactions(df):
    import plotly.graph_objects as go

    fig = go.Figure(
        data=[
            go.Bar(
                x=df["Year"],
                y=df["Net invested"],
                marker_color=BLUE,
                text=df["Net invested"].map(lambda v: f"${v:,.0f}"),
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title=dict(
            text="Transactions",
            font=dict(size=18, color=NAVY, family="Georgia, serif"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=16, r=16, t=56, b=16),
        height=320,
        xaxis=dict(title=""),
        yaxis=dict(title="", tickprefix="$", tickformat=",.0f", showgrid=True, gridcolor="#eee"),
        showlegend=False,
    )
    return fig


def chart_lt_st(lt: float, st: float, tax_year_label: str):
    import plotly.graph_objects as go

    categories = ["Short-term unrealized", "Long-term unrealized"]
    values = [st, lt]
    colors = [RED if st < 0 else BLUE, GREEN if lt >= 0 else RED]
    fig = go.Figure(
        go.Bar(
            y=categories,
            x=values,
            orientation="h",
            marker_color=colors,
            text=[f"${v:,.0f}" for v in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=dict(
            text=f"Unrealized gains — {tax_year_label}",
            font=dict(size=18, color=NAVY, family="Georgia, serif"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=16, r=48, t=56, b=16),
        height=260,
        xaxis=dict(
            tickprefix="$",
            tickformat=",.0f",
            zeroline=True,
            zerolinecolor="#ccc",
            showgrid=True,
            gridcolor="#eee",
        ),
        yaxis=dict(title=""),
        showlegend=False,
    )
    return fig
