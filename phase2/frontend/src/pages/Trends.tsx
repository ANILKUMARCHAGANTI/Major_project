import { useState, useEffect } from 'react'
import { apiFetch } from '../context/AuthContext'

interface HistoryItem {
  date: string
  readiness_score: number
  fatigue_index: number
  recovery_score: number
  hydration_score: number
  nutrition_score: number
  acute_chronic_ratio: number
}

export default function Trends() {
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(30)

  useEffect(() => {
    apiFetch(`/dashboard/history?days=${days}`)
      .then((r) => r.json())
      .then((d) => setHistory(d.history || []))
      .finally(() => setLoading(false))
  }, [days])

  if (loading) return <div>Loading trends...</div>
  if (history.length === 0) return (
    <div>
      <h1 style={{ margin: '0 0 24px' }}>Trends</h1>
      <p style={{ color: 'var(--text-muted)' }}>No history yet. Log daily data to see trends.</p>
    </div>
  )

  const metrics = ['readiness_score', 'recovery_score', 'hydration_score', 'nutrition_score', 'fatigue_index', 'acute_chronic_ratio'] as const
  const maxReadiness = Math.max(...history.map((h) => h.readiness_score), 1)

  return (
    <div>
      <h1 style={{ margin: '0 0 24px' }}>Trends</h1>
      <div style={{ marginBottom: 20 }}>
        <label style={{ marginRight: 8, color: 'var(--text-muted)' }}>Period</label>
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
          <option value={90}>90 days</option>
        </select>
      </div>

      <div style={{
        padding: 24,
        background: 'var(--bg-card)',
        borderRadius: 12,
        border: '1px solid var(--border)',
        overflowX: 'auto',
      }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16 }}>Readiness Score Over Time</h3>
        <div style={{
          display: 'flex',
          alignItems: 'flex-end',
          gap: 4,
          height: 200,
          minWidth: Math.max(400, history.length * 12),
        }}>
          {history.map((h, i) => (
            <div
              key={h.date}
              title={`${h.date}: ${h.readiness_score}`}
              style={{
                flex: 1,
                minWidth: 8,
                height: `${(h.readiness_score / 100) * 100}%`,
                minHeight: 4,
                background: h.readiness_score >= 70 ? 'var(--success)' : h.readiness_score >= 50 ? 'var(--warning)' : 'var(--danger)',
                borderRadius: 4,
                opacity: 0.9,
              }}
            />
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
          <span>{history[0]?.date}</span>
          <span>{history[history.length - 1]?.date}</span>
        </div>
      </div>

      <div style={{ marginTop: 24 }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 16 }}>History Table</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: 10, borderBottom: '1px solid var(--border)' }}>Date</th>
                {metrics.map((m) => (
                  <th key={m} style={{ textAlign: 'right', padding: 10, borderBottom: '1px solid var(--border)' }}>
                    {m.replace(/_/g, ' ')}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {[...history].reverse().map((h) => (
                <tr key={h.date}>
                  <td style={{ padding: 10, borderBottom: '1px solid var(--border)' }}>{h.date}</td>
                  {metrics.map((m) => (
                    <td key={m} style={{ textAlign: 'right', padding: 10, borderBottom: '1px solid var(--border)' }}>
                      {Number(h[m]).toFixed(1)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
