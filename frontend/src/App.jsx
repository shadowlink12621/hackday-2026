import { useState, useRef } from 'react';
import { validateDocument } from './api';
import './index.css';

function App() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [domainMode, setDomainMode] = useState('expense');
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
      setResult(null);
      setError(null);
    }
  };

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

  const handleAnalyze = async () => {
    if (!file) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await validateDocument(file, domainMode);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to the validation engine.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <header>
        <h1>ClaimGuard</h1>
        <p>AI assisted claim review with deterministic policy checks</p>
      </header>
      
      <main className="container">
        {/* Left Panel: Input */}
        <section className="panel">
          <h2>Input Document</h2>

          <label className="domain-label" htmlFor="domain-mode">Claim type</label>
          <select
            id="domain-mode"
            className="domain-select"
            value={domainMode}
            onChange={(e) => setDomainMode(e.target.value)}
          >
            <option value="expense">Corporate Expense</option>
            <option value="health_insurance">Health Insurance</option>
          </select>
          
          <div 
            className="upload-area"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleFileChange} 
              accept="image/jpeg,image/png"
            />
            
            {previewUrl ? (
              <img src={previewUrl} alt="Document Preview" className="preview-image" />
            ) : (
              <>
                <div className="upload-icon">📄</div>
                <p>Drag and drop a document here</p>
                <p className="data-label" style={{marginTop: '0.5rem', fontSize: '0.8rem'}}>or click to browse</p>
              </>
            )}
          </div>
          
          <button 
            className="btn" 
            onClick={handleAnalyze} 
            disabled={!file || loading}
          >
            {loading ? <span className="loader"></span> : 'Analyze Document'}
          </button>
          
          {error && <div style={{color: 'var(--error)', marginTop: '1rem', textAlign: 'center'}}>{error}</div>}
        </section>
        
        {/* Right Panel: Output & Telemetry */}
        <section className="panel">
          <h2>Telemetry & Validation</h2>
          
          <div className="results">
            {!result && !loading && (
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)'}}>
                Upload a document to see Gemma 4 and deterministic engine results.
              </div>
            )}
            
            {loading && (
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--accent)'}}>
                <div className="loader" style={{width: '40px', height: '40px', borderWidth: '4px', marginBottom: '1rem'}}></div>
                <p>Gemma 4 is processing the document...</p>
              </div>
            )}

            {result && (
              <>
                {/* AI Perception (Gemma 4) */}
                <div className="section-card">
                  <h3>🧠 Gemma 4 Perception (JSON Schema)</h3>
                  <div className="data-row">
                    <span className="data-label">Document Type</span>
                    <span className="data-value">{domainMode === 'health_insurance' ? 'Health insurance bill' : 'Expense receipt'}</span>
                  </div>
                  <div className="data-row">
                    <span className="data-label">Date Extracted</span>
                    <span className="data-value">{result.perception.structured_data.date_extracted || 'None'}</span>
                  </div>
                  <div className="data-row">
                    <span className="data-label">Confidence</span>
                    <span className="data-value" style={{color: result.perception.confidence >= 0.7 ? 'var(--success)' : 'var(--error)'}}>
                      {(result.perception.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Deterministic Verification (Code) */}
                <div className="section-card" style={{flex: 1}}>
                  <h3>⚙️ Deterministic Rule Verification</h3>
                  <div style={{marginTop: '1rem'}}>
                    {result.validation.results.map((rule, idx) => (
                      <div key={idx} className={`rule-item ${rule.passed ? 'pass' : 'fail'}`}>
                        <div className="rule-icon">{rule.passed ? '✅' : '❌'}</div>
                        <div className="rule-content">
                          <h4>{rule.rule_name}</h4>
                          <p>{rule.message}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className={`status-badge ${result.validation.is_valid ? 'valid' : 'invalid'}`}>
                  {result.validation.is_valid ? 'DOCUMENT ACCEPTED' : 'DOCUMENT REJECTED'}
                </div>
              </>
            )}
          </div>
        </section>
      </main>
    </>
  );
}

export default App;
