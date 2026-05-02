import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import './SipCalculatorPage.css'

const INVESTED_COLOR = '#c7d2fe'
const RETURNS_COLOR = '#2563eb'

function formatInr(n: number) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Math.round(n))
}

function sipFutureValue(monthly: number, annualPct: number, years: number) {
  const n = years * 12
  const r = annualPct / 100 / 12
  if (r === 0) return monthly * n
  return monthly * ((Math.pow(1 + r, n) - 1) / r)
}

function lumpsumFutureValue(principal: number, annualPct: number, years: number) {
  return principal * Math.pow(1 + annualPct / 100, years)
}

export function SipCalculatorPage() {
  const [mode, setMode] = useState<'sip' | 'lumpsum'>('sip')
  const [monthly, setMonthly] = useState(25000)
  const [lumpsum, setLumpsum] = useState(500000)
  const [rate, setRate] = useState(12)
  const [years, setYears] = useState(10)

  const { invested, total, returns } = useMemo(() => {
    if (mode === 'sip') {
      const fv = sipFutureValue(monthly, rate, years)
      const inv = monthly * 12 * years
      return { invested: inv, total: fv, returns: Math.max(0, fv - inv) }
    }
    const fv = lumpsumFutureValue(lumpsum, rate, years)
    return { invested: lumpsum, total: fv, returns: Math.max(0, fv - lumpsum) }
  }, [mode, monthly, lumpsum, rate, years])

  const chartData = [
    { name: 'Invested amount', value: invested },
    { name: 'Est. returns', value: returns },
  ]

  return (
    <div className="sip-page">
      <div className="container sip-layout">
        <section className="sip-card">
          <header className="sip-card-head">
            <h1>SIP calculator</h1>
            <div className="sip-tabs" role="tablist">
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'sip'}
                className={mode === 'sip' ? 'sip-tab active' : 'sip-tab'}
                onClick={() => setMode('sip')}
              >
                SIP
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={mode === 'lumpsum'}
                className={mode === 'lumpsum' ? 'sip-tab active' : 'sip-tab'}
                onClick={() => setMode('lumpsum')}
              >
                Lumpsum
              </button>
            </div>
          </header>

          <div className="sip-card-body">
            <div className="sip-controls">
              {mode === 'sip' ? (
                <div className="sip-row">
                  <label className="sip-label">Monthly investment</label>
                  <div className="sip-input-wrap">
                    <span className="sip-prefix">₹</span>
                    <input
                      className="sip-input"
                      type="number"
                      min={500}
                      max={500000}
                      step={500}
                      value={monthly}
                      onChange={(e) => setMonthly(Number(e.target.value) || 0)}
                    />
                  </div>
                  <input
                    className="sip-slider"
                    type="range"
                    min={500}
                    max={100000}
                    step={500}
                    value={Math.min(monthly, 100000)}
                    onChange={(e) => setMonthly(Number(e.target.value))}
                  />
                </div>
              ) : (
                <div className="sip-row">
                  <label className="sip-label">Lumpsum amount</label>
                  <div className="sip-input-wrap">
                    <span className="sip-prefix">₹</span>
                    <input
                      className="sip-input"
                      type="number"
                      min={10000}
                      max={10000000}
                      step={10000}
                      value={lumpsum}
                      onChange={(e) => setLumpsum(Number(e.target.value) || 0)}
                    />
                  </div>
                  <input
                    className="sip-slider"
                    type="range"
                    min={10000}
                    max={5000000}
                    step={10000}
                    value={Math.min(lumpsum, 5000000)}
                    onChange={(e) => setLumpsum(Number(e.target.value))}
                  />
                </div>
              )}

              <div className="sip-row">
                <label className="sip-label">Expected return rate (p.a.)</label>
                <div className="sip-input-wrap pct">
                  <input
                    className="sip-input"
                    type="number"
                    min={1}
                    max={30}
                    step={0.5}
                    value={rate}
                    onChange={(e) => setRate(Number(e.target.value) || 0)}
                  />
                  <span className="sip-suffix">%</span>
                </div>
                <input
                  className="sip-slider"
                  type="range"
                  min={1}
                  max={25}
                  step={0.5}
                  value={rate}
                  onChange={(e) => setRate(Number(e.target.value))}
                />
              </div>

              <div className="sip-row">
                <label className="sip-label">Time period</label>
                <div className="sip-input-wrap yr">
                  <input
                    className="sip-input"
                    type="number"
                    min={1}
                    max={40}
                    step={1}
                    value={years}
                    onChange={(e) => setYears(Number(e.target.value) || 0)}
                  />
                  <span className="sip-suffix">Yr</span>
                </div>
                <input
                  className="sip-slider"
                  type="range"
                  min={1}
                  max={40}
                  step={1}
                  value={years}
                  onChange={(e) => setYears(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="sip-chart-wrap">
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={chartData}
                    cx="50%"
                    cy="50%"
                    innerRadius={68}
                    outerRadius={96}
                    paddingAngle={2}
                    dataKey="value"
                  >
                    <Cell fill={INVESTED_COLOR} />
                    <Cell fill={RETURNS_COLOR} />
                  </Pie>
                  <Tooltip
                    formatter={(value) => formatInr(Number(value))}
                    contentStyle={{ borderRadius: 8 }}
                  />
                  <Legend verticalAlign="top" height={36} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <footer className="sip-footer">
            <dl className="sip-summary">
              <div>
                <dt>Invested amount</dt>
                <dd>{formatInr(invested)}</dd>
              </div>
              <div>
                <dt>Est. returns</dt>
                <dd>{formatInr(returns)}</dd>
              </div>
              <div className="highlight">
                <dt>Total value</dt>
                <dd>{formatInr(total)}</dd>
              </div>
            </dl>
            <button type="button" className="sip-invest-btn">
              Invest now
            </button>
          </footer>
        </section>

        <aside className="sip-sidebar">
          <div className="sip-promo">
            <div className="sip-promo-art" aria-hidden>
              ₹
            </div>
            <h2>Invest in mutual funds</h2>
            <p>Start building wealth with SIPs alongside your stock sleeve.</p>
            <Link to="/products/mutual-funds" className="sip-promo-btn">
              Invest now
            </Link>
          </div>
          <div className="sip-links-card">
            <h3>Popular calculators</h3>
            <ul>
              <li>
                <button type="button">Lumpsum calculator</button>
              </li>
              <li>
                <button type="button">SWP calculator</button>
              </li>
              <li>
                <button type="button">Mutual fund returns calculator</button>
              </li>
              <li>
                <button type="button">Income tax calculator</button>
              </li>
              <li>
                <button type="button">PPF calculator</button>
              </li>
            </ul>
          </div>
        </aside>
      </div>
    </div>
  )
}
