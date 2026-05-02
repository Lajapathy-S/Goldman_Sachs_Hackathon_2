"""Shared Claude helpers for Streamlit (Agent chat + goal coach)."""

from __future__ import annotations

import os
from typing import Any

# Default if ANTHROPIC_MODEL is unset. Older IDs (e.g. claude-3-5-sonnet-20241022) are retired and will 404.
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"


def resolved_model_name() -> str:
    return os.environ.get("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL).strip() or DEFAULT_ANTHROPIC_MODEL


def _model() -> str:
    return resolved_model_name()


def claude_complete(api_key: str, system: str, user_text: str, max_tokens: int = 1200) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=_model(),
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_text}],
    )
    block = msg.content[0]
    return block.text if hasattr(block, "text") else str(block)


def claude_chat_with_history(
    api_key: str,
    system: str,
    history: list[tuple[str, str]],
    new_user_message: str,
    max_tokens: int = 1200,
) -> str:
    """history: list of (role, content) with role 'user' or 'assistant'."""
    import anthropic

    msgs: list[dict[str, str]] = []
    for role, content in history:
        r = "user" if role == "user" else "assistant"
        msgs.append({"role": r, "content": content})
    msgs.append({"role": "user", "content": new_user_message})

    client = anthropic.Anthropic(api_key=api_key)
    out = client.messages.create(
        model=_model(),
        max_tokens=max_tokens,
        system=system,
        messages=msgs,
    )
    block = out.content[0]
    return block.text if hasattr(block, "text") else str(block)


WHATIF_SYSTEM = """You are **REBA**, a friendly financial educator for complete beginners (retail investors).

Scope (strict):
- You ONLY discuss personal finance and investing topics: money, saving, budgeting, debt, taxes at a high level,
  portfolios, mutual funds, stocks (general), retirement accounts, inflation, markets, risk, withdrawals, goals, fees,
  diversification, and related "what if" scenarios. Nothing else.
- Questions about **buying vs selling**, **when people trade**, **holding vs selling**, or vague prompts like
  *buy/sell the stock* are **in scope**. Answer with educational bullets: planning, time horizon, diversification,
  costs, taxes, emotions, and why nobody can promise the “right” time to trade. Do **not** tell them to buy or sell
  a specific security; keep it general and remind them this is not personal advice.
- Saving for a **vacation**, **travel**, **education**, a **home**, an **emergency fund**, or other **short- or long-term
  money goals** is in scope—answer with practical bullets (timing, liquidity, diversification, trade-offs).
- Use the **refusal template** (exactly the two bullets below) **only** when the topic is clearly **not** about money or
  investing (e.g. coding, homework, sports, recipes, health, politics, gossip, creative writing, general chit-chat).
  **Never** use that refusal for investing or trading questions, even if the message is short or poorly worded.
  Refusal template (only when off-topic):
  - I only answer **finance and investing** questions in simple language (I’m REBA).
  - Try a money question—for example: *What if inflation stays high?* or *What if I need to withdraw next year?*
- Never pretend to be a licensed advisor; this is educational, not personal advice.

Format:
- Answer ONLY with bullet points. Start every bullet with "- " (markdown list). Use 7–11 bullets when you do answer.
- Cover the "what if" clearly, in plain language. No guarantees, no promised returns.
- Do NOT use: alpha, beta, Sharpe ratio, standard deviation (unless you define it in one short phrase—prefer omitting).
- Do not name real companies or tickers; say "diversified mutual funds" or "sample stocks" if needed.
- Keep each bullet one or two short sentences.
- For any answer that involves changing portfolio mix / buy-sell / withdrawal / risk adjustment, include these transparently:
  1) **Costs** (fees, spreads, expense ratios, or transaction costs that may apply),
  2) **Tax implications** (possible gains/loss realization, taxable events, and a brief local-tax caution),
  3) **Goal alignment** (how the adjustment supports the user’s long-term goal and timeline).
- Translate complex logic into beginner language. If you use technical reasoning, add a plain-English line like:
  "Simple logic: ...".
- Prefer this structure when relevant:
  - What changes
  - Why
  - Costs
  - Tax implications
  - Long-term goal alignment
  - Simple logic
- Business-grade interaction requirement:
  - Give the core answer first.
  - Then always end with exactly **3 follow-up questions** a planner/analyst would ask before finalizing advice.
  - The 3 questions must be **specific to the user's prompt** (scenario-aware), not a fixed generic set.
  - Label them clearly as:
    - **Question 1:** ...
    - **Question 2:** ...
    - **Question 3:** ..."""


