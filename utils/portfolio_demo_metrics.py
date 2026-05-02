"""
Portfolio metrics with live Yahoo Finance data and static fallback.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

import numpy as np
import pandas as pd

from utils.tax_calculator import DEMO_US_PORTFOLIO, holding_metrics

try:
    import yfinance as yf
except Exception:
    yf = None

AS_OF = date.today()

LIVE_US_PORTFOLIO: list[dict[str, Any]] = [
    {"name": "Apple Inc.", "symbol": "AAPL", "asset_type": "Stock", "buy_date": "2021-03-12", "buy_price": 124.0, "quantity": 24},
    {"name": "Microsoft Corp.", "symbol": "MSFT", "asset_type": "Stock", "buy_date": "2021-08-09", "buy_price": 289.0, "quantity": 14},
    {"name": "NVIDIA Corp.", "symbol": "NVDA", "asset_type": "Stock", "buy_date": "2022-10-17", "buy_price": 122.0, "quantity": 32},
    {"name": "JPMorgan Chase", "symbol": "JPM", "asset_type": "Stock", "buy_date": "2020-11-20", "buy_price": 108.0, "quantity": 19},
    {"name": "Exxon Mobil", "symbol": "XOM", "asset_type": "Stock", "buy_date": "2020-06-04", "buy_price": 52.0, "quantity": 30},
    {"name": "Vanguard S&P 500 ETF", "symbol": "VOO", "asset_type": "Mutual Fund", "buy_date": "2020-09-10", "buy_price": 305.0, "quantity": 14},
    {"name": "Vanguard Total Stock Market ETF", "symbol": "VTI", "asset_type": "Mutual Fund", "buy_date": "2021-01-22", "buy_price": 199.0, "quantity": 17},
    {"name": "Vanguard Total International Stock ETF", "symbol": "VXUS", "asset_type": "Mutual Fund", "buy_date": "2021-04-16", "buy_price": 64.0, "quantity": 42},
    {"name": "Vanguard Total Bond Market ETF", "symbol": "BND", "asset_type": "Mutual Fund", "buy_date": "2022-02-14", "buy_price": 79.0, "quantity": 40},
    {"name": "iShares Core U.S. Aggregate Bond ETF", "symbol": "AGG", "asset_type": "Mutual Fund", "buy_date": "2022-07-25", "buy_price": 104.0, "quantity": 29},
]

_CACHE: dict[str, Any] = {"quotes": None, "quotes_ts": None, "history": None, "history_ts": None}


def _cache_is_fresh(ts: datetime | None, ttl_sec: int) -> bool:
    if ts is None:
        return False
    return (datetime.now(timezone.utc) - ts).total_seconds() < ttl_sec


def _symbols() -> list[str]:
    return [h["symbol"] for h in LIVE_US_PORTFOLIO]


def _download_quotes() -> dict[str, dict[str, float]]:
    if yf is None:
        raise RuntimeError("yfinance unavailable")
    if _cache_is_fresh(_CACHE.get("quotes_ts"), 300) and isinstance(_CACHE.get("quotes"), dict):
        return _CACHE["quotes"]

    symbols = _symbols()
    hist = yf.download(
        symbols,
        period="15d",
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    if hist is None or len(hist) == 0:
        raise RuntimeError("empty quote history")

    out: dict[str, dict[str, float]] = {}
    for s in symbols:
        if isinstance(hist.columns, pd.MultiIndex):
            if (s, "Close") not in hist.columns:
                continue
            ser = hist[(s, "Close")].dropna()
        else:
            ser = hist["Close"].dropna()
        if len(ser) == 0:
            continue
        last = float(ser.iloc[-1])
        prev = float(ser.iloc[-2]) if len(ser) > 1 else last
        out[s] = {"last": last, "prev": prev}

    if not out:
        raise RuntimeError("no valid quote rows")
    _CACHE["quotes"] = out
    _CACHE["quotes_ts"] = datetime.now(timezone.utc)
    return out


def _download_history() -> pd.DataFrame:
    if yf is None:
        raise RuntimeError("yfinance unavailable")
    if _cache_is_fresh(_CACHE.get("history_ts"), 900) and isinstance(_CACHE.get("history"), pd.DataFrame):
        return _CACHE["history"]

    symbols = _symbols()
    hist = yf.download(
        symbols,
        start="2020-01-01",
        interval="1d",
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    if hist is None or len(hist) == 0:
        raise RuntimeError("empty history")
    _CACHE["history"] = hist
    _CACHE["history_ts"] = datetime.now(timezone.utc)
    return hist


def _live_holdings_with_prices() -> tuple[list[dict[str, Any]], bool]:
    try:
        q = _download_quotes()
        out: list[dict[str, Any]] = []
        for h in LIVE_US_PORTFOLIO:
            cp = float(q.get(h["symbol"], {}).get("last", h["buy_price"]))
            out.append({**h, "current_price": cp})
        return out, True
    except Exception:
        # Fallback keeps the same live portfolio symbols, using buy_price as current_price.
        out = [{**h, "current_price": float(h["buy_price"])} for h in LIVE_US_PORTFOLIO]
        return out, False


def _rows() -> tuple[list[dict[str, Any]], bool]:
    holdings, live = _live_holdings_with_prices()
    return [holding_metrics(h, AS_OF) for h in holdings], live


def snapshot() -> dict[str, Any]:
    rows, live = _rows()
    invested = sum(r["invested_value"] for r in rows)
    current = sum(r["current_value"] for r in rows)
    try:
        q = _download_quotes() if live else {}
        qty_map = {h["symbol"]: float(h["quantity"]) for h in LIVE_US_PORTFOLIO}
        day_chg = 0.0
        for s, qty in qty_map.items():
            if s in q:
                day_chg += qty * (q[s]["last"] - q[s]["prev"])
    except Exception:
        day_chg = current * -0.009
    total_gain = current - invested
    base_holdings = LIVE_US_PORTFOLIO if live else DEMO_US_PORTFOLIO
    oldest = min(datetime.strptime(str(h["buy_date"])[:10], "%Y-%m-%d").date() for h in base_holdings)
    years = max((AS_OF - oldest).days / 365.25, 0.25)
    cagr = (current / invested) ** (1 / years) - 1 if invested > 0 else 0.0

    lt_pl = sum(r["unrealized_gain_loss"] for r in rows if r["is_long_term"])
    st_pl = sum(r["unrealized_gain_loss"] for r in rows if not r["is_long_term"])

    return {
        "invested": invested,
        "current": current,
        "one_day_change": day_chg,
        "one_day_pct": (day_chg / current * 100.0) if current else 0.0,
        "all_time_gain": total_gain,
        "cagr_pct": cagr * 100,
        "lt_unrealized_pl": lt_pl,
        "st_unrealized_pl": st_pl,
        "as_of": AS_OF,
        "data_source": "live_yahoo" if live else "static_fallback",
        "data_source_label": "Live Yahoo Finance" if live else "Static fallback",
    }


def snapshot_for_focus(focus: str) -> dict[str, Any]:
    """Headline metrics for a subset: focus is 'stocks' or 'mutual_fund' (demo asset_type)."""
    if focus not in ("stocks", "mutual_fund"):
        return snapshot()
    want = "Stock" if focus == "stocks" else "Mutual Fund"
    holdings, live = _live_holdings_with_prices()
    holdings = [h for h in holdings if h.get("asset_type") == want]
    rows = [holding_metrics(h, AS_OF) for h in holdings]
    if not rows:
        return snapshot()
    invested = sum(r["invested_value"] for r in rows)
    current = sum(r["current_value"] for r in rows)
    try:
        q = _download_quotes() if live else {}
        qty_map = {h["symbol"]: float(h["quantity"]) for h in holdings}
        day_chg = 0.0
        for s, qty in qty_map.items():
            if s in q:
                day_chg += qty * (q[s]["last"] - q[s]["prev"])
    except Exception:
        day_chg = current * -0.009
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
        "one_day_pct": (day_chg / current * 100.0) if current else 0.0,
        "all_time_gain": total_gain,
        "cagr_pct": cagr * 100,
        "lt_unrealized_pl": lt_pl,
        "st_unrealized_pl": st_pl,
        "as_of": AS_OF,
        "data_source": "live_yahoo" if live else "static_fallback",
        "data_source_label": "Live Yahoo Finance" if live else "Static fallback",
    }


def allocation_by_focus(focus: str) -> pd.DataFrame:
    """Per-symbol weights within stocks-only or mutual-fund-only demo holdings."""
    want = "Stock" if focus == "stocks" else "Mutual Fund"
    holdings, _ = _live_holdings_with_prices()
    rows = [holding_metrics(h, AS_OF) for h in holdings if h.get("asset_type") == want]
    return pd.DataFrame(
        {
            "label": [r["symbol"] for r in rows],
            "value": [r["current_value"] for r in rows],
        }
    )


def performance_monthly() -> pd.DataFrame:
    """Live month-end portfolio value from Yahoo; synthetic fallback if unavailable."""
    try:
        hist = _download_history()
        qty = {h["symbol"]: float(h["quantity"]) for h in LIVE_US_PORTFOLIO}
        close_map: dict[str, pd.Series] = {}
        for s in _symbols():
            if isinstance(hist.columns, pd.MultiIndex):
                if (s, "Close") not in hist.columns:
                    continue
                ser = hist[(s, "Close")]
            else:
                ser = hist["Close"]
            close_map[s] = ser.astype(float).ffill()
        if not close_map:
            raise RuntimeError("missing close map")
        idx = sorted(set().union(*(ser.index for ser in close_map.values())))
        df = pd.DataFrame(index=pd.DatetimeIndex(idx))
        for s, ser in close_map.items():
            df[s] = ser.reindex(df.index).ffill()
        vals = pd.Series(0.0, index=df.index)
        for s, q in qty.items():
            if s in df.columns:
                vals = vals + q * df[s]
        vals = vals.dropna()
        month = vals.resample("ME").last().dropna()
        if len(month) < 2:
            raise RuntimeError("insufficient monthly points")
        return pd.DataFrame({"Month": month.index, "Value": month.values})
    except Exception:
        snap = snapshot()
        end = float(snap["current"])
        start = float(snap["invested"]) * 0.88
        months = pd.date_range("2020-01-01", AS_OF.isoformat(), freq="ME")
        n = len(months)
        if n < 2:
            return pd.DataFrame({"Month": months, "Value": [end]})
        t = np.arange(n, dtype=float)
        w = (t / (n - 1)) ** 1.12
        base = start + (end - start) * w
        ripple = 1.0 + 0.022 * np.sin(np.linspace(0, 5 * np.pi, n))
        dip = 1.0 - 0.04 * np.exp(-0.5 * ((t - (n - 1) * 0.35) / max(n * 0.08, 1)) ** 2)
        vals = base * ripple * dip
        vals[-1] = end
        return pd.DataFrame({"Month": months, "Value": vals})


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
    rows, _ = _rows()
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
    rows, _ = _rows()
    return pd.DataFrame(
        {
            "label": [r["symbol"] for r in rows],
            "value": [r["current_value"] for r in rows],
        }
    )


def transactions_annual() -> pd.DataFrame:
    """Net invested by buy year from configured portfolio (still static quantities)."""
    buckets: dict[str, float] = {}
    for h in LIVE_US_PORTFOLIO:
        y = str(datetime.strptime(str(h["buy_date"])[:10], "%Y-%m-%d").year)
        buckets[y] = buckets.get(y, 0.0) + float(h["quantity"]) * float(h["buy_price"])
    years = sorted(buckets.keys())
    return pd.DataFrame({"Year": years, "Net invested": [round(buckets[y], 0) for y in years]})


def returns_by_type(duration_key: str) -> list[dict[str, Any]]:
    """
    Demo 1-day style moves by bucket. Other durations scale the move for illustration.
    """
    rows, live = _rows()
    stock_rows = [r for r in rows if r["asset_type"] == "Stock"]
    mf_rows = [r for r in rows if r["asset_type"] == "Mutual Fund"]
    s_val = sum(r["current_value"] for r in stock_rows)
    m_val = sum(r["current_value"] for r in mf_rows)

    s_ret = -0.0082
    m_ret = -0.0090
    if live:
        try:
            hist = _download_history()
            lookback = {"1 Day": 1, "1 Week": 5, "1 Month": 21, "3 Month": 63}.get(duration_key, 1)
            bucket_syms = {
                "stocks": [h["symbol"] for h in LIVE_US_PORTFOLIO if h["asset_type"] == "Stock"],
                "mf": [h["symbol"] for h in LIVE_US_PORTFOLIO if h["asset_type"] == "Mutual Fund"],
            }
            qty_map = {h["symbol"]: float(h["quantity"]) for h in LIVE_US_PORTFOLIO}

            def _bucket_ret(syms: list[str]) -> float:
                vals_now = 0.0
                vals_then = 0.0
                for s in syms:
                    if isinstance(hist.columns, pd.MultiIndex):
                        if (s, "Close") not in hist.columns:
                            continue
                        ser = hist[(s, "Close")].dropna()
                    else:
                        ser = hist["Close"].dropna()
                    if len(ser) < 2:
                        continue
                    now = float(ser.iloc[-1])
                    if duration_key == "YTD":
                        ystart = datetime(date.today().year, 1, 1)
                        ser2 = ser[ser.index >= ystart]
                        then = float(ser2.iloc[0]) if len(ser2) else float(ser.iloc[max(0, len(ser) - 2)])
                    else:
                        then = float(ser.iloc[max(0, len(ser) - 1 - lookback)])
                    q = qty_map.get(s, 0.0)
                    vals_now += q * now
                    vals_then += q * then
                return (vals_now / vals_then - 1.0) if vals_then > 0 else 0.0

            s_ret = _bucket_ret(bucket_syms["stocks"])
            m_ret = _bucket_ret(bucket_syms["mf"])
        except Exception:
            pass

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
    ]


def portfolio_health_score() -> dict[str, Any]:
    """
    Simple demo health score for the sample portfolio (0-100).
    Combines diversification, allocation balance, concentration, and growth trend.
    """
    rows, _ = _rows()
    if not rows:
        return {
            "score": 0,
            "label": "Poor",
            "color": "#dc2626",
            "components": {},
        }

    total = sum(float(r["current_value"]) for r in rows) or 1.0
    n_holdings = len(rows)
    max_w = max(float(r["current_value"]) / total for r in rows)

    stock_v = sum(float(r["current_value"]) for r in rows if r["asset_type"] == "Stock")
    stock_pct = stock_v / total * 100.0
    target_stock = 60.0

    snap = snapshot()
    cagr_pct = float(snap["cagr_pct"])

    diversification = min(35.0, n_holdings * 7.0)
    balance = max(0.0, 30.0 - abs(stock_pct - target_stock) * 0.75)
    concentration = max(0.0, 20.0 - max(0.0, max_w * 100.0 - 28.0) * 0.9)
    growth = min(15.0, max(0.0, (cagr_pct + 2.0) * 1.2))

    score = int(round(diversification + balance + concentration + growth))
    score = max(0, min(100, score))

    if score < 35:
        label, color = "Bad", "#dc2626"
    elif score < 55:
        label, color = "Needs work", "#f59e0b"
    elif score < 75:
        label, color = "Fair", "#facc15"
    else:
        label, color = "Good", "#16a34a"

    return {
        "score": score,
        "label": label,
        "color": color,
        "components": {
            "diversification": round(diversification, 1),
            "balance": round(balance, 1),
            "concentration": round(concentration, 1),
            "growth": round(growth, 1),
        },
    }
