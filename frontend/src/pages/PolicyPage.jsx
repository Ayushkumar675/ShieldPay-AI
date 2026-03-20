import React, { useState, useEffect } from 'react'
import { CreditCard, Shield, IndianRupee, TrendingUp, Clock } from 'lucide-react'
import api from '../services/api'

export default function PolicyPage() {
  const [policy, setPolicy] = useState(null)
  const [premium, setPremium] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    loadPolicy()
    loadPremium()
  }, [])

  const loadPolicy = async () => {
    const data = await api.getActivePolicy()
    if (data?.policy) setPolicy(data.policy)
  }

  const loadPremium = async () => {
    const data = await api.getPremiumQuote()
    if (data?.premium_quote) setPremium(data.premium_quote)
  }

  const handlePurchase = async () => {
    setLoading(true)
    const result = await api.purchasePolicy({ coverage_amount: 2000 })
    if (result?.policy) {
      setPolicy(result.policy)
    }
    setLoading(false)
  }

  return (
    <div className="animate-in">
      <div className="page-header">
        <h2>My Policy</h2>
        <p>Manage your weekly micro-insurance coverage</p>
      </div>

      {/* Active Policy Card */}
      {policy ? (
        <div className="card" style={{
          marginBottom: 24,
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.08))',
          border: '1px solid rgba(99, 102, 241, 0.25)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <span className="badge success" style={{ marginBottom: 12, display: 'inline-block' }}>
                <Shield size={12} /> Active Coverage
              </span>
              <h3 style={{ fontSize: 22, fontWeight: 800, marginBottom: 4 }}>
                Weekly Income Protection
              </h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
                Policy ID: {policy.id?.substring(0, 12)}...
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 36, fontWeight: 800, color: 'var(--accent-primary)' }}>
                ₹{policy.coverage_amount?.toLocaleString()}
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>max coverage / week</div>
            </div>
          </div>

          <div style={{
            marginTop: 24, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
            gap: 16, padding: '16px 0', borderTop: '1px solid var(--border-color)'
          }}>
            <div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Premium</div>
              <div style={{ fontSize: 18, fontWeight: 700 }}>₹{policy.premium_amount?.toFixed(0)}/wk</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Risk Score</div>
              <div style={{ fontSize: 18, fontWeight: 700 }}>{(policy.risk_score * 100).toFixed(0)}%</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Start Date</div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{policy.start_date?.split('T')[0]}</div>
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>Renewal</div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>{policy.auto_renew ? '✅ Auto' : 'Manual'}</div>
            </div>
          </div>
        </div>
      ) : (
        <div className="card" style={{ marginBottom: 24, textAlign: 'center', padding: 40 }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🛡</div>
          <h3 style={{ fontSize: 20, marginBottom: 8 }}>No Active Policy</h3>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 20 }}>
            Get covered! Purchase weekly micro-insurance to protect your delivery income.
          </p>
          <button className="btn btn-primary" onClick={handlePurchase} disabled={loading}>
            {loading ? 'Processing...' : 'Purchase Coverage — ₹2,000/week'}
          </button>
        </div>
      )}

      {/* Premium Breakdown */}
      {premium && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            <h3>📐 Premium Calculation Breakdown</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            <div style={{ padding: '12px 16px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-glass)' }}>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Base Price</div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>₹{premium.breakdown?.base_price}</div>
            </div>
            <div style={{ padding: '12px 16px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-glass)' }}>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Income Volatility</div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>₹{premium.breakdown?.income_volatility}</div>
            </div>
            <div style={{ padding: '12px 16px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-glass)' }}>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Risk Multiplier</div>
              <div style={{ fontSize: 20, fontWeight: 700 }}>{premium.breakdown?.risk_multiplier}x</div>
            </div>
            <div style={{ padding: '12px 16px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-glass)' }}>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Reliability Discount</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--accent-success)' }}>
                -{premium.breakdown?.reliability_discount}
              </div>
            </div>
          </div>
          <div style={{
            marginTop: 16, padding: 12, borderRadius: 'var(--radius-sm)',
            background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.15)',
            fontSize: 13, color: 'var(--text-secondary)',
          }}>
            <strong style={{ color: 'var(--accent-primary)' }}>Formula:</strong>{' '}
            {premium.formula}
          </div>
        </div>
      )}

      {/* Coverage Details */}
      <div className="card">
        <div className="card-header">
          <h3>📋 What's Covered</h3>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 12 }}>
          {[
            { icon: '🌧', title: 'Weather Disruptions', desc: 'Heavy rain, flooding, cyclones blocking routes' },
            { icon: '🏭', title: 'Warehouse Shutdowns', desc: 'Power failure, flooding, equipment breakdown' },
            { icon: '🚧', title: 'Curfew / Lockdowns', desc: 'Regional lockdowns affecting delivery zones' },
            { icon: '🚗', title: 'Traffic Gridlock', desc: 'Severe congestion impacting delivery slots' },
            { icon: '📦', title: 'Parcel Allocation Drop', desc: 'Sudden reduction in dispatch volume' },
          ].map((item, i) => (
            <div key={i} style={{
              padding: '14px 16px', borderRadius: 'var(--radius-sm)',
              background: 'var(--bg-glass)', border: '1px solid var(--border-color)',
              display: 'flex', gap: 12, alignItems: 'start',
            }}>
              <span style={{ fontSize: 24 }}>{item.icon}</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 2 }}>{item.title}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
