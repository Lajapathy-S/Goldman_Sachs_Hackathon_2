import { useMemo, useState } from 'react'
import { postRebalance } from '../api/rebalance'
import { SAMPLE_PORTFOLIO } from '../data/samplePortfolio'
import type { PortfolioHolding, RebalanceApiResponse, ScenarioId } from '../types/rebalance'
import { computeCurrentAllocation } from '../utils/allocation'
import './RebalancePage.css'

const SCENARIOS: { id: ScenarioId; title: string; description: string }[] = [
  {
    id: 'market-drop',
    title: 'Market drop',
    description: 'What if the market drops by about 20%?',
  },
  {
    id: 'high-inflation',
    title: 'High inflation',
    description: 'What if inflation stays high?',
  },
  {
    id: 'planned-withdrawal',
    title: 'Planned withdrawal',
    description: 'What if I need about 20% of my funds next year?',
  },
  {
    id: 'income-risk',
    title: 'Income risk',
    description: 'What if I lose income for ~6 months?',
  },
  {
    id: 'timeline-sooner',
    title: 'Need money sooner',
    description: 'What if I need my money sooner than planned?',
  },
]

const GOAL_KEY = 'aichemist_goal_profile'

function loadGoalProfile() {
  try {
    const raw = localStorage.getItem(GOAL_KEY)
    if (!raw) return null
    return JSON.parse(raw) as Record<string, unknown>
  } catch {
    return null
  }
}

function emptyRow(): PortfolioHolding {
  return { name: '', type: 'mutual_fund', value: 0, risk: 'medium' }
}

