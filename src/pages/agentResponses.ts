export type TransparentPlan = {
  headline: string
  strategy: string[]
  why: string
  costs: string
  tax: string
  goals: string
}

export const SCENARIO_PRESETS: { id: string; label: string; prompt: string; plan: TransparentPlan }[] =
  [
    {
      id: 'market-down',
      label: 'Market drops ~20%',
      prompt: 'What if the market drops by 20%?',
      plan: {
        headline: 'Lean into your plan: rebalance toward targets, don’t panic-sell growth assets.',
        strategy: [
          'Check your current split (e.g. stocks vs mutual funds) against the mix you chose for your goal date.',
          'If equities are now below target because of the drop, consider buying back to target in 2–3 small steps (not one lump sum) using new cash or shifting from a stable sleeve.',
          'If you are close to needing the money in under 3 years, cap how much you “buy the dip” and keep the next 12–18 months of withdrawals in lower-volatility mutual funds.',
        ],
        why: 'After a broad 20% fall, most portfolios drift under their equity target. Rebalancing buys discipline: you sell what is relatively high and add to what is relatively low. That is the same simple math institutions use — not a prediction that markets will bounce immediately.',
        costs: 'Mutual funds may have expense ratios only (no extra fee for this logic). If you trade stocks, you may pay brokerage and spread. This demo does not place trades — your broker’s schedule applies.',
        tax: 'Selling in taxable accounts can trigger capital gains. Prefer funding rebalancing with new contributions or use tax-advantaged accounts when possible. Loss harvesting is optional and situational — we are not giving tax advice; a qualified professional should review your jurisdiction.',
        goals: 'This keeps your risk level aligned with the goal you set (e.g. retirement in 2040). You avoid accidentally becoming too conservative after a crash and missing recovery, or too aggressive after a rally.',
      },
    },
    {
      id: 'inflation',
      label: 'High inflation',
      prompt: 'What if inflation stays high?',
      plan: {
        headline: 'Preserve purchasing power without betting everything on one “inflation play.”',
        strategy: [
          'Review how much of your mutual fund sleeve is short-term debt vs inflation-sensitive assets (within fund fact sheets).',
          'If your goals are long term, keep a diversified equity core; stocks have historically helped real returns over decades, but year-to-year they are noisy.',
          'If withdrawals start within a few years, add or keep a short-duration / high-quality bond mutual fund bucket for spending — not timing the macro cycle.',
        ],
        why: 'High inflation hurts cash and long fixed-rate bonds most. A measured shift increases resilience for spending you cannot delay, while keeping growth assets for money you will not need soon.',
        costs: 'Switching funds may have exit loads or transaction fees depending on product — check your scheme documents. Expense ratios differ by fund category.',
        tax: 'Exchanging funds in taxable accounts may realize gains or losses. In some regions, debt-fund taxation differs from equity — verify locally before acting.',
        goals: 'The adjustment matches a split between money you will spend soon (stability) and money compounding for later (growth), which is how we protect both peace of mind and long-term wealth.',
      },
    },
    {
      id: 'withdraw',
      label: 'Withdraw 20% next year',
      prompt: 'What if I need to withdraw 20% of my funds next year?',
      plan: {
        headline: 'Build a “spend runway” first, then rebalance the rest to your risk target.',
        strategy: [
          'Move the amount you need for withdrawals (here ~20% of portfolio) into mutual funds with low volatility and clear liquidity — treat it as a 12-month runway.',
          'Rebalance the remaining ~80% to your long-term stock vs mutual-fund mix so you are not accidentally over-risked after carving out cash.',
          'If the withdrawal is from taxable accounts, plan sales in consultation with tax guidance to spread liability if sensible.',
        ],
        why: 'Large near-term withdrawals change your risk capacity. Parking the withdrawal bucket reduces forced selling during a downturn; rebalancing the remainder keeps your long-term stack coherent.',
        costs: 'Possible redemption fees or bid–ask on stocks. Some funds have minimum holding periods — your statements list this.',
        tax: 'Withdrawals and sales may trigger income or capital gains. The order of selling (lots with gain vs loss) matters in many tax systems — transparency means flagging this early, not hiding it.',
        goals: 'You secure the expense you described while keeping the rest of the portfolio pointed at the horizon you still have after this withdrawal.',
      },
    },
  ]