GOAL_COACH_SYSTEM = """You are a financial coach for beginners. The user completed a short goal questionnaire.

Rules:
- The JSON includes **mainGoalLabel** (e.g. Home, Retirement, Education, Emergency fund). Use that exact goal in your bullets—do not replace it with another goal.
- Respond ONLY with bullet points. Start every bullet with "- ". Use 8–12 bullets.
- Summarize what their answers imply for how much risk might feel okay and how to think about time horizon.
- Mention diversification and avoiding "all in one bet" in simple words.
- Remind them this is educational, not personal financial advice.
- No alpha, beta, Sharpe.
- Include a section in bullets titled **Suggested now (educational examples)**, tailored to goal + years + risk, with:
  1) **Stocks now (examples):** 3–5 examples using real, well-known listed companies (large and liquid),
  2) **Mutual funds now (examples):** 3–5 examples using real, widely available mutual funds / index funds.
- Keep suggestions practical ("what kind of assets now"), not guaranteed picks.
- Use **US market examples by default** (US-listed companies and US mutual funds/ETFs), unless the user explicitly asks for another country.
- Add one short caution line: "Examples only; verify current market price, expense ratio, and suitability before investing."
- Be warm and practical."""


def whatif_reply(
    api_key: str | None, user_text: str, history: list[tuple[str, str]]
) -> tuple[str, str, str | None]:
    """Returns (reply_text, source, api_error). source is 'claude' or 'fallback'; api_error set if Claude failed."""
    if not api_key:
        return _fallback_whatif_bullets(user_text), "fallback", None
    try:
        text = claude_chat_with_history(api_key, WHATIF_SYSTEM, history, user_text)
        if not text.strip():
            return _fallback_whatif_bullets(user_text), "fallback", "Empty response from Claude."
        return text.strip(), "claude", None
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        return _fallback_whatif_bullets(user_text), "fallback", err[:800]


def goal_coach_reply(api_key: str | None, profile: dict[str, Any]) -> tuple[str, str, str | None]:
    if not api_key:
        return _fallback_goal_bullets(profile), "fallback", None
    try:
        import json

        user = f"Goal profile (JSON):\n{json.dumps(profile, indent=2)}\n\nWrite the bullet summary for this person."
        text = claude_complete(api_key, GOAL_COACH_SYSTEM, user, max_tokens=900)
        if not text.strip():
            return _fallback_goal_bullets(profile), "fallback", "Empty response from Claude."
        return text.strip(), "claude", None
    except Exception as e:
        err = f"{type(e).__name__}: {e}"
        return _fallback_goal_bullets(profile), "fallback", err[:800]


