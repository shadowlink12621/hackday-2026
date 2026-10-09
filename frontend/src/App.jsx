import { useState, useEffect } from 'react';
import { processDocument, getClaims, saveDecision, getAuditCsv } from './api';
import './index.css';

import Header from './components/Header';
import UploadZone from './components/UploadZone';
import ResultsDashboard from './components/ResultsDashboard';
import HistoryTable from './components/HistoryTable';
import ErrorBoundary from './components/ErrorBoundary';
import PolicyNavigator from './components/PolicyNavigator';
import ScamCheckTab from './components/ScamCheckTab';

function App() {
  const [activeTab, setActiveTab] = useState('claims');
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
      setPreviewUrl(URL.createObjectURL(selected));
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
    } catch {
      alert('Failed to submit decision');
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
    } catch {
      alert('Failed to download CSV');
    }
  };

  return (
    <ErrorBoundary>
      <Header />

      <main className="page">
        <div className="hero">
          <div>
            <div className="eyebrow">CLAIMGUARD · BENEFIT & READINESS COMPANION</div>
            <h1>Insurance Claim Readiness & Benefit Navigator</h1>
            <p className="subtitle">
              Verify medical bills, index 60+ page policy wordings with citations, track 30-day statutory deadlines, and audit suspicious messages.
            </p>
          </div>
          <div className="hero-stat">
            <span>MODEL</span>
            <strong>Gemma 4 Multimodal</strong>
            <small>Local RAG + Citations</small>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>
          <button
            onClick={() => setActiveTab('claims')}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: activeTab === 'claims' ? '1px solid #38bdf8' : '1px solid rgba(255,255,255,0.1)',
              background: activeTab === 'claims' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(255,255,255,0.03)',
              color: activeTab === 'claims' ? '#38bdf8' : '#94a3b8',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            📄 Expense & Bill Auditor
          </button>
          <button
            onClick={() => setActiveTab('policy')}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: activeTab === 'policy' ? '1px solid #10b981' : '1px solid rgba(255,255,255,0.1)',
              background: activeTab === 'policy' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255,255,255,0.03)',
              color: activeTab === 'policy' ? '#10b981' : '#94a3b8',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            🏥 Patient Case & 59-Page Policy RAG
          </button>
          <button
            onClick={() => setActiveTab('scam')}
            style={{
              padding: '8px 16px',
              borderRadius: '6px',
              border: activeTab === 'scam' ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.1)',
              background: activeTab === 'scam' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255,255,255,0.03)',
              color: activeTab === 'scam' ? '#ef4444' : '#94a3b8',
              fontWeight: 600,
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            🛡️ ScamCheck (IRDAI Bima Bharosa)
          </button>
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

        {/* Tab 1: Claims & Expense Auditor */}
        {activeTab === 'claims' && (
          <div className="work-grid">
            <div>
              <UploadZone
                domainMode={domainMode}
                setDomainMode={setDomainMode}
                file={file}
                previewUrl={previewUrl}
                loading={loading}
                handleFileChange={handleFileChange}
                handleAnalyze={handleAnalyze}
                setFile={setFile}
                setPreviewUrl={setPreviewUrl}
                setResult={setResult}
                setError={setError}
              />

              <HistoryTable
                claimsHistory={claimsHistory}
                handleDecision={handleDecision}
                handleExportCsv={handleExportCsv}
              />
            </div>

            <ResultsDashboard result={result} loading={loading} />
          </div>
        )}

        {/* Tab 2: Policy Navigator & Patient Case */}
        {activeTab === 'policy' && <PolicyNavigator />}

        {/* Tab 3: ScamCheck */}
        {activeTab === 'scam' && <ScamCheckTab />}
      </main>
    </ErrorBoundary>
  );
}

export default App;
