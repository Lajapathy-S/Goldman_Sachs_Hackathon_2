import 'dotenv/config'
import express from 'express'
import cors from 'cors'
import Anthropic from '@anthropic-ai/sdk'
import { parseRebalanceJson, rebalanceResponseSchema } from './rebalanceSchema.js'
import { buildMockRebalance } from './mockRebalance.js'

const PORT = Number(process.env.PORT) || 8787
const MODEL = process.env.ANTHROPIC_MODEL || 'claude-3-5-sonnet-20241022'

const SCENARIO_PROMPTS = {
  'market-drop':
    'What if the broad market drops about 20%? Reduce high-risk single-stock exposure where sensible and shift part of the portfolio toward diversified mutual funds or steadier sleeves. Use only placeholder asset names.',
  'high-inflation':
    'What if inflation stays high for a while? Reduce idle cash where too large, keep sensible diversified equity exposure for long-term goals, and suggest diversified mutual funds rather than chasing single hot names. Placeholder assets only.',
  'planned-withdrawal':
    'What if the user needs to withdraw about 20% of portfolio value next year? Move that portion toward low-risk / liquid mutual funds or cash-like funds and reduce volatility for that slice.',
  'income-risk':
    'What if the user may lose income for about 6 months? Increase emergency / liquid allocation and reduce the riskiest stock sleeve.',
  'timeline-sooner':
    'What if the user needs their money sooner than planned? Reduce portfolio risk and shift toward safer diversified mutual funds instead of concentrated stocks.',
}

const app = express()
app.use(cors({ origin: true }))
app.use(express.json({ limit: '512kb' }))

function buildUserPrompt(scenarioId, portfolio, goalProfile) {
  const scenarioText = SCENARIO_PROMPTS[scenarioId] || SCENARIO_PROMPTS['market-drop']
  return `You are helping a beginner retail investor. Output VALID JSON ONLY — no markdown, no prose outside JSON.

Rules:
- Use simple words. Do NOT use: alpha, beta, Sharpe ratio, standard deviation, or volatility unless you explain in one short beginner sentence (prefer avoid entirely).
- Do not promise returns or guarantee outcomes.
- Do not name real tickers or real companies. Use generic labels like "Sample stock A", "Diversified equity fund", "Liquid fund".
- recommendedAllocation stocks/mutualFunds/cashOrLiquidFunds must be numbers that sum to 100 (percent).
- actions: 2 to 4 items simulating buy/sell/shift with clear reasons.

Selected scenario id: ${scenarioId}
Scenario description: ${scenarioText}

Optional goal profile (JSON): ${JSON.stringify(goalProfile || null)}

Current holdings (JSON array): ${JSON.stringify(portfolio)}

Compute current allocation by grouping: stock type -> stocks bucket, mutual_fund -> mutualFunds bucket, cash_or_liquid -> cashOrLiquidFunds bucket (by value).

Return JSON with this exact shape and keys:
{
  "scenario": "short label",
  "portfolioHealth": "one sentence",
  "riskLevelBefore": "plain words e.g. Moderate",
  "riskLevelAfter": "plain words",
  "summary": "2 sentences max",
  "recommendedAllocation": { "stocks": number, "mutualFunds": number, "cashOrLiquidFunds": number },
  "actions": [{ "action": "", "amountOrPercent": "", "fromAsset": "", "toAsset": "", "reason": "" }],
  "transparencyNotes": { "costs": "", "taxes": "", "riskExplanation": "", "goalAlignment": "" },
  "beginnerExplanation": "short paragraph"
}`
}

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, hasClaudeKey: Boolean(process.env.ANTHROPIC_API_KEY) })
})

app.post('/api/rebalance', async (req, res) => {
  try {
    const { portfolio, scenarioId, goalProfile } = req.body || {}
    if (!Array.isArray(portfolio) || portfolio.length === 0) {
      return res.status(400).json({ error: 'portfolio array required' })
    }
    const allowed = Object.keys(SCENARIO_PROMPTS)
    if (!scenarioId || !allowed.includes(scenarioId)) {
      return res.status(400).json({ error: 'invalid scenarioId', allowed })
    }

    for (const row of portfolio) {
      if (!row.name || !row.type || row.value == null || !row.risk) {
        return res.status(400).json({
          error: 'each holding needs name, type, value, risk',
        })
      }
      if (!['stock', 'mutual_fund', 'cash_or_liquid'].includes(row.type)) {
        return res.status(400).json({ error: 'invalid type' })
      }
      if (!['low', 'medium', 'high'].includes(row.risk)) {
        return res.status(400).json({ error: 'invalid risk' })
      }
    }

    if (!process.env.ANTHROPIC_API_KEY) {
      const mock = buildMockRebalance(scenarioId, portfolio)
      return res.json({ ...mock, _source: 'mock' })
    }

    const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })
    const textContent = await client.messages.create({
      model: MODEL,
      max_tokens: 4096,
      messages: [
        {
          role: 'user',
          content: buildUserPrompt(scenarioId, portfolio, goalProfile),
        },
      ],
    })

    const block = textContent.content?.[0]
    const rawText = block && block.type === 'text' ? block.text : ''
    if (!rawText) {
      const mock = buildMockRebalance(scenarioId, portfolio)
      return res.json({ ...mock, _source: 'mock_fallback', _warning: 'empty_claude_response' })
    }

    try {
      const parsed = parseRebalanceJson(rawText)
      rebalanceResponseSchema.parse(parsed)
      return res.json({ ...parsed, _source: 'claude' })
    } catch (e) {
      console.error('JSON parse/validate failed:', e.message)
      const mock = buildMockRebalance(scenarioId, portfolio)
      return res.json({
        ...mock,
        _source: 'mock_fallback',
        _warning: 'invalid_json_from_model',
      })
    }
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'server_error', message: String(err.message || err) })
  }
})

app.listen(PORT, () => {
  console.log(`API listening on http://localhost:${PORT}`)
})
