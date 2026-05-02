import type { PortfolioHolding } from '../types/rebalance'

export function computeCurrentAllocation(portfolio: PortfolioHolding[]) {
  let stocks = 0
  let mutualFunds = 0
  let cashOrLiquidFunds = 0
  for (const h of portfolio) {
    const v = Number(h.value) || 0
    if (h.type === 'stock') stocks += v
    else if (h.type === 'mutual_fund') mutualFunds += v
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
