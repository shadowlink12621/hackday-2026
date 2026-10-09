import { useState, useEffect } from 'react';
import { validateDocument, fetchClaims, recordClaimDecision, getAuditCsv, fetchModelStatus } from './api';
import './index.css';

import Header from './components/Header';
import UploadZone from './components/UploadZone';
import ResultsDashboard from './components/ResultsDashboard';
import HistoryTable from './components/HistoryTable';
import ErrorBoundary from './components/ErrorBoundary';
import FeatureShaderCards from './components/ui/feature-shader-cards';
import BenefitCalendar from './components/BenefitCalendar';
import ScamCheck from './components/ScamCheck';
import InsurerKnowledge from './components/InsurerKnowledge';
import PolicyNavigatorTab from './components/PolicyNavigatorTab';

const appTabs = [
  { id: 'navigator', label: 'Policy Navigator' },
  { id: 'claims', label: 'Claims Workspace' },
  { id: 'calendar', label: 'Benefit Calendar' },
  { id: 'scamcheck', label: 'ScamCheck' },
  { id: 'insurers', label: 'Insurer Knowledge' },
];

function App() {
  const [file, setFile] = useState(null);
  const [domainMode, setDomainMode] = useState('expense');
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [claimsHistory, setClaimsHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('claims');
  const [modelStatus, setModelStatus] = useState(null);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const loadHistory = async () => {
    try {
      const history = await fetchClaims();
      setClaimsHistory(history);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadHistory();
    let active = true;
    const refreshModelStatus = () => fetchModelStatus()
      .then((status) => active && setModelStatus(status))
      .catch(() => active && setModelStatus(null));
    refreshModelStatus();
    const intervalId = window.setInterval(refreshModelStatus, 30000);
    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
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
      const data = await validateDocument(file, domainMode);
      setResult(data);
      await loadHistory();
    } catch (err) {
      setError(err.message || 'Failed to connect to the backend.');
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (claimId, decision) => {
    setActionLoadingId(claimId);
    try {
      await recordClaimDecision(claimId, decision);
      await loadHistory();
      if (result && result.claim_id === claimId) {
        setResult(null);
        setFile(null);
        setPreviewUrl(null);
      }
    } catch (err) {
      setError(err.message || 'Failed to submit decision.');
    } finally {
      setActionLoadingId(null);
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
      <Header modelStatus={modelStatus} />
      
      <main className="page">
        <div className="hero">
          <div>
            <div className="eyebrow">DOCUMENT PROCESSING ENGINE</div>
            <h1>Automate Expense & Health Claims</h1>
            <p className="subtitle">Upload a receipt or medical bill. Gemma 4 extracts the data, and our deterministic Python engine verifies fraud hashes and policy limits in real-time.</p>
          </div>
          <div className="hero-stat">
            <span>MODEL</span>
            <strong>{modelStatus?.active_backend === 'cloud_gemma' ? 'Cloud Gemma 4' : modelStatus?.active_backend === 'local_ollama' ? 'Local Ollama Gemma' : modelStatus?.active_backend === 'offline_mock' ? 'Offline fallback' : 'Checking model…'}</strong>
            <small>{modelStatus?.active_backend === 'offline_mock' ? 'Offline mode ready' : modelStatus ? 'Runtime model status' : 'Waiting for backend'}</small>
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

        <nav className="app-tabs" role="tablist" aria-label="ClaimGuard workspaces">
          {appTabs.map((tab) => (
            <button
              type="button"
              role="tab"
              id={`tab-${tab.id}`}
              aria-selected={activeTab === tab.id}
              aria-controls={`panel-${tab.id}`}
              className={activeTab === tab.id ? 'app-tab active' : 'app-tab'}
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {activeTab === 'claims' && (
          <div id="panel-claims" className="app-tab-panel" role="tabpanel" aria-labelledby="tab-claims" tabIndex={0}>
        
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
              actionLoadingId={actionLoadingId}
            />
          </div>
          
          <ResultsDashboard 
            result={result} 
            loading={loading} 
          />
        </div>
        <FeatureShaderCards />
          </div>
        )}
        {activeTab === 'calendar' && (
          <div id="panel-calendar" className="app-tab-panel" role="tabpanel" aria-labelledby="tab-calendar" tabIndex={0}>
            <BenefitCalendar claims={claimsHistory} />
          </div>
        )}
        {activeTab === 'scamcheck' && (
          <div id="panel-scamcheck" className="app-tab-panel" role="tabpanel" aria-labelledby="tab-scamcheck" tabIndex={0}>
            <ScamCheck />
          </div>
        )}
        {activeTab === 'insurers' && (
          <div id="panel-insurers" className="app-tab-panel" role="tabpanel" aria-labelledby="tab-insurers" tabIndex={0}>
            <InsurerKnowledge />
          </div>
        )}
        {activeTab === 'navigator' && (
          <div id="panel-navigator" className="app-tab-panel" role="tabpanel" aria-labelledby="tab-navigator" tabIndex={0}>
            <PolicyNavigatorTab />
          </div>
        )}
      </main>
    </ErrorBoundary>
  );
}

export default App;
