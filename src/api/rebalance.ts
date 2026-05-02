import type { PortfolioHolding, RebalanceApiResponse, ScenarioId } from '../types/rebalance'

export type GoalProfilePayload = {
  mainGoal?: string
  years?: number
  comfort?: string
  riskLabel?: string
} | null

export async function postRebalance(
  portfolio: PortfolioHolding[],
  scenarioId: ScenarioId,
  goalProfile?: GoalProfilePayload,
): Promise<RebalanceApiResponse> {
  const res = await fetch('/api/rebalance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ portfolio, scenarioId, goalProfile }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.error || data.message || `Request failed (${res.status})`)
  }
  return data as RebalanceApiResponse
}
