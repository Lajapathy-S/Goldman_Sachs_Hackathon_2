"""
Simplified U.S. federal tax helpers for educational Streamlit demo only.
Not personalized tax advice — rates/brackets are rounded 2024-style rules of thumb.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

# --- 2024 ordinary income brackets (upper bound of bracket → marginal rate on next dollar in that band)
ORDINARY_BRACKETS: dict[str, list[tuple[float, float]]] = {
    "Single": [
        (11_600, 0.10),
        (47_150, 0.12),
        (100_525, 0.22),
        (191_950, 0.24),
        (243_725, 0.32),
        (609_350, 0.35),
        (float("inf"), 0.37),
    ],
    "Married Filing Jointly": [
        (23_200, 0.10),
        (94_300, 0.12),
        (201_050, 0.22),
        (383_900, 0.24),
        (487_450, 0.32),
        (731_200, 0.35),
        (float("inf"), 0.37),
    ],
    "Head of Household": [
        (16_550, 0.10),
        (63_100, 0.12),
        (100_500, 0.22),
        (191_950, 0.24),
        (243_700, 0.32),
        (609_350, 0.35),
        (float("inf"), 0.37),
    ],
    "Married Filing Separately": [
        (11_600, 0.10),
        (47_150, 0.12),
        (100_525, 0.22),
        (191_950, 0.24),
        (243_725, 0.32),
        (365_600, 0.35),
        (float("inf"), 0.37),
    ],
}

# Long-term capital gains: upper bound of taxable income → rate on LTCG in that band (simplified)
LTCG_BRACKETS: dict[str, list[tuple[float, float]]] = {
    "Single": [(47_025, 0.0), (518_900, 0.15), (float("inf"), 0.20)],
    "Married Filing Jointly": [(94_050, 0.0), (583_750, 0.15), (float("inf"), 0.20)],
    "Head of Household": [(63_000, 0.0), (551_350, 0.15), (float("inf"), 0.20)],
    "Married Filing Separately": [(47_025, 0.0), (291_850, 0.15), (float("inf"), 0.20)],
}

NIIT_THRESHOLDS: dict[str, float] = {
    "Single": 200_000,
    "Married Filing Jointly": 250_000,
    "Married Filing Separately": 125_000,
    "Head of Household": 200_000,
}

FILING_STATUSES = list(ORDINARY_BRACKETS.keys())

RiskRank = {"High": 3, "Medium": 2, "Low": 1}


def estimate_ordinary_income_tax_rate(taxable_income: float, filing_status: str) -> float:
    """Marginal federal ordinary income rate at this taxable income (demo)."""
    if filing_status not in ORDINARY_BRACKETS:
        filing_status = "Single"
    ti = max(0.0, float(taxable_income))
    for cap, rate in ORDINARY_BRACKETS[filing_status]:
        if ti <= cap:
            return rate
    return 0.37


def estimate_long_term_capital_gains_rate(taxable_income: float, filing_status: str) -> float:
    if filing_status not in LTCG_BRACKETS:
        filing_status = "Single"
    ti = max(0.0, float(taxable_income))
    for cap, rate in LTCG_BRACKETS[filing_status]:
        if ti <= cap:
            return rate
    return 0.20


def _parse_buy_date(buy_date: Any) -> date:
    if isinstance(buy_date, date) and not isinstance(buy_date, datetime):
        return buy_date
    if isinstance(buy_date, datetime):
        return buy_date.date()
    if isinstance(buy_date, str):
        return datetime.strptime(buy_date[:10], "%Y-%m-%d").date()
    raise ValueError("buy_date must be date, datetime, or YYYY-MM-DD string")


def is_long_term_holding(buy_date: Any, as_of: date | None = None) -> bool:
    """Long-term if held more than 1 year (>365 days from buy to as_of)."""
    d0 = _parse_buy_date(buy_date)
    ref = as_of or date.today()
    return (ref - d0).days > 365


def holding_metrics(holding: dict[str, Any], as_of: date | None = None) -> dict[str, Any]:
    q = float(holding["quantity"])
    buy = float(holding["buy_price"])
    cur = float(holding["current_price"])
    invested = q * buy
    current_value = q * cur
    unrealized = current_value - invested
    lt = is_long_term_holding(holding["buy_date"], as_of)
    days = (as_of or date.today()) - _parse_buy_date(holding["buy_date"])
    gain_type = "Long Term" if lt else "Short Term"
    return {
        "name": holding["name"],
        "symbol": holding["symbol"],
        "asset_type": holding["asset_type"],
        "invested_value": invested,
        "current_value": current_value,
        "unrealized_gain_loss": unrealized,
        "holding_period_days": days.days,
        "gain_type": gain_type,
        "is_long_term": lt,
    }


def _niit_applies(profile: dict[str, Any]) -> bool:
    fs = profile.get("filing_status", "Single")
    thresh = NIIT_THRESHOLDS.get(fs, 200_000)
    # Demo: use taxable_income as stand-in for MAGI-style check
    return float(profile.get("taxable_income", 0)) > thresh


def _niit_rate() -> float:
    return 0.038


def federal_tax_on_gain(
    gain: float,
    is_long_term: bool,
    profile: dict[str, Any],
    apply_niit_to_this_gain: bool = False,
) -> float:
    if gain <= 0:
        return 0.0
    ti = float(profile.get("taxable_income", 0))
    fs = profile.get("filing_status", "Single")
    if is_long_term:
        r = estimate_long_term_capital_gains_rate(ti, fs)
    else:
        r = estimate_ordinary_income_tax_rate(ti, fs)
    tax = gain * r
    if apply_niit_to_this_gain and _niit_applies(profile):
        tax += gain * _niit_rate()
    return tax


def dividend_federal_estimate(holding: dict[str, Any], profile: dict[str, Any]) -> float:
    amt = float(holding.get("expected_dividend_income") or 0)
    if amt <= 0:
        return 0.0
    d_type = (holding.get("dividend_type") or "Qualified").strip()
    ti = float(profile.get("taxable_income", 0))
    fs = profile.get("filing_status", "Single")
    if d_type.lower().startswith("non"):
        r = estimate_ordinary_income_tax_rate(ti, fs)
    else:
        r = estimate_long_term_capital_gains_rate(ti, fs)
    tax = amt * r
    if _niit_applies(profile):
        tax += amt * _niit_rate()
    return tax


def calculate_holding_tax(holding: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    m = holding_metrics(holding)
    g = m["unrealized_gain_loss"]
    tax_if_sell = federal_tax_on_gain(
        g, m["is_long_term"], profile, apply_niit_to_this_gain=True
    )
    div_tax = dividend_federal_estimate(holding, profile)
    return {**m, "estimated_federal_tax_if_sold_now": tax_if_sell, "estimated_annual_dividend_tax": div_tax}


def calculate_tax_summary(portfolio: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    rows = [calculate_holding_tax(h, profile) for h in portfolio]
    total_unrealized_gains = sum(max(0.0, r["unrealized_gain_loss"]) for r in rows)
    total_unrealized_losses = sum(min(0.0, r["unrealized_gain_loss"]) for r in rows)
    est_sell_today = sum(r["estimated_federal_tax_if_sold_now"] for r in rows)
    dividend_income = sum(float(h.get("expected_dividend_income") or 0) for h in portfolio)
    dividend_tax_total = sum(r["estimated_annual_dividend_tax"] for r in rows)
    tlh_potential = abs(total_unrealized_losses)
    total_mv = sum(r["current_value"] for r in rows) or 1.0

    niit_warning: str | None = None
    niit_estimate_on_gain = 0.0
    if _niit_applies(profile):
        niit_warning = (
            f"For this demo, taxable income (~${float(profile.get('taxable_income', 0)):,.0f}) is above the "
            f"NIIT threshold for **{profile.get('filing_status', 'Single')}**, so an extra **3.8%** may apply to "
            f"some investment income in simplified modeling."
        )
        niit_estimate_on_gain = 0.038 * max(0.0, total_unrealized_gains)

    concentration_warning: str | None = None
    concentration_symbol: str | None = None
    concentration_pct = 0.0
    for r in rows:
        share = r["current_value"] / total_mv
        if share > 0.25:
            concentration_warning = (
                f"**{r['symbol']}** is about **{share*100:.1f}%** of portfolio value—larger than the **25%** "
                f"concentration guideline used in this demo."
            )
            concentration_symbol = r["symbol"]
            concentration_pct = share * 100.0
            break

    return {
        "holdings_detail": rows,
        "estimated_federal_tax_if_sold_today": est_sell_today,
        "total_unrealized_gains": total_unrealized_gains,
        "total_unrealized_losses": total_unrealized_losses,
        "dividend_income": dividend_income,
        "expected_dividend_income": dividend_income,
        "estimated_annual_dividend_tax": dividend_tax_total,
        "expected_dividend_tax": dividend_tax_total,
        "tax_loss_harvesting_potential": tlh_potential,
        "total_current_value": total_mv,
        "niit_warning": niit_warning,
        "niit_estimate_on_gain": niit_estimate_on_gain,
        "concentration_warning": concentration_warning,
        "concentration_symbol": concentration_symbol,
        "concentration_pct": concentration_pct,
    }


def detect_tax_opportunities(
    portfolio: list[dict[str, Any]], profile: dict[str, Any]
) -> list[dict[str, Any]]:
    summary = calculate_tax_summary(portfolio, profile)
    rows = summary["holdings_detail"]
    total_mv = sum(r["current_value"] for r in rows) or 1.0
    opps: list[dict[str, Any]] = []

    if summary["total_unrealized_losses"] < 0:
        opps.append(
            {
                "title": "Tax-loss harvesting opportunity",
                "priority": "High",
                "explanation": "Some holdings show unrealized losses. In a taxable account, realized losses can often offset realized capital gains, and up to $3,000 of net losses may offset ordinary income per year (with carryforward rules).",
                "beginner_translation": "Selling a loser can sometimes lower the tax bill from your winners—but the rules are picky.",
                "possible_action": "Consider reviewing loss positions with a tax professional before year-end planning.",
                "estimated_impact": f"Rough loss pool: about ${abs(summary['total_unrealized_losses']):,.0f} unrealized (demo only).",
            }
        )

    st_gainers = [r for r in rows if r["unrealized_gain_loss"] > 0 and not r["is_long_term"]]
    if st_gainers:
        gsum = sum(r["unrealized_gain_loss"] for r in st_gainers)
        ts = sum(r["estimated_federal_tax_if_sold_now"] for r in st_gainers)
        syms = ", ".join(r["symbol"] for r in st_gainers)
        opps.append(
            {
                "title": "Short-term gain warning",
                "priority": "Medium",
                "explanation": "Gains on positions held one year or less are generally taxed at federal ordinary income rates, which are often higher than long-term rates.",
                "beginner_translation": "Quick flips can mean a bigger tax bite than waiting for long-term treatment.",
                "possible_action": "You may want to check whether holding longer could change how the gain is taxed.",
                "estimated_impact": f"Positions: {syms}. Combined unrealized gains ~${gsum:,.0f}; demo tax if all sold today ~${ts:,.0f}.",
            }
        )

    lt_gainers = [r for r in rows if r["unrealized_gain_loss"] > 0 and r["is_long_term"]]
    if lt_gainers:
        gsum = sum(r["unrealized_gain_loss"] for r in lt_gainers)
        syms = ", ".join(r["symbol"] for r in lt_gainers)
        opps.append(
            {
                "title": "Long-term capital gain reminder",
                "priority": "Low",
                "explanation": "Long-term gains may qualify for lower federal long-term capital gains rates (0%, 15%, or 20% in this demo) depending on taxable income.",
                "beginner_translation": "The IRS often taxes patience a bit more gently than short-term trading.",
                "possible_action": "Consider comparing long-term rates to your ordinary rate before selling.",
                "estimated_impact": f"Positions: {syms}. Combined unrealized gains ~${gsum:,.0f}.",
            }
        )

    if summary["dividend_income"] >= 500 or summary["dividend_income"] / total_mv >= 0.01:
        opps.append(
            {
                "title": "Dividend income may be taxable",
                "priority": "Medium",
                "explanation": "Qualified dividends are often taxed like long-term gains; non-qualified dividends are often taxed at ordinary rates. You may owe tax even if you do not sell.",
                "beginner_translation": "Some account activity shows up on your return without you clicking “sell.”",
                "possible_action": "Consider reviewing your 1099-DIV-style statements with a tax preparer.",
                "estimated_impact": f"Demo annual dividend tax estimate ~${summary['estimated_annual_dividend_tax']:,.0f} on ~${summary['dividend_income']:,.0f} dividends.",
            }
        )

    if _niit_applies(profile):
        opps.append(
            {
                "title": "Net Investment Income Tax (NIIT) may apply",
                "priority": "High",
                "explanation": "For this demo, if taxable income is above the NIIT threshold for your filing status, an extra 3.8% federal tax may apply to certain investment income in simplified modeling.",
                "beginner_translation": "Higher earners can pay an extra layer on some investment income.",
                "possible_action": "You may want to check NIIT rules with a CPA using your actual MAGI.",
                "estimated_impact": "Demo adds 3.8% on modeled gains/dividends when over threshold.",
            }
        )

    for r in rows:
        if r["current_value"] / total_mv > 0.25:
            opps.append(
                {
                    "title": f"Concentrated position: {r['symbol']}",
                    "priority": "Medium",
                    "explanation": "A large single-stock or single-fund position can mean both risk and a big tax event if you sell.",
                    "beginner_translation": "Too many eggs in one basket can mean a chunky tax bill if you exit.",
                    "possible_action": "Consider reviewing diversification and partial-sale strategies with a professional.",
                    "estimated_impact": f"~{r['current_value']/total_mv*100:.1f}% of portfolio value.",
                }
            )

    if any(o["title"] == "Tax-loss harvesting opportunity" for o in opps):
        opps.append(
            {
                "title": "Wash sale rule reminder",
                "priority": "Medium",
                "explanation": "If you sell at a loss and buy the same or substantially identical investment within 30 days before or after the sale, the loss may be disallowed for current-year use.",
                "beginner_translation": "You usually cannot sell red, buy right back, and still claim the loss immediately.",
                "possible_action": "Consider waiting more than 30 days or choosing a different investment if harvesting losses.",
                "estimated_impact": "Loss disallowance risk if rules are triggered.",
            }
        )

    return opps


STRATEGIES = (
    "Sell proportionally",
    "Sell loss-making holdings first",
    "Sell long-term holdings first",
    "Sell high-risk holdings first",
)


def simulate_sale_scenario(
    portfolio: list[dict[str, Any]],
    profile: dict[str, Any],
    sell_percentage: float,
    strategy: str,
) -> dict[str, Any]:
    if strategy not in STRATEGIES:
        strategy = STRATEGIES[0]
    sell_pct = max(0.0, min(100.0, float(sell_percentage))) / 100.0
    rows = [calculate_holding_tax(h, profile) for h in portfolio]
    total_mv = sum(r["current_value"] for r in rows) or 1.0
    target_sale = total_mv * sell_pct

    # Build sale allocation per holding (current_value sold)
    n = len(rows)
    sale_by_idx: dict[int, float] = {i: 0.0 for i in range(n)}

    if sell_pct <= 0 or target_sale <= 0:
        return {
            "amount_sold": 0.0,
            "realized_gain_loss": 0.0,
            "estimated_federal_tax": 0.0,
            "holdings_affected": [],
            "holdings_affected_detail": [],
            "effective_tax_rate_pct": 0.0,
            "explanation": "No sale selected. Taxes shown are zero in this demo scenario.",
            "strategy": strategy,
            "sell_percentage": sell_percentage,
        }

    if strategy == "Sell proportionally":
        for i, r in enumerate(rows):
            sale_by_idx[i] = r["current_value"] * sell_pct
    else:
        order = list(range(n))
        if strategy == "Sell loss-making holdings first":
            order.sort(key=lambda i: rows[i]["unrealized_gain_loss"])
        elif strategy == "Sell long-term holdings first":
            order.sort(key=lambda i: (not rows[i]["is_long_term"], -rows[i]["unrealized_gain_loss"]))
        elif strategy == "Sell high-risk holdings first":
            order.sort(
                key=lambda i: -RiskRank.get(portfolio[i].get("risk_level", "Medium"), 2)
            )
        remaining = target_sale
        for i in order:
            if remaining <= 0:
                break
            cap = rows[i]["current_value"]
            take = min(cap, remaining)
            sale_by_idx[i] = take
            remaining -= take
        if remaining > 1e-6:
            left_idxs = [i for i in range(n) if rows[i]["current_value"] - sale_by_idx[i] > 1e-6]
            mv_left = sum(rows[i]["current_value"] - sale_by_idx[i] for i in left_idxs)
            if mv_left > 0:
                for i in left_idxs:
                    room = rows[i]["current_value"] - sale_by_idx[i]
                    add = remaining * (room / mv_left)
                    add = min(add, room)
                    sale_by_idx[i] += add

    realized = 0.0
    tax_total = 0.0
    affected: list[str] = []
    for i, r in enumerate(rows):
        sold = sale_by_idx[i]
        if sold <= 0:
            continue
        frac = sold / r["current_value"] if r["current_value"] > 0 else 0.0
        gain_part = r["unrealized_gain_loss"] * frac
        realized += gain_part
        tax_total += federal_tax_on_gain(
            gain_part, r["is_long_term"], profile, apply_niit_to_this_gain=True
        )
        gl = "gain" if gain_part >= 0 else "loss"
        affected.append(
            f"{r['symbol']}: sold about ${sold:,.0f} of value; estimated {gl} ${abs(gain_part):,.0f}"
        )

    amount_sold = sum(sale_by_idx.values())
    if realized > 1e-6:
        eff_rate = min(100.0, max(0.0, (tax_total / realized) * 100))
    elif tax_total > 0:
        eff_rate = 0.0
    else:
        eff_rate = 0.0

    holdings_detail: list[dict[str, Any]] = []
    for i, r in enumerate(rows):
        sold = sale_by_idx[i]
        if sold <= 0:
            continue
        frac = sold / r["current_value"] if r["current_value"] > 0 else 0.0
        gain_part = r["unrealized_gain_loss"] * frac
        holdings_detail.append(
            {
                "symbol": r["symbol"],
                "name": r["name"],
                "sold_value": sold,
                "estimated_gain": gain_part,
            }
        )

    expl = (
        f"You modeled selling about **{sell_percentage:.0f}%** of the portfolio using **{strategy}**. "
        f"This creates about **${realized:,.0f}** of realized gain/loss (demo) and about **${tax_total:,.0f}** "
        f"of estimated federal tax. The estimate assumes each slice sold keeps the same short-term vs long-term "
        f"character as the whole position."
    )

    return {
        "amount_sold": amount_sold,
        "realized_gain_loss": realized,
        "estimated_federal_tax": tax_total,
        "holdings_affected": affected,
        "holdings_affected_detail": holdings_detail,
        "effective_tax_rate_pct": eff_rate,
        "explanation": expl,
        "strategy": strategy,
        "sell_percentage": sell_percentage,
    }


def compute_tax_narratives(summary: dict[str, Any]) -> dict[str, str]:
    """Short advisor-style insight strings for the Tax Snapshot (demo)."""
    rows = summary.get("holdings_detail", [])
    lt_pos = sum(
        r["unrealized_gain_loss"]
        for r in rows
        if r["unrealized_gain_loss"] > 0 and r["is_long_term"]
    )
    st_pos = sum(
        r["unrealized_gain_loss"]
        for r in rows
        if r["unrealized_gain_loss"] > 0 and not r["is_long_term"]
    )
    if lt_pos >= st_pos * 1.1:
        i1 = (
            "Your tax exposure may be moderate in this demo because a larger share of gains "
            "appears long-term, which often uses lower federal rates than short-term gains."
        )
    elif st_pos > 0:
        i1 = (
            "Your profile shows meaningful short-term gain exposure—if sold soon, those gains "
            "may be taxed at ordinary income rates in this simplified model."
        )
    else:
        i1 = (
            "Most positions look long-term or flat in this demo, which can mean a simpler tax picture "
            "than heavy short-term trading."
        )

    driver = max(rows, key=lambda r: r["estimated_federal_tax_if_sold_now"])
    i2 = (
        f"Your largest tax driver is {driver['symbol']} ({driver['name']}) with about "
        f"${driver['estimated_federal_tax_if_sold_now']:,.0f} estimated federal tax if sold now (demo)."
    )

    tlh = summary.get("tax_loss_harvesting_potential", 0.0)
    if tlh > 0:
        i3 = (
            f"You have about ${tlh:,.0f} of unrealized losses that may be reviewed for "
            f"tax-loss harvesting before realizing large gains."
        )
    else:
        i3 = (
            "There are no unrealized losses in this demo portfolio—tax-loss harvesting is less relevant "
            "until a position dips below cost."
        )

    return {"insight1": i1, "insight2": i2, "insight3": i3}


def generate_professional_copy_summary(
    portfolio: list[dict[str, Any]],
    summary: dict[str, Any],
    profile: dict[str, Any],
) -> str:
    """Concise copy-friendly paragraph tied to this portfolio (not generic)."""
    rows = summary.get("holdings_detail", [])
    tax_if_all = summary.get("estimated_federal_tax_if_sold_today", 0.0)
    tlh = summary.get("tax_loss_harvesting_potential", 0.0)
    div_inc = summary.get("dividend_income", 0.0)

    gainers = [r for r in rows if r["unrealized_gain_loss"] > 0]
    gainers.sort(key=lambda r: r["unrealized_gain_loss"], reverse=True)
    top_syms = [g["symbol"] for g in gainers[:2]]

    parts = [
        f"Based on this demo portfolio, the estimated federal tax if everything were sold today is about "
        f"${tax_if_all:,.0f} (simplified U.S. federal assumptions)."
    ]
    if top_syms:
        and_join = " and ".join(top_syms)
        parts.append(f"The largest taxable gains appear to come from {and_join}.")
    if tlh > 0:
        parts.append(
            f"There is also about ${tlh:,.0f} of unrealized loss that may be reviewed for tax-loss harvesting."
        )
    if div_inc > 0:
        parts.append(
            f"Expected dividend income in this demo is about ${div_inc:,.0f}—remember dividend taxation "
            f"depends on qualified vs non-qualified treatment."
        )
    if summary.get("niit_warning"):
        parts.append(
            "Income may be high enough that Net Investment Income Tax (NIIT) could apply—confirm with a tax pro."
        )
    if summary.get("concentration_warning"):
        parts.append(
            "One holding is concentrated relative to the portfolio—large sales may move taxes meaningfully."
        )
    parts.append(
        "Before selling, compare scenarios and watch wash sale rules if you buy back similar investments."
    )
    return " ".join(parts)


def build_premium_opportunity_cards(
    portfolio: list[dict[str, Any]],
    summary: dict[str, Any],
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Holding-specific opportunity cards for the premium Tax Planning UI.
    Each dict: title, priority, what_we_found, why_it_matters, possible_action, estimated_impact, tone
    """
    cards: list[dict[str, Any]] = []
    rows = summary.get("holdings_detail", [])
    total_cv = summary.get("total_current_value", 0.0) or 1.0

    for r in rows:
        if r["unrealized_gain_loss"] < -1e-6:
            loss_amt = abs(r["unrealized_gain_loss"])
            cards.append(
                {
                    "title": f"Tax-loss review: {r['name']}",
                    "priority": "High",
                    "what_we_found": (
                        f"**{r['name']}** ({r['symbol']}) has an unrealized **loss** of about "
                        f"**${loss_amt:,.0f}**."
                    ),
                    "why_it_matters": (
                        "Losses can offset capital gains. If losses exceed gains, up to **$3,000** of excess "
                        "loss may offset ordinary income in a year (federal, simplified)."
                    ),
                    "possible_action": (
                        "Review whether realizing this loss fits your plan—and avoid a **wash sale** if you "
                        "repurchase the same or substantially identical security."
                    ),
                    "estimated_impact": f"Potential loss offset up to **${loss_amt:,.0f}** of gains (demo).",
                    "tone": "success",
                }
            )

    if rows:
        top = max(rows, key=lambda r: r["unrealized_gain_loss"])
        if top["unrealized_gain_loss"] > 0:
            etax = top["estimated_federal_tax_if_sold_now"]
            cards.append(
                {
                    "title": f"Largest gain: {top['symbol']}",
                    "priority": "High",
                    "what_we_found": (
                        f"**{top['name']}** has the **largest unrealized gain** in this demo (~"
                        f"${top['unrealized_gain_loss']:,.0f})."
                    ),
                    "why_it_matters": (
                        "Selling this position first may create the **biggest tax bill** compared with other holdings."
                    ),
                    "possible_action": (
                        "Model partial sales or sequencing (e.g., losses first) before a large exit."
                    ),
                    "estimated_impact": f"About **${etax:,.0f}** estimated federal tax if sold now (demo).",
                    "tone": "warning",
                }
            )

    for r in rows:
        if r["unrealized_gain_loss"] > 0 and not r["is_long_term"]:
            cards.append(
                {
                    "title": f"Short-term gain: {r['symbol']}",
                    "priority": "Medium",
                    "what_we_found": (
                        f"**{r['name']}** is **short-term** with ~**${r['unrealized_gain_loss']:,.0f}** unrealized gain."
                    ),
                    "why_it_matters": (
                        "Short-term gains are modeled at **ordinary income** rates—often higher than long-term rates."
                    ),
                    "possible_action": (
                        "If you can wait, holding until long-term status may reduce modeled federal tax—if that fits your goals."
                    ),
                    "estimated_impact": (
                        f"Estimated tax if sold now: ~**${r['estimated_federal_tax_if_sold_now']:,.0f}** (demo)."
                    ),
                    "tone": "warning",
                }
            )

    div_inc = summary.get("dividend_income", 0.0)
    if div_inc > 0:
        cards.append(
            {
                "title": "Dividend taxation",
                "priority": "Medium",
                "what_we_found": (
                    f"This portfolio expects about **${div_inc:,.0f}** of **dividend income** in the demo year."
                ),
                "why_it_matters": (
                    "**Qualified** dividends are modeled at long-term rates; **non-qualified** dividends use ordinary rates."
                ),
                "possible_action": (
                    "Check your 1099-DIV breakdown and how dividends land in **taxable vs tax-advantaged** accounts."
                ),
                "estimated_impact": f"Modeled dividend tax (demo): ~**${summary.get('estimated_annual_dividend_tax', 0):,.0f}**.",
                "tone": "info",
            }
        )

    if summary.get("niit_warning"):
        cards.append(
            {
                "title": "NIIT may apply",
                "priority": "Medium",
                "what_we_found": summary["niit_warning"],
                "why_it_matters": (
                    "NIIT adds **3.8%** on certain investment income above thresholds (modeled simply here)."
                ),
                "possible_action": (
                    "Confirm filing status, MAGI, and whether NIIT applies to your situation with a tax professional."
                ),
                "estimated_impact": (
                    f"Modeled NIIT on the demo gain: ~**${summary.get('niit_estimate_on_gain', 0):,.0f}**."
                ),
                "tone": "warning",
            }
        )

    if summary.get("concentration_warning"):
        sym = summary.get("concentration_symbol")
        pct = summary.get("concentration_pct", 0.0)
        name = sym or ""
        for p in portfolio:
            if p.get("symbol") == sym:
                name = str(p.get("name", sym))
                break
        cards.append(
            {
                "title": f"Concentration: {sym}",
                "priority": "Medium",
                "what_we_found": summary["concentration_warning"],
                "why_it_matters": (
                    f"**{name}** is a large share of the portfolio—selling it could move taxes and risk more than smaller positions."
                ),
                "possible_action": (
                    "Consider gradual sales, diversification over time, or scenario planning before a big exit."
                ),
                "estimated_impact": (
                    f"This holding is about **{pct:.0f}%** of portfolio value in the demo."
                ),
                "tone": "warning",
            }
        )

    for p in portfolio:
        at = str(p.get("asset_type", "")).lower()
        if at == "mutual fund":
            sym = p.get("symbol", "")
            nm = p.get("name", sym)
            cards.append(
                {
                    "title": f"Fund distributions: {sym}",
                    "priority": "Low",
                    "what_we_found": (
                        f"**{nm}** is a **mutual fund**. Funds can pass **capital gains distributions** even if you did not sell."
                    ),
                    "why_it_matters": (
                        "A taxable distribution can add to your return even when the NAV drops—plan for possible year-end surprises."
                    ),
                    "possible_action": (
                        "Watch fund company estimates in Q4 and consider tax location (taxable vs IRA) for future purchases."
                    ),
                    "estimated_impact": "Varies by fund year—this demo does not model a specific distribution amount.",
                    "tone": "info",
                }
            )

    if summary.get("tax_loss_harvesting_potential", 0) > 0:
        cards.append(
            {
                "title": "Wash sale reminder",
                "priority": "Medium",
                "what_we_found": (
                    "If you **harvest a loss** and buy the **same or substantially identical** investment within "
                    "**30 days** before or after, the loss may be **disallowed** for the current year."
                ),
                "why_it_matters": (
                    "The IRS wash sale rule can surprise beginners who sell and rebuy quickly to stay invested."
                ),
                "possible_action": (
                    "Wait more than 30 days, use a different but not substantially identical holding, or plan with a CPA."
                ),
                "estimated_impact": "Loss disallowance risk if rules are triggered.",
                "tone": "warning",
            }
        )

    return cards


