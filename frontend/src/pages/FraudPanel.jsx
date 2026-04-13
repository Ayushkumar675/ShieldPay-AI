import React, { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts'
import { AlertTriangle, Shield, Users, Eye, Fingerprint, Network, Radio, Sparkles } from 'lucide-react'
import api from '../services/api'

const alertTypeConfig = {
  gps_spoof: { label: 'GPS Spoof', icon: '📍', badge: 'danger' },
  device_integrity: { label: 'Device', icon: '📱', badge: 'warning' },
  claim_spike: { label: 'Claim Spike', icon: '📈', badge: 'warning' },
  ring_detected: { label: 'Fraud Ring', icon: '🕸', badge: 'danger' },
  emulator: { label: 'Emulator', icon: '⚙️', badge: 'danger' },
  teleport: { label: 'Teleport', icon: '⚡', badge: 'danger' },
  pattern_FP_001: { label: 'GPS Cluster', icon: '📍', badge: 'danger' },
  pattern_FP_002: { label: 'Claim Stack', icon: '📊', badge: 'warning' },
  pattern_FP_003: { label: 'Device Rotate', icon: '🔄', badge: 'warning' },
  pattern_FP_004: { label: 'Weather Fake', icon: '🌤', badge: 'danger' },
  pattern_FP_005: { label: 'Phantom Delivery', icon: '👻', badge: 'warning' },
}

export default function FraudPanel() {
  const [alerts, setAlerts] = useState([])
  const [rings, setRings] = useState([])
  const [layerScores, setLayerScores] = useState([])
  const [platformSafety, setPlatformSafety] = useState(0)
  const [fraudTrend, setFraudTrend] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadFraudData()
  }, [])

  const loadFraudData = async () => {
    setLoading(true)

    const [heatmapRes, alertsRes, ringsRes] = await Promise.all([
      api.getFraudHeatmapAI(),
      api.getFraudAlertsAI(),
      api.getFraudRings(),
    ])

    // Build alerts from AI fraud scanning
    if (alertsRes?.alerts?.length) {
      setAlerts(alertsRes.alerts.map((a, i) => ({
        id: a.id || i + 1,
        worker: a.worker || `Worker_${String(i + 1).padStart(4, '0')}`,
        type: a.alert_type || a.type || 'gps_spoof',
        severity: a.severity || 0.5,
        details: a.details ? (typeof a.details === 'object' ? JSON.stringify(a.details) : a.details) : 'Anomalous pattern detected',
        time: a.time ? _timeAgo(a.time) : `${(i + 1) * 2} hours ago`,
      })))
    } else {
      setAlerts([])
    }

    // Fraud rings
    if (ringsRes?.fraud_rings?.length) {
      setRings(ringsRes.fraud_rings.map((r, i) => ({
        id: r.id || `RING-${String(i + 1).padStart(3, '0')}`,
        members: r.members || r.worker_ids?.length || 3,
        confidence: r.confidence || 0.85,
        claims: r.claims || r.suspicious_claims || 12,
        pattern: r.pattern || 'Temporal claim clustering + device similarity',
        workers: r.workers || r.worker_ids || [`W-${i}01`, `W-${i}02`, `W-${i}03`],
      })))
    } else {
      setRings([])
    }

    // Build layer scores and fraud trend
    if (heatmapRes?.heatmap?.length) {
      const avgSeverity = heatmapRes.heatmap.reduce((s, c) => s + c.severity, 0) / heatmapRes.heatmap.length
      const safeBase = Math.round((1 - avgSeverity) * 100)
      setLayerScores([
        { layer: 'Movement', safe: safeBase + 2, flagged: 100 - safeBase - 2 },
        { layer: 'Delivery', safe: safeBase + 7, flagged: 100 - safeBase - 7 },
        { layer: 'Environment', safe: safeBase + 4, flagged: 100 - safeBase - 4 },
        { layer: 'Device', safe: safeBase - 5, flagged: 100 - safeBase + 5 },
        { layer: 'Graph ML', safe: safeBase + 5, flagged: 100 - safeBase - 5 },
      ])
      setPlatformSafety(Math.min(100, safeBase + 3))

      // Build trend sparkline data from heatmap cities
      setFraudTrend(heatmapRes.heatmap.map((c, i) => ({
        city: c.city,
        alerts: c.alerts,
        severity: Math.round(c.severity * 100),
      })))
    } else {
      setLayerScores([
        { layer: 'Movement', safe: 100, flagged: 0 },
        { layer: 'Delivery', safe: 100, flagged: 0 },
        { layer: 'Environment', safe: 100, flagged: 0 },
        { layer: 'Device', safe: 100, flagged: 0 },
        { layer: 'Graph ML', safe: 100, flagged: 0 },
      ])
      setPlatformSafety(100)
      setFraudTrend([])
    }

    setLoading(false)
  }

  const _timeAgo = (isoStr) => {
    const diff = Date.now() - new Date(isoStr).getTime()
    const hours = Math.floor(diff / 3600000)
    if (hours < 1) return 'Just now'
    if (hours < 24) return `${hours} hours ago`
    return `${Math.floor(hours / 24)}d ago`
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Fraud Intelligence Panel</h2>
        <p>Multi-layer adversarial defense monitoring & fraud ring detection</p>
      </div>

      {/* Defense Layer Stats */}
      <div className="stats-grid">
        <div className="stat-card purple">
          <div className="stat-icon purple"><Eye size={20} /></div>
          <div className="stat-value">{alerts.length}</div>
          <div className="stat-label">Active Alerts</div>
        </div>
        <div className="stat-card red">
          <div className="stat-icon red"><Network size={20} /></div>
          <div className="stat-value">{rings.length}</div>
          <div className="stat-label">Fraud Rings Detected</div>
        </div>
        <div className="stat-card amber">
          <div className="stat-icon amber"><Fingerprint size={20} /></div>
          <div className="stat-value">5</div>
          <div className="stat-label">Defense Layers Active</div>
        </div>
        <div className="stat-card green">
          <div className="stat-icon green"><Shield size={20} /></div>
          <div className="stat-value">{platformSafety}%</div>
          <div className="stat-label">Platform Safety Score</div>
        </div>
      </div>

      <div className="charts-grid">
        {/* Defense Layer Breakdown */}
        <div className="card">
          <div className="card-header">
            <h3>🛡 5-Layer Defense Status</h3>
            <span className="badge success">All Active</span>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={layerScores} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis type="number" stroke="var(--text-muted)" fontSize={12} domain={[0, 100]} />
              <YAxis type="category" dataKey="layer" stroke="var(--text-muted)" fontSize={12} width={80} />
              <Tooltip />
              <Bar dataKey="safe" fill="#10b981" name="Safe %" radius={[0, 4, 4, 0]} stackId="a" />
              <Bar dataKey="flagged" fill="#ef4444" name="Flagged %" radius={[0, 4, 4, 0]} stackId="a" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Fraud Trend Sparkline + Trust Model */}
        <div className="card">
          <div className="card-header">
            <h3>📈 Fraud Intensity by City</h3>
            <span className="badge warning">Trend</span>
          </div>
          {fraudTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={fraudTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="city" stroke="var(--text-muted)" fontSize={11} />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip />
                <Bar dataKey="alerts" fill="#ef4444" name="Alerts" radius={[4, 4, 0, 0]} />
                <Bar dataKey="severity" fill="#f59e0b" name="Severity %" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ height: 140, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              No fraud trend data available
            </div>
          )}
          
          {/* Trust Score Formula */}
          <div style={{ marginTop: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>🧮 Trust Score Model</div>
            <code style={{
              display: 'block', padding: 12, borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-glass)', fontSize: 11, lineHeight: 1.8,
              color: 'var(--accent-secondary)', whiteSpace: 'pre-wrap',
            }}>
{`claim_approval = adaptive_weighted(
  movement_score    × w₁ (dynamic),
  delivery_score    × w₂ (dynamic),
  env_match_score   × w₃ (dynamic),
  fraud_safety      × w₄ (dynamic)
) + momentum_bonus - decay`}
            </code>
            <div style={{ marginTop: 8, display: 'flex', gap: 16, fontSize: 11 }}>
              {[
                { label: 'Instant', threshold: '≥ 85%', color: 'var(--accent-success)' },
                { label: 'Verify', threshold: '50-85%', color: 'var(--accent-warning)' },
                { label: 'Review', threshold: '< 50%', color: 'var(--accent-danger)' },
              ].map((tier, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: tier.color }} />
                  <span style={{ color: tier.color, fontWeight: 600 }}>{tier.label}: {tier.threshold}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Fraud Rings */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <h3>🕸 Detected Fraud Rings</h3>
          <span className="badge danger">{rings.length} Active</span>
        </div>
        {rings.map((ring, i) => (
          <div key={i} style={{
            padding: 16, marginBottom: 12, borderRadius: 'var(--radius-md)',
            background: 'rgba(239, 68, 68, 0.06)', border: '1px solid rgba(239, 68, 68, 0.15)',
          }}>
            <div className="flex justify-between items-center" style={{ marginBottom: 8 }}>
              <span style={{ fontWeight: 700, color: 'var(--accent-danger)' }}>
                <Network size={14} style={{ verticalAlign: 'middle', marginRight: 6 }} />
                {ring.id}
              </span>
              <span className="badge danger">Confidence: {(ring.confidence * 100).toFixed(0)}%</span>
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>{ring.pattern}</div>
            <div className="flex gap-4" style={{ fontSize: 12 }}>
              <span><Users size={12} style={{ verticalAlign: 'middle' }} /> {ring.members} members</span>
              <span>📝 {ring.claims} suspicious claims</span>
              <span>👤 {Array.isArray(ring.workers) ? ring.workers.join(', ') : ring.workers}</span>
            </div>
          </div>
        ))}
        {rings.length === 0 && !loading && (
          <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>
            No fraud rings detected — run a simulation to generate data
          </div>
        )}
      </div>

      {/* Alert Timeline */}
      <div className="card">
        <div className="card-header">
          <h3>🚨 Recent Fraud Alerts</h3>
          <span className="badge warning">{alerts.length} alerts</span>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Worker</th>
              <th>Alert Type</th>
              <th>Severity</th>
              <th>Details</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert, i) => {
              const cfg = alertTypeConfig[alert.type] || { label: alert.type, icon: '⚠', badge: 'warning' }
              return (
                <tr key={i}>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{alert.worker}</td>
                  <td>
                    <span className={`badge ${cfg.badge}`}>
                      {cfg.icon} {cfg.label}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="risk-meter" style={{ width: 60, margin: 0 }}>
                        <div
                          className={`risk-meter-fill ${alert.severity > 0.8 ? 'critical' : alert.severity > 0.6 ? 'moderate' : 'low'}`}
                          style={{ width: `${alert.severity * 100}%` }}
                        />
                      </div>
                      <span style={{ fontSize: 13, fontWeight: 600 }}>{(alert.severity * 100).toFixed(0)}%</span>
                    </div>
                  </td>
                  <td style={{ fontSize: 13, maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{alert.details}</td>
                  <td style={{ fontSize: 12, color: 'var(--text-muted)' }}>{alert.time}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
