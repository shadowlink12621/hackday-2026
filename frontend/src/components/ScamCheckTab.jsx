import React, { useState } from 'react';
import { checkScamMessage } from '../api';

export default function ScamCheckTab() {
  const [messageText, setMessageText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async (event) => {
    event.preventDefault();
    if (!messageText.trim() || loading) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      setResult(await checkScamMessage(messageText.trim()));
    } catch (err) {
      setError(err.message || 'Scam check service is unavailable.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="scam-grid">
      <form className="card scam-input" onSubmit={handleAnalyze}>
        <div className="card-heading"><div><div className="eyebrow">CONSUMER PROTECTION</div><h2>Check a suspicious message</h2></div></div>
        <p>Paste the SMS, email, or chat text you want to review. A result is shown only when the local ClaimGuard service responds.</p>
        <label htmlFor="scam-message">Message text</label>
        <textarea id="scam-message" rows={8} value={messageText} onChange={(event) => setMessageText(event.target.value)} placeholder="Paste message text here" />
        <button className="primary-button" type="submit" disabled={loading || !messageText.trim()}>{loading ? 'Checking…' : 'Check message'}</button>
        {error && <p className="notice notice-error" role="alert">{error}</p>}
      </form>

      <section className="card scam-result" aria-live="polite">
        <div className="eyebrow">RESULT</div>
        <h2>Indicators found</h2>
        {!result && !loading && <p className="muted-copy">No message has been checked in this session.</p>}
        {loading && <p role="status">Checking message text…</p>}
        {result && <>
          <p><strong>{result.risk_level || (result.is_suspicious ? 'Review recommended' : 'No indicators detected')}</strong></p>
          <p>{result.guidance}</p>
          {result.detected_red_flags?.length > 0 && <ul>{result.detected_red_flags.map((flag, index) => <li key={`${index}-${flag}`}>{flag}</li>)}</ul>}
          {result.official_portal_link && <a href={result.official_portal_link} target="_blank" rel="noreferrer">Open official grievance portal</a>}
        </>}
      </section>
    </div>
  );
}
