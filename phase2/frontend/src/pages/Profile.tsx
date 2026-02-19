import { useState, useEffect } from 'react'
import { apiFetch } from '../context/AuthContext'

interface ProfileData {
  id: number
  email: string
  full_name: string
  sport: string
  body_mass_kg: number
  bmr_kcal: number
  vo2max: number
}

export default function Profile() {
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [edit, setEdit] = useState<Partial<ProfileData>>({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    apiFetch('/profile/me')
      .then(async (r) => {
        if (!r.ok) {
          if (r.status === 401) {
            localStorage.removeItem('token')
            window.location.href = '/login'
            throw new Error('Session expired')
          }
          throw new Error('Failed to load profile')
        }
        return r.json()
      })
      .then(setProfile)
      .catch(() => setProfile(null))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (profile) setEdit(profile)
  }, [profile])

  const save = async () => {
    setSaving(true)
    setMessage(null)
    try {
      const res = await apiFetch('/profile/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: edit.full_name,
          sport: edit.sport,
          body_mass_kg: edit.body_mass_kg,
          bmr_kcal: edit.bmr_kcal,
          vo2max: edit.vo2max,
        }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        const msg = typeof err.detail === 'string' ? err.detail : err.detail?.[0]?.msg || 'Save failed'
        throw new Error(msg)
      }
      const updated = await res.json()
      setProfile(updated)
      setMessage({ type: 'success', text: 'Profile saved successfully.' })
      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      setMessage({ type: 'error', text: err instanceof Error ? err.message : 'Save failed' })
    } finally {
      setSaving(false)
    }
  }

  if (loading || !profile) return <div>Loading profile...</div>

  return (
    <div>
      <h1 style={{ margin: '0 0 24px' }}>Profile</h1>
      <div style={{
        maxWidth: 500,
        padding: 24,
        background: 'var(--bg-card)',
        borderRadius: 12,
        border: '1px solid var(--border)',
      }}>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: 14 }}>Email</label>
          <span>{profile.email}</span>
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: 14 }}>Full Name</label>
          <input
            value={edit.full_name ?? ''}
            onChange={(e) => setEdit((p) => ({ ...p, full_name: e.target.value }))}
            style={inputStyle}
          />
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: 14 }}>Sport</label>
          <input
            value={edit.sport ?? ''}
            onChange={(e) => setEdit((p) => ({ ...p, sport: e.target.value }))}
            style={inputStyle}
            placeholder="e.g. running, cycling"
          />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <div>
            <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: 14 }}>Body Mass (kg)</label>
            <input
              type="number"
              step={0.1}
              value={edit.body_mass_kg ?? ''}
              onChange={(e) => setEdit((p) => ({ ...p, body_mass_kg: parseFloat(e.target.value) || 0 }))}
              style={inputStyle}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: 14 }}>BMR (kcal/day)</label>
            <input
              type="number"
              value={edit.bmr_kcal ?? ''}
              onChange={(e) => setEdit((p) => ({ ...p, bmr_kcal: parseFloat(e.target.value) || 0 }))}
              style={inputStyle}
            />
          </div>
        </div>
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', marginBottom: 6, color: 'var(--text-muted)', fontSize: 14 }}>VO2max (ml/kg/min)</label>
          <input
            type="number"
            step={0.1}
            value={edit.vo2max ?? ''}
            onChange={(e) => setEdit((p) => ({ ...p, vo2max: parseFloat(e.target.value) || 0 }))}
            style={inputStyle}
          />
        </div>
        <button onClick={save} disabled={saving} style={buttonStyle}>
          {saving ? 'Saving...' : 'Save Profile'}
        </button>
        {message && (
          <p style={{
            marginTop: 16,
            color: message.type === 'success' ? 'var(--success)' : 'var(--danger)',
            fontSize: 14,
          }}>
            {message.text}
          </p>
        )}
      </div>
      <p style={{ marginTop: 24, fontSize: 12, color: 'var(--text-muted)' }}>
        Data is stored in SQLite (local) or Supabase (cloud) — configure <code>DATABASE_URL</code> in <code>.env</code>.
      </p>
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
