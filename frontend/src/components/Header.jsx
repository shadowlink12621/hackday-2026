import React from 'react';

function modelBadge(modelStatus) {
  if (!modelStatus) return { className: 'model-status-unavailable', label: 'AI STATUS UNAVAILABLE', detail: 'Backend model status has not loaded' };
  switch (modelStatus.active_backend) {
    case 'cloud_gemma':
      return { className: 'model-status-gemma', label: 'CLOUD KEY CONFIGURED', detail: `${modelStatus.cloud_model || 'Google GenAI'} · connection not verified` };
    case 'local_ollama':
      return { className: 'model-status-local', label: 'OLLAMA · ONLINE', detail: modelStatus.local_models?.[0] || 'Local model' };
    default:
      return { className: 'model-status-offline', label: 'OFFLINE · SOURCE SEARCH', detail: 'No cloud or local model is active' };
  }
}

export default function Header({ modelStatus }) {
  const badge = modelBadge(modelStatus);
  return (
    <header className="topbar">
      <a href="/" className="brand">
        <div className="brand-mark">cg</div>
        <div>
          ClaimGuard <span className="brand-accent">AI</span>
          <small>UNIVERSAL VALIDATOR</small>
        </div>
      </a>
      <div className="topbar-right">
        <div className={`model-status ${badge.className}`} title={badge.detail} aria-live="polite">
          <i></i>
          <div><strong>{badge.label}</strong><small>{badge.detail}</small></div>
        </div>
      </div>
    </header>
  );
}
