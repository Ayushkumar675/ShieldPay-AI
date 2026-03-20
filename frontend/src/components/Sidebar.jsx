import React from 'react'
import { Shield, LayoutDashboard, FileText, CreditCard, AlertTriangle, CloudLightning, LogOut, User } from 'lucide-react'

export default function Sidebar({ user, isAdmin, activePage, onNavigate, onLogout }) {
  const workerNav = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'claims', label: 'My Claims', icon: FileText },
    { id: 'policy', label: 'My Policy', icon: CreditCard },
    { id: 'disruptions', label: 'Disruptions', icon: CloudLightning },
  ]

  const adminNav = [
    { id: 'dashboard', label: 'Analytics', icon: LayoutDashboard },
    { id: 'claims', label: 'All Claims', icon: FileText },
    { id: 'fraud', label: 'Fraud Detection', icon: AlertTriangle },
    { id: 'disruptions', label: 'Disruptions', icon: CloudLightning },
  ]

  const navItems = isAdmin ? adminNav : workerNav

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-icon">
          <Shield size={22} color="white" />
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
            </button>
          )
        })}
      </nav>

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
