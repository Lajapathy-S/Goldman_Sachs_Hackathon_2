import { Link, NavLink, Outlet } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import './LoggedInShell.css'

const links = [
  { to: '/dashboard', label: 'Portfolio', icon: '◫' },
  { to: '/goals', label: 'Guided Goal-Setting', icon: '◎' },
  { to: '/agents', label: 'Agent', icon: '✦' },
  { to: '/rebalance', label: 'AI Rebalance', icon: '⚡' },
]

export function LoggedInShell() {
  const { user, logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    function onResize() {
      if (window.innerWidth >= 900) setSidebarOpen(false)
    }
    window.addEventListener('resize', onResize)
    return () => window.removeEventListener('resize', onResize)
  }, [])

  return (
    <div className="page-shell page-shell--app">
      {sidebarOpen && (
        <button
          type="button"
          className="app-sidebar-backdrop"
          aria-label="Close menu"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside className={`app-sidebar ${sidebarOpen ? 'app-sidebar--open' : ''}`} id="app-sidebar">
        <div className="app-sidebar-brand-row">
          <Link to="/dashboard" className="app-sidebar-brand" onClick={() => setSidebarOpen(false)}>
            <span className="brand-dot" aria-hidden />
            <span className="brand-text">aichemist</span>
          </Link>
        </div>

        <div className="app-sidebar-section">
          <button type="button" className="app-sidebar-heading">
            Workspace
            <span className="app-sidebar-chevron" aria-hidden />
          </button>
          <nav className="app-sidebar-nav" aria-label="Workspace">
            {links.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `app-sidebar-link${isActive ? ' app-sidebar-link--active' : ''}`
                }
                onClick={() => setSidebarOpen(false)}
              >
                <span className="app-sidebar-ico" aria-hidden>
                  {item.icon}
                </span>
                <span className="app-sidebar-label">{item.label}</span>
              </NavLink>
            ))}
          </nav>
        </div>

        <div className="app-sidebar-spacer" />

        <div className="app-sidebar-footer">
          <span className="app-sidebar-user" title={user?.email}>
            {user?.username}
          </span>
          <button type="button" className="app-sidebar-logout" onClick={logout}>
            Log out
          </button>
        </div>
      </aside>

      <div className="app-main-column">
        <header className="app-topbar">
          <button
            type="button"
            className="app-menu-toggle"
            aria-expanded={sidebarOpen}
            aria-controls="app-sidebar"
            onClick={() => setSidebarOpen((v) => !v)}
          >
            <span className="sr-only">Menu</span>
            <span className="nav-menu-icon" aria-hidden />
          </button>
          <Link to="/dashboard" className="app-topbar-title">
            aichemist
          </Link>
        </header>

        <main className="main-content main-content--app">
          <Outlet />
        </main>

        <footer className="site-footer site-footer--app">
          <p className="site-footer-disclaimer">
            Educational simulation — not financial advice. AIChemist does not execute trades.
          </p>
        </footer>
      </div>
    </div>
  )
}
