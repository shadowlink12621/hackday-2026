import React, { useRef } from 'react';

export default function UploadZone({ 
  domainMode, setDomainMode, file, previewUrl, 
  loading, handleFileChange, handleAnalyze, setFile, setPreviewUrl, setResult, setError
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
      const dropped = e.dataTransfer.files[0];
      setFile(dropped);
      setPreviewUrl(URL.createObjectURL(dropped));
      setResult(null);
      setError(null);
    }
  };

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
          accept="image/jpeg,image/png,.jpg,.jpeg,.png"
        />
        
        {previewUrl ? (
          <img src={previewUrl} alt="Receipt Preview" className="preview-image" />
        ) : (
          <>
            <div className="upload-icon upload-symbol">↑</div>
            <strong>Drag and drop file here</strong>
            <span>JPEG or PNG up to 5 MB</span>
          </>
        )}
      </div>
      
      <button 
        className="primary-button" 
        onClick={handleAnalyze} 
        disabled={!file || loading}
      >
        {loading ? <div className="spinner"></div> : 'Process Claim'}
      </button>
    </section>
  );
}
