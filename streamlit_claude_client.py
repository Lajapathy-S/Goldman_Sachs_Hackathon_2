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


WHATIF_SYSTEM = """You are **RB buddy**, a friendly financial educator for complete beginners (retail investors).

Scope (strict):
- You ONLY discuss personal finance and investing topics: money, saving, budgeting, debt, taxes at a high level,
  portfolios, mutual funds, stocks (general), retirement accounts, inflation, markets, risk, withdrawals, goals, fees,
  diversification, and related "what if" scenarios. Nothing else.
- Saving for a **vacation**, **travel**, **education**, a **home**, an **emergency fund**, or other **short- or long-term
  money goals** is in scope—answer with practical bullets (timing, liquidity, diversification, trade-offs).
- If the user asks about anything outside that scope (coding, homework, sports, recipes, health, politics, gossip,
  creative writing, general chit-chat, or other non-finance topics), you MUST NOT answer their request. Respond with
  exactly these two bullets and nothing else:
  - I only answer **finance and investing** questions in simple language (I’m RB buddy).
  - Try a money question—for example: *What if inflation stays high?* or *What if I need to withdraw next year?*
- Never pretend to be a licensed advisor; this is educational, not personal advice.

Format:
- Answer ONLY with bullet points. Start every bullet with "- " (markdown list). Use 4–8 bullets when you do answer.
- Cover the "what if" clearly, in plain language. No guarantees, no promised returns.
- Do NOT use: alpha, beta, Sharpe ratio, standard deviation (unless you define it in one short phrase—prefer omitting).
- Do not name real companies or tickers; say "diversified mutual funds" or "sample stocks" if needed.
- Keep each bullet one or two short sentences."""


GOAL_COACH_SYSTEM = """You are a financial coach for beginners. The user completed a short goal questionnaire.

Rules:
- Respond ONLY with bullet points. Start every bullet with "- ". Use 5–8 bullets.
- Summarize what their answers imply for how much risk might feel okay and how to think about time horizon.
- Mention diversification and avoiding "all in one bet" in simple words.
- Remind them this is educational, not personal financial advice.
- No alpha, beta, Sharpe. No real stock names.
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
    if "20" in t and ("market" in t or "drop" in t or "crash" in t):
        return (
            "- A large market drop can feel scary; many people trim the riskiest single stocks first.\n"
            "- Shifting part toward **diversified mutual funds** can make the ride a bit steadier.\n"
            "- It often helps to rebalance in **small steps** instead of one big emotional trade.\n"
            "- Keep money you need soon in **liquid / low-bounce** sleeves.\n"
            "- Watch **costs and taxes** before selling; this demo does not place real trades.\n"
            "- Use **AI Rebalance** in this app for a structured practice plan."
        )
    if "inflation" in t:
        return (
            "- High inflation can erode **cash** that sits idle for years.\n"
            "- Long-term money often stays partly in **diversified equity funds**—but no outcome is guaranteed.\n"
            "- Money you need in the next few years may belong in **steadier, shorter-term** fund types.\n"
            "- Avoid chasing one “magic” asset; **diversification** still matters.\n"
            "- Revisit your plan when your **timeline or spending** changes.\n"
            "- This is educational only—not personal advice."
        )
    if "withdraw" in t or "cash" in t:
        return (
            "- If you need a **large withdrawal soon**, consider parking that slice in **liquid funds** first.\n"
            "- The rest can stay aligned with your **long-term** mix.\n"
            "- Selling in **taxable** accounts may have tax effects—check with a professional.\n"
            "- Plan withdrawals in **chunks** when possible instead of panic selling.\n"
            "- Try the **Planned withdrawal** scenario under **AI Rebalance** for a practice run.\n"
            "- Not financial advice—just a simple mental model."
        )
    return (
        "- I’d start by writing down **when** you need the money and how bumpy a ride you can stand.\n"
        "- Compare today’s mix to that simple plan; if you’re far off, adjust in **2–3 small steps**.\n"
        "- Prefer funding changes with **new savings**; selling triggers **costs and possible taxes**.\n"
        "- For story-based practice, use **AI Rebalance** and pick a what-if scenario.\n"
        "- Add **ANTHROPIC_API_KEY** in Streamlit secrets for richer AI answers here.\n"
        "- Educational only—not a recommendation to buy or sell anything."
    )


def _fallback_goal_bullets(profile: dict[str, Any]) -> str:
    g = profile.get("mainGoalLabel") or profile.get("mainGoal", "your goal")
    y = profile.get("years", "?")
    r = profile.get("riskLabel", "balanced")
    return (
        f"- Your answers point to a **{r}** comfort style with about **{y} years** in view.\n"
        f"- Main theme: **{g}**—keep that as the north star when markets get noisy.\n"
        "- Shorter timelines usually mean **less** in the riskiest sleeve; longer ones allow more growth focus.\n"
        "- **Diversified mutual funds** often beat guessing single winners for beginners.\n"
        "- Revisit this once a year or after a big life change (job, family, health).\n"
        "- This summary is educational—not personal financial advice.\n"
        "- Add **ANTHROPIC_API_KEY** in secrets for a tailored AI write-up."
    )
