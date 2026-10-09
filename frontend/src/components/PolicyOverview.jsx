import React from 'react';

export default function PolicyOverview({ summary }) {
  if (!summary) return null;
  return (
    <div className="card" style={{ padding: '24px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
      <div>
        <div style={{ color: '#8d9ba8', fontSize: '12px', fontWeight: 'bold' }}>INSURER</div>
        <h2 style={{ margin: '0', color: '#fff' }}>{summary.insurer?.value}</h2>
        <div style={{ color: '#0d6efd', fontWeight: '600' }}>{summary.plan_name?.value}</div>
      </div>
      <div>
        <div style={{ color: '#8d9ba8', fontSize: '12px', fontWeight: 'bold' }}>SUM INSURED</div>
        <h2 style={{ margin: '0', color: '#fff' }}>{summary.sum_insured?.value}</h2>
        <div style={{ color: '#198754' }}>Valid until {summary.end_date?.value}</div>
      </div>
      <div style={{ gridColumn: '1 / -1', background: 'rgba(255,255,255,0.05)', padding: '12px', borderRadius: '8px' }}>
        <strong style={{ color: '#fff' }}>Policy Holder:</strong> {summary.policy_holder?.value} <br/>
        <strong style={{ color: '#fff' }}>Policy No:</strong> {summary.policy_number?.value}
      </div>
    </div>
  );
}
