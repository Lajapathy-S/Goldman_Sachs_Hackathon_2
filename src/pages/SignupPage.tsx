import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './AuthPages.css'

export function SignupPage() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const res = signup(username, email, password)
    if (res.ok) navigate('/dashboard')
    else setError(res.error ?? 'Could not create account.')
  }

  return (
    <div className="auth-split">
      <aside className="auth-split-left">
        <Link to="/" className="auth-brand">
          <span className="brand-dot light" aria-hidden />
          <span className="brand-text light">aichemist</span>
        </Link>
        <h1 className="auth-split-headline">Wealth management, without the jargon.</h1>
        <p className="auth-split-lead">
          Track stocks and mutual funds, understand risk in plain language, and rebalance when your
          goals change.
        </p>
        <ul className="auth-split-list">
          <li>Unified portfolio view</li>
          <li>Risk snapshot & scenarios</li>
          <li>Guided rebalancing tips</li>
        </ul>
      </aside>

      <section className="auth-split-right">
        <h2 className="auth-form-title">Create account</h2>
        <p className="auth-switch">
          Already have an account? <Link to="/login">Log in →</Link>
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <p className="auth-error">{error}</p>}
          <label className="auth-field">
            <span className="auth-label">Username</span>
            <input
              className="auth-input"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </label>
          <label className="auth-field">
            <span className="auth-label">Email</span>
            <input
              className="auth-input"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </label>
          <label className="auth-field">
            <span className="auth-label">Password</span>
            <input
              className="auth-input"
              type="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
          </label>
          <p className="auth-hint">Minimum 6 characters. Stored locally in this demo.</p>
          <div className="auth-actions">
            <button type="submit" className="btn btn-pill btn-primary auth-submit">
              Sign up
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}
