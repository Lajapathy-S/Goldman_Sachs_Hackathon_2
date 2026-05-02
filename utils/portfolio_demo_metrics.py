"""
Hardcoded U.S. demo portfolio metrics for the Streamlit Portfolio page.
Aligned with DEMO_US_PORTFOLIO + tax_calculator.holding_metrics.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from utils.tax_calculator import DEMO_US_PORTFOLIO, holding_metrics

AS_OF = date(2026, 5, 2)

# Demo 1-day move (illustrative, not live market data)
ONE_DAY_PCT = -0.009


def _rows() -> list[dict[str, Any]]:
    return [holding_metrics(h, AS_OF) for h in DEMO_US_PORTFOLIO]


def snapshot() -> dict[str, Any]:
    rows = _rows()
    invested = sum(r["invested_value"] for r in rows)
    current = sum(r["current_value"] for r in rows)
    day_chg = current * ONE_DAY_PCT
    total_gain = current - invested
    oldest = min(datetime.strptime(str(h["buy_date"])[:10], "%Y-%m-%d").date() for h in DEMO_US_PORTFOLIO)
    years = max((AS_OF - oldest).days / 365.25, 0.25)
    cagr = (current / invested) ** (1 / years) - 1 if invested > 0 else 0.0

    lt_pl = sum(r["unrealized_gain_loss"] for r in rows if r["is_long_term"])
    st_pl = sum(r["unrealized_gain_loss"] for r in rows if not r["is_long_term"])

    return {
        "invested": invested,
        "current": current,
        "one_day_change": day_chg,
        "one_day_pct": ONE_DAY_PCT * 100,
        "all_time_gain": total_gain,
        "cagr_pct": cagr * 100,
        "lt_unrealized_pl": lt_pl,
        "st_unrealized_pl": st_pl,
        "as_of": AS_OF,
    }


def snapshot_for_focus(focus: str) -> dict[str, Any]:
    """Headline metrics for a subset: focus is 'stocks' or 'mutual_fund' (demo asset_type)."""
    if focus not in ("stocks", "mutual_fund"):
        return snapshot()
    want = "Stock" if focus == "stocks" else "Mutual Fund"
    holdings = [h for h in DEMO_US_PORTFOLIO if h.get("asset_type") == want]
    rows = [holding_metrics(h, AS_OF) for h in holdings]
    if not rows:
        return snapshot()
    invested = sum(r["invested_value"] for r in rows)
    current = sum(r["current_value"] for r in rows)
    day_chg = current * ONE_DAY_PCT
    total_gain = current - invested
    oldest = min(datetime.strptime(str(h["buy_date"])[:10], "%Y-%m-%d").date() for h in holdings)
    years = max((AS_OF - oldest).days / 365.25, 0.25)
    cagr = (current / invested) ** (1 / years) - 1 if invested > 0 else 0.0
    lt_pl = sum(r["unrealized_gain_loss"] for r in rows if r["is_long_term"])
    st_pl = sum(r["unrealized_gain_loss"] for r in rows if not r["is_long_term"])
    return {
        "invested": invested,
        "current": current,
        "one_day_change": day_chg,
        "one_day_pct": ONE_DAY_PCT * 100,
        "all_time_gain": total_gain,
        "cagr_pct": cagr * 100,
        "lt_unrealized_pl": lt_pl,
        "st_unrealized_pl": st_pl,
        "as_of": AS_OF,
    }


def allocation_by_focus(focus: str) -> pd.DataFrame:
    """Per-symbol weights within stocks-only or mutual-fund-only demo holdings."""
    want = "Stock" if focus == "stocks" else "Mutual Fund"
    rows = [holding_metrics(h, AS_OF) for h in DEMO_US_PORTFOLIO if h.get("asset_type") == want]
    return pd.DataFrame(
        {
            "label": [r["symbol"] for r in rows],
            "value": [r["current_value"] for r in rows],
        }
    )


def performance_monthly() -> pd.DataFrame:
    """Synthetic month-end values ending at modeled current value (educational)."""
    snap = snapshot()
    end = float(snap["current"])
    start = float(snap["invested"]) * 0.92
    months = pd.date_range("2021-01-01", AS_OF.isoformat(), freq="ME")
    n = len(months)
    if n < 2:
        return pd.DataFrame({"Month": months, "Value": [end]})
    # Smooth growth curve ending at `end`
    t = pd.Series(range(n), dtype=float)
    w = (t / (n - 1)) ** 1.15
    vals = start + (end - start) * w
    return pd.DataFrame({"Month": months, "Value": vals.values})


def filter_performance(df: pd.DataFrame, range_key: str) -> pd.DataFrame:
    if df.empty:
        return df
    end = df["Month"].max()
    if range_key == "ALL":
        return df
    if range_key == "YTD":
        start = pd.Timestamp(year=end.year, month=1, day=1)
    elif range_key == "1M":
        start = end - pd.DateOffset(months=1)
    elif range_key == "3M":
        start = end - pd.DateOffset(months=3)
    elif range_key == "6M":
        start = end - pd.DateOffset(months=6)
    elif range_key == "1Y":
        start = end - pd.DateOffset(years=1)
    elif range_key == "3Y":
        start = end - pd.DateOffset(years=3)
    elif range_key == "5Y":
        start = end - pd.DateOffset(years=5)
    else:
        return df
    out = df[df["Month"] >= start]
    return out if len(out) > 1 else df.tail(min(3, len(df)))


def allocation_by_investment_type() -> pd.DataFrame:
    rows = _rows()
    stock_v = sum(r["current_value"] for r in rows if r["asset_type"] == "Stock")
    mf_v = sum(r["current_value"] for r in rows if r["asset_type"] == "Mutual Fund")
    total = stock_v + mf_v or 1.0
    return pd.DataFrame(
        {
            "label": ["Stocks", "Mutual funds"],
            "value": [stock_v, mf_v],
            "pct": [stock_v / total * 100, mf_v / total * 100],
        }
    )


def allocation_by_asset() -> pd.DataFrame:
    rows = _rows()
    return pd.DataFrame(
        {
            "label": [r["symbol"] for r in rows],
            "value": [r["current_value"] for r in rows],
        }
    )


def transactions_annual() -> pd.DataFrame:
    """Illustrative net invested per calendar year (USD)."""
    return pd.DataFrame(
        {
            "Year": ["2022", "2023", "2024", "2025", "2026 (YTD)"],
            "Net invested": [8500, 9200, 10100, 9800, 2400],
        }
    )


def returns_by_type(duration_key: str) -> list[dict[str, Any]]:
    """
    Demo 1-day style moves by bucket. Other durations scale the move for illustration.
    """
    scale = {
        "1 Day": 1.0,
        "1 Week": 1.4,
        "1 Month": 2.2,
        "3 Month": 3.0,
        "YTD": 2.5,
    }.get(duration_key, 1.0)

    rows = _rows()
    stock_rows = [r for r in rows if r["asset_type"] == "Stock"]
    mf_rows = [r for r in rows if r["asset_type"] == "Mutual Fund"]
    s_val = sum(r["current_value"] for r in stock_rows)
    m_val = sum(r["current_value"] for r in mf_rows)
    # Uncorrelated demo noise
    s_ret = -0.0082 * scale
    m_ret = -0.0090 * scale
    s_chg = s_val * s_ret
    m_chg = m_val * m_ret
    return [
        {
            "name": "Stocks",
            "value": s_val,
            "change": s_chg,
            "pct": s_ret * 100,
            "in_portfolio": True,
        },
        {
            "name": "Mutual funds",
            "value": m_val,
            "change": m_chg,
            "pct": m_ret * 100,
            "in_portfolio": True,
        },
        {
            "name": "Fixed income",
            "value": None,
            "change": None,
            "pct": None,
            "in_portfolio": False,
        },
        {
            "name": "NPS / workplace",
            "value": None,
            "change": None,
            "pct": None,
            "in_portfolio": False,
        },
    ]