def get_premium_simple_plan(portfolio: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, str]:
    """Structured copy for the 'Quantify the value' premium card (demo)."""
    summary = calculate_tax_summary(portfolio, profile)
    rows = summary["holdings_detail"]
    tlh = summary["tax_loss_harvesting_potential"]
    loss_rows = [r for r in rows if r["unrealized_gain_loss"] < 0]
    st_gainers = [r for r in rows if r["unrealized_gain_loss"] > 0 and not r["is_long_term"]]

    if loss_rows:
        lr = min(loss_rows, key=lambda r: r["unrealized_gain_loss"])
        main = f"Review **{lr['name']}** before selling large profitable positions."
        impact = (
            f"You currently have about **${tlh:,.0f}** of unrealized losses that may offset part of your capital gains (demo)."
        )
        why = (
            "Losses can reduce taxable gains. If losses exceed gains, up to **$3,000** may offset ordinary income in a year "
            "(federal, simplified)."
        )
        review = (
            "Check **wash sale** rules before selling and buying back the same or substantially identical investment."
        )
    elif st_gainers:
        sg = max(st_gainers, key=lambda r: r["unrealized_gain_loss"])
        main = f"Treat **{sg['symbol']}** as a short-term tax hotspot until it goes long-term (if that fits your plan)."
        impact = (
            f"Short-term gains are modeled at ordinary rates—**{sg['symbol']}** shows about "
            f"**${sg['unrealized_gain_loss']:,.0f}** unrealized gain (demo)."
        )
        why = (
            "Waiting for long-term status can sometimes lower the modeled federal rate on gains—but markets and goals matter too."
        )
        review = "Confirm your holding period dates and whether waiting aligns with your risk tolerance."
    elif summary.get("concentration_warning"):
        sym = summary.get("concentration_symbol", "a holding")
        main = f"Plan exits from **{sym}** carefully—it is a large share of this demo portfolio."
        impact = (
            f"Estimated federal tax if **everything** were sold today is about **${summary['estimated_federal_tax_if_sold_today']:,.0f}** (demo)."
        )
        why = "Concentrated positions can mean a large tax event in one year if you sell all at once."
        review = "Use scenario analysis to model partial sales and sequencing."
    else:
        main = "Favor a **planned** selling approach rather than one-off reactions to headlines."
        impact = (
            f"Estimated federal tax if all positions were sold today: about **${summary['estimated_federal_tax_if_sold_today']:,.0f}** (demo)."
        )
        why = "Long-term gains are often modeled at lower rates than short-term gains in this educational tool."
        review = "Revisit inputs (taxable income, filing status) before relying on any estimate."

    return {
        "main_recommendation": main,
        "estimated_impact": impact,
        "why_it_matters": why,
        "what_to_review": review,
    }


