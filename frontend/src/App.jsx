import { useState, useRef, useEffect } from 'react';
import { processDocument, getClaims, saveDecision, getAuditCsv } from './api';
import './index.css';

function App() {
  const [file, setFile] = useState(null);
  const [domainMode, setDomainMode] = useState('expense');
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [claimsHistory, setClaimsHistory] = useState([]);
  const fileInputRef = useRef(null);

  const loadHistory = async () => {
    try {
      const history = await getClaims();
      setClaimsHistory(history);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

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
      // Reload history to show the newly added claim
      await loadHistory();
    } catch (err) {
      setError(err.message || 'Failed to connect to the backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision) => {
    if (!result || !result.claim_id) return;
    
    try {
      await saveDecision(result.claim_id, decision);
      alert(`Claim ${decision} successfully!`);
      setResult(null);
      setFile(null);
      setPreviewUrl(null);
      await loadHistory();
    } catch (err) {
      alert("Failed to submit decision");
    }
  };

  const handleExportCsv = async (e) => {
    e.preventDefault();
    try {
      const blob = await getAuditCsv();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'audit_report.csv';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to download CSV");
    }
  };

  return (
    <>
      <header>
        <h1>ClaimGuard</h1>
        <p>Universal AI Claims Validator (Expenses & Health Insurance)</p>
      </header>
      
      <main className="container">
        {/* Left Panel: Input & History */}
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

          <div style={{ marginTop: '2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2>Recent Claims</h2>
              <button className="btn" style={{ padding: '0.5rem 1rem', fontSize: '0.9rem', marginTop: 0 }} onClick={handleExportCsv}>
                Export Full CSV Audit
              </button>
            </div>
            <div className="table-container">
              <table className="items-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Amount (INR)</th>
                  </tr>
                </thead>
                <tbody>
                  {claimsHistory.map(claim => (
                    <tr key={claim.id}>
                      <td>#{claim.id}</td>
                      <td>{claim.domain}</td>
                      <td>
                        <span className={`status-badge ${claim.is_valid ? 'valid' : 'invalid'}`} style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', width: 'auto' }}>
                          {claim.status || (claim.is_valid ? 'Valid' : 'Flagged')}
                        </span>
                      </td>
                      <td>₹{claim.total_inr}</td>
                    </tr>
                  ))}
                  {claimsHistory.length === 0 && (
                    <tr>
                      <td colSpan="4" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No claims processed yet.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
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

            {result && result.validation && (
              <>
                {/* Glowing Badge for Overall Status */}
                <div className={`status-badge ${result.validation.is_valid ? 'valid' : 'invalid'}`}>
                  {result.validation.is_valid ? 'SYSTEM APPROVED' : 'FLAGGED / MANUAL REVIEW'}
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
                    <span className="data-value" style={{ color: 'var(--accent)' }}>₹{result.validation.final_amount_inr}</span>
                  </div>
                </div>

                {/* Line Items Table */}
                <div className="section-card">
                  <h3 style={{ marginBottom: '1rem' }}>🛒 Line Items</h3>
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

                {/* Manager Decision */}
                <div className="section-card" style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                  <button className="btn" style={{ flex: 1, background: 'var(--success)' }} onClick={() => handleDecision('Approved')}>
                    Approve Claim
                  </button>
                  <button className="btn" style={{ flex: 1, background: 'var(--error)' }} onClick={() => handleDecision('Rejected')}>
                    Reject Claim
                  </button>
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
