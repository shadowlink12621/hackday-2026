import React, { useState } from 'react';
import { chatCase } from '../api';

export default function CaseChat({ caseId }) {
  const [q, setQ] = useState('');
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!q) return;
    setLoading(true);
    setHistory([...history, { role: 'user', text: q }]);
    try {
      const res = await chatCase(caseId, q);
      setHistory(h => [...h, { role: 'ai', text: res.answer, citations: res.citations, is_fallback: res.is_fallback }]);
    } catch (err) {
      setHistory(h => [...h, { role: 'ai', text: 'Error connecting to chat.', error: true }]);
    }
    setQ('');
    setLoading(false);
  };

  return (
    <div className="card" style={{ padding: '20px', marginTop: '16px', background: 'rgba(0,0,0,0.4)' }}>
      <h3 style={{ margin: '0 0 12px', color: '#fff' }}>Policy AI Assistant</h3>
      <div style={{ maxHeight: '300px', overflowY: 'auto', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {history.map((msg, i) => (
          <div key={i} style={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', background: msg.role === 'user' ? '#0d6efd' : '#2a2d35', padding: '12px', borderRadius: '12px', maxWidth: '85%', color: '#fff' }}>
            <div style={{ fontSize: '14px', lineHeight: '1.5' }}>{msg.text}</div>
            {msg.citations?.length > 0 && (
              <div style={{ marginTop: '8px', display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                {msg.citations.map((c, ci) => (
                  <span key={ci} style={{ fontSize: '11px', background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px' }} title={c.quote}>p.{c.page}</span>
                ))}
              </div>
            )}
            {msg.is_fallback && <div style={{ fontSize: '10px', color: '#f39c12', marginTop: '4px' }}>DEMO CACHE</div>}
          </div>
        ))}
      </div>
      <form onSubmit={handleAsk} style={{ display: 'flex', gap: '8px' }}>
        <input type="text" value={q} onChange={e => setQ(e.target.value)} placeholder="e.g. Is cataract covered for me?" style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.2)', color: '#fff' }} />
        <button type="submit" className="primary-button" style={{ margin: 0, width: 'auto', padding: '0 20px' }} disabled={loading}>{loading ? '...' : 'Ask'}</button>
      </form>
    </div>
  );
}
