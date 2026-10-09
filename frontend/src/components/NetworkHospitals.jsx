import React from 'react';

export default function NetworkHospitals({ network }) {
  if (!network) return null;
  const isOpen = network.type === 'open_to_all';
  return (
    <div className="card" style={{ padding: '20px', marginTop: '16px' }}>
      <h3 style={{ margin: '0 0 12px', color: '#fff' }}>Network & Cashless</h3>
      {isOpen ? (
        <div style={{ display: 'inline-block', padding: '8px 16px', background: '#19875422', color: '#198754', borderRadius: '8px', fontWeight: 'bold' }}>
          ✅ Open to any hospital (Reimbursement allowed)
        </div>
      ) : (
        <div>
          <div style={{ color: '#eaf1f2' }}>Cashless available at network hospitals only.</div>
          {network.link && <a href={network.link.value} target="_blank" rel="noreferrer" style={{ color: '#0d6efd', display: 'inline-block', marginTop: '8px' }}>View Network Hospitals ↗</a>}
        </div>
      )}
    </div>
  );
}
