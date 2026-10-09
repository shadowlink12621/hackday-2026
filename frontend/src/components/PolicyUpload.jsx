import React, { useState } from 'react';

export default function PolicyUpload({ onUpload }) {
  const [file, setFile] = useState(null);

  return (
    <div className="card" style={{ padding: '24px', textAlign: 'center', marginTop: '16px' }}>
      <h2 style={{ color: '#fff', marginBottom: '16px' }}>Upload Policy Document</h2>
      <p style={{ color: '#8d9ba8', marginBottom: '24px' }}>Please upload your insurance policy (PDF/JPG/PNG)</p>
      <input type="file" accept=".pdf,image/*" onChange={e => setFile(e.target.files[0])} style={{ color: '#fff' }} />
      {file && (
        <button className="primary-button" onClick={() => onUpload(file)}>
          Upload & Analyze {file.name}
        </button>
      )}
    </div>
  );
}