export function RebalancePage() {
  const [holdings, setHoldings] = useState<PortfolioHolding[]>(() =>
    SAMPLE_PORTFOLIO.map((h) => ({ ...h })),
  )
  const [scenarioId, setScenarioId] = useState<ScenarioId>('market-drop')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<RebalanceApiResponse | null>(null)

  const current = useMemo(() => computeCurrentAllocation(holdings), [holdings])

  async function runSimulation() {
    const valid = holdings.filter((h) => h.name.trim() && Number(h.value) > 0)
    if (valid.length === 0) {
      setError('Add at least one holding with a name and positive value.')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const goalProfile = loadGoalProfile()
      const data = await postRebalance(valid, scenarioId, goalProfile)
      setResult(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  function updateRow(i: number, patch: Partial<PortfolioHolding>) {
    setHoldings((rows) => rows.map((r, j) => (j === i ? { ...r, ...patch } : r)))
  }

  function addRow() {
    setHoldings((rows) => [...rows, emptyRow()])
  }

  function removeRow(i: number) {
    setHoldings((rows) => rows.filter((_, j) => j !== i))
  }

  return (
    <div className="rb-page">
      <div className="rb-inner">
        <header className="rb-head">
          <h1>AI rebalance (simulation)</h1>
          <p className="rb-lead">
            Enter placeholder holdings, pick a story, and get a{' '}
            <strong>practice-only</strong> plan. Nothing here places real trades.
          </p>
        </header>

        <section className="rb-panel">
          <div className="rb-panel-head">
            <h2>Your holdings</h2>
            <button type="button" className="rb-btn secondary" onClick={() => setHoldings(SAMPLE_PORTFOLIO.map((h) => ({ ...h })))}>
              Load sample portfolio
            </button>
          </div>
          <div className="rb-table-wrap">
            <table className="rb-table">
              <thead>
                <tr>
                  <th>Asset name</th>
                  <th>Type</th>
                  <th>Value (₹)</th>
                  <th>Risk</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {holdings.map((row, i) => (
                  <tr key={i}>
                    <td>
                      <input
                        className="rb-input"
                        value={row.name}
                        placeholder="e.g. Sample fund"
                        onChange={(e) => updateRow(i, { name: e.target.value })}
                      />
                    </td>
                    <td>
                      <select
                        className="rb-select"
                        value={row.type}
                        onChange={(e) =>
                          updateRow(i, { type: e.target.value as PortfolioHolding['type'] })
                        }
                      >
                        <option value="stock">Stock</option>
                        <option value="mutual_fund">Mutual fund</option>
                        <option value="cash_or_liquid">Cash / liquid fund</option>
                      </select>
                    </td>
                    <td>
                      <input
                        className="rb-input num"
                        type="number"
                        min={0}
                        value={row.value || ''}
                        onChange={(e) => updateRow(i, { value: Number(e.target.value) })}
                      />
                    </td>
                    <td>
                      <select
                        className="rb-select"
                        value={row.risk}
                        onChange={(e) =>
                          updateRow(i, { risk: e.target.value as PortfolioHolding['risk'] })
                        }
                      >
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </td>
                    <td>
                      <button type="button" className="rb-icon-btn" onClick={() => removeRow(i)} aria-label="Remove row">
                        ×
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button type="button" className="rb-btn ghost" onClick={addRow}>
            + Add row
          </button>

          <h3 className="rb-subh">Current allocation (by type)</h3>
          <AllocationBar
            label="Stocks"
            pct={current.stocks}
            color="#1e3a8a"
          />
          <AllocationBar
            label="Mutual funds"
            pct={current.mutualFunds}
            color="#3b82f6"
          />
          <AllocationBar
            label="Cash / liquid"
            pct={current.cashOrLiquidFunds}
            color="#93c5fd"
          />
        </section>

        <section className="rb-panel">
          <h2>What-if scenario</h2>
          <div className="rb-scenarios">
            {SCENARIOS.map((s) => (
              <label key={s.id} className={`rb-scenario ${scenarioId === s.id ? 'active' : ''}`}>
                <input
                  type="radio"
                  name="sc"
                  checked={scenarioId === s.id}
                  onChange={() => setScenarioId(s.id)}
                />
                <span className="rb-scenario-body">
                  <strong>{s.title}</strong>
                  <span>{s.description}</span>
                </span>
              </label>
            ))}
          </div>
          <button
            type="button"
            className="rb-btn primary"
            disabled={loading}
            onClick={runSimulation}
          >
            {loading ? 'Running simulation…' : 'Get AI recommendation'}
          </button>
          {error && <p className="rb-error">{error}</p>}
        </section>

        {result && (
          <section className="rb-results">
            <div className="rb-meta">
              <span className="rb-badge">
                Source: {result._source === 'claude' ? 'Claude API' : 'Built-in simulation'}
              </span>
              {result._warning && (
                <span className="rb-badge warn">Fallback: {result._warning}</span>
              )}
            </div>
            <h2>Recommended mix (practice)</h2>
            <p className="rb-summary">{result.summary}</p>
            <div className="rb-grid-two">
              <div>
                <h3>Health check</h3>
                <p>{result.portfolioHealth}</p>
                <p>
                  <strong>Risk feel before:</strong> {result.riskLevelBefore}
                  <br />
                  <strong>Risk feel after:</strong> {result.riskLevelAfter}
                </p>
              </div>
              <div>
                <h3>Suggested allocation (%)</h3>
                <AllocationBar label="Stocks" pct={result.recommendedAllocation.stocks} color="#1e3a8a" />
                <AllocationBar
                  label="Mutual funds"
                  pct={result.recommendedAllocation.mutualFunds}
                  color="#3b82f6"
                />
                <AllocationBar
                  label="Cash / liquid"
                  pct={result.recommendedAllocation.cashOrLiquidFunds}
                  color="#93c5fd"
                />
              </div>
            </div>

            <h3>Simulated moves</h3>
            <ul className="rb-actions">
              {result.actions.map((a, i) => (
                <li key={i}>
                  <div className="rb-action-top">
                    <strong>{a.action}</strong> · {a.amountOrPercent}
                  </div>
                  <div className="rb-action-row">
                    From <em>{a.fromAsset}</em> → To <em>{a.toAsset}</em>
                  </div>
                  <p className="rb-why">{a.reason}</p>
                </li>
              ))}
            </ul>

            <h3>Transparency (non-advisory)</h3>
            <div className="rb-trans">
              <p>
                <strong>Costs:</strong> {result.transparencyNotes.costs}
              </p>
              <p>
                <strong>Taxes:</strong> {result.transparencyNotes.taxes}
              </p>
              <p>
                <strong>Risk in plain words:</strong> {result.transparencyNotes.riskExplanation}
              </p>
              <p>
                <strong>Goals:</strong> {result.transparencyNotes.goalAlignment}
              </p>
            </div>

            <div className="rb-beginner">{result.beginnerExplanation}</div>

            <p className="rb-disclaimer">
              This is an educational simulation, not financial advice.
            </p>
          </section>
        )}
      </div>
    </div>
  )
}

function AllocationBar({
  label,
  pct,
  color,
}: {
  label: string
  pct: number
  color: string
}) {
  return (
    <div className="rb-bar-wrap">
      <div className="rb-bar-label">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="rb-bar-track">
        <div className="rb-bar-fill" style={{ width: `${Math.min(100, pct)}%`, background: color }} />
      </div>
    </div>
  )
}
