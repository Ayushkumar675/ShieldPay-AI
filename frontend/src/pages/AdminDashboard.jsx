import React, { useState, useEffect } from 'react'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { Users, IndianRupee, AlertTriangle, Shield, TrendingUp, Activity, Zap, Sparkles, Radio } from 'lucide-react'
import api from '../services/api'

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#a855f7', '#22d3ee']

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
            {p.name}: ₹{p.value?.toLocaleString()}
          </p>
        ))}
      </div>
    )
  }
  return null
}

const THROTTLE_COLORS = {
  NORMAL: '#10b981',
  ELEVATED: '#f59e0b',
  HIGH_ALERT: '#ef4444',
  LOCKDOWN: '#dc2626',
}

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState(null)
  const [liquidityTrend, setLiquidityTrend] = useState([])
  const [heatmapData, setHeatmapData] = useState([])
  const [warehouseRisk, setWarehouseRisk] = useState([])
  const [claimBreakdown, setClaimBreakdown] = useState([])
  const [financialSummary, setFinancialSummary] = useState(null)
  const [aiInsights, setAiInsights] = useState(null)
  const [systemHealth, setSystemHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAllData()
  }, [])

  const loadAllData = async () => {
    setLoading(true)
    const [analyticsData, trendData, heatmap, warehouses, insights, health] = await Promise.all([
      api.getFraudAnalytics(),
      api.getFinancialTrend(),
      api.getFraudHeatmapAI(),
      api.getWarehouseRisk(),
      api.getAiInsights(),
      api.getSystemHealth(),
    ])

    if (analyticsData) setAnalytics(analyticsData)

    if (trendData?.trend) {
      setLiquidityTrend(trendData.trend)
      setFinancialSummary(trendData.summary)
    }

    if (heatmap?.heatmap) setHeatmapData(heatmap.heatmap)
    if (warehouses?.warehouses) setWarehouseRisk(warehouses.warehouses)
    if (insights) setAiInsights(insights)
    if (health) setSystemHealth(health)

    // Build claim breakdown from analytics
    if (analyticsData?.claims_breakdown) {
      const cb = analyticsData.claims_breakdown
      const total = cb.total || 1
      setClaimBreakdown([
        { name: 'Auto Approved', value: Math.round((cb.auto_approved / total) * 100) || 45, color: '#10b981' },
        { name: 'Soft Verify', value: Math.round((cb.soft_verify / total) * 100) || 25, color: '#f59e0b' },
        { name: 'Delayed Review', value: Math.round((cb.delayed_review / total) * 100) || 15, color: '#ef4444' },
        { name: 'Rejected', value: Math.round((cb.rejected / total) * 100) || 10, color: '#64748b' },
        { name: 'Other', value: Math.max(0, 100 - Math.round((cb.auto_approved / total) * 100) - Math.round((cb.soft_verify / total) * 100) - Math.round((cb.delayed_review / total) * 100) - Math.round((cb.rejected / total) * 100)) || 5, color: '#6366f1' },
      ])
    } else {
      setClaimBreakdown([
        { name: 'Auto Approved', value: 45, color: '#10b981' },
        { name: 'Soft Verify', value: 25, color: '#f59e0b' },
        { name: 'Delayed Review', value: 15, color: '#ef4444' },
        { name: 'Rejected', value: 10, color: '#64748b' },
        { name: 'Other', value: 5, color: '#6366f1' },
      ])
    }

    setLoading(false)
  }

  const totalPremiums = financialSummary?.total_premiums || analytics?.financials?.total_premiums_collected || 0
  const totalPayouts = financialSummary?.total_payouts || analytics?.financials?.total_payouts || 0
  const liquidityRatio = financialSummary?.liquidity_ratio || analytics?.financials?.liquidity_ratio || 0
  const totalAlerts = analytics?.fraud_stats?.total_alerts || heatmapData.reduce((s, c) => s + c.alerts, 0) || 0
  const totalClaims = analytics?.claims_breakdown?.total || liquidityTrend.reduce((s, w) => s + (w.claims_count || 0), 0) || 0

  const throttleState = systemHealth?.throttle_state || 'NORMAL'
  const throttleColor = THROTTLE_COLORS[throttleState] || '#10b981'

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Admin Analytics</h2>
        <p>Platform intelligence, fraud monitoring, and liquidity analytics</p>
      </div>

      {/* AI Weekly Summary + System Health Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: 16, marginBottom: 20 }}>
        {aiInsights?.summary && (
          <div className="ai-insight-banner" id="admin-ai-summary">
            <div className="ai-insight-icon">
              <Sparkles size={18} />
            </div>
            <div className="ai-insight-content">
              <div className="ai-insight-title">AI Platform Summary</div>
              <div className="ai-insight-text">{aiInsights.summary}</div>
            </div>
          </div>
        )}
        
        {/* Throttle State Indicator */}
        <div className="throttle-indicator" style={{
          padding: '16px 24px', borderRadius: 'var(--radius-lg)',
          background: `${throttleColor}10`, border: `1px solid ${throttleColor}30`,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
          minWidth: 140, gap: 4,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className={`pulse-dot ${throttleState === 'NORMAL' ? '' : 'warning'}`} style={{
              width: 10, height: 10, borderRadius: '50%', background: throttleColor,
              boxShadow: `0 0 8px ${throttleColor}`,
            }} />
            <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, color: throttleColor }}>
              {throttleState.replace('_', ' ')}
            </span>
          </div>
          <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Payout Throttle</span>
        </div>
      </div>

      {/* Anomaly Spotlight */}
      {aiInsights?.anomaly && aiInsights.anomaly.severity !== 'normal' && (
        <div className="anomaly-spotlight" style={{
          padding: '14px 20px', borderRadius: 'var(--radius-md)', marginBottom: 20,
          background: aiInsights.anomaly.severity === 'critical' ? 'rgba(239, 68, 68, 0.08)' : 'rgba(245, 158, 11, 0.08)',
          border: `1px solid ${aiInsights.anomaly.severity === 'critical' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)'}`,
          display: 'flex', alignItems: 'center', gap: 12,
        }}>
          <AlertTriangle size={18} color={aiInsights.anomaly.severity === 'critical' ? '#ef4444' : '#f59e0b'} />
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: aiInsights.anomaly.severity === 'critical' ? '#ef4444' : '#f59e0b' }}>
              Anomaly: {aiInsights.anomaly.metric} — {aiInsights.anomaly.value}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{aiInsights.anomaly.message}</div>
          </div>
        </div>
      )}

      {/* Stat Cards */}
      <div className="stats-grid">
        <div className="stat-card indigo">
          <div className="stat-icon indigo"><IndianRupee size={20} /></div>
          <div className="stat-value">₹{(totalPremiums / 1000).toFixed(0)}K</div>
          <div className="stat-label">Premiums Collected</div>
          <div className="stat-change up"><TrendingUp size={12} /> AI-Computed</div>
        </div>

        <div className="stat-card green">
          <div className="stat-icon green"><IndianRupee size={20} /></div>
          <div className="stat-value">₹{(totalPayouts / 1000).toFixed(0)}K</div>
          <div className="stat-label">Total Payouts</div>
          <div className="stat-change down"><Activity size={12} /> Live Data</div>
        </div>

        <div className="stat-card amber">
          <div className="stat-icon amber"><Shield size={20} /></div>
          <div className="stat-value">{liquidityRatio.toFixed(1)}x</div>
          <div className="stat-label">Liquidity Ratio</div>
          <div className="stat-change up"><Zap size={12} /> {liquidityRatio > 1.5 ? 'Healthy' : 'Warning'}</div>
        </div>

        <div className="stat-card red">
          <div className="stat-icon red"><AlertTriangle size={20} /></div>
          <div className="stat-value">{totalAlerts}</div>
          <div className="stat-label">Fraud Alerts</div>
          <div className="stat-change down"><Activity size={12} /> {totalAlerts > 30 ? 'Elevated' : 'Normal'}</div>
        </div>

        <div className="stat-card purple">
          <div className="stat-icon purple"><Users size={20} /></div>
          <div className="stat-value">{totalClaims}</div>
          <div className="stat-label">Total Claims</div>
        </div>

        <div className="stat-card cyan">
          <div className="stat-icon cyan"><Zap size={20} /></div>
          <div className="stat-value">₹{((totalPremiums - totalPayouts) / 1000).toFixed(0)}K</div>
          <div className="stat-label">Reserve Balance</div>
          <div className="stat-change up"><TrendingUp size={12} /> {totalPremiums > totalPayouts ? 'Sufficient' : 'Low'}</div>
        </div>
      </div>

      <div className="charts-grid">
        {/* Premium vs Payout Trend */}
        <div className="card">
          <div className="card-header">
            <h3>💰 Premium vs Payout Flow</h3>
            <span className="badge info">{liquidityTrend.length}-Week Trend</span>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={liquidityTrend}>
              <defs>
                <linearGradient id="premGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="payGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="week" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="premiums" stroke="#10b981" fill="url(#premGrad)" name="Premiums" />
              <Area type="monotone" dataKey="payouts" stroke="#ef4444" fill="url(#payGrad)" name="Payouts" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Claims Breakdown Pie */}
        <div className="card">
          <div className="card-header">
            <h3>📊 Claims Distribution</h3>
            <span className="badge success">Live</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
            <ResponsiveContainer width="60%" height={280}>
              <PieChart>
                <Pie
                  data={claimBreakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {claimBreakdown.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ flex: 1 }}>
              {claimBreakdown.map((item, i) => (
                <div key={i} className="flex items-center gap-2" style={{ marginBottom: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: item.color }} />
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)', flex: 1 }}>{item.name}</span>
                  <span style={{ fontSize: 13, fontWeight: 700 }}>{item.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Fraud Heatmap */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <h3>🗺 Fraud Alert Heatmap — City Distribution</h3>
          <span className="badge danger">AI-Powered</span>
        </div>
        <div className="heatmap-grid">
          {heatmapData.map((city, i) => (
            <div
              key={i}
              className="heatmap-cell"
              style={{
                background: `${city.color}15`,
                border: `1px solid ${city.color}30`,
              }}
            >
              <div className="city-name">{city.city}</div>
              <div className="alert-count" style={{ color: city.color }}>{city.alerts}</div>
              <div className="severity">Severity: {(city.severity * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      </div>

      {/* High-Risk Warehouses */}
      <div className="card">
        <div className="card-header">
          <h3>🏭 High-Risk Warehouse Zones</h3>
          <span className="badge warning">AI Predictions</span>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Warehouse</th>
              <th>City</th>
              <th>Risk Score</th>
              <th>Risk Level</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {warehouseRisk.map((wh, i) => (
              <tr key={i}>
                <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{wh.id}</td>
                <td>{wh.city}</td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div className="risk-meter" style={{ width: 80, margin: 0 }}>
                      <div
                        className={`risk-meter-fill ${wh.risk > 0.7 ? 'critical' : wh.risk > 0.4 ? 'moderate' : 'low'}`}
                        style={{ width: `${wh.risk * 100}%` }}
                      />
                    </div>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{(wh.risk * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td>
                  <span className={`badge ${wh.risk > 0.7 ? 'danger' : wh.risk > 0.4 ? 'warning' : 'success'}`}>
                    {wh.risk > 0.7 ? 'Critical' : wh.risk > 0.4 ? 'Moderate' : 'Low'}
                  </span>
                </td>
                <td>
                  <span className={`badge ${wh.risk > 0.7 ? 'danger' : 'info'}`}>
                    {wh.risk > 0.7 ? '⚠ Alert' : '✓ Normal'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
