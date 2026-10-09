import React, { useRef } from 'react';

export default function UploadZone({ 
  domainMode, setDomainMode, file, previewUrl, 
  loading, handleFileChange, handleAnalyze, allowCloudProcessing, setAllowCloudProcessing,
}) {
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange({ target: { files: e.dataTransfer.files } });
    }
  };

  const isPdf = file && (file.type === 'application/pdf' || file.name?.toLowerCase().endsWith('.pdf'));

  return (
    <section className="card intake-card">
      <div className="card-heading">
        <div>
          <div className="eyebrow">STEP 1</div>
          <h2>Intake Form</h2>
        </div>
        <div className="step-tag">INPUT</div>
      </div>

      <div>
        <label className="field-label">Select Claim Type</label>
        <select 
          value={domainMode} 
          onChange={(e) => setDomainMode(e.target.value)}
          className="domain-select"
        >
          <option value="expense">Corporate Expense</option>
          <option value="health_insurance">Health Insurance (Medical Bill)</option>
        </select>
      </div>
      
      <div 
        className="dropzone"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileChange} 
          accept="image/jpeg,image/png,application/pdf,.jpg,.jpeg,.png,.pdf"
        />
        
        {isPdf ? (
          <div style={{ textAlign: 'center', padding: '16px' }}>
            <div style={{ fontSize: '48px', marginBottom: '8px' }}>📄</div>
            <strong style={{ color: '#38bdf8', wordBreak: 'break-word' }}>{file.name}</strong>
            <div style={{ color: '#94a3b8', fontSize: '12px', marginTop: '4px' }}>
              PDF · {(file.size / 1024).toFixed(0)} KB
            </div>
          </div>
        ) : previewUrl ? (
          <img src={previewUrl} alt="Receipt Preview" className="preview-image" />
        ) : (
          <>
            <div className="upload-icon upload-symbol">↑</div>
            <strong>Drag and drop file here</strong>
            <span>JPG or PNG up to 5 MB · PDF up to 20 MB</span>
          </>
        )}
      </div>

      <label className="consent-line upload-cloud-consent">
        <input type="checkbox" checked={allowCloudProcessing} onChange={(event) => setAllowCloudProcessing(event.target.checked)} />
        I consent to send this document to Gemma for extraction. Leave unchecked for local/offline processing.
      </label>

      <label className="consent-line upload-cloud-consent">
        <input type="checkbox" checked={allowCloudProcessing} onChange={(event) => setAllowCloudProcessing(event.target.checked)} />
        I consent to send this document to the configured cloud AI provider for extraction. Leave unchecked for local/offline processing.
      </label>
      
      <button 
        className="primary-button" 
        id="process-claim-btn"
        onClick={handleAnalyze} 
        disabled={!file || loading}
      >
        {loading ? <div className="spinner"></div> : 'Process Claim'}
      </button>
    </section>
  );
}
