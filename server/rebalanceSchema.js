import { z } from 'zod'

export const rebalanceResponseSchema = z.object({
  scenario: z.string(),
  portfolioHealth: z.string(),
  riskLevelBefore: z.string(),
  riskLevelAfter: z.string(),
  summary: z.string(),
  recommendedAllocation: z.object({
    stocks: z.number(),
    mutualFunds: z.number(),
    cashOrLiquidFunds: z.number(),
  }),
  actions: z.array(
    z.object({
      action: z.string(),
      amountOrPercent: z.string(),
      fromAsset: z.string(),
      toAsset: z.string(),
      reason: z.string(),
    }),
  ),
  transparencyNotes: z.object({
    costs: z.string(),
    taxes: z.string(),
    riskExplanation: z.string(),
    goalAlignment: z.string(),
  }),
  beginnerExplanation: z.string(),
})

export function parseRebalanceJson(raw) {
  let text = typeof raw === 'string' ? raw.trim() : String(raw)
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/)
  if (fence) text = fence[1].trim()
  const parsed = JSON.parse(text)
  return rebalanceResponseSchema.parse(parsed)
}
