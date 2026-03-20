import React, { useState } from 'react'
import api from '../services/api'
import { Shield, Truck, Eye, EyeOff } from 'lucide-react'

export default function LoginPage({ onLogin }) {
  const [isRegister, setIsRegister] = useState(false)
  const [role, setRole] = useState('worker')
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    platform: 'amazon',
    warehouse_id: 'WH-001',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPw, setShowPw] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      let result
      if (isRegister) {
        result = await api.register({ ...form, role })
      } else {
        result = await api.login({ email: form.email, password: form.password })
      }

      if (result?.access_token) {
        onLogin(result)
      } else {
        setError(result?.detail || 'Authentication failed. Please try again.')
      }
    } catch (err) {
      setError('Connection error. Is the backend running?')
    }
    setLoading(false)
  }

  return (
    <div className="auth-page">
      <div className="auth-card animate-in">
        <div className="auth-logo">
          <div className="logo-circle">
            <Shield size={30} color="white" />
          </div>
          <h2>ShieldPay AI</h2>
          <p className="auth-subtitle">
            {isRegister
              ? 'Create your income protection account'
              : 'Sign in to your dashboard'}
          </p>
        </div>

        {error && (
          <div style={{
            padding: '10px 14px',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.2)',
            color: 'var(--accent-danger)',
            fontSize: '13px',
            marginBottom: '16px'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <div className="role-selector">
                <button
                  type="button"
                  className={`role-btn ${role === 'worker' ? 'active' : ''}`}
                  onClick={() => setRole('worker')}
                >
                  <Truck size={14} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                  Delivery Worker
                </button>
                <button
                  type="button"
                  className={`role-btn ${role === 'admin' ? 'active' : ''}`}
                  onClick={() => setRole('admin')}
                >
                  <Shield size={14} style={{ marginRight: 4, verticalAlign: 'middle' }} />
                  Admin
                </button>
              </div>

              <div className="form-group">
                <label>Full Name</label>
                <input
                  className="form-input"
                  placeholder="Enter your name"
                  value={form.name}
                  onChange={e => setForm({ ...form, name: e.target.value })}
                  required
                />
              </div>
            </>
          )}

          <div className="form-group">
            <label>Email</label>
            <input
              className="form-input"
              type="email"
              placeholder="you@example.com"
              value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>

          {isRegister && (
            <div className="form-group">
              <label>Phone</label>
              <input
                className="form-input"
                placeholder="+91 98765 43210"
                value={form.phone}
                onChange={e => setForm({ ...form, phone: e.target.value })}
                required
              />
            </div>
          )}

          <div className="form-group">
            <label>Password</label>
            <div style={{ position: 'relative' }}>
              <input
                className="form-input"
                type={showPw ? 'text' : 'password'}
                placeholder="••••••••"
                value={form.password}
                onChange={e => setForm({ ...form, password: e.target.value })}
                required
              />
              <button
                type="button"
                onClick={() => setShowPw(!showPw)}
                style={{
                  position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer'
                }}
              >
                {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {isRegister && role === 'worker' && (
            <div style={{ display: 'flex', gap: '12px' }}>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Platform</label>
                <select
                  className="form-input"
                  value={form.platform}
                  onChange={e => setForm({ ...form, platform: e.target.value })}
                >
                  <option value="amazon">Amazon</option>
                  <option value="flipkart">Flipkart</option>
                  <option value="meesho">Meesho</option>
                  <option value="jiomart">JioMart</option>
                </select>
              </div>
              <div className="form-group" style={{ flex: 1 }}>
                <label>Warehouse</label>
                <select
                  className="form-input"
                  value={form.warehouse_id}
                  onChange={e => setForm({ ...form, warehouse_id: e.target.value })}
                >
                  {Array.from({ length: 15 }, (_, i) => (
                    <option key={i} value={`WH-${String(i + 1).padStart(3, '0')}`}>
                      WH-{String(i + 1).padStart(3, '0')}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <button className="btn btn-primary w-full" type="submit" disabled={loading}
            style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}>
            {loading ? 'Processing...' : isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div className="auth-toggle">
          {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
          <a onClick={() => { setIsRegister(!isRegister); setError('') }}>
            {isRegister ? 'Sign In' : 'Register'}
          </a>
        </div>
      </div>
    </div>
  )
}
