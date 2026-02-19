import { useState, useEffect } from 'react'
import { apiFetch } from '../context/AuthContext'

interface AlertItem {
  id: number
  alert_type: string
  severity: string
  message: string
  created_at: string
}

export default function Alerts() {
  const [alerts, setAlerts] = useState<AlertItem[]>([])
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(14)

  useEffect(() => {
    apiFetch(`/alerts?days=${days}`)
      .then((r) => r.json())
      .then(setAlerts)
      .finally(() => setLoading(false))
  }, [days])

  const severityColor = (s: string) =>
    s === 'high' ? 'var(--danger)' : s === 'medium' ? 'var(--warning)' : 'var(--text-muted)'

  return (
    <div>
      <h1 style={{ margin: '0 0 24px' }}>Alerts</h1>
      <div style={{ marginBottom: 20 }}>
        <label style={{ marginRight: 8, color: 'var(--text-muted)' }}>Show last</label>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          style={{
            padding: '8px 12px',
            borderRadius: 8,
            border: '1px solid var(--border)',
            background: 'var(--bg)',
            color: 'var(--text)',
          }}
        >
          <option value={7}>7 days</option>
          <option value={14}>14 days</option>
          <option value={30}>30 days</option>
        </select>
      </div>

      {loading ? (
        <div>Loading...</div>
      ) : alerts.length === 0 ? (
        <p style={{ color: 'var(--text-muted)' }}>No alerts in this period.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {alerts.map((a) => (
            <div
              key={a.id}
              style={{
                padding: 16,
                background: 'var(--bg-card)',
                borderRadius: 12,
                border: '1px solid var(--border)',
                borderLeft: `4px solid ${severityColor(a.severity)}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <span style={{
                  textTransform: 'uppercase',
                  fontSize: 12,
                  fontWeight: 600,
                  color: severityColor(a.severity),
                }}>
                  {a.alert_type.replace(/_/g, ' ')}
                </span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{a.created_at?.slice(0, 10)}</span>
              </div>
              <p style={{ margin: 0 }}>{a.message}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
