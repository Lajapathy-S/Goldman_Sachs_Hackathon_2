export type HoldingType = 'stock' | 'mutual_fund' | 'cash_or_liquid'
export type RiskLevel = 'low' | 'medium' | 'high'

export type PortfolioHolding = {
  name: string
  type: HoldingType
  value: number
  risk: RiskLevel
}

export type ScenarioId =
  | 'market-drop'
  | 'high-inflation'
  | 'planned-withdrawal'
  | 'income-risk'
  | 'timeline-sooner'

export type RebalanceApiResponse = {
  scenario: string
  portfolioHealth: string
  riskLevelBefore: string
  riskLevelAfter: string
  summary: string
  recommendedAllocation: {
    stocks: number
    mutualFunds: number
    cashOrLiquidFunds: number
  }
  actions: {
    action: string
    amountOrPercent: string
    fromAsset: string
    toAsset: string
    reason: string
  }[]
  transparencyNotes: {
    costs: string
    taxes: string
    riskExplanation: string
    goalAlignment: string
  }
  beginnerExplanation: string
  _source?: 'claude' | 'mock' | 'mock_fallback'
  _warning?: string
}