def gain_breakdown_plain_summary(summary: dict[str, Any]) -> str:
    """One short paragraph below the gain breakdown table (demo)."""
    rows = summary.get("holdings_detail", [])
    pos = [r for r in rows if r["unrealized_gain_loss"] > 0]
    neg = [r for r in rows if r["unrealized_gain_loss"] < 0]
    lt_share = sum(r["unrealized_gain_loss"] for r in pos if r["is_long_term"])
    st_share = sum(r["unrealized_gain_loss"] for r in pos if not r["is_long_term"])
    parts: list[str] = []
    if lt_share >= st_share and lt_share > 0:
        parts.append(
            "Most of your **taxable gain** in this demo comes from **long-term** holdings, which may receive "
            "**lower** federal tax rates than short-term gains."
        )
    elif st_share > 0:
        parts.append(
            "A meaningful part of gains is **short-term** in this demo, which may be taxed at **ordinary** rates if sold soon."
        )
    if neg:
        parts.append(
            f"**{len(neg)}** loss-making holding(s) may help **offset** gains if tax-loss harvesting fits your situation."
        )
    return " ".join(parts) if parts else "This demo portfolio is roughly balanced between gains and losses across positions."


def generate_simple_tax_plan(portfolio: list[dict[str, Any]], profile: dict[str, Any]) -> list[str]:
    opps = detect_tax_opportunities(portfolio, profile)
    lines = [
        "Review loss-making stocks or mutual funds before selling profitable holdings, if tax-loss harvesting fits your situation.",
        "Avoid unnecessary short-term selling if it creates higher ordinary-income tax on gains.",
        "Check whether waiting until a holding becomes long-term may reduce the federal rate on gains.",
        "Remember that dividends may be taxable even if you do not sell shares.",
        "Be careful about wash sale rules if selling at a loss and buying back a substantially identical investment too soon.",
        "Use the scenario analysis slider before making a sell decision to see a demo tax range.",
    ]
    if any("NIIT" in o["title"] for o in opps):
        lines.append(
            "If your income is high enough, ask a professional whether the Net Investment Income Tax affects you."
        )
    if any("Concentrated" in o["title"] for o in opps):
        lines.append(
            "Consider whether large single positions match your comfort with risk and tax timing."
        )
    return lines


