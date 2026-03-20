import React, { useState } from 'react';
import { Info, X, PlayCircle, CheckCircle, Shield, AlertTriangle } from 'lucide-react';

const DemoGuide = () => {
  const [isOpen, setIsOpen] = useState(true);
  const [step, setStep] = useState(1);

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed', bottom: 20, right: 20,
          background: '#6366f1', color: 'white',
          padding: '10px 16px', borderRadius: '30px',
          boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)',
          border: 'none', cursor: 'pointer', zIndex: 1000,
          display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600
        }}
      >
        <Info size={18} /> Demo Guide
      </button>
    );
  }

  const steps = [
    { title: "Purchase Policy", desc: "Start by ensuring workers have active income protection coverage.", icon: Shield },
    { title: "Simulate Disruption", desc: "Trigger 'Heavy Rain' in Mumbai to activate the risk engine.", icon: AlertTriangle },
    { title: "Auto-Claim Generation", desc: "The AI detects affected workers and calculates income loss instantly.", icon: PlayCircle },
    { title: "Confirm Payout", desc: "For higher risk cases, manually confirm the claim to release funds.", icon: CheckCircle },
    { title: "Review Analytics", desc: "Observe the liquidity reserve decrease and fraud alerts in real-time.", icon: Info },
  ];

  return (
    <div style={{
      position: 'fixed', bottom: 20, right: 20,
      width: 320, background: 'white',
      borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
      border: '1px solid #e2e8f0', zIndex: 1000,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    }}>
      <div style={{
        padding: '16px', borderBottom: '1px solid #f1f5f9',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        background: '#f8fafc', borderTopLeftRadius: '12px', borderTopRightRadius: '12px'
      }}>
        <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#334155' }}>
          🛡️ ShieldPay Demo Flow
        </h4>
        <button 
          onClick={() => setIsOpen(false)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
        >
          <X size={16} />
        </button>
      </div>

      <div style={{ padding: '16px' }}>
        {steps.map((s, i) => (
          <div key={i} style={{ 
            display: 'flex', gap: 12, marginBottom: 16,
            opacity: step === i + 1 ? 1 : 0.4,
            filter: step === i + 1 ? 'none' : 'grayscale(100%)',
            transition: 'all 0.3s' 
          }}>
            <div style={{
              minWidth: 24, height: 24, borderRadius: '50%',
              background: step > i + 1 ? '#10b981' : (step === i + 1 ? '#6366f1' : '#cbd5e1'),
              color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '12px', fontWeight: 'bold'
            }}>
              {step > i + 1 ? <CheckCircle size={14} /> : i + 1}
            </div>
            <div>
              <h5 style={{ margin: '0 0 4px 0', fontSize: '13px', color: '#1e293b' }}>{s.title}</h5>
              <p style={{ margin: 0, fontSize: '11px', color: '#64748b', lineHeight: '1.4' }}>{s.desc}</p>
            </div>
          </div>
        ))}
      </div>

      <div style={{ 
        padding: '12px 16px', borderTop: '1px solid #f1f5f9',
        display: 'flex', justifyContent: 'space-between' 
      }}>
        <button 
          disabled={step === 1}
          onClick={() => setStep(s => Math.max(1, s - 1))}
          style={{ 
            border: 'none', background: 'none', color: '#64748b', 
            fontSize: '12px', cursor: step === 1 ? 'not-allowed' : 'pointer' 
          }}
        >
          Previous
        </button>
        <button 
          onClick={() => setStep(s => Math.min(5, s + 1))}
          style={{ 
            background: '#6366f1', color: 'white', border: 'none',
            padding: '6px 16px', borderRadius: '6px', fontSize: '12px',
            cursor: 'pointer', fontWeight: 600
          }}
        >
          {step === 5 ? 'Finish' : 'Next Step'}
        </button>
      </div>
    </div>
  );
};

export default DemoGuide;