def _fallback_whatif_bullets(user_text: str) -> str:
    t = user_text.lower()

    def _follow_up_questions() -> str:
        # Scenario-aware prompts so follow-up questions are tailored, not static.
        if "withdraw" in t or "cash" in t or "need" in t:
            return (
                "- **Question 1:** What is the exact withdrawal date, and can it be split into tranches instead of one-time selling?\n"
                "- **Question 2:** Which account will you sell from first (taxable vs tax-advantaged), and do you know the unrealized gains there?\n"
                "- **Question 3:** After withdrawing this amount, what minimum emergency-cash buffer do you want to keep?"
            )
        if "inflation" in t:
            return (
                "- **Question 1:** Over what horizon (3, 5, 10+ years) are you trying to protect purchasing power?\n"
                "- **Question 2:** What proportion is currently in cash/fixed-income versus equities/funds?\n"
                "- **Question 3:** Are there near-term expenses that require stability before we increase growth exposure?"
            )
        if "20" in t and ("market" in t or "drop" in t or "crash" in t):
            return (
                "- **Question 1:** If markets drop another 10-15%, would you add, hold, or reduce risk further?\n"
                "- **Question 2:** Which holdings are most concentrated and causing the largest drawdown in your portfolio?\n"
                "- **Question 3:** Do you have planned cash inflows (salary/bonuses) that can fund rebalancing without forced selling?"
            )
        if any(w in t for w in ("buy", "sell", "trading", "trade", "stock", "stocks", "share", "fund", "portfolio")):
            return (
                "- **Question 1:** What is the objective of this move: reduce risk, raise cash, or improve long-term return potential?\n"
                "- **Question 2:** What is your maximum acceptable short-term drawdown after this change?\n"
                "- **Question 3:** Are there tax lots, fees, or lock-ins we should prioritize before deciding what to buy/sell first?"
            )
        return (
            "- **Question 1:** What is your target goal date and how flexible is it?\n"
            "- **Question 2:** What is your current allocation across stocks, funds, and cash today?\n"
            "- **Question 3:** What constraints matter most right now: taxes, liquidity, or limiting drawdown?"
        )

    if any(w in t for w in ("buy", "sell", "trading", "trade")) and any(
        w in t for w in ("stock", "stocks", "share", "fund", "portfolio", "market", "invest")
    ):
        core = (
            "- **Buying vs selling** is personal: it depends on your **goal date**, **risk comfort**, and whether this "
            "money is **long-term** or needed soon.\n"
            "- Many beginners reduce regret by using **diversified mutual funds** instead of one-off bets on single names.\n"
            "- Selling can trigger **taxes and fees**; buying after a spike can mean paying more volatility—there is no "
            "guaranteed “right time.”\n"
            "- A simple habit is to **rebalance in small steps** toward a target mix rather than one emotional all-in move.\n"
            "- If the question is vague, clarify **when** you need the money and **how much** loss you could tolerate for "
            "that timeline.\n"
            "- This is not a recommendation to buy or sell any specific security."
        )
        return core + "\n" + _follow_up_questions()
    if "20" in t and ("market" in t or "drop" in t or "crash" in t):
        core = (
            "- A large market drop can feel scary; a common adjustment is trimming the riskiest slice and adding to **diversified mutual funds** in small steps.\n"
            "- **Costs:** switching can involve brokerage, spreads, or fund expense ratios, so frequent churn can hurt returns.\n"
            "- **Tax implications:** selling appreciated holdings may realize capital gains; check local rules before executing.\n"
            "- **Long-term goal alignment:** this can reduce short-term shock while keeping growth exposure for goals that are years away.\n"
            "- **Simple logic:** keep near-term money stable, and let long-term money stay diversified instead of reacting in one big move.\n"
            "- Use **REBA** under **Agents** to talk through scenario trade-offs."
        )
        return core + "\n" + _follow_up_questions()
    if "inflation" in t:
        core = (
            "- High inflation can erode idle **cash**, so many people keep long-horizon money partly in diversified growth assets.\n"
            "- **Costs:** changing funds may involve exit loads, transaction charges, or higher expense ratios.\n"
            "- **Tax implications:** reallocating in taxable accounts can trigger gains/losses; treatment differs by region and asset type.\n"
            "- **Long-term goal alignment:** the split should match your timeline (near-term spending bucket vs long-term compounding bucket).\n"
            "- **Simple logic:** protect soon-needed money with steadier options, and keep distant-goal money diversified for growth potential.\n"
            "- Not personal advice."
        )
        return core + "\n" + _follow_up_questions()
    if "withdraw" in t or "cash" in t:
        core = (
            "- If you need a **large withdrawal soon**, many investors first park that slice in liquid / low-volatility options.\n"
            "- **Costs:** check redemption fees, spread impact, and any penalties for early exits.\n"
            "- **Tax implications:** sales in taxable accounts can create reportable gains/losses; sequence of selling matters.\n"
            "- **Long-term goal alignment:** ring-fencing the withdrawal bucket helps the remaining portfolio stay aligned with long-term goals.\n"
            "- **Simple logic:** secure near-term cash needs first, then keep the rest invested to match your timeline.\n"
            "- Not financial advice—just a transparent educational framework."
        )
        return core + "\n" + _follow_up_questions()
    core = (
        "- Start with two anchors: **timeline** (when money is needed) and **risk comfort** (how much drawdown you can handle).\n"
        "- **Costs:** any adjustment can involve fees, spreads, or fund expenses, so avoid over-trading.\n"
        "- **Tax implications:** selling can realize gains/losses; check local tax treatment before changing allocations.\n"
        "- **Long-term goal alignment:** your mix should map to your goal date, not short-term headlines.\n"
        "- **Simple logic:** keep short-term money stable and long-term money diversified, then rebalance in small steps.\n"
        "- Not a recommendation to buy or sell anything."
    )
    return core + "\n" + _follow_up_questions()


