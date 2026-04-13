import React, { useState, useEffect } from 'react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { Shield, TrendingUp, Package, IndianRupee, AlertTriangle, Zap, Activity, Sparkles, Clock } from 'lucide-react'
import api from '../services/api'

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: 'var(--bg-secondary)', padding: '10px 14px',
        borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)',
        boxShadow: 'var(--shadow-md)', fontSize: '13px',
      }}>
        <p style={{ fontWeight: 600, marginBottom: 4 }}>{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color }}>
            {p.name}: {typeof p.value === 'number' && p.value < 10 ? p.value.toFixed(2) : p.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}

// Radial Trust Gauge component
const TrustGauge = ({ score }) => {
  const radius = 60
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score * circumference)
  const color = score > 0.85 ? '#10b981' : score > 0.5 ? '#f59e0b' : '#ef4444'
  
  return (
    <div className="trust-gauge">
      <svg width="160" height="160" viewBox="0 0 160 160">
        <circle className="gauge-bg" cx="80" cy="80" r={radius} />
        <circle
          className="gauge-fill"
          cx="80" cy="80" r={radius}
          stroke={color}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1.5s ease' }}
        />
      </svg>
      <div className="gauge-value">
        <div className="value" style={{ color }}>{(score * 100).toFixed(0)}%</div>
        <div className="label">TRUST</div>
      </div>
    </div>
  )
}

