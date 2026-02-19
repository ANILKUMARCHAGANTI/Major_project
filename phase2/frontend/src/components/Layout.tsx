import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const nav = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/inputs', label: 'Inputs' },
  { to: '/alerts', label: 'Alerts' },
  { to: '/recommendations', label: 'Recommendations' },
  { to: '/trends', label: 'Trends' },
  { to: '/profile', label: 'Profile' },
]

export default function Layout() {
  const { logout } = useAuth()
  const navigate = useNavigate()

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <aside style={{
        width: 220,
        background: 'var(--bg-card)',
        borderRight: '1px solid var(--border)',
        padding: '24px 0',
      }}>
        <div style={{ padding: '0 20px 20px', borderBottom: '1px solid var(--border)', marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Athlete Readiness</h2>
          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Phase 2</span>
        </div>
        <nav>
          {nav.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              style={({ isActive }) => ({
                display: 'block',
                padding: '10px 20px',
                color: isActive ? 'var(--accent)' : 'var(--text-muted)',
                borderLeft: isActive ? '3px solid var(--accent)' : '3px solid transparent',
                textDecoration: 'none',
              })}
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div style={{ padding: 20, marginTop: 'auto', fontSize: 11, color: 'var(--text-muted)' }}>
          <div style={{ marginBottom: 12 }}>Database</div>
          <div style={{ marginBottom: 12 }}>SQLite or Supabase</div>
          <button
            onClick={() => { logout(); navigate('/login') }}
            style={{
              background: 'transparent',
              border: '1px solid var(--border)',
              color: 'var(--text-muted)',
              padding: '8px 16px',
              borderRadius: 8,
              width: '100%',
            }}
          >
            Logout
          </button>
        </div>
      </aside>
      <main style={{ flex: 1, padding: 32, overflow: 'auto' }}>
        <Outlet />
      </main>
    </div>
  )
}
