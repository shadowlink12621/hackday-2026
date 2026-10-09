import { useState, useRef } from 'react';
import { processDocument } from './api';
import './index.css';

function App() {
  const [file, setFile] = useState(null);
  const [domainMode, setDomainMode] = useState('expense');
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
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
      const data = await processDocument(file, domainMode);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Failed to connect to the backend.');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    if (!result || !result.perception.structured_data.items) return;
    const items = result.perception.structured_data.items;
    
    const header = ['Description', 'Category', 'Amount'];
    const rows = items.map(item => [`"${item.description}"`, `"${item.category || ''}"`, item.amount]);
    const csvContent = [header, ...rows].map(e => e.join(",")).join("\n");
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "claim_items.csv");
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <>
      <header>
        <h1>ClaimGuard</h1>
        <p>Universal AI Claims Validator (Expenses & Health Insurance)</p>
      </header>
      
      <main className="container">
        {/* Left Panel: Input */}
        <section className="panel">
          <h2>Input Claim</h2>

          <div style={{ marginBottom: '1.5rem' }}>
            <label className="data-label" style={{ display: 'block', marginBottom: '0.5rem' }}>Select Claim Type:</label>
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
              accept="image/*,application/pdf"
            />
            
            {previewUrl ? (
              <img src={previewUrl} alt="Receipt Preview" className="preview-image" />
            ) : (
              <>
                <div className="upload-icon">🧾</div>
                <p>Drag and drop a receipt/bill here</p>
                <p className="data-label" style={{marginTop: '0.5rem', fontSize: '0.8rem'}}>or click to browse</p>
              </>
            )}
          </div>
          
          <button 
            className="btn" 
            onClick={handleAnalyze} 
            disabled={!file || loading}
          >
            {loading ? <span className="loader"></span> : 'Process Claim'}
          </button>
          
          {error && <div style={{color: 'var(--error)', marginTop: '1rem', textAlign: 'center'}}>{error}</div>}
        </section>
        
        {/* Right Panel: Output & Dashboard */}
        <section className="panel" style={{ overflowY: 'auto' }}>
          <h2>Results Dashboard</h2>
          
          <div className="results">
            {!result && !loading && (
              <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--text-muted)'}}>
                Upload a claim to see AI extraction and validation results.
              </div>
            )}
            
            {loading && (
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--accent)'}}>
                <div className="loader" style={{width: '40px', height: '40px', borderWidth: '4px', marginBottom: '1rem'}}></div>
                <p>Gemma 4 is processing...</p>
              </div>
            )}

            {result && (
              <>
                {/* Glowing Badge for Overall Status */}
                <div className={`status-badge ${result.verification.is_valid ? 'valid' : 'invalid'}`}>
                  {result.verification.is_valid ? 'APPROVED' : 'FLAGGED / MANUAL REVIEW'}
                </div>

                {/* Extracted Data summary */}
                <div className="section-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ margin: 0 }}>🧠 Gemma 4 Extracted Data</h3>
                    <span className="data-label" style={{ fontSize: '0.8rem' }}>Model: {result.metadata.model_used}</span>
                  </div>
                  
                  <div className="data-row">
                    <span className="data-label">Provider/Vendor</span>
                    <span className="data-value">{result.perception.structured_data.provider_name || result.perception.structured_data.vendor_name}</span>
                  </div>
                  <div className="data-row">
                    <span className="data-label">Patient/Employee</span>
                    <span className="data-value">{result.perception.structured_data.patient_or_employee_name || 'N/A'}</span>
                  </div>
                  <div className="data-row">
                    <span className="data-label">Total Amount</span>
                    <span className="data-value">{result.perception.structured_data.total_extracted} {result.perception.structured_data.currency}</span>
                  </div>
                  <div className="data-row">
                    <span className="data-label">Final Amount (INR)</span>
                    <span className="data-value" style={{ color: 'var(--accent)' }}>₹{result.verification.final_amount_inr}</span>
                  </div>
                </div>

                {/* Line Items Table */}
                <div className="section-card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3 style={{ margin: 0 }}>🛒 Line Items</h3>
                    <button className="btn" style={{ margin: 0, padding: '0.5rem 1rem', fontSize: '0.9rem' }} onClick={exportToCSV}>
                      Export to CSV
                    </button>
                  </div>
                  <div className="table-container">
                    <table className="items-table">
                      <thead>
                        <tr>
                          <th>Description</th>
                          <th>Category</th>
                          <th style={{ textAlign: 'right' }}>Amount</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.perception.structured_data.items.map((item, idx) => (
                          <tr key={idx}>
                            <td>{item.description}</td>
                            <td><span style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', fontSize: '0.8rem' }}>{item.category || 'misc'}</span></td>
                            <td style={{ textAlign: 'right' }}>{item.amount.toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Deterministic Verification Results */}
                <div className="section-card">
                  <h3 style={{ marginBottom: '1rem' }}>⚙️ Engine Verification</h3>
                  <div>
                    {result.verification.results.map((rule, idx) => (
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
              </>
            )}
          </div>
        </section>
      </main>
    </>
  );
}

export default App;