export default function WorkerDashboard() {
  const [stats, setStats] = useState({
    weekly_insured_income: 0,
    total_claims: 0,
    approved_claims: 0,
    reliability_score: 0,
  })
  const [riskData, setRiskData] = useState([])
  const [incomeData, setIncomeData] = useState([])
  const [trustScore, setTrustScore] = useState(0)
  const [trustBreakdown, setTrustBreakdown] = useState(null)
  const [currentRisk, setCurrentRisk] = useState(null)
  const [narrative, setNarrative] = useState('')
  const [trustNarrative, setTrustNarrative] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    setLoading(true)
    try {
      const [dashData, forecastData, narrativeData] = await Promise.all([
        api.getWorkerDashboard(),
        api.getWorkerForecast(),
        api.getWorkerNarrative(),
      ])

      if (dashData?.worker_profile) {
        const income = dashData.worker_profile.avg_income || 1500
        setStats({
          weekly_insured_income: income * 6,
          total_claims: dashData.claims_history?.length || 0,
          approved_claims: dashData.claims_history?.filter(c => ['paid', 'auto_approved'].includes(c.status)).length || 0,
          reliability_score: dashData.worker_profile.reliability || 0.85
        })
        setTrustScore(dashData.trust_score || 0.85)
        setTrustNarrative(dashData.trust_narrative || '')
      }

      if (forecastData) {
        setRiskData(forecastData.risk_forecast || [])
        setIncomeData(forecastData.income_forecast || [])
        setCurrentRisk(forecastData.current_risk || null)
        setNarrative(forecastData.narrative || '')
      }

      if (narrativeData?.trust_narrative) {
        setTrustNarrative(narrativeData.trust_narrative)
      }
    } catch (err) {
      console.error('API error:', err)
    }
    setLoading(false)
  }

  const riskLevel = currentRisk?.risk_level || (riskData[3]?.risk > 0.7 ? 'high' : riskData[3]?.risk > 0.4 ? 'moderate' : 'low')
  const riskScore = currentRisk?.risk_score || riskData[3]?.risk || 0.5

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Worker Dashboard</h2>
        <p>Your income protection overview & real-time risk monitoring</p>
      </div>

      {/* AI Insight Banner */}
      {narrative && (
        <div className="ai-insight-banner" id="ai-insight-banner">
          <div className="ai-insight-icon">
            <Sparkles size={18} />
          </div>
          <div className="ai-insight-content">
            <div className="ai-insight-title">AI Insight</div>
            <div className="ai-insight-text">{narrative}</div>
          </div>
        </div>
      )}

      {/* Stat Cards */}
      <div className="stats-grid">
        <div className="stat-card indigo">
          <div className="stat-icon indigo"><IndianRupee size={20} /></div>
          <div className="stat-value">₹{stats.weekly_insured_income?.toLocaleString() || '0'}</div>
          <div className="stat-label">Weekly Insured Income</div>
          <div className="stat-change up">
            <TrendingUp size={12} /> Protected this week
          </div>
        </div>

        <div className="stat-card green">
          <div className="stat-icon green"><Shield size={20} /></div>
          <div className="stat-value">{(trustScore * 100).toFixed(0)}%</div>
          <div className="stat-label">Trust Score</div>
          <div className="stat-change up">
            <Activity size={12} /> {trustScore > 0.85 ? 'Excellent' : trustScore > 0.5 ? 'Good' : 'Needs improvement'}
          </div>
        </div>

        <div className="stat-card amber">
          <div className="stat-icon amber"><Package size={20} /></div>
          <div className="stat-value">{stats.total_claims || 0}</div>
          <div className="stat-label">Total Claims</div>
          <div className="stat-change up">
            <Zap size={12} /> {stats.approved_claims || 0} approved
          </div>
        </div>

        <div className="stat-card red">
          <div className="stat-icon red"><AlertTriangle size={20} /></div>
          <div className="stat-value" style={{ textTransform: 'capitalize' }}>{riskLevel}</div>
          <div className="stat-label">Current Risk Level</div>
          <div className="risk-meter">
            <div
              className={`risk-meter-fill ${riskLevel === 'critical' || riskLevel === 'high' ? 'critical' : riskLevel === 'moderate' ? 'moderate' : 'low'}`}
              style={{ width: `${riskScore * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Risk & Parcel Trend */}
        <div className="card">
          <div className="card-header">
            <h3>📊 Logistics Risk vs Parcels (7 Days)</h3>
            <span className="badge info">AI-Predicted</span>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={riskData}>
              <defs>
                <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="parcelGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="day" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="risk" stroke="#ef4444" fill="url(#riskGrad)" name="Risk Score" />
              <Area type="monotone" dataKey="parcels" stroke="#6366f1" fill="url(#parcelGrad)" name="Parcels" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Income Forecast */}
        <div className="card">
          <div className="card-header">
            <h3>💰 Income Forecast vs Normal</h3>
            <span className="badge warning">AI Projected</span>
          </div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={incomeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="week" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="normal" fill="rgba(99, 102, 241, 0.3)" name="Normal Income" radius={[4, 4, 0, 0]} />
              <Bar dataKey="predicted" fill="#6366f1" name="Predicted Income" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trust Score Section with Gauge */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <h3>🛡 Trust Score Breakdown</h3>
          <span className={`badge ${trustScore > 0.85 ? 'success' : trustScore > 0.5 ? 'warning' : 'danger'}`}>
            {trustScore > 0.85 ? 'Instant Payout' : trustScore > 0.5 ? 'Quick Verify' : 'Under Review'}
          </span>
        </div>
        
        <div style={{ display: 'grid', gridTemplateColumns: '180px 1fr', gap: 32, alignItems: 'center' }}>
          {/* Radial Gauge */}
          <TrustGauge score={trustScore} />
          
          {/* Breakdown Bars */}
          <div>
            {trustNarrative && (
              <div className="ai-narrative-inline" style={{ marginBottom: 16 }}>
                <Sparkles size={14} style={{ flexShrink: 0 }} />
                <span>{trustNarrative}</span>
              </div>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
              {[
                { label: 'Movement Verification', key: 'mobility_stability', color: '--accent-success', fallback: 0.85 },
                { label: 'Delivery Activity', key: 'behavioral_trust', color: '--accent-primary', fallback: 0.78 },
                { label: 'Environmental Match', key: 'disruption_match', color: '--accent-secondary', fallback: 0.60 },
                { label: 'Historical Trust', key: null, color: '--accent-purple', fallback: trustScore },
                { label: 'Fraud Safety', key: 'fraud_safety', color: '--accent-warning', fallback: 0.90 },
              ].map((item, i) => {
                const score = item.key && trustBreakdown?.[item.key]?.value != null
                  ? trustBreakdown[item.key].value
                  : item.fallback
                return (
                  <div key={i} style={{ padding: '8px 0' }}>
                    <div className="flex justify-between items-center" style={{ marginBottom: 4 }}>
                      <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{item.label}</span>
                      <span style={{ fontSize: 13, fontWeight: 700 }}>{(score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="risk-meter">
                      <div
                        style={{
                          height: '100%', borderRadius: 4,
                          width: `${score * 100}%`,
                          background: `var(${item.color})`,
                          transition: 'width 1.5s ease',
                        }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Payout Protection Tiers */}
      <div className="card">
        <div className="card-header">
          <h3>⚡ Payout Protection Tiers</h3>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          <div className={`payout-tier-card ${trustScore >= 0.85 ? 'active' : ''}`} style={{
            padding: 20, borderRadius: 'var(--radius-md)',
            background: trustScore >= 0.85 ? 'rgba(16, 185, 129, 0.15)' : 'rgba(16, 185, 129, 0.06)',
            border: `1px solid ${trustScore >= 0.85 ? 'rgba(16, 185, 129, 0.4)' : 'rgba(16, 185, 129, 0.15)'}`,
            textAlign: 'center', transition: 'all 0.3s ease',
          }}>
            <div style={{ fontSize: 28, marginBottom: 4 }}>⚡</div>
            <div style={{ fontWeight: 700, color: 'var(--accent-success)', marginBottom: 4 }}>Instant Payout</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Trust Score ≥ 85%</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Funds in seconds</div>
            {trustScore >= 0.85 && <div className="badge success" style={{ marginTop: 8 }}>✓ Your Tier</div>}
          </div>
          <div className={`payout-tier-card ${trustScore >= 0.5 && trustScore < 0.85 ? 'active' : ''}`} style={{
            padding: 20, borderRadius: 'var(--radius-md)',
            background: trustScore >= 0.5 && trustScore < 0.85 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(245, 158, 11, 0.06)',
            border: `1px solid ${trustScore >= 0.5 && trustScore < 0.85 ? 'rgba(245, 158, 11, 0.4)' : 'rgba(245, 158, 11, 0.15)'}`,
            textAlign: 'center', transition: 'all 0.3s ease',
          }}>
            <div style={{ fontSize: 28, marginBottom: 4 }}>✋</div>
            <div style={{ fontWeight: 700, color: 'var(--accent-warning)', marginBottom: 4 }}>Quick Verify</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Trust Score 50-85%</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>In-app confirmation</div>
            {trustScore >= 0.5 && trustScore < 0.85 && <div className="badge warning" style={{ marginTop: 8 }}>✓ Your Tier</div>}
          </div>
          <div className={`payout-tier-card ${trustScore < 0.5 ? 'active' : ''}`} style={{
            padding: 20, borderRadius: 'var(--radius-md)',
            background: trustScore < 0.5 ? 'rgba(239, 68, 68, 0.15)' : 'rgba(239, 68, 68, 0.06)',
            border: `1px solid ${trustScore < 0.5 ? 'rgba(239, 68, 68, 0.4)' : 'rgba(239, 68, 68, 0.15)'}`,
            textAlign: 'center', transition: 'all 0.3s ease',
          }}>
            <div style={{ fontSize: 28, marginBottom: 4 }}>🔍</div>
            <div style={{ fontWeight: 700, color: 'var(--accent-danger)', marginBottom: 4 }}>Under Review</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Trust Score &lt; 50%</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>24-48 hour review</div>
            {trustScore < 0.5 && <div className="badge danger" style={{ marginTop: 8 }}>✓ Your Tier</div>}
          </div>
        </div>
      </div>
    </div>
  )
}
