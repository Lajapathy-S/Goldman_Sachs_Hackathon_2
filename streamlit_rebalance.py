"""Mock + Claude rebalance logic for Streamlit (no Node required)."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from pydantic import BaseModel

from streamlit_claude_client import resolved_model_name


class RecommendedAllocation(BaseModel):
    stocks: float
    mutualFunds: float
    cashOrLiquidFunds: float


class ActionItem(BaseModel):
    action: str
    amountOrPercent: str
    fromAsset: str
    toAsset: str
    reason: str


class TransparencyNotes(BaseModel):
    costs: str
    taxes: str
    riskExplanation: str
    goalAlignment: str


class RebalanceResponse(BaseModel):
    scenario: str
    portfolioHealth: str
    riskLevelBefore: str
    riskLevelAfter: str
    summary: str
    recommendedAllocation: RecommendedAllocation
    actions: list[ActionItem]
    transparencyNotes: TransparencyNotes
    beginnerExplanation: str


SCENARIO_PROMPTS: dict[str, str] = {
    "market-drop": (
        "What if the broad market drops about 20%? Reduce high-risk single-stock exposure "
        "where sensible and shift part of the portfolio toward diversified mutual funds or "
        "steadier sleeves. Use only placeholder asset names."
    ),
    "high-inflation": (
        "What if inflation stays high for a while? Reduce idle cash where too large, keep "
        "sensible diversified equity exposure for long-term goals, and suggest diversified "
        "mutual funds rather than chasing single hot names. Placeholder assets only."
    ),
    "planned-withdrawal": (
        "What if the user needs to withdraw about 20% of portfolio value next year? Move "
        "that portion toward low-risk / liquid mutual funds or cash-like funds and reduce "
        "volatility for that slice."
    ),
    "income-risk": (
        "What if the user may lose income for about 6 months? Increase emergency / liquid "
        "allocation and reduce the riskiest stock sleeve."
    ),
    "timeline-sooner": (
        "What if the user needs their money sooner than planned? Reduce portfolio risk and "
        "shift toward safer diversified mutual funds instead of concentrated stocks."
    ),
}

SCENARIO_LABEL = {
    "market-drop": "Market drop (~20%)",
    "high-inflation": "High inflation",
    "planned-withdrawal": "Planned withdrawal (20% next year)",
    "income-risk": "Income interruption (~6 months)",
    "timeline-sooner": "Need money sooner",
}


def sum_by_type(portfolio: list[dict[str, Any]]) -> dict[str, float]:
    stocks = mutual_funds = cash = 0.0
    for row in portfolio:
        v = float(row.get("value") or 0)
        t = row.get("type")
        if t == "stock":
            stocks += v
        elif t == "mutual_fund":
            mutual_funds += v
        else:
            cash += v
    total = stocks + mutual_funds + cash or 1.0
    return {
        "stocks": round(stocks / total * 1000) / 10,
        "mutualFunds": round(mutual_funds / total * 1000) / 10,
        "cashOrLiquidFunds": round(cash / total * 1000) / 10,
        "total": total,
    }


def build_mock_rebalance(scenario_id: str, portfolio: list[dict[str, Any]]) -> dict[str, Any]:
    before = sum_by_type(portfolio)
    rec = {
        "stocks": before["stocks"],
        "mutualFunds": before["mutualFunds"],
        "cashOrLiquidFunds": before["cashOrLiquidFunds"],
    }

    def shift(from_stock: float, to_mf: float, to_cash: float) -> None:
        nonlocal rec
        rec["stocks"] = max(5.0, round((before["stocks"] + from_stock) * 10) / 10)
        rec["mutualFunds"] = max(10.0, round((before["mutualFunds"] + to_mf) * 10) / 10)
        rec["cashOrLiquidFunds"] = max(
            5.0, round((before["cashOrLiquidFunds"] + to_cash) * 10) / 10
        )
        s = rec["stocks"] + rec["mutualFunds"] + rec["cashOrLiquidFunds"]
        rec["stocks"] = round(rec["stocks"] / s * 1000) / 10
        rec["mutualFunds"] = round(rec["mutualFunds"] / s * 1000) / 10
        rec["cashOrLiquidFunds"] = round((100 - rec["stocks"] - rec["mutualFunds"]) * 10) / 10

    summary = ""
    actions: list[dict[str, str]] = []

    if scenario_id == "market-drop":
        shift(-12, 10, 2)
        summary = (
            "Trim concentrated stock risk and lean on diversified mutual funds while "
            "keeping a small stability bucket."
        )
        actions = [
            {
                "action": "Simulated shift",
                "amountOrPercent": "~12% of portfolio from stocks toward mutual funds",
                "fromAsset": "Higher-risk stock sleeve",
                "toAsset": "Broad diversified mutual funds",
                "reason": (
                    "When markets fall sharply, single stocks often swing more than funds. "
                    "Spreading into diversified funds can make the ride steadier for beginners."
                ),
            },
            {
                "action": "Simulated trim",
                "amountOrPercent": "Optional top-up to cash/liquid sleeve",
                "fromAsset": "Remaining stock trades (if any)",
                "toAsset": "Liquid / cash-style mutual fund",
                "reason": (
                    "Keeps money you might need soon easier to access without timing a recovery."
                ),
            },
        ]
    elif scenario_id == "high-inflation":
        shift(-5, 3, 2)
        summary = (
            "Reduce idle cash drag, keep long-term growth via diversified equity funds, "
            "and add a modest stability sleeve."
        )
        actions = [
            {
                "action": "Simulated shift",
                "amountOrPercent": "~5% from idle cash toward diversified equity funds",
                "fromAsset": "Cash / liquid sleeve",
                "toAsset": "Diversified equity mutual funds",
                "reason": (
                    "Cash loses buying power when prices rise. Moving only part reduces risk "
                    "of missing long-term growth."
                ),
            },
        ]
    elif scenario_id == "planned-withdrawal":
        shift(-8, -2, 10)
        summary = (
            "Park the amount you need next year in liquid, lower-bounce assets; keep the "
            "rest invested to plan."
        )
        actions = [
            {
                "action": "Simulated carve-out",
                "amountOrPercent": "~20% of portfolio into liquid / low-volatility sleeve",
                "fromAsset": "Stock and riskier fund sleeves",
                "toAsset": "Cash / liquid mutual funds",
                "reason": (
                    "Money you will spend soon should not ride the same bumps as long-term "
                    "growth money."
                ),
            },
        ]
    elif scenario_id == "income-risk":
        shift(-10, 2, 8)
        summary = (
            "Build a larger emergency buffer and dial back the riskiest sleeve until "
            "income stabilizes."
        )
        actions = [
            {
                "action": "Simulated shift",
                "amountOrPercent": "~8–10% toward liquid / short-duration funds",
                "fromAsset": "Higher-risk stocks",
                "toAsset": "Liquid or short-duration mutual funds",
                "reason": (
                    "If paychecks pause, you want several months of expenses where you can tap "
                    "without forced selling at bad times."
                ),
            },
        ]
    elif scenario_id == "timeline-sooner":
        shift(-15, 5, 10)
        summary = (
            "Shorten the runway: move toward steadier funds because you have less time to "
            "recover from dips."
        )
        actions = [
            {
                "action": "Simulated de-risk",
                "amountOrPercent": (
                    "~15% from stocks toward diversified bond-style / balanced mutual funds"
                ),
                "fromAsset": "Stock sleeve",
                "toAsset": "Balanced or bond-oriented mutual funds",
                "reason": (
                    "When the goal is closer, large swings hurt more than they help. Steadier "
                    "funds match a shorter clock."
                ),
            },
        ]
    else:
        summary = "Keep your current mix unless goals or timing change; revisit twice a year."

    total = before["total"]
    return {
        "scenario": SCENARIO_LABEL.get(scenario_id, scenario_id),
        "portfolioHealth": (
            "Very small portfolio — focus on saving habit before fine-tuning."
            if total < 1000
            else "Portfolio mix is readable; next step is aligning risk with when you need the money."
        ),
        "riskLevelBefore": (
            "Higher (stock-heavy)"
            if before["stocks"] >= 55
            else "Moderate"
            if before["stocks"] >= 35
            else "Lower"
        ),
        "riskLevelAfter": (
            "Higher (stock-heavy)"
            if rec["stocks"] >= 55
            else "Moderate"
            if rec["stocks"] >= 35
            else "Lower"
        ),
        "summary": summary,
        "recommendedAllocation": {
            "stocks": rec["stocks"],
            "mutualFunds": rec["mutualFunds"],
            "cashOrLiquidFunds": rec["cashOrLiquidFunds"],
        },
        "actions": actions,
        "transparencyNotes": {
            "costs": (
                "Demo only: real brokers charge brokerage, spreads, and fund expense ratios. "
                "Check your statements before trading."
            ),
            "taxes": (
                "Selling winners in taxable accounts may trigger taxes. This toy model does "
                "not calculate tax — talk to a qualified professional."
            ),
            "riskExplanation": (
                "We describe risk in plain words (how bumpy the ride may feel), not using "
                "Greek letters or Wall Street shorthand."
            ),
            "goalAlignment": (
                "Any shift here is meant to match the scenario you picked — not to promise "
                "returns or beat the market."
            ),
        },
        "beginnerExplanation": (
            'Think of this as a practice drill: you told us a story (“what if…”), and we '
            "showed one simple way to adjust your buckets. Real life needs your broker, "
            "goals, and maybe an advisor."
        ),
    }


def build_user_prompt(
    scenario_id: str, portfolio: list[dict[str, Any]], goal_profile: Any
) -> str:
    scenario_text = SCENARIO_PROMPTS.get(scenario_id, SCENARIO_PROMPTS["market-drop"])
    return f"""You are helping a beginner retail investor. Output VALID JSON ONLY — no markdown, no prose outside JSON.

