import React, { useState, useEffect } from 'react'
import { Shield, LayoutDashboard, FileText, CreditCard, AlertTriangle, CloudLightning, LogOut, User, Radio } from 'lucide-react'
import api from '../services/api'

export default function Sidebar({ user, isAdmin, activePage, onNavigate, onLogout }) {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    loadHealth()
    // Refresh health every 30 seconds
    const interval = setInterval(loadHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadHealth = async () => {
    const data = await api.getSystemHealth()
    if (data) setHealth(data)
  }

  const healthColor = health?.health === 'healthy' ? '#10b981'
    : health?.health === 'caution' ? '#f59e0b'
    : health?.health === 'critical' ? '#ef4444'
    : '#64748b'

  const workerNav = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'claims', label: 'My Claims', icon: FileText },
    { id: 'policy', label: 'My Policy', icon: CreditCard },
    { id: 'disruptions', label: 'Disruptions', icon: CloudLightning },
  ]

  const adminNav = [
    { id: 'dashboard', label: 'Analytics', icon: LayoutDashboard },
    { id: 'claims', label: 'All Claims', icon: FileText },
    { id: 'fraud', label: 'Fraud Detection', icon: AlertTriangle, badge: health?.active_fraud_alerts || 0 },
    { id: 'disruptions', label: 'Disruptions', icon: CloudLightning },
  ]

  const navItems = isAdmin ? adminNav : workerNav

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon" style={{ position: 'relative' }}>
          <Shield size={22} color="white" />
          {/* System Pulse Dot */}
          <div className="system-pulse" style={{
            position: 'absolute', top: -2, right: -2,
            width: 10, height: 10, borderRadius: '50%',
            background: healthColor,
            boxShadow: `0 0 6px ${healthColor}`,
            border: '2px solid var(--bg-secondary)',
          }} />
        </div>
        <div>
          <h1>ShieldPay AI</h1>
          <span>Income Protection</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(item => {
          const Icon = item.icon
          return (
            <button
              key={item.id}
              className={`nav-link ${activePage === item.id ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
            >
              <Icon size={18} />
              {item.label}
              {item.badge > 0 && (
                <span className="nav-badge" style={{
                  marginLeft: 'auto', background: 'var(--accent-danger)',
                  color: 'white', fontSize: 10, fontWeight: 700,
                  padding: '2px 6px', borderRadius: 10, minWidth: 18,
                  textAlign: 'center', lineHeight: '14px',
                }}>
                  {item.badge > 99 ? '99+' : item.badge}
                </span>
              )}
            </button>
          )
        })}
      </nav>

      {/* System Status */}
      {isAdmin && health && (
        <div style={{
          padding: '10px 14px', marginBottom: 8, borderRadius: 'var(--radius-sm)',
          background: `${healthColor}08`, border: `1px solid ${healthColor}20`,
          fontSize: 11,
        }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 4 }}>
            <Radio size={12} color={healthColor} />
            <span style={{ fontWeight: 600, color: healthColor, textTransform: 'capitalize' }}>
              System {health.health}
            </span>
          </div>
          <div style={{ color: 'var(--text-muted)' }}>
            Liquidity: {health.liquidity_ratio?.toFixed(1)}x
          </div>
        </div>
      )}

      <div className="sidebar-footer">
        <div className="nav-link" style={{ cursor: 'default', opacity: 0.8 }}>
          <User size={18} />
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {user?.name || 'User'}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
              {user?.role}
            </div>
          </div>
        </div>
        <button className="nav-link" onClick={onLogout} style={{ color: 'var(--accent-danger)', marginTop: '4px' }}>
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </aside>
  )
}
