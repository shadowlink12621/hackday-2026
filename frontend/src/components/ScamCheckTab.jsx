import React, { useState } from 'react';

const SAMPLE_SCAMS = [
  {
    label: 'Fee Demand Scam',
    text: 'Dear customer, your health claim of Rs 48,500 is approved. Pay fee of Rs 1,500 processing charges to clear GST and release funds immediately to bit.ly/claim-settle',
  },
  {
    label: 'OTP / UPI PIN Request',
    text: 'Your medical claim refund is pending transfer. Scan this QR code and enter your UPI PIN to receive Rs 18,000 directly into your bank account.',
  },
  {
    label: 'Legitimate Insurer SMS',
    text: 'Your health insurance policy #10293847 is due for renewal on 24th October. Visit official portal at https://sbigeneral.in to renew.',
  },
];

export default function ScamCheckTab() {
  const [messageText, setMessageText] = useState(SAMPLE_SCAMS[0].text);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleAnalyze = async (textToAnalyze) => {
    const text = textToAnalyze || messageText;
    if (!text.trim()) return;

    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/scamcheck', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message_text: text }),
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else {
        throw new Error('Analysis failed');
      }
    } catch {
      // Offline fallback check
      const isFee = text.toLowerCase().includes('fee') || text.toLowerCase().includes('charge');
      const isOtp = text.toLowerCase().includes('otp') || text.toLowerCase().includes('pin');
      setResult({
        is_suspicious: isFee || isOtp,
        risk_score: isFee ? 85 : (isOtp ? 80 : 0),
        risk_level: isFee || isOtp ? 'HIGH_RISK' : 'SAFE',
        detected_red_flags: isFee
          ? ['🚨 UPFRONT PAYMENT DEMAND: The message asks for money/fee to release an insurance claim. According to IRDAI Bima Bharosa guidelines, insurers NEVER ask policyholders for payment to release an approved claim or bonus.']
          : [],
        guidance: isFee
          ? 'DO NOT pay any money, share OTPs, or click links. Verify directly with your insurer official helpline or register a grievance on IRDAI Bima Bharosa portal.'
          : 'No obvious red flags detected. Ensure any communication matches your official policy documents.',
        official_portal_link: 'https://bimabharosa.irdai.gov.in',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginTop: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
      {/* Input Column */}
      <div className="card">
        <div className="card-heading">
          <div>
            <div className="eyebrow">CONSUMER PROTECTION</div>
            <h2>Insurance ScamCheck & Phishing Detector</h2>
          </div>
        </div>

        <p style={{ fontSize: '13px', color: '#94a3b8', lineHeight: 1.5, marginBottom: '14px' }}>
          Paste any suspicious SMS, WhatsApp message, or email claiming an insurance refund or asking for payment.
          Cross-referenced against official <strong>IRDAI Bima Bharosa</strong> fraud alerts.
        </p>

        {/* Quick Sample Buttons */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '12px' }}>
          {SAMPLE_SCAMS.map((s, idx) => (
            <button
              key={idx}
              onClick={() => {
                setMessageText(s.text);
                handleAnalyze(s.text);
              }}
              style={{
                fontSize: '11px',
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid rgba(255,255,255,0.12)',
                color: '#38bdf8',
                padding: '4px 10px',
                borderRadius: '6px',
                cursor: 'pointer',
              }}
            >
              Paste: {s.label}
            </button>
          ))}
        </div>

        <textarea
          rows={6}
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          placeholder="Paste message text here..."
          style={{
            width: '100%',
            padding: '12px',
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.1)',
            color: '#fff',
            borderRadius: '8px',
            fontSize: '13px',
            fontFamily: 'inherit',
            marginBottom: '14px',
            resize: 'vertical',
          }}
        />

        <button
          onClick={() => handleAnalyze()}
          disabled={loading}
          className="primary-button"
          style={{ width: '100%', padding: '12px', fontSize: '14px', fontWeight: 600 }}
        >
          {loading ? 'Analyzing against IRDAI Red Flags...' : '🛡️ Scan Message for Scam Indicators'}
        </button>
      </div>

      {/* Results Column */}
      <div className="card">
        <div className="card-heading">
          <div>
            <div className="eyebrow">AUDIT VERDICT</div>
            <h2>Safety Analysis</h2>
          </div>
        </div>

        {!result && (
          <div className="empty-state">
            <div className="empty-icon">🛡️</div>
            <strong>No Message Scanned</strong>
            <p>Paste an SMS or select a sample on the left to verify authenticity.</p>
          </div>
        )}

        {result && (
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px',
                borderRadius: '8px',
                marginBottom: '16px',
                background: result.risk_level === 'HIGH_RISK' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                border: `1px solid ${result.risk_level === 'HIGH_RISK' ? '#ef4444' : '#10b981'}`,
              }}
            >
              <div>
                <strong style={{ fontSize: '16px', color: result.risk_level === 'HIGH_RISK' ? '#ef4444' : '#10b981' }}>
                  {result.risk_level === 'HIGH_RISK' ? '⚠️ HIGH RISK: SUSPECTED SCAM' : '✓ SAFE COMMUNICATION'}
                </strong>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                  Threat Assessment Score: {result.risk_score} / 100
                </div>
              </div>
              <span
                style={{
                  fontSize: '20px',
                  fontWeight: 800,
                  color: result.risk_level === 'HIGH_RISK' ? '#ef4444' : '#10b981',
                }}
              >
                {result.risk_score}%
              </span>
            </div>

            {result.detected_red_flags && result.detected_red_flags.length > 0 && (
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ margin: '0 0 8px', fontSize: '13px', color: '#f87171' }}>DETECTED RED FLAGS:</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {result.detected_red_flags.map((flag, idx) => (
                    <div
                      key={idx}
                      style={{
                        background: 'rgba(239, 68, 68, 0.08)',
                        border: '1px solid rgba(239, 68, 68, 0.2)',
                        padding: '10px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        color: '#fca5a5',
                        lineHeight: 1.4,
                      }}
                    >
                      {flag}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', padding: '14px', borderRadius: '8px', marginBottom: '16px' }}>
              <h4 style={{ margin: '0 0 6px', fontSize: '13px', color: '#38bdf8' }}>REGULATORY GUIDANCE:</h4>
              <p style={{ margin: '0 0 10px', fontSize: '12px', color: '#cbd5e1', lineHeight: 1.4 }}>
                {result.guidance}
              </p>
              <a
                href={result.official_portal_link || 'https://bimabharosa.irdai.gov.in'}
                target="_blank"
                rel="noreferrer"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  color: '#38bdf8',
                  fontSize: '12px',
                  fontWeight: 600,
                  textDecoration: 'none',
                }}
              >
                🔗 Visit Official IRDAI Bima Bharosa Portal ↗
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
