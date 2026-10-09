import { useState, useEffect } from 'react';
import { processDocument, getClaims, getHealth, getModelStatus, saveDecision, getAuditCsv } from './api';
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
import PolicyNavigator from './components/PolicyNavigator';

const appTabs = [
  { id: 'navigator', label: 'Policy Navigator' },
  { id: 'claims', label: 'Claims Workspace' },
  { id: 'calendar', label: 'Benefit Calendar' },
  { id: 'scamcheck', label: 'ScamCheck' },
  { id: 'insurers', label: 'Insurer Knowledge' },
];

function App() {
  const [activeTab, setActiveTab] = useState('claims');
  const [file, setFile] = useState(null);
  const [domainMode, setDomainMode] = useState('expense');
  const [previewUrl, setPreviewUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [claimsHistory, setClaimsHistory] = useState([]);
  const [modelStatus, setModelStatus] = useState(null);
  const [actionLoadingId, setActionLoadingId] = useState(null);
  const [authResolved, setAuthResolved] = useState(false);
  const [authRequired, setAuthRequired] = useState(false);
  const [authorized, setAuthorized] = useState(false);
  const [accessToken, setAccessToken] = useState('');
  const [authError, setAuthError] = useState('');
  const [allowCloudProcessing, setAllowCloudProcessing] = useState(false);

  const loadHistory = async () => {
    try {
      const history = await getClaims();
      setClaimsHistory(history);
    } catch (err) {
      console.error(err);
    }
  };

  const loadModelStatus = async () => {
    try {
      setModelStatus(await getModelStatus());
    } catch {
      setModelStatus(null);
    }
  };

  useEffect(() => {
    getHealth().then(async (health) => {
      const requiresAuth = Boolean(health.authentication_required);
      setAuthRequired(requiresAuth);
      const savedToken = sessionStorage.getItem('claimguard_access_token') || '';
      if (!requiresAuth) {
        setAuthorized(true);
        await loadHistory();
        await loadModelStatus();
      } else if (savedToken) {
        try {
          setClaimsHistory(await getClaims());
          setAuthorized(true);
          await loadModelStatus();
        } catch {
          sessionStorage.removeItem('claimguard_access_token');
        }
      }
      setAuthResolved(true);
    }).catch((err) => {
      setAuthError(err.message || 'Could not reach the ClaimGuard API.');
      setAuthResolved(true);
    });
  }, []);

  const handleAuthorize = async (event) => {
    event.preventDefault();
    sessionStorage.setItem('claimguard_access_token', accessToken.trim());
    try {
      setClaimsHistory(await getClaims());
      setAuthorized(true);
      await loadModelStatus();
      setAuthError('');
    } catch (err) {
      sessionStorage.removeItem('claimguard_access_token');
      setAuthError(err.message);
    }
  };

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png'];
      const maxBytes = selected.type === 'application/pdf' ? 20 * 1024 * 1024 : 5 * 1024 * 1024;
      if (!allowedTypes.includes(selected.type) || selected.size > maxBytes) {
        setError(!allowedTypes.includes(selected.type) ? 'Upload a PDF, JPEG, or PNG document.' : `File is larger than ${selected.type === 'application/pdf' ? '20' : '5'} MB.`);
        setFile(null);
        setPreviewUrl(null);
        setResult(null);
        return;
      }
      setFile(selected);
      // Only create image preview for images, not PDFs
      if (selected.type.startsWith('image/')) {
        setPreviewUrl(URL.createObjectURL(selected));
      } else {
        setPreviewUrl(null);
      }
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const data = await processDocument(file, domainMode, allowCloudProcessing);
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
      await saveDecision(claimId, decision);
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
    } catch {
      alert('Failed to download CSV');
    }
  };

  if (!authResolved) return <main className="access-gate"><p>Connecting to ClaimGuard…</p></main>;
  if (authRequired && !authorized) return (
    <main className="access-gate">
      <form className="card access-gate-form" onSubmit={handleAuthorize}>
        <div className="eyebrow">PRIVATE WORKSPACE</div>
        <h1>ClaimGuard access</h1>
        <p>Enter the administrator-configured access token. It stays in this browser session only.</p>
        <label>Access token<input type="password" value={accessToken} onChange={(event) => setAccessToken(event.target.value)} autoComplete="current-password" required /></label>
        {authError && <p className="notice notice-error" role="alert">{authError}</p>}
        <button className="primary-button" type="submit">Unlock workspace</button>
      </form>
    </main>
  );

  return (
    <ErrorBoundary>
      <Header modelStatus={modelStatus} />
      
      <main className="page">
        <div className="hero">
          <div>
            <div className="eyebrow">CLAIMGUARD · INSURANCE CLAIM COMPANION</div>
            <h1>Insurance Claim Readiness &amp; Benefit Navigator</h1>
            <p className="subtitle">
              Upload PDFs, images or bills. AI extracts data, deterministic engine verifies policy limits, and you manage approvals.
            </p>
          </div>
          <div className="hero-stat">
            <span>MODEL</span>
            <strong>{modelStatus?.active_backend === 'cloud_gemma' ? 'Cloud Gemma 4' : modelStatus?.active_backend === 'local_ollama' ? 'Local Ollama Gemma' : modelStatus?.active_backend === 'offline_mock' ? 'Offline fallback' : 'Checking model…'}</strong>
            <small>{modelStatus?.active_backend === 'offline_mock' ? 'Offline mode ready' : modelStatus ? 'Runtime model status' : 'Waiting for backend'}</small>
          </div>
        </div>

        {/* Navigation Tabs */}
        {error && (
          <div className="notice notice-error">
            <div>
              <strong>Error</strong>
              <p style={{ margin: '4px 0 0' }}>{error}</p>
            </div>
            <button onClick={() => setError(null)}>×</button>
          </div>
        )}

      {file?.type === 'application/pdf' && !result && (
        <div className="notice notice-info pdf-notice" role="status">
          <div>
            <strong>PDF detected</strong>
            <p style={{ margin: '4px 0 0' }}>ClaimGuard reads searchable text across every page. If you enable cloud processing below, Gemma also reads page images and scanned pages.</p>
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
              allowCloudProcessing={allowCloudProcessing}
              setAllowCloudProcessing={setAllowCloudProcessing}
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
            <PolicyNavigator />
          </div>
        )}
      </main>
    </ErrorBoundary>
  );
}

export default App;
