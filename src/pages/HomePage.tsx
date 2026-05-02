import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './HomePage.css'

export function HomePage() {
  const { user } = useAuth()
  if (user) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div className="home">
      <section className="home-hero container">
        <div className="home-hero-grid">
          <div>
            <h1 className="home-title">
              Investing for those who take it seriously.
            </h1>
            <ul className="home-features" aria-label="Highlights">
              <li>
                <span className="home-feature-icon" aria-hidden>
                  ○
                </span>
                Multi-asset investing
              </li>
              <li>
                <span className="home-feature-icon" aria-hidden>
                  ▦
                </span>
                AI agents & guidance
              </li>
              <li>
                <span className="home-feature-icon" aria-hidden>
                  ↑
                </span>
                Clear cash & yield context
              </li>
            </ul>
          </div>
          <div className="home-hero-cta-wrap">
            <Link to="/signup" className="btn btn-pill btn-primary home-cta-large">
              Get started
              <span className="home-cta-arrow" aria-hidden>
                →
              </span>
            </Link>
          </div>
        </div>

        <div className="home-visual" aria-hidden>
          <div className="home-visual-back">
            <div className="home-visual-chart" />
            <ul className="home-visual-tickers">
              <li>BTC · diversified</li>
              <li>S&P 500 index</li>
              <li>Municipal bonds</li>
            </ul>
          </div>
          <div className="home-visual-phone">
            <div className="home-visual-phone-inner">
              <p className="home-visual-label">Buy · sample</p>
              <p className="home-visual-amt">$100</p>
              <p className="home-visual-sub">Cash buying power</p>
            </div>
          </div>
        </div>

        <p className="home-intro container narrow">
          AIChemist helps people who are new to markets track stocks and mutual funds in one calm
          place. See what you own, how risky it feels, and get plain-language ideas when life or the
          economy shifts — so you can rebalance without guesswork.
        </p>
      </section>
    </div>
  )
}
