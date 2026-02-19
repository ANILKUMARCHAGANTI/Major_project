import { useState, useEffect } from 'react'
import { apiFetch } from '../context/AuthContext'

interface RecItem {
  id: number
  category: string
  priority: number
  message: string
  created_at: string
}

export default function Recommendations() {
  const [recs, setRecs] = useState<RecItem[]>([])
  const [loading, setLoading] = useState(true)
  const [days, setDays] = useState(7)

  useEffect(() => {
    apiFetch(`/recommendations?days=${days}`)
      .then((r) => r.json())
      .then(setRecs)
      .finally(() => setLoading(false))
  }, [days])

  const categoryColor = (c: string) =>
    c === 'hydration' ? '#22d3ee' : c === 'recovery' ? '#34d399' : c === 'nutrition' ? '#fbbf24' : '#a78bfa'

  return (
    <div>
      <h1 style={{ margin: '0 0 24px' }}>Recommendations</h1>
      <p style={{ color: 'var(--text-muted)', margin: '0 0 20px', fontSize: 14 }}>
        Context-aware, non-medical guidance based on your logs.
      </p>
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
      ) : recs.length === 0 ? (
        <p style={{ color: 'var(--text-muted)' }}>No recommendations yet. Log some data to get personalized guidance.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {recs.map((r) => (
            <div
              key={r.id}
              style={{
                padding: 16,
                background: 'var(--bg-card)',
                borderRadius: 12,
                border: '1px solid var(--border)',
                borderLeft: `4px solid ${categoryColor(r.category)}`,
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <span style={{
                  textTransform: 'capitalize',
                  fontSize: 12,
                  fontWeight: 600,
                  color: categoryColor(r.category),
                }}>
                  {r.category}
                </span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{r.created_at?.slice(0, 10)}</span>
              </div>
              <p style={{ margin: 0 }}>{r.message}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
