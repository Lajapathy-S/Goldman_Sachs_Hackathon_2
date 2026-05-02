import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { LoggedInShell } from './LoggedInShell'
import './Layout.css'

type DropdownProps = {
  label: string
  items: { to: string; label: string }[]
}

function Dropdown({ label, items }: DropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (!ref.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  return (
    <div className="nav-dropdown" ref={ref}>
      <button
        type="button"
        className="nav-dropdown-trigger"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {label}
        <span className="nav-dropdown-chevron" aria-hidden />
      </button>
      {open && (
        <div className="nav-dropdown-panel" role="menu">
          {items.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className="nav-dropdown-link"
              role="menuitem"
              onClick={() => setOpen(false)}
            >
              {item.label}
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export function Layout() {
  const { user } = useAuth()
  const location = useLocation()
  const isAuthPage = location.pathname === '/login' || location.pathname === '/signup'
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  useEffect(() => {
    setMobileNavOpen(false)
  }, [location.pathname])

  if (isAuthPage) {
    return <Outlet />
  }

  const loggedInNav = Boolean(user)

  if (loggedInNav) {
    return <LoggedInShell />
  }

  return (
    <div className="page-shell">
      <header className="site-header">
        <div className="site-header-inner container">
          <Link to="/" className="brand">
            <span className="brand-dot" aria-hidden />
            <span className="brand-text">aichemist</span>
          </Link>

          <button
            type="button"
            className="nav-menu-toggle"
            aria-expanded={mobileNavOpen}
            aria-controls="mobile-nav"
            onClick={() => setMobileNavOpen((v) => !v)}
          >
            <span className="sr-only">Menu</span>
            <span className="nav-menu-icon" aria-hidden />
          </button>

          <nav className="site-nav" aria-label="Main">
            <Dropdown
              label="Products"
              items={[
                { to: '/products/stocks', label: 'Stocks' },
                { to: '/products/mutual-funds', label: 'Mutual funds' },
              ]}
            />
            <NavLink to="/agents" className="nav-link-plain">
              Agents
            </NavLink>
            <Dropdown
              label="Tools & resources"
              items={[
                { to: '/tools/sip-calculator', label: 'SIP calculator' },
                { to: '/dashboard', label: 'Portfolio' },
              ]}
            />
            <Dropdown
              label="Company"
              items={[{ to: '/company/about', label: 'About' }]}
            />
          </nav>

          <div className="site-header-actions">
            <Link to="/login" className="btn btn-pill btn-primary">
              Log in
            </Link>
            <Link to="/signup" className="btn btn-pill btn-outline">
              Sign up
            </Link>
          </div>
        </div>

        {mobileNavOpen && (
          <div id="mobile-nav" className="mobile-nav-panel container">
            <Link to="/products/stocks" className="mobile-nav-link">
              Stocks
            </Link>
            <Link to="/products/mutual-funds" className="mobile-nav-link">
              Mutual funds
            </Link>
            <Link to="/agents" className="mobile-nav-link">
              Agents
            </Link>
            <Link to="/tools/sip-calculator" className="mobile-nav-link">
              SIP calculator
            </Link>
            <Link to="/dashboard" className="mobile-nav-link">
              Portfolio
            </Link>
            <Link to="/company/about" className="mobile-nav-link">
              About
            </Link>
          </div>
        )}
      </header>

      <main className="main-content">
        <Outlet />
      </main>

      <footer className="site-footer">
        <div className="container site-footer-inner">
          <p className="site-footer-disclaimer">
            Educational demo. Not investment advice. AIChemist is a learning project inspired by
            modern wealth platforms.
          </p>
        </div>
      </footer>
    </div>
  )
}