const FINANCIAL_PATTERN =
  /\b(portfolio|rebalanc|market|stock|mutual|fund|invest|withdraw|inflation|bond|equity|risk|allocat|tax|scenario|what\s*if|drop|crash|yield|dividend|sip|etf|cash|retire|goal|macro|interest|recess|volatil|loss|gain|percent|%\s|apy|return|asset|diversif|bear|bull|correction|allocation|expense|capital\s*gain|harvest|income|savings|debt|credit|loan|mortgage|pension|401k|ira|nominee|sip|lumpsum|index|sector|crypto|gold|commod|forex|dollar|rupee|inr|fed|rbi|rate\s*hike)\b/i

const OFF_TOPIC_PATTERN =
  /\b(recipe|cook|weather|joke|poem|python|javascript|code|debug|movie|netflix|game|fortnite|sports|football|cricket|celebr|dating|homework|essay|translate\s+to\s+french)\b/i

export function isFinancialQuery(text: string): boolean {
  const t = text.trim()
  if (t.length < 2) return false
  if (OFF_TOPIC_PATTERN.test(t)) return false
  if (FINANCIAL_PATTERN.test(t)) return true
  // Short greetings → steer to finance
  if (/^(hi|hello|hey|thanks|thank you)\b/i.test(t) && t.length < 40) return true
  return false
}

function planById(id: string): TransparentPlan | null {
  return SCENARIO_PRESETS.find((s) => s.id === id)?.plan ?? null
}

export function matchScenario(text: string): TransparentPlan | null {
  const lower = text.toLowerCase().replace(/\s+/g, ' ')

  const marketDown = planById('market-down')
  const inflationPlan = planById('inflation')
  const withdrawPlan = planById('withdraw')
  if (!marketDown || !inflationPlan || !withdrawPlan) return null

  if (
    /(\b20\s*%|\b20 percent|drops?\s+by|drop\s+of|crash|bear\s+market|correction)\b/.test(lower) &&
    /(market|portfolio|stock|equit|index|mutual|fund)\b/.test(lower)
  ) {
    return marketDown
  }

  if (/\binflation\b/.test(lower)) {
    return inflationPlan
  }

  if (
    /(withdraw|take\s+out|need\s+cash|pull\s+out|redemption)\b/.test(lower) &&
    /(20\s*%|20 percent|fifth|next\s+year|within\s+a\s+year|one\s+year)\b/.test(lower)
  ) {
    return withdrawPlan
  }

  if (
    /what\s+if\b/.test(lower) &&
    /withdraw/.test(lower) &&
    /(next\s+year|year|20)/.test(lower)
  ) {
    return withdrawPlan
  }

  return null
}

export function genericFinancialResponse(): TransparentPlan {
  return {
    headline: 'Start from your target mix, then adjust in small steps.',
    strategy: [
      'Write down your goal year and how much volatility you can tolerate — that implies a stock vs mutual-fund range.',
      'Compare today’s weights to that range. If you are more than about 5 percentage points off, schedule 2–3 rebalance trades rather than one emotional trade.',
      'Prefer funding changes with new money; if you must sell, choose lots and accounts with tax guidance.',
    ],
    why: 'We keep decisions rule-based: distance from target + time horizon + upcoming cash needs. No black box — just whether you are off-plan and by how much.',
    costs: 'Only what your broker and fund charge. This assistant does not execute orders or add a fee.',
    tax: 'Selling can realize gains or losses. Large moves in taxable accounts deserve a quick review with a tax advisor.',
    goals: 'Any recommendation here is about sticking to the risk level that matches when you need the money — not outperforming a benchmark next month.',
  }
}
