import React from 'react';

export default function ExclusionsPanel({ exclusions }) {
  if (!exclusions) return null;
  return (
    <div className="card" style={{ padding: '20px', marginTop: '16px', borderLeft: '4px solid #dc3545' }}>
      <h3 style={{ margin: '0 0 12px', color: '#fff' }}>Waiting Periods & Exclusions</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', color: '#eaf1f2', fontSize: '14px' }}>
        <div><strong style={{ color: '#dc3545' }}>Initial Wait:</strong> {exclusions.initial_wait?.value || 'None'}</div>
        <div><strong style={{ color: '#dc3545' }}>Pre-existing Diseases:</strong> {exclusions.pre_existing_wait?.value || 'None'}</div>
        <div><strong style={{ color: '#dc3545' }}>Specific Illnesses:</strong> {exclusions.specific_illness_wait?.value || 'None'}</div>
        {exclusions.permanent?.length > 0 && (
          <div style={{ marginTop: '8px' }}>
            <strong style={{ color: '#dc3545' }}>Permanent Exclusions:</strong>
            <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
              {exclusions.permanent.map((p, i) => <li key={i}>{p.value}</li>)}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
