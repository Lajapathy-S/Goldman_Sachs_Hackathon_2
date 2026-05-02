import './ProductsPages.css'

export function StocksPage() {
  return (
    <article className="product-page container">
      <h1>Stocks</h1>
      <p className="product-lead">
        Own pieces of companies you believe in. AIChemist summarizes what each holding does for
        your portfolio and flags concentration so you are never surprised by a single stock.
      </p>
      <div className="product-grid">
        <section className="product-card">
          <h2>Simple allocation view</h2>
          <p>
            See equities as a share of your total wealth next to mutual funds and cash. Percentages
            update as markets move, in language that does not require a finance degree.
          </p>
        </section>
        <section className="product-card">
          <h2>Risk in plain words</h2>
          <p>
            We translate volatility and sector mix into a short risk snapshot. When uncertainty rises,
            you get context on what might swing more — not alarmist alerts.
          </p>
        </section>
        <section className="product-card">
          <h2>Rebalance nudges</h2>
          <p>
            When your goals or the economy shift, we suggest gentle trims or adds so your stock
            sleeve stays aligned with the plan you chose.
          </p>
        </section>
        <section className="product-card">
          <h2>Education on demand</h2>
          <p>
            Tooltips and short explainers cover dividends, market cap, and why diversification
            matters — built for people who are serious about learning while they invest.
          </p>
        </section>
      </div>
    </article>
  )
}