# --- Demo portfolio (Stock / Mutual Fund only)
DEMO_US_PORTFOLIO: list[dict[str, Any]] = [
    {
        "name": "Sample U.S. Growth Stock",
        "symbol": "DEMO1",
        "asset_type": "Stock",
        "quantity": 100,
        "buy_price": 45.0,
        "current_price": 78.0,
        "buy_date": "2024-06-15",
        "risk_level": "High",
        "category": "Growth",
        "expected_dividend_income": 120.0,
        "dividend_type": "Qualified",
        "tax_category": "Equity",
    },
    {
        "name": "Sample Index Mutual Fund",
        "symbol": "DEMOMX",
        "asset_type": "Mutual Fund",
        "quantity": 250,
        "buy_price": 36.0,
        "current_price": 42.5,
        "buy_date": "2022-03-01",
        "risk_level": "Medium",
        "category": "Index",
        "expected_dividend_income": 890.0,
        "dividend_type": "Qualified",
        "tax_category": "Mutual Fund",
    },
    {
        "name": "Sample Value Stock",
        "symbol": "DEMO2",
        "asset_type": "Stock",
        "quantity": 80,
        "buy_price": 62.0,
        "current_price": 54.0,
        "buy_date": "2025-01-10",
        "risk_level": "Medium",
        "category": "Value",
        "expected_dividend_income": 200.0,
        "dividend_type": "Non-Qualified",
        "tax_category": "Equity",
    },
    {
        "name": "Sample Balanced Mutual Fund",
        "symbol": "DEMOBAL",
        "asset_type": "Mutual Fund",
        "quantity": 400,
        "buy_price": 22.0,
        "current_price": 24.8,
        "buy_date": "2023-11-20",
        "risk_level": "Low",
        "category": "Balanced",
        "expected_dividend_income": 640.0,
        "dividend_type": "Qualified",
        "tax_category": "Mutual Fund",
    },
    {
        "name": "Sample Sector Stock",
        "symbol": "DEMO3",
        "asset_type": "Stock",
        "quantity": 40,
        "buy_price": 110.0,
        "current_price": 205.0,
        "buy_date": "2019-05-01",
        "risk_level": "High",
        "category": "Sector",
        "expected_dividend_income": 80.0,
        "dividend_type": "Qualified",
        "tax_category": "Equity",
    },
]

DEMO_USER_PROFILE: dict[str, Any] = {
    "annual_income": 185_000,
    "taxable_income": 165_000,
    "filing_status": "Single",
    "state": "California",
    "age": 38,
    "investment_goal": "Retirement",
    "goal_time_horizon_years": 22,
}
