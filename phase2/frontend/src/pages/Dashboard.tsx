import { useState, useEffect } from 'react'
import { apiFetch } from '../context/AuthContext'

interface LatestData {
  log_date: string
  metrics: Record<string, number>
  breakdown: Record<string, unknown>
}

export default function Dashboard() {
  const [data, setData] = useState<LatestData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch('/dashboard/latest')
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div>Loading dashboard...</div>
  if (!data?.metrics) return (
    <div>
      <h1 style={{ margin: '0 0 24px' }}>Dashboard</h1>
      <p style={{ color: 'var(--text-muted)' }}>No data yet. Go to <a href="/inputs">Inputs</a> to log your first day.</p>
    </div>
  )

  const m = data.metrics
  const readinessColor = m.readiness_score >= 70 ? 'var(--success)' : m.readiness_score >= 50 ? 'var(--warning)' : 'var(--danger)'

  return (
    <div>
      <h1 style={{ margin: '0 0 8px' }}>Dashboard</h1>
      <p style={{ color: 'var(--text-muted)', margin: '0 0 24px', fontSize: 14 }}>Latest: {data.log_date}</p>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
        gap: 16,
        marginBottom: 32,
      }}>
        <MetricCard label="Readiness" value={m.readiness_score} suffix="" color={readinessColor} />
        <MetricCard label="Fatigue Index" value={m.fatigue_index} suffix="/10" />
        <MetricCard label="Recovery" value={m.recovery_score} suffix="" color="var(--success)" />
        <MetricCard label="Hydration" value={m.hydration_score} suffix="" />
        <MetricCard label="Nutrition" value={m.nutrition_score} suffix="" />
        <MetricCard label="Consistency" value={m.consistency_score} suffix="" />
        <MetricCard label="Acute:Chronic" value={m.acute_chronic_ratio} suffix="" />
        <MetricCard label="Load Balance" value={m.training_load_balance} suffix="" />
      </div>

      {data.breakdown && Object.keys(data.breakdown).length > 0 && (
        <div style={{
          padding: 24,
          background: 'var(--bg-card)',
          borderRadius: 12,
          border: '1px solid var(--border)',
        }}>
          <h2 style={{ margin: '0 0 16px', fontSize: 18 }}>Explainability</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 16 }}>
            Formula breakdowns for each metric. All values are transparent and traceable.
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
            {Object.entries(data.breakdown).map(([name, b]) => (
              <details key={name} style={{
                padding: 12,
                background: 'var(--bg)',
                borderRadius: 8,
                minWidth: 200,
              }}>
                <summary style={{ cursor: 'pointer', fontWeight: 600 }}>
                  {(b as { value?: number }).value != null
                    ? `${String(name).replace(/_/g, ' ')}: ${(b as { value: number }).value}`
                    : name}
                </summary>
                <pre style={{ margin: '8px 0 0', fontSize: 12, color: 'var(--text-muted)', overflow: 'auto' }}>
                  {JSON.stringify(b, null, 2)}
                </pre>
              </details>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function MetricCard({
  label,
  value,
  suffix,
  color = 'var(--text)',
}: {
  label: string
  value: number
  suffix: string
  color?: string
}) {
  return (
    <div style={{
      padding: 20,
      background: 'var(--bg-card)',
      borderRadius: 12,
      border: '1px solid var(--border)',
      textAlign: 'center',
    }}>
      <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{Number(value).toFixed(1)}{suffix}</div>
    </div>
  )
}
