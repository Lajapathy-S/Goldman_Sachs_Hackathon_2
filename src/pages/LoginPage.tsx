import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './AuthPages.css'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPw, setShowPw] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const res = login(username, password)
    if (res.ok) navigate(from || '/dashboard', { replace: true })
    else setError(res.error ?? 'Could not log in.')
  }

  return (
    <div className="auth-split">
      <aside className="auth-split-left">
        <Link to="/" className="auth-brand">
          <span className="brand-dot light" aria-hidden />
          <span className="brand-text light">aichemist</span>
        </Link>
        <h1 className="auth-split-headline">Investing for those who take it seriously.</h1>
        <ul className="auth-split-list">
          <li>Multi-asset investing</li>
          <li>Industry-leading clarity on yields</li>
          <li>AI-powered automation</li>
          <li>Human-readable support</li>
        </ul>
        <div className="auth-chips" aria-label="Product areas">
          <span className="auth-chip">Stocks</span>
          <span className="auth-chip">Mutual funds</span>
          <span className="auth-chip">ETFs</span>
          <span className="auth-chip">High-yield cash</span>
          <span className="auth-chip">Bonds</span>
        </div>
        <p className="auth-legal">
          Demo environment. Use username <strong>admin</strong> and password <strong>admin</strong>{' '}
          to explore.
        </p>
      </aside>

      <section className="auth-split-right">
        <h2 className="auth-form-title">Log in</h2>
        <p className="auth-switch">
          New to AIChemist?{' '}
          <Link to="/signup">Create account →</Link>
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <p className="auth-error">{error}</p>}
          <label className="auth-field">
            <span className="auth-label">Username or email</span>
            <input
              className="auth-input"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </label>
          <label className="auth-field">
            <span className="auth-label">Password</span>
            <span className="auth-input-wrap">
              <input
                className="auth-input has-toggle"
                type={showPw ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
              <button
                type="button"
                className="auth-toggle-pw"
                onClick={() => setShowPw((v) => !v)}
                aria-label={showPw ? 'Hide password' : 'Show password'}
              >
                {showPw ? 'Hide' : 'Show'}
              </button>
            </span>
          </label>
          <p className="auth-forgot">
            <button type="button" className="auth-link-btn">
              Forgot your password?
            </button>
          </p>
          <div className="auth-actions">
            <button type="submit" className="btn btn-pill btn-primary auth-submit">
              Log in
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}
