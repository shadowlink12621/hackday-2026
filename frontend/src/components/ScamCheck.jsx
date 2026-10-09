import React, { useState } from 'react';
import { checkScamMessage } from '../api';

export default function ScamCheck() {
  const [message, setMessage] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      setResult(await checkScamMessage(message.trim()));
    } catch (err) {
      setError(err.message || 'Could not analyze this message.');
    } finally {
      setLoading(false);
    }
  };

  const riskLevel = result?.risk_level?.toLowerCase() || 'safe';

  return (
    <section className="card companion-card scam-card" aria-labelledby="scamcheck-title">
      <div className="eyebrow">MESSAGE SAFETY</div>
      <h2 id="scamcheck-title">ScamCheck</h2>
      <p className="companion-intro">Paste a suspicious insurance SMS, email, or WhatsApp message. ClaimGuard checks for common fee, credential, link, and pressure tactics.</p>
      <form className="scam-form" onSubmit={handleSubmit}>
        <label className="field-label" htmlFor="scam-message">Message to check</label>
        <textarea
          id="scam-message"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Paste the message here. Remove personal details first if possible."
          rows={7}
          maxLength={10000}
          required
        />
        <div className="scam-form-footer">
          <small>{message.length}/10,000 characters</small>
          <button className="primary-button" type="submit" disabled={loading || !message.trim()}>
            {loading ? 'Checking…' : 'Analyze message'}
          </button>
        </div>
      </form>

      {error && <div className="notice notice-error scam-error" role="alert">{error}</div>}

      {result && (
        <section className={`scam-result risk-${riskLevel}`} aria-live="polite">
          <div className="scam-score-row">
            <div>
              <div className="eyebrow">RISK ASSESSMENT</div>
              <h3>{result.risk_level?.replaceAll('_', ' ') || 'RESULT'}</h3>
            </div>
            <div className="scam-score"><strong>{result.risk_score}</strong><span>/100</span></div>
          </div>
          <div className="risk-meter" role="meter" aria-label="Message risk score" aria-valuemin="0" aria-valuemax="100" aria-valuenow={result.risk_score}>
            <span style={{ width: `${Math.max(0, Math.min(100, result.risk_score || 0))}%` }} />
          </div>
          {result.detected_red_flags?.length ? (
            <div className="scam-flags">
              <h4>Signals found</h4>
              <ul>{result.detected_red_flags.map((flag, index) => <li key={`${index}-${flag}`}>{flag}</li>)}</ul>
            </div>
          ) : <p className="scam-no-flags">No obvious red flags were detected. This does not prove the sender is genuine.</p>}
          <div className="scam-guidance"><strong>What to do</strong><p>{result.guidance}</p></div>
          {result.official_portal_link && (
            <a className="official-link" href={result.official_portal_link} target="_blank" rel="noreferrer">Open IRDAI Bima Bharosa ↗</a>
          )}
          <small className="companion-footnote">Automated screening can miss scams. Verify using contact details from your policy or insurer's official website; never use a number or link from a suspicious message.</small>
        </section>
      )}
    </section>
  );
}
