import React from 'react';

export default function PolicyFacts({ facts }) {
  if (!facts || facts.length === 0) return null;

  const getStatusStyle = (status) => {
    switch (status) {
      case 'source_found':
        return { bg: 'rgba(13, 110, 253, 0.1)', color: '#6ea8fe', label: 'Source Found', border: '1px solid #0d6efd' };
      case 'verify_scope':
        return { bg: 'rgba(253, 126, 20, 0.1)', color: '#fd7e14', label: 'Verify Scope', border: '1px solid #fd7e14' };
      case 'conflict_review':
        return { bg: 'rgba(220, 53, 69, 0.1)', color: '#dc3545', label: 'Conflict / Review Needed', border: '1px solid #dc3545' };
      default:
        return { bg: 'rgba(255, 255, 255, 0.1)', color: '#fff', label: 'Unknown', border: '1px solid #444' };
    }
  };

  const handlePageClick = (e, page) => {
    // Attempt to open PDF at specific page if supported. 
    // Usually this is done via standard href like `#page=9` for PDF viewers.
    // For this UI, we just alert or rely on default browser behavior for PDFs if we had the actual file.
    // We will leave the href so it tries to trigger it if a viewer is active.
  };

  return (
    <div style={{ marginTop: '16px' }}>
      <h3 style={{ color: '#fff', marginBottom: '16px' }}>Extracted Policy Facts</h3>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
        {facts.map((fact, index) => {
          const style = getStatusStyle(fact.status);
          return (
            <div key={index} className="card" style={{ padding: '20px', borderLeft: `4px solid ${style.border.split(' ')[2]}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <h4 style={{ margin: '0 0 8px', color: '#fff', fontSize: '18px' }}>{fact.topic}</h4>
                <div style={{ background: style.bg, color: style.color, padding: '4px 10px', borderRadius: '16px', fontSize: '12px', fontWeight: 'bold' }}>
                  {style.label}
                </div>
              </div>
              <p style={{ margin: '0 0 12px', color: '#eaf1f2', lineHeight: '1.5' }}>
                {fact.summary}
              </p>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {fact.pages.map((p) => (
                  <a 
                    key={p} 
                    href={`#page=${p}`} 
                    onClick={(e) => handlePageClick(e, p)}
                    style={{ background: 'rgba(255,255,255,0.1)', padding: '4px 8px', borderRadius: '4px', color: '#8d9ba8', textDecoration: 'none', fontSize: '13px' }}
                    title={`View PDF Page ${p}`}
                  >
                    📄 Page {p}
                  </a>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
