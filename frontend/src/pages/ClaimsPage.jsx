import React, { useState, useEffect } from 'react'
import { FileText, CheckCircle, Clock, XCircle, Zap, AlertTriangle } from 'lucide-react'
import api from '../services/api'

const statusConfig = {
  paid: { label: 'Paid', badge: 'success', icon: CheckCircle },
  auto_approved: { label: 'Auto Approved', badge: 'success', icon: Zap },
  soft_verify: { label: 'Needs Confirm', badge: 'warning', icon: Clock },
  delayed_review: { label: 'Under Review', badge: 'info', icon: Clock },
  rejected: { label: 'Rejected', badge: 'danger', icon: XCircle },
  pending: { label: 'Pending', badge: 'info', icon: Clock },
}

export default function ClaimsPage({ isAdmin }) {
  const [claims, setClaims] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadClaims()
  }, [])

  const loadClaims = async () => {
    setLoading(true)

    // Try AI recent claims first (from simulation)
    const aiClaims = await api.getRecentClaims()
    if (aiClaims?.claims?.length) {
      setClaims(aiClaims.claims)
      setLoading(false)
      return
    }

    // Fall back to DB-backed claims
    const data = isAdmin ? await api.getAllClaims() : await api.getMyClaims()
    if (data?.claims?.length) {
      setClaims(data.claims)
    }

    setLoading(false)
  }

  const filtered = filter === 'all' ? claims : claims.filter(c => c.status === filter)

  const handleConfirm = async (claimId) => {
    await api.confirmClaim(claimId)
    loadClaims()
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>{isAdmin ? 'All Claims' : 'My Claims'}</h2>
        <p>{isAdmin ? 'Platform-wide claim management & review' : 'Track your income protection claims'}</p>
      </div>

      {/* Summary Stats */}
      <div className="stats-grid" style={{ marginBottom: 20 }}>
        <div className="stat-card green">
          <div className="stat-value">{claims.filter(c => ['paid', 'auto_approved'].includes(c.status)).length}</div>
          <div className="stat-label">Approved / Paid</div>
        </div>
        <div className="stat-card amber">
          <div className="stat-value">{claims.filter(c => c.status === 'soft_verify').length}</div>
          <div className="stat-label">Awaiting Confirmation</div>
        </div>
        <div className="stat-card indigo">
          <div className="stat-value">{claims.filter(c => c.status === 'delayed_review').length}</div>
          <div className="stat-label">Under Review</div>
        </div>
        <div className="stat-card red">
          <div className="stat-value">₹{claims.reduce((s, c) => s + (c.payout || 0), 0).toLocaleString()}</div>
          <div className="stat-label">Total Payouts</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2" style={{ marginBottom: 16 }}>
        {['all', 'paid', 'auto_approved', 'soft_verify', 'delayed_review', 'rejected'].map(f => (
          <button
            key={f}
            className={`btn ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: 12, padding: '6px 14px' }}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'All' : statusConfig[f]?.label || f}
          </button>
        ))}
      </div>

      {/* Claims Table */}
      <div className="card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Claim ID</th>
              <th>Disruption</th>
              <th>Type</th>
              <th>Trust Score</th>
              <th>Payout Tier</th>
              <th>Status</th>
              <th>Payout</th>
              <th>Date</th>
              {!isAdmin && <th>Action</th>}
            </tr>
          </thead>
          <tbody>
            {filtered.map((claim, i) => {
              const cfg = statusConfig[claim.status] || statusConfig.pending
              const StatusIcon = cfg.icon
              const trustVal = claim.trust || claim.trust_score?.composite_score || 0
              return (
                <tr key={i}>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {claim.id?.substring(0, 8) || `CLM-${i}`}
                  </td>
                  <td>{claim.trigger || claim.trigger_id || '—'}</td>
                  <td>
                    <span className="badge info" style={{ textTransform: 'capitalize' }}>
                      {(claim.type || claim.disruption_type || '').replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td>
                    <span style={{
                      fontWeight: 700,
                      color: trustVal > 0.85
                        ? 'var(--accent-success)'
                        : trustVal > 0.5 ? 'var(--accent-warning)' : 'var(--accent-danger)'
                    }}>
                      {(trustVal * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${claim.tier === 'instant' ? 'success' : claim.tier === 'soft_verify' ? 'warning' : 'danger'}`}>
                      {claim.tier || claim.payout_tier || '—'}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${cfg.badge}`}>
                      <StatusIcon size={12} />
                      {cfg.label}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {claim.payout > 0 ? `₹${claim.payout.toLocaleString()}` : '—'}
                  </td>
                  <td style={{ fontSize: 13 }}>{claim.date || claim.created_at?.split('T')[0] || '—'}</td>
                  {!isAdmin && (
                    <td>
                      {claim.status === 'soft_verify' && (
                        <button
                          className="btn btn-success"
                          style={{ fontSize: 12, padding: '4px 12px' }}
                          onClick={() => handleConfirm(claim.id)}
                        >
                          Confirm
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              )
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={isAdmin ? 8 : 9} style={{ textAlign: 'center', padding: 40, color: 'var(--text-muted)' }}>
                  No claims found — run a disruption simulation to generate AI-processed claims
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
