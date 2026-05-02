import './ProductsPages.css'

export function MutualFundsPage() {
  return (
    <article className="product-page container">
      <h1>Mutual funds</h1>
      <p className="product-lead">
        Pool your money with other investors into professionally managed baskets. Ideal when you want
        broad exposure without picking every stock yourself — we make fees and categories easy to
        compare.
      </p>
      <div className="product-grid">
        <section className="product-card">
          <h2>One place for fund facts</h2>
          <p>
            Expense ratios, category, and benchmark — surfaced without PDF hunting. You always know
            what kind of fund you hold and how it fits next to direct stocks.
          </p>
        </section>
        <section className="product-card">
          <h2>Overlap awareness</h2>
          <p>
            Multiple funds can hide the same underlying names. We highlight overlap so your
            diversification is real, not accidental duplication.
          </p>
        </section>
        <section className="product-card">
          <h2>SIP-ready mindset</h2>
          <p>
            Pair recurring investments with our SIP calculator. See how steady contributions and
            average costs interact with your broader portfolio targets.
          </p>
        </section>
        <section className="product-card">
          <h2>Macro scenarios</h2>
          <p>
            When rates or inflation narratives change, we outline how typical equity and bond funds
            might behave — so you can rebalance calmly instead of reacting to headlines alone.
          </p>
        </section>
      </div>
    </article>
  )
}
