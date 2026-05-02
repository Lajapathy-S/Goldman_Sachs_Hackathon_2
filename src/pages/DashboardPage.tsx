import { useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import './DashboardPage.css'

const PORTFOLIO_ID = 'PAN · GPDPD2443Q'

const CURRENT_VALUE = 168_200
const INVESTED = 131_961
const DAY_CHANGE = -1529
const DAY_PCT = -0.9
const ALL_TIME_GAIN = 36_239
const ALL_TIME_PA = 8.7

const STOCKS_PCT_BY_TYPE = 22
const MF_PCT_BY_TYPE = 78
const STOCKS_PCT_BY_ASSET = 28
const MF_PCT_BY_ASSET = 72

const TX_FY = [
  { fy: 'FY-23', amount: 180_000 },
  { fy: 'FY-24', amount: 240_000 },
  { fy: 'FY-25', amount: 195_000 },
  { fy: 'FY-26', amount: 310_000 },
  { fy: 'FY-27', amount: 125_000 },
]

type PerfPoint = { t: string; v: number }

function buildPerformanceSeries(): PerfPoint[] {
  const out: PerfPoint[] = []
  let v = 42_000
  const start = new Date(2021, 0, 1)
  const end = new Date(2026, 4, 1)
  for (let d = new Date(start); d <= end; d.setMonth(d.getMonth() + 1)) {
    const noise = (Math.sin(out.length * 0.4) + 1) * 800
    v = v * 1.008 + noise * 0.15
    out.push({
      t: d.toISOString().slice(0, 7),
      v: Math.round(v),
    })
  }
  const last = out[out.length - 1]
  if (last) {
    const scale = CURRENT_VALUE / last.v
    return out.map((p) => ({ ...p, v: Math.round(p.v * scale) }))
  }
  return out
}

const PERF_ALL = buildPerformanceSeries()

type PerfRange =
  | 'ALL'
  | 'YTD'
  | '1M'
  | '3M'
  | '6M'
  | '1Y'
  | '3Y'
  | '5Y'
  | 'CUSTOM'

function filterPerf(range: PerfRange, data: PerfPoint[]): PerfPoint[] {
  if (data.length === 0) return data
  const end = new Date(data[data.length - 1].t + '-01')
  let start: Date
  switch (range) {
    case 'ALL':
      return data
    case 'YTD':
      start = new Date(end.getFullYear(), 0, 1)
      break
    case '1M':
      start = new Date(end)
      start.setMonth(start.getMonth() - 1)
      break
    case '3M':
      start = new Date(end)
      start.setMonth(start.getMonth() - 3)
      break
    case '6M':
      start = new Date(end)
      start.setMonth(start.getMonth() - 6)
      break
    case '1Y':
      start = new Date(end)
      start.setFullYear(start.getFullYear() - 1)
      break
    case '3Y':
      start = new Date(end)
      start.setFullYear(start.getFullYear() - 3)
      break
    case '5Y':
      start = new Date(end)
      start.setFullYear(start.getFullYear() - 5)
      break
    default:
      return data
  }
  const startStr = start.toISOString().slice(0, 7)
  return data.filter((p) => p.t >= startStr)
}

function formatInr(n: number, compact = false) {
  if (compact) {
    const abs = Math.abs(n)
    const sign = n < 0 ? '-' : ''
    if (abs >= 10000000) return `${sign}₹${(abs / 10000000).toFixed(2)} Cr`
    if (abs >= 100000) return `${sign}₹${(abs / 100000).toFixed(2)} L`
    if (abs >= 1000) return `${sign}₹${(abs / 1000).toFixed(2)} K`
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(n)
}

function formatAxisInr(v: number) {
  const abs = Math.abs(v)
  if (abs >= 100000) return `${(v / 100000).toFixed(1)}L`
  if (abs >= 1000) return `${(v / 1000).toFixed(0)}K`
  return String(v)
}

type DurationKey = '1D' | '1W' | '1M' | 'YTD' | '1Y'

const RETURNS_BY_DURATION: Record<
  DurationKey,
  { mutualFunds: { amt: number; pct: number }; stocks: { amt: number; pct: number } }
> = {
  '1D': {
    mutualFunds: { amt: -1204, pct: -0.85 },
    stocks: { amt: -325, pct: -1.05 },
  },
  '1W': {
    mutualFunds: { amt: 2100, pct: 1.5 },
    stocks: { amt: -890, pct: -2.1 },
  },
  '1M': {
    mutualFunds: { amt: 5600, pct: 4.0 },
    stocks: { amt: 3200, pct: 5.2 },
  },
  YTD: {
    mutualFunds: { amt: 12400, pct: 8.1 },
    stocks: { amt: 7800, pct: 11.4 },
  },
  '1Y': {
    mutualFunds: { amt: 18900, pct: 12.6 },
    stocks: { amt: 14200, pct: 18.2 },
  },
}

export function DashboardPage() {
  const [perfRange, setPerfRange] = useState<PerfRange>('ALL')
  const [allocMode, setAllocMode] = useState<'type' | 'asset'>('type')
  const [duration, setDuration] = useState<DurationKey>('1D')

  const perfData = useMemo(() => filterPerf(perfRange, PERF_ALL), [perfRange])

  const allocData = useMemo(() => {
    const stocks = allocMode === 'type' ? STOCKS_PCT_BY_TYPE : STOCKS_PCT_BY_ASSET
    const mf = allocMode === 'type' ? MF_PCT_BY_TYPE : MF_PCT_BY_ASSET
    return [
      { name: 'Stocks', value: stocks, color: '#1e40af' },
      { name: 'Mutual funds', value: mf, color: '#60a5fa' },
    ]
  }, [allocMode])

  const ret = RETURNS_BY_DURATION[duration]

  const perfRanges: { key: PerfRange; label: string }[] = [
    { key: 'ALL', label: 'ALL TIME' },
    { key: 'YTD', label: 'YTD' },
    { key: '1M', label: '1M' },
    { key: '3M', label: '3M' },
    { key: '6M', label: '6M' },
    { key: '1Y', label: '1Y' },
    { key: '3Y', label: '3Y' },
    { key: '5Y', label: '5Y' },
    { key: 'CUSTOM', label: 'CUSTOM' },
  ]

  return (
    <div className="vr-dash">
      <div className="vr-dash-inner container">
        <div className="vr-summary-bar">
          <div className="vr-summary-id">{PORTFOLIO_ID}</div>
          <div className="vr-summary-metrics">
            <div className="vr-metric">
              <span className="vr-metric-label">Current value</span>
              <strong className="vr-metric-value">{formatInr(CURRENT_VALUE, true)}</strong>
              <span className="vr-metric-sub">Invested {formatInr(INVESTED)}</span>
            </div>
            <div className="vr-metric">
              <span className="vr-metric-label">1 day change</span>
              <strong className={`vr-metric-value ${DAY_CHANGE < 0 ? 'neg' : 'pos'}`}>
                {formatInr(DAY_CHANGE)} ({DAY_PCT}%)
              </strong>
            </div>
            <div className="vr-metric">
              <span className="vr-metric-label">All-time returns</span>
              <strong className="vr-metric-value pos">
                +{formatInr(ALL_TIME_GAIN)} · {ALL_TIME_PA}% p.a.
              </strong>
            </div>
          </div>
        </div>

        <nav className="vr-subtabs" aria-label="Portfolio sections">
          <span className="vr-subtab active">Dashboard</span>
        </nav>

        <div className="vr-cards">
          <section className="vr-card">
            <h2 className="vr-card-title">Performance</h2>
            <div className="vr-chip-row" role="group" aria-label="Time range">
              {perfRanges.map(({ key, label }) => (
                <button
                  key={key}
                  type="button"
                  className={perfRange === key ? 'vr-chip active' : 'vr-chip'}
                  onClick={() => setPerfRange(key)}
                  disabled={key === 'CUSTOM'}
                >
                  {label}
                </button>
              ))}
            </div>
            <div className="vr-chart-block">
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={perfData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="t"
                    tick={{ fontSize: 11 }}
                    tickFormatter={(s) => (s as string).slice(0, 4)}
                    minTickGap={28}
                  />
                  <YAxis
                    tickFormatter={formatAxisInr}
                    tick={{ fontSize: 11 }}
                    width={44}
                  />
                  <Tooltip
                    formatter={(v) => [formatInr(Number(v)), 'Value']}
                    labelFormatter={(l) => String(l)}
                  />
                  <Line
                    type="monotone"
                    dataKey="v"
                    stroke="#1e40af"
                    strokeWidth={2}
                    dot={false}
                    name="Portfolio"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <button type="button" className="vr-card-link">
              See performance details →
            </button>
          </section>

          <section className="vr-card">
            <h2 className="vr-card-title">Allocation</h2>
            <div className="vr-toggle">
              <button
                type="button"
                className={allocMode === 'asset' ? 'vr-toggle-btn active' : 'vr-toggle-btn'}
                onClick={() => setAllocMode('asset')}
              >
                By asset
              </button>
              <button
                type="button"
                className={allocMode === 'type' ? 'vr-toggle-btn active' : 'vr-toggle-btn'}
                onClick={() => setAllocMode('type')}
              >
                By investment type
              </button>
            </div>
            <div className="vr-alloc-body">
              <ul className="vr-alloc-legend">
                {allocData.map((d) => (
                  <li key={d.name}>
                    <span className="vr-alloc-dot" style={{ background: d.color }} />
                    <span className="vr-alloc-name">{d.name}</span>
                    <span className="vr-alloc-pct">{d.value}%</span>
                  </li>
                ))}
              </ul>
              <div className="vr-alloc-chart">
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie
                      data={allocData}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={58}
                      outerRadius={88}
                      paddingAngle={2}
                    >
                      {allocData.map((e) => (
                        <Cell key={e.name} fill={e.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => [`${v}%`, 'Share']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
            <button type="button" className="vr-card-link">
              See detailed breakdown →
            </button>
          </section>

          <section className="vr-card">
            <h2 className="vr-card-title">Transactions</h2>
            <p className="vr-card-sub">Amount invested annually, net of withdrawals.</p>
            <div className="vr-chart-block">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={TX_FY} margin={{ top: 28, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                  <XAxis dataKey="fy" tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={formatAxisInr} tick={{ fontSize: 11 }} width={44} />
                  <Tooltip formatter={(v) => [formatInr(Number(v)), 'Invested']} />
                  <Bar dataKey="amount" fill="#1e40af" radius={[4, 4, 0, 0]}>
                    {TX_FY.map((_, i) => (
                      <Cell key={i} fill={i % 2 === 0 ? '#1e40af' : '#3b82f6'} />
                    ))}
                    <LabelList
                      dataKey="amount"
                      position="top"
                      formatter={(v) => formatInr(Number(v))}
                      style={{ fontSize: 11, fill: '#374151' }}
                    />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <button type="button" className="vr-card-link">
              See all transactions →
            </button>
          </section>

          <section className="vr-card">
            <div className="vr-card-head-row">
              <h2 className="vr-card-title">Returns by investment type</h2>
              <label className="vr-duration">
                <span className="vr-duration-label">Duration</span>
                <select
                  className="vr-duration-select"
                  value={duration}
                  onChange={(e) => setDuration(e.target.value as DurationKey)}
                >
                  <option value="1D">1 day</option>
                  <option value="1W">1 week</option>
                  <option value="1M">1 month</option>
                  <option value="YTD">YTD</option>
                  <option value="1Y">1 year</option>
                </select>
              </label>
            </div>
            <ul className="vr-returns-list">
              <li>
                <span className="vr-ret-name">Mutual funds</span>
                <span className={`vr-ret-val ${ret.mutualFunds.amt < 0 ? 'neg' : 'pos'}`}>
                  {formatInr(ret.mutualFunds.amt)} ({ret.mutualFunds.pct}%)
                </span>
              </li>
              <li>
                <span className="vr-ret-name">Stocks</span>
                <span className={`vr-ret-val ${ret.stocks.amt < 0 ? 'neg' : 'pos'}`}>
                  {formatInr(ret.stocks.amt)} ({ret.stocks.pct}%)
                </span>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </div>
  )
}
