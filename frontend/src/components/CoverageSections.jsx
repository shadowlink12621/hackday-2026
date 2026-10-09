import React from 'react';

const iconMap = { eyes: '👁', dental: '🦷', ortho: '🦴', maternity: '🤰', room_rent: '🛏️' };

export default function CoverageSections({ sections }) {
  if (!sections || !sections.length) return null;
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px', marginTop: '16px' }}>
      {sections.map(sec => (
        <div key={sec.key} className="card" style={{ padding: '20px' }}>
          <h3 style={{ margin: '0 0 12px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>{iconMap[sec.key] || '📄'}</span> {sec.title}
          </h3>
          <div style={{ fontSize: '14px', color: '#eaf1f2' }}>
            <div style={{ marginBottom: '8px' }}>
              <span style={{ color: '#8d9ba8' }}>Limit:</span> {sec.limit ? sec.limit.value : <span style={{ color: '#666' }}>Not stated</span>}
              {sec.limit?.page && <span style={{ marginLeft: '8px', background: '#0d6efd44', padding: '2px 6px', borderRadius: '4px', fontSize: '11px', color: '#6ea8fe' }} title={sec.limit.quote}>p.{sec.limit.page}</span>}
            </div>
            <div style={{ marginBottom: '8px' }}>
              <span style={{ color: '#8d9ba8' }}>Wait Period:</span> {sec.waiting_period ? sec.waiting_period.value : <span style={{ color: '#666' }}>None</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
