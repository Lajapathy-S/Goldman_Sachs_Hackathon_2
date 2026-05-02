import type { PortfolioHolding } from '../types/rebalance'

export const SAMPLE_PORTFOLIO: PortfolioHolding[] = [
  {
    name: 'Sample stock A (placeholder)',
    type: 'stock',
    value: 42_000,
    risk: 'high',
  },
  {
    name: 'Sample stock B (placeholder)',
    type: 'stock',
    value: 18_000,
    risk: 'medium',
  },
  {
    name: 'Diversified equity mutual fund (placeholder)',
    type: 'mutual_fund',
    value: 68_000,
    risk: 'medium',
  },
  {
    name: 'Balanced mutual fund (placeholder)',
    type: 'mutual_fund',
    value: 32_000,
    risk: 'low',
  },
  {
    name: 'Liquid / cash-style mutual fund (placeholder)',
    type: 'cash_or_liquid',
    value: 22_000,
    risk: 'low',
  },
]
