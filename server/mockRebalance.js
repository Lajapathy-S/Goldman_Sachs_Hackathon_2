/**
 * Deterministic educational simulation when ANTHROPIC_API_KEY is unset or API fails.
 */

function sumByType(portfolio) {
  let stocks = 0
  let mutualFunds = 0
  let cashOrLiquidFunds = 0
  for (const row of portfolio) {
    const v = Number(row.value) || 0
    if (row.type === 'stock') stocks += v
    else if (row.type === 'mutual_fund') mutualFunds += v
    else cashOrLiquidFunds += v
  }
  const total = stocks + mutualFunds + cashOrLiquidFunds || 1
  return {
    stocks: Math.round((stocks / total) * 1000) / 10,
    mutualFunds: Math.round((mutualFunds / total) * 1000) / 10,
    cashOrLiquidFunds: Math.round((cashOrLiquidFunds / total) * 1000) / 10,
    total,
  }
}

const SCENARIO_LABEL = {
  'market-drop': 'Market drop (~20%)',
  'high-inflation': 'High inflation',
  'planned-withdrawal': 'Planned withdrawal (20% next year)',
  'income-risk': 'Income interruption (~6 months)',
  'timeline-sooner': 'Need money sooner',
}

export function buildMockRebalance(scenarioId, portfolio) {
  const before = sumByType(portfolio)
  const total = before.total

  let rec = {
    stocks: before.stocks,
    mutualFunds: before.mutualFunds,
    cashOrLiquidFunds: before.cashOrLiquidFunds,
  }

  const shift = (fromStock, toMF, toCash) => {
    rec.stocks = Math.max(5, Math.round((before.stocks + fromStock) * 10) / 10)
    rec.mutualFunds = Math.max(10, Math.round((before.mutualFunds + toMF) * 10) / 10)
    rec.cashOrLiquidFunds = Math.max(5, Math.round((before.cashOrLiquidFunds + toCash) * 10) / 10)
    const s = rec.stocks + rec.mutualFunds + rec.cashOrLiquidFunds
    rec.stocks = Math.round((rec.stocks / s) * 1000) / 10
    rec.mutualFunds = Math.round((rec.mutualFunds / s) * 1000) / 10
    rec.cashOrLiquidFunds = Math.round((100 - rec.stocks - rec.mutualFunds) * 10) / 10
  }

  let summary = ''
  let actions = []

  switch (scenarioId) {
    case 'market-drop':
      shift(-12, 10, 2)
      summary =
        'Trim concentrated stock risk and lean on diversified mutual funds while keeping a small stability bucket.'
      actions = [
        {
          action: 'Simulated shift',
          amountOrPercent: '~12% of portfolio from stocks toward mutual funds',
          fromAsset: 'Higher-risk stock sleeve',
          toAsset: 'Broad diversified mutual funds',
          reason:
            'When markets fall sharply, single stocks often swing more than funds. Spreading into diversified funds can make the ride steadier for beginners.',
        },
        {
          action: 'Simulated trim',
          amountOrPercent: 'Optional top-up to cash/liquid sleeve',
          fromAsset: 'Remaining stock trades (if any)',
          toAsset: 'Liquid / cash-style mutual fund',
          reason: 'Keeps money you might need soon easier to access without timing a recovery.',
        },
      ]
      break
    case 'high-inflation':
      shift(-5, 3, 2)
      summary =
        'Reduce idle cash drag, keep long-term growth via diversified equity funds, and add a modest stability sleeve.'
      actions = [
        {
          action: 'Simulated shift',
          amountOrPercent: '~5% from idle cash toward diversified equity funds',
          fromAsset: 'Cash / liquid sleeve',
          toAsset: 'Diversified equity mutual funds',
          reason:
            'Cash loses buying power when prices rise. Moving only part reduces risk of missing long-term growth.',
        },
      ]
      break
    case 'planned-withdrawal':
      shift(-8, -2, 10)
      summary =
        'Park the amount you need next year in liquid, lower-bounce assets; keep the rest invested to plan.'
      actions = [
        {
          action: 'Simulated carve-out',
          amountOrPercent: '~20% of portfolio into liquid / low-volatility sleeve',
          fromAsset: 'Stock and riskier fund sleeves',
          toAsset: 'Cash / liquid mutual funds',
          reason:
            'Money you will spend soon should not ride the same bumps as long-term growth money.',
        },
      ]
      break
    case 'income-risk':
      shift(-10, 2, 8)
      summary =
        'Build a larger emergency buffer and dial back the riskiest sleeve until income stabilizes.'
      actions = [
        {
          action: 'Simulated shift',
          amountOrPercent: '~8–10% toward liquid / short-duration funds',
          fromAsset: 'Higher-risk stocks',
          toAsset: 'Liquid or short-duration mutual funds',
          reason:
            'If paychecks pause, you want several months of expenses where you can tap without forced selling at bad times.',
        },
      ]
      break
    case 'timeline-sooner':
      shift(-15, 5, 10)
      summary =
        'Shorten the runway: move toward steadier funds because you have less time to recover from dips.'
      actions = [
        {
          action: 'Simulated de-risk',
          amountOrPercent: '~15% from stocks toward diversified bond-style / balanced mutual funds',
          fromAsset: 'Stock sleeve',
          toAsset: 'Balanced or bond-oriented mutual funds',
          reason:
            'When the goal is closer, large swings hurt more than they help. Steadier funds match a shorter clock.',
        },
      ]
      break
    default:
      summary = 'Keep your current mix unless goals or timing change; revisit twice a year.'
  }

  return {
    scenario: SCENARIO_LABEL[scenarioId] || scenarioId,
    portfolioHealth:
      total < 1000
        ? 'Very small portfolio — focus on saving habit before fine-tuning.'
        : 'Portfolio mix is readable; next step is aligning risk with when you need the money.',
    riskLevelBefore:
      before.stocks >= 55 ? 'Higher (stock-heavy)' : before.stocks >= 35 ? 'Moderate' : 'Lower',
    riskLevelAfter:
      rec.stocks >= 55 ? 'Higher (stock-heavy)' : rec.stocks >= 35 ? 'Moderate' : 'Lower',
    summary,
    recommendedAllocation: {
      stocks: rec.stocks,
      mutualFunds: rec.mutualFunds,
      cashOrLiquidFunds: rec.cashOrLiquidFunds,
    },
    actions,
    transparencyNotes: {
      costs:
        'Demo only: real brokers charge brokerage, spreads, and fund expense ratios. Check your statements before trading.',
      taxes:
        'Selling winners in taxable accounts may trigger taxes. This toy model does not calculate tax — talk to a qualified professional.',
      riskExplanation:
        'We describe risk in plain words (how bumpy the ride may feel), not using Greek letters or Wall Street shorthand.',
      goalAlignment:
        'Any shift here is meant to match the scenario you picked — not to promise returns or beat the market.',
    },
    beginnerExplanation:
      'Think of this as a practice drill: you told us a story (“what if…”), and we showed one simple way to adjust your buckets. Real life needs your broker, goals, and maybe an advisor.',
  }
}
