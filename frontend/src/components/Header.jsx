import React from 'react';

export default function Header() {
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
        <span className="track-label">STAGE 2: INTEGRATION</span>
        <div className="connection online">
          <i></i> ONLINE
        </div>
      </div>
    </header>
  );
}