def _fallback_goal_bullets(profile: dict[str, Any]) -> str:
    g = profile.get("mainGoalLabel") or profile.get("mainGoal", "your goal")
    y_raw = profile.get("years", "?")
    try:
        y_num = int(y_raw)
    except Exception:
        y_num = 10
    y = y_raw
    r = profile.get("riskLabel", "balanced")
    if y_num <= 5 or "cautious" in str(r).lower():
        stock_examples = "Microsoft, Johnson & Johnson, Procter & Gamble, Coca-Cola"
        mf_examples = (
            "Vanguard Total Bond Market Index Fund (VBTLX), Vanguard Wellesley Income Fund (VWINX), "
            "Fidelity 500 Index Fund (FXAIX), Vanguard Short-Term Treasury Fund (VFISX)"
        )
    elif y_num <= 12:
        stock_examples = "Apple, Microsoft, Johnson & Johnson, JPMorgan Chase, Costco"
        mf_examples = (
            "Vanguard 500 Index Fund (VFIAX), Fidelity Total Market Index Fund (FSKAX), "
            "Vanguard Balanced Index Fund (VBIAX), American Funds Fundamental Investors (ANCFX)"
        )
    else:
        stock_examples = "Apple, Microsoft, Alphabet, Visa, UnitedHealth Group"
        mf_examples = (
            "Vanguard Total Stock Market Index Fund (VTSAX), Fidelity 500 Index Fund (FXAIX), "
            "Vanguard Growth Index Fund (VIGAX), Vanguard Total International Stock Index Fund (VTIAX)"
        )
    return (
        f"- Your answers point to a **{r}** comfort style with about **{y} years** in view.\n"
        f"- Main theme: **{g}**—keep that as the north star when markets get noisy.\n"
        "- Shorter timelines usually mean **less** in the riskiest sleeve; longer ones allow more growth focus.\n"
        "- **Diversified mutual funds** often beat guessing single winners for beginners.\n"
        "- **Suggested now (educational examples):**\n"
        f"- **Stocks now (examples):** {stock_examples}.\n"
        f"- **Mutual funds now (examples):** {mf_examples}.\n"
        "- Examples only; verify current market price, expense ratio, and suitability before investing.\n"
        "- Revisit this once a year or after a big life change (job, family, health).\n"
        "- This summary is educational—not personal financial advice.\n"
        "- Add **ANTHROPIC_API_KEY** in secrets for a tailored AI write-up."
    )
