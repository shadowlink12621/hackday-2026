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
      await loadHistory();
    } catch (err) {
      setError(err.message || 'Failed to connect to the backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (claimId, decision) => {
    try {
      await saveDecision(claimId, decision);
      await loadHistory();
      if (result && result.claim_id === claimId) {
        setResult(null);
        setFile(null);
        setPreviewUrl(null);
      }
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
      <header className="topbar">
        <a href="/" className="brand">
          <div className="brand-mark">cg</div>
          <div>
            ClaimGuard <span className="brand-accent">AI</span>
            <small>UNIVERSAL VALIDATOR</small>
          </div>
        </a>
        <div className="topbar-right">
          <span className="track-label">STAGE 2: INTEGRATION</span>
          <div className="connection online">
            <i></i> ONLINE
          </div>
        </div>
      </header>
      
      <main className="page">
        <div className="hero">
          <div>
            <div className="eyebrow">DOCUMENT PROCESSING ENGINE</div>
            <h1>Automate Expense & Health Claims</h1>
            <p className="subtitle">Upload a receipt or medical bill. Gemma 4 extracts the data, and our deterministic Python engine verifies fraud hashes and policy limits in real-time.</p>
          </div>
          <div className="hero-stat">
            <span>MODEL</span>
            <strong>Gemma 2.5 Flash</strong>
            <small>Multimodal Extraction</small>
          </div>
        </div>

        {error && (
          <div className="notice notice-error">
            <div>
              <strong>Connection Error</strong>
              <p style={{ margin: '4px 0 0' }}>{error}</p>
            </div>
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}
        
        <div className="work-grid">
          {/* Left Panel: Input & History */}
          <div>
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
                  accept="image/*,application/pdf"
                />
                
                {previewUrl ? (
                  <img src={previewUrl} alt="Receipt Preview" className="preview-image" />
                ) : (
                  <>
                    <div className="upload-icon upload-symbol">↑</div>
                    <strong>Drag and drop file here</strong>
                    <span>JPG, PNG up to 5MB</span>
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

            {/* History Section */}
            <section className="card history-card">
              <div className="card-heading history-heading">
                <h2>Recent Claims</h2>
                <button className="secondary-button" onClick={handleExportCsv}>
                  Export CSV
                </button>
              </div>
              
              {claimsHistory.length > 0 ? (
                <div className="table-wrap">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Amount</th>
                        <th className="right">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {claimsHistory.map(claim => (
                        <tr key={claim.id}>
                          <td className="claim-id">#{claim.id}</td>
                          <td>{claim.domain === 'health_insurance' ? 'Health' : 'Expense'}</td>
                          <td>
                            <span className={`status-pill ${claim.status === 'Approved' ? 'pill-valid' : (claim.status === 'Rejected' ? 'pill-review' : 'pill-pending')}`}>
                              {claim.status || (claim.is_valid ? 'Valid' : 'Flagged')}
                            </span>
                          </td>
                          <td>₹{claim.total_inr}</td>
                          <td className="right">
                            {(!claim.status || claim.status === 'Pending') && (
                              <div className="action-buttons" style={{ justifyContent: 'flex-end' }}>
                                <button onClick={() => handleDecision(claim.id, 'Approved')}>Approve</button>
                                <button className="reject-button" onClick={() => handleDecision(claim.id, 'Rejected')}>Reject</button>
                              </div>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="history-empty">
                  No claims processed yet.
                </div>
              )}
            </section>
          </div>
          
          {/* Right Panel: Output & Dashboard */}
          <section className="card results-card">
            <div className="card-heading">
              <div>
                <div className="eyebrow">STEP 2</div>
                <h2>Validation Results</h2>
              </div>
              {result && result.metadata && result.metadata.is_fallback_mock && (
                <div className="mock-tag">MOCK DATA</div>
              )}
            </div>
            
            {!result && !loading && (
              <div className="empty-state">
                <div className="empty-icon">▨</div>
                <strong>No Active Claim</strong>
                <p>Upload a document on the left to see Gemma 4 extraction and engine verification.</p>
              </div>
            )}
            
            {loading && (
              <div className="empty-state">
                <div className="spinner spinner-large"></div>
                <strong>Processing...</strong>
                <p>Running multimodal extraction and deterministic checks.</p>
              </div>
            )}

            {result && result.validation && (
              <>
                <div className={`decision-banner ${result.validation.is_valid ? 'decision-pass' : 'decision-review'}`}>
                  <div className="decision-icon">
                    {result.validation.is_valid ? '✓' : '!'}
                  </div>
                  <div>
                    <strong>{result.validation.is_valid ? 'SYSTEM APPROVED' : 'FLAGGED / MANUAL REVIEW'}</strong>
                    <small>Claim #{result.claim_id || 'N/A'}</small>
                  </div>
                  {result.perception && result.perception.confidence && (
                    <div className="confidence">
                      CONFIDENCE: {(result.perception.confidence * 100).toFixed(0)}%
                    </div>
                  )}
                </div>

                <div className="summary-grid">
                  <div className="summary-tile">
                    <span>PROVIDER / VENDOR</span>
                    <strong>{result.perception.structured_data.provider_name || result.perception.structured_data.vendor_name || 'Unknown'}</strong>
                  </div>
                  <div className="summary-tile">
                    <span>PATIENT / EMPLOYEE</span>
                    <strong>{result.perception.structured_data.patient_or_employee_name || 'N/A'}</strong>
                  </div>
                  <div className="summary-tile">
                    <span>ORIGINAL AMOUNT</span>
                    <strong>{result.perception.structured_data.total_extracted} {result.perception.structured_data.currency}</strong>
                  </div>
                  <div className="summary-tile">
                    <span>FINAL AMOUNT (INR)</span>
                    <strong className="amount">₹{result.validation.final_amount_inr}</strong>
                  </div>
                </div>

                <div className="rules-heading subheading">
                  <h3>ENGINE VERIFICATION <span className="count-tag">{result.validation.results.length} RULES</span></h3>
                </div>
                
                <div className="rules-list">
                  {result.validation.results.map((rule, idx) => (
                    <div key={idx} className="rule-row">
                      <div className={`rule-dot ${rule.passed ? 'rule-ok' : 'rule-fail'}`}>
                        {rule.passed ? '✓' : '×'}
                      </div>
                      <div>
                        <strong>{rule.rule_name}</strong>
                        <p>{rule.message}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="rules-heading subheading" style={{ marginTop: '24px' }}>
                  <h3>LINE ITEMS</h3>
                </div>
                
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Description</th>
                        <th>Category</th>
                        <th className="right">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.perception.structured_data.items.map((item, idx) => (
                        <tr key={idx}>
                          <td>{item.description}</td>
                          <td><span className="category-tag">{item.category || 'misc'}</span></td>
                          <td className="right">{item.amount.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>
        </div>
      </main>
    </>
  );
}

export default App;