Rules:
- Use simple words. Do NOT use: alpha, beta, Sharpe ratio, standard deviation, or volatility unless you explain in one short beginner sentence (prefer avoid entirely).
- Do not promise returns or guarantee outcomes.
- Do not name real tickers or real companies. Use generic labels like "Sample stock A", "Diversified equity fund", "Liquid fund".
- recommendedAllocation stocks/mutualFunds/cashOrLiquidFunds must be numbers that sum to 100 (percent).
- actions: 2 to 4 items simulating buy/sell/shift with clear reasons.

Selected scenario id: {scenario_id}
Scenario description: {scenario_text}

Optional goal profile (JSON): {json.dumps(goal_profile)}

Current holdings (JSON array): {json.dumps(portfolio)}

Compute current allocation by grouping: stock type -> stocks bucket, mutual_fund -> mutualFunds bucket, cash_or_liquid -> cashOrLiquidFunds bucket (by value).

Return JSON with this exact shape and keys:
{{
  "scenario": "short label",
  "portfolioHealth": "one sentence",
  "riskLevelBefore": "plain words e.g. Moderate",
  "riskLevelAfter": "plain words",
  "summary": "2 sentences max",
  "recommendedAllocation": {{ "stocks": number, "mutualFunds": number, "cashOrLiquidFunds": number }},
  "actions": [{{ "action": "", "amountOrPercent": "", "fromAsset": "", "toAsset": "", "reason": "" }}],
  "transparencyNotes": {{ "costs": "", "taxes": "", "riskExplanation": "", "goalAlignment": "" }},
  "beginnerExplanation": "short paragraph"
}}"""


def parse_rebalance_json(raw: str) -> RebalanceResponse:
    text = raw.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    data = json.loads(text)
    return RebalanceResponse.model_validate(data)


def run_rebalance(
    portfolio: list[dict[str, Any]],
    scenario_id: str,
    goal_profile: Any,
    api_key: str | None,
    model: str | None = None,
) -> dict[str, Any]:
    if scenario_id not in SCENARIO_PROMPTS:
        raise ValueError("invalid scenario")

    if not api_key:
        out = build_mock_rebalance(scenario_id, portfolio)
        out["_source"] = "mock"
        return out

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    mdl = model or resolved_model_name()
    msg = client.messages.create(
        model=mdl,
        max_tokens=4096,
        messages=[
            {"role": "user", "content": build_user_prompt(scenario_id, portfolio, goal_profile)}
        ],
    )
    block = msg.content[0]
    raw_text = block.text if hasattr(block, "text") else ""
    if not raw_text:
        out = build_mock_rebalance(scenario_id, portfolio)
        out["_source"] = "mock_fallback"
        out["_warning"] = "empty_claude_response"
        return out
    try:
        parsed = parse_rebalance_json(raw_text)
        d = parsed.model_dump()
        d["_source"] = "claude"
        return d
    except Exception:
        out = build_mock_rebalance(scenario_id, portfolio)
        out["_source"] = "mock_fallback"
        out["_warning"] = "invalid_json_from_model"
        return out
