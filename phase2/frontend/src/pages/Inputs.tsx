import { useState } from 'react'
import { apiFetch } from '../context/AuthContext'

export default function Inputs() {
  const [sessionForm, setSessionForm] = useState({
    session_date: new Date().toISOString().slice(0, 10),
    session_mins: 60,
    intensity: 6,
    distance_km: 10,
    activity_type: 'general',
    notes: '',
  })
  const [sessionSuccess, setSessionSuccess] = useState('')
  const [date, setDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [form, setForm] = useState({
    sleep_hours: 7,
    soreness: 3,
    mood: 5,
    water_intake_L: 2.5,
    sweat_loss_L: 1.5,
    calories_in: 2200,
    activity_calories: 500,
    temp_c: 22,
    humidity: 0.5,
  })
  const [result, setResult] = useState<unknown>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await apiFetch('/inputs/daily', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ log_date: date, ...form }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        const detail = err.detail
        let msg = 'Failed to submit'
        if (typeof detail === 'string') msg = detail
        else if (Array.isArray(detail) && detail.length > 0)
          msg = detail.map((d: { msg?: string; loc?: unknown[] }) => d.msg || JSON.stringify(d)).join('; ')
        else if (detail?.message) msg = detail.message
        else if (res.status === 401) msg = 'Session expired. Please log in again.'
        else if (res.status === 500) msg = 'Server error. Check that the backend is running.'
        throw new Error(msg)
      }
      const data = await res.json()
      setResult(data)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed'
      setError(msg)
      console.error('Submit error:', err)
    } finally {
      setLoading(false)
    }
  }

  const fields = [
    { key: 'sleep_hours', label: 'Sleep (hours)', min: 0, max: 24, step: 0.5 },
    { key: 'soreness', label: 'Soreness (0-10)', min: 0, max: 10, step: 0.5 },
    { key: 'mood', label: 'Mood (0-10)', min: 0, max: 10, step: 0.5 },
    { key: 'water_intake_L', label: 'Water Intake (L)', min: 0, max: 20, step: 0.25 },
    { key: 'sweat_loss_L', label: 'Sweat Loss (L)', min: 0, max: 15, step: 0.25 },
    { key: 'calories_in', label: 'Calories In (kcal)', min: 0, max: 10000, step: 50 },
    { key: 'activity_calories', label: 'Activity Calories (kcal)', min: 0, max: 5000, step: 50 },
    { key: 'temp_c', label: 'Temperature (°C)', min: -10, max: 50, step: 1 },
    { key: 'humidity', label: 'Humidity (0-1)', min: 0, max: 1, step: 0.05 },
  ] as const

  return (
    <div>
      <h1 style={{ margin: '0 0 24px' }}>Daily Log Input</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 16 }}>
        Ensure the backend is running on port 8000. Data: SQLite or Supabase (see backend <code>.env</code>).
      </p>
      <form onSubmit={submit} style={{
        maxWidth: 520,
        padding: 24,
        background: 'var(--bg-card)',
        borderRadius: 12,
        border: '1px solid var(--border)',
        marginBottom: 24,
      }}>
        <div style={{ marginBottom: 20 }}>
          <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: 14 }}>Date</label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            style={inputStyle}
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {fields.map(({ key, label, min, max, step }) => (
            <div key={key}>
              <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: 14 }}>{label}</label>
              <input
                type="number"
                value={form[key]}
                onChange={(e) => setForm((f) => ({ ...f, [key]: parseFloat(e.target.value) || 0 }))}
                min={min}
                max={max}
                step={step}
                style={inputStyle}
              />
            </div>
          ))}
        </div>
        {error && <p style={{ color: 'var(--danger)', marginTop: 16 }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ ...buttonStyle, marginTop: 24 }}>
          {loading ? 'Submitting...' : 'Submit Daily Log'}
        </button>
      </form>

      {result && (
        <div style={{
          padding: 24,
          background: 'var(--bg-card)',
          borderRadius: 12,
          border: '1px solid var(--border)',
        }}>
          <h2 style={{ margin: '0 0 16px', fontSize: 18 }}>Response</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
            {result.metrics && Object.entries(result.metrics).filter(([k]) => !['breakdown'].includes(k)).map(([k, v]) => (
              <div key={k} style={{
                padding: 12,
                background: 'var(--bg)',
                borderRadius: 8,
                textAlign: 'center',
              }}>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{k.replace(/_/g, ' ')}</div>
                <div style={{ fontSize: 20, fontWeight: 600 }}>{Number(v).toFixed(1)}</div>
              </div>
            ))}
          </div>
          {result.alerts?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <h3 style={{ margin: '0 0 8px', fontSize: 14 }}>Alerts</h3>
              <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--warning)' }}>
                {result.alerts.map((a: { message: string }) => (
                  <li key={a.message}>{a.message}</li>
                ))}
              </ul>
            </div>
          )}
          {result.recommendations?.length > 0 && (
            <div>
              <h3 style={{ margin: '0 0 8px', fontSize: 14 }}>Recommendations</h3>
              <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--success)' }}>
                {result.recommendations.map((r: { message: string }) => (
                  <li key={r.message}>{r.message}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      <details style={{
        marginTop: 32,
        padding: 24,
        background: 'var(--bg-card)',
        borderRadius: 12,
        border: '1px solid var(--border)',
      }}>
        <summary style={{ cursor: 'pointer', fontWeight: 600, marginBottom: 16 }}>Log Training Session</summary>
        <form
          onSubmit={async (e) => {
            e.preventDefault()
            setSessionSuccess('')
            try {
              const res = await apiFetch('/inputs/session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(sessionForm),
              })
              const data = await res.json()
              setSessionSuccess(data.message || 'Session logged')
            } catch (err) {
              setSessionSuccess('Failed: ' + (err instanceof Error ? err.message : 'Unknown'))
            }
          }}
          style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, maxWidth: 500 }}
        >
          <div>
            <label style={{ display: 'block', marginBottom: 6, fontSize: 14 }}>Date</label>
            <input type="date" value={sessionForm.session_date} onChange={(e) => setSessionForm((f) => ({ ...f, session_date: e.target.value }))} style={inputStyle} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 6, fontSize: 14 }}>Duration (min)</label>
            <input type="number" value={sessionForm.session_mins} onChange={(e) => setSessionForm((f) => ({ ...f, session_mins: Number(e.target.value) || 0 }))} style={inputStyle} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 6, fontSize: 14 }}>Intensity (0-10)</label>
            <input type="number" min={0} max={10} step={0.5} value={sessionForm.intensity} onChange={(e) => setSessionForm((f) => ({ ...f, intensity: Number(e.target.value) || 0 }))} style={inputStyle} />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 6, fontSize: 14 }}>Distance (km)</label>
            <input type="number" min={0} step={0.1} value={sessionForm.distance_km} onChange={(e) => setSessionForm((f) => ({ ...f, distance_km: Number(e.target.value) || 0 }))} style={inputStyle} />
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'block', marginBottom: 6, fontSize: 14 }}>Activity Type</label>
            <input value={sessionForm.activity_type} onChange={(e) => setSessionForm((f) => ({ ...f, activity_type: e.target.value }))} style={inputStyle} placeholder="e.g. running, cycling" />
          </div>
          <div style={{ gridColumn: '1 / -1' }}>
            <button type="submit" style={buttonStyle}>Log Session</button>
            {sessionSuccess && <span style={{ marginLeft: 12, color: 'var(--success)' }}>{sessionSuccess}</span>}
          </div>
        </form>
      </details>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 12px',
  borderRadius: 8,
  border: '1px solid var(--border)',
  background: 'var(--bg)',
  color: 'var(--text)',
}

const buttonStyle: React.CSSProperties = {
  padding: '10px 20px',
  background: 'var(--accent)',
  color: 'var(--bg)',
  border: 'none',
  borderRadius: 8,
  fontWeight: 600,
}
