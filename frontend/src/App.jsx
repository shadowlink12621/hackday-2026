import { useState, useEffect } from 'react';
import { processDocument, getClaims, saveDecision, getAuditCsv } from './api';
import './index.css';

import Header from './components/Header';
import UploadZone from './components/UploadZone';
import ResultsDashboard from './components/ResultsDashboard';
import HistoryTable from './components/HistoryTable';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  const [file, setFile] = useState(null);
  const [domainMode, setDomainMode] = useState('expense');
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [claimsHistory, setClaimsHistory] = useState([]);

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
      setPreviewUrl(selected.type === 'application/pdf' ? null : URL.createObjectURL(selected));
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
    <ErrorBoundary>
      <Header />
      
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

      {file?.type === 'application/pdf' && !result && (
        <div className="notice notice-info pdf-notice" role="status">
          <div>
            <strong>PDF detected</strong>
            <p style={{ margin: '4px 0 0' }}>After submission, ClaimGuard will scan its searchable text and show policy highlights, claim traps, and next steps.</p>
          </div>
        </div>
      )}
        
        <div className="work-grid">
          <div>
            <UploadZone 
              domainMode={domainMode} setDomainMode={setDomainMode}
              file={file} previewUrl={previewUrl} loading={loading}
              handleFileChange={handleFileChange}
              handleAnalyze={handleAnalyze}
              setFile={setFile} setPreviewUrl={setPreviewUrl}
              setResult={setResult} setError={setError}
            />

            <HistoryTable 
              claimsHistory={claimsHistory}
              handleDecision={handleDecision}
              handleExportCsv={handleExportCsv}
            />
          </div>
          
          <ResultsDashboard 
            result={result} 
            loading={loading} 
          />
        </div>
      </main>
    </ErrorBoundary>
  );
}

export default App;
