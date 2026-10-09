import React, { useState } from 'react';
import { addEvent, getCaseIcsUrl } from '../api';

export default function DeadlinesCalendar({ caseId }) {
  const [date, setDate] = useState('');
  const [type, setType] = useState('admission');

  const handleSubmit = async (e) => {
    e.preventDefault();
    await addEvent(caseId, { type, date, note: 'User added event' });
    alert("Event added (mock)");
  };

  return (
    <div className="card" style={{ padding: '24px', marginTop: '16px' }}>
      <h3 style={{ margin: '0 0 16px', color: '#fff' }}>Claim Deadlines</h3>
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
        <input type="date" required value={date} onChange={e => setDate(e.target.value)} style={{ padding: '8px', borderRadius: '6px', border: '1px solid #444', background: '#222', color: '#fff' }} />
        <select value={type} onChange={e => setType(e.target.value)} style={{ padding: '8px', borderRadius: '6px', border: '1px solid #444', background: '#222', color: '#fff' }}>
          <option value="admission">Admission Date</option>
          <option value="discharge">Discharge Date</option>
        </select>
        <button type="submit" className="primary-button" style={{ margin: 0, height: 'auto', padding: '0 16px', width: 'auto' }}>Track Event</button>
      </form>
      {caseId && (
        <a href={getCaseIcsUrl(caseId)} download className="primary-button" style={{ textDecoration: 'none', width: 'auto', display: 'inline-block' }}>
          Download .ics Deadlines
        </a>
      )}
    </div>
  );
}
