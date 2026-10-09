import React, { useState } from 'react';

export default function CaseRegistration({ onRegister }) {
  const [formData, setFormData] = useState({
    name: '', dob: '', gender: '', blood_group: '', height_cm: '', weight_kg: '',
    conditions: '', smoker: false, allergies: '', medications: '', phone: '', email: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onRegister({ ...formData, conditions: formData.conditions.split(',').map(c => c.trim()).filter(Boolean) });
  };

  return (
    <div className="card" style={{ padding: '24px', maxWidth: '600px', margin: '0 auto' }}>
      <h2 style={{ margin: '0 0 16px', color: '#fff' }}>Register New Case</h2>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <input type="text" placeholder="Full Name" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} style={inputStyle} />
        <div style={{ display: 'flex', gap: '12px' }}>
          <input type="date" required value={formData.dob} onChange={e => setFormData({...formData, dob: e.target.value})} style={inputStyle} />
          <select value={formData.gender} onChange={e => setFormData({...formData, gender: e.target.value})} style={inputStyle}>
            <option value="">Select Gender</option><option value="M">Male</option><option value="F">Female</option>
          </select>
        </div>
        <input type="text" placeholder="Pre-existing conditions (comma separated)" value={formData.conditions} onChange={e => setFormData({...formData, conditions: e.target.value})} style={inputStyle} />
        <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fff' }}>
          <input type="checkbox" checked={formData.smoker} onChange={e => setFormData({...formData, smoker: e.target.checked})} /> Smoker
        </label>
        <button type="submit" className="primary-button">Register Case</button>
      </form>
    </div>
  );
}

const inputStyle = { padding: '12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.2)', color: '#fff' };
