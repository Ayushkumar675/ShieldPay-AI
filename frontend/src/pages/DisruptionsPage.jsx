import React, { useState, useEffect } from 'react'
import { CloudLightning, CloudRain, Factory, Car, Package, AlertTriangle, RefreshCw } from 'lucide-react'
import api from '../services/api'

const typeConfig = {
  weather: { icon: CloudRain, color: '#22d3ee', label: 'Weather' },
  warehouse_shutdown: { icon: Factory, color: '#f59e0b', label: 'Warehouse' },
  traffic_gridlock: { icon: Car, color: '#ef4444', label: 'Traffic' },
  curfew_lockdown: { icon: AlertTriangle, color: '#a855f7', label: 'Curfew' },
  parcel_allocation_drop: { icon: Package, color: '#6366f1', label: 'Parcel Drop' },
}

export default function DisruptionsPage() {
  const [disruptions, setDisruptions] = useState([])
  const [filter, setFilter] = useState('all')
  const [simulating, setSimulating] = useState(null)
  const [lastSimResult, setLastSimResult] = useState(null)

  useEffect(() => {
    loadDisruptions()
  }, [])

  const loadDisruptions = async () => {
    // Try AI endpoint first, then fallback to existing integration endpoint
    const aiData = await api.getActiveDisruptionsAI()
    if (aiData?.disruptions?.length) {
      setDisruptions(aiData.disruptions)
    } else {
      const data = await api.getActiveDisruptions()
      if (data?.active_disruptions?.length) {
        setDisruptions(data.active_disruptions)
      }
    }
  }

  const handleSimulate = async (type, city = 'Mumbai') => {
    setSimulating(type)
    const result = await api.simulateDisruption(type, city)
    if (result) {
      setLastSimResult(result)
      // Refresh disruptions after simulation
      await loadDisruptions()
    }
    setSimulating(null)
  }

  const filtered = filter === 'all' ? disruptions
    : filter === 'active' ? disruptions.filter(d => d.is_active)
    : disruptions.filter(d => d.type === filter)

  const timeAgo = (dateStr) => {
    if (!dateStr) return 'Unknown'
    const diff = Date.now() - new Date(dateStr).getTime()
    const hours = Math.floor(diff / 3600000)
    if (hours < 1) return 'Just now'
    if (hours < 24) return `${hours}h ago`
    return `${Math.floor(hours / 24)}d ago`
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>Disruption Monitor</h2>
        <p>Real-time logistics disruption tracking & parametric triggers</p>
      </div>

      {/* Active counts */}
      <div className="stats-grid" style={{ marginBottom: 20 }}>
        <div className="stat-card cyan">
          <div className="stat-icon cyan"><CloudLightning size={20} /></div>
          <div className="stat-value">{disruptions.filter(d => d.is_active).length}</div>
          <div className="stat-label">Active Disruptions</div>
        </div>
        <div className="stat-card red">
          <div className="stat-icon red"><AlertTriangle size={20} /></div>
          <div className="stat-value">{disruptions.filter(d => d.severity >= 0.8).length}</div>
          <div className="stat-label">Critical Severity</div>
        </div>
        <div className="stat-card amber">
          <div className="stat-icon amber"><Factory size={20} /></div>
          <div className="stat-value">{disruptions.filter(d => d.type === 'warehouse_shutdown').length}</div>
          <div className="stat-label">Warehouse Shutdowns</div>
        </div>
        <div className="stat-card indigo">
          <div className="stat-icon indigo"><CloudRain size={20} /></div>
          <div className="stat-value">{disruptions.filter(d => d.type === 'weather').length}</div>
          <div className="stat-label">Weather Events</div>
        </div>
      </div>

      {/* Simulation Controls */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="card-header">
          <h3>⚡ AI Simulation Controls</h3>
          <span className="badge info">Trigger Events</span>
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button
            className="btn btn-primary"
            onClick={() => handleSimulate('heavy_rain', 'Mumbai')}
            disabled={simulating}
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px' }}
          >
            {simulating === 'heavy_rain' ? <RefreshCw size={14} className="spinning" /> : <CloudRain size={14} />}
            🌧 Simulate Heavy Rain Event
          </button>
          <button
            className="btn btn-warning"
            onClick={() => handleSimulate('warehouse_shutdown', 'Chennai')}
            disabled={simulating}
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-warning)', border: '1px solid rgba(245, 158, 11, 0.3)' }}
          >
            {simulating === 'warehouse_shutdown' ? <RefreshCw size={14} className="spinning" /> : <Factory size={14} />}
            🏭 Simulate Warehouse Shutdown
          </button>
          <button
            className="btn btn-danger"
            onClick={() => handleSimulate('fraud_cluster', 'Delhi')}
            disabled={simulating}
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-danger)', border: '1px solid rgba(239, 68, 68, 0.3)' }}
          >
            {simulating === 'fraud_cluster' ? <RefreshCw size={14} className="spinning" /> : <AlertTriangle size={14} />}
            🕵 Simulate Fraud Attack Cluster
          </button>
        </div>
      </div>

      {/* Simulation Results */}
      {lastSimResult && (
        <div className="card" style={{ marginBottom: 20, borderLeft: '3px solid var(--accent-primary)' }}>
          <div className="card-header">
            <h3>📊 Last Simulation Results</h3>
            <span className="badge success">Completed</span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12 }}>
            <div style={{ padding: '8px 12px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-glass)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Total Processed</div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>{lastSimResult.stats?.total_processed || 0}</div>
            </div>
            <div style={{ padding: '8px 12px', borderRadius: 'var(--radius-sm)', background: 'rgba(16, 185, 129, 0.08)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Auto Approved</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-success)' }}>{lastSimResult.stats?.auto_approved || 0}</div>
            </div>
            <div style={{ padding: '8px 12px', borderRadius: 'var(--radius-sm)', background: 'rgba(245, 158, 11, 0.08)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Manual Review</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-warning)' }}>{lastSimResult.stats?.manual_review || 0}</div>
            </div>
            <div style={{ padding: '8px 12px', borderRadius: 'var(--radius-sm)', background: 'rgba(239, 68, 68, 0.08)' }}>
              <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>Flagged / Rejected</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-danger)' }}>{(lastSimResult.stats?.flagged || 0) + (lastSimResult.stats?.auto_rejected || 0)}</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2" style={{ marginBottom: 16 }}>
        {['all', 'active', 'weather', 'warehouse_shutdown', 'traffic_gridlock', 'parcel_allocation_drop'].map(f => (
          <button
            key={f}
            className={`btn ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
            style={{ fontSize: 12, padding: '6px 14px' }}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'All' : f === 'active' ? 'Active' :
             typeConfig[f]?.label || f.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* Disruption Cards */}
      <div style={{ display: 'grid', gap: 12 }}>
        {filtered.map((d, i) => {
          const cfg = typeConfig[d.type] || typeConfig.weather
          const Icon = cfg.icon
          return (
            <div key={i} className="card" style={{
              borderLeft: `3px solid ${cfg.color}`,
              opacity: d.is_active ? 1 : 0.6,
            }}>
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <div style={{
                    width: 44, height: 44, borderRadius: 'var(--radius-md)',
                    background: `${cfg.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Icon size={22} color={cfg.color} />
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 2 }}>{d.description}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                      {d.zone} • {d.city || 'Unknown'} • {timeAgo(d.detected_at)}
                    </div>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className={`badge ${d.is_active ? (d.severity > 0.8 ? 'danger' : 'warning') : 'info'}`}>
                    {d.is_active ? '🔴 Active' : '✅ Resolved'}
                  </span>
                  <div style={{ marginTop: 8 }}>
                    <div className="flex items-center gap-2">
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Severity:</span>
                      <div className="risk-meter" style={{ width: 60, margin: 0 }}>
                        <div
                          className={`risk-meter-fill ${d.severity > 0.8 ? 'critical' : d.severity > 0.5 ? 'moderate' : 'low'}`}
                          style={{ width: `${d.severity * 100}%` }}
                        />
                      </div>
                      <span style={{ fontSize: 13, fontWeight: 700 }}>{(d.severity * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Extra data */}
              {(d.weather_data || d.traffic_data) && (
                <div style={{
                  marginTop: 12, padding: '8px 12px', borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-glass)', fontSize: 12, color: 'var(--text-secondary)',
                  display: 'flex', gap: 16,
                }}>
                  {d.weather_data && (
                    <>
                      <span>🌧 {d.weather_data.condition?.replace(/_/g, ' ')}</span>
                      <span>💧 {d.weather_data.rainfall_mm}mm rain</span>
                    </>
                  )}
                  {d.traffic_data && (
                    <span>🚗 Congestion: {(d.traffic_data.congestion_index * 100).toFixed(0)}%</span>
                  )}
                </div>
              )}
            </div>
          )
        })}
        {filtered.length === 0 && (
          <div className="card" style={{ textAlign: 'center', padding: 40 }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>🌤</div>
            <p style={{ color: 'var(--text-muted)' }}>No disruptions matching filter — use simulation buttons above to generate events</p>
          </div>
        )}
      </div>
    </div>
  )
}
