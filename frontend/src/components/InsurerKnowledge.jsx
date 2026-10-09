import React, { useEffect, useState } from 'react';
import { fetchInsurerKnowledge, fetchInsurers } from '../api';

function insurerLabel(key) {
  return key.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function InsurerKnowledge() {
  const [insurers, setInsurers] = useState([]);
  const [selected, setSelected] = useState('');
  const [knowledge, setKnowledge] = useState(null);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    fetchInsurers()
      .then((data) => {
        if (!active) return;
        const available = data.insurers || [];
        setInsurers(available);
        setSelected(available[0] || '');
      })
      .catch((err) => active && setError(err.message || 'Could not load insurer guides.'))
      .finally(() => active && setLoadingList(false));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!selected) return undefined;
    let active = true;
    setLoadingDetails(true);
    setError('');
    setKnowledge(null);
    fetchInsurerKnowledge(selected)
      .then((data) => active && setKnowledge(data))
      .catch((err) => active && setError(err.message || 'Could not load this insurer guide.'))
      .finally(() => active && setLoadingDetails(false));
    return () => { active = false; };
  }, [selected]);

  return (
    <section className="card companion-card" aria-labelledby="insurer-title">
      <div className="eyebrow">REFERENCE LIBRARY</div>
      <h2 id="insurer-title">Insurer Knowledge</h2>
      <p className="companion-intro">Review insurer-specific gotchas from the local ClaimGuard knowledge base before submitting or following up on a claim.</p>

      {loadingList ? <p className="inline-loading">Loading insurer list…</p> : insurers.length > 0 ? (
        <div className="insurer-layout">
          <nav className="insurer-picker" aria-label="Choose insurer">
            {insurers.map((insurer) => (
              <button
                type="button"
                key={insurer}
                className={selected === insurer ? 'insurer-choice selected' : 'insurer-choice'}
                aria-pressed={selected === insurer}
                onClick={() => setSelected(insurer)}
              >
                {insurerLabel(insurer)}
              </button>
            ))}
          </nav>

          <div className="insurer-detail" aria-live="polite">
            {loadingDetails ? <p className="inline-loading">Loading guide…</p> : knowledge && (
              <>
                <div className="insurer-detail-heading">
                  <div>
                    <div className="eyebrow">INSURER GUIDE</div>
                    <h3>{knowledge.title || insurerLabel(selected)}</h3>
                  </div>
                  <span className="companion-count">LOCAL REFERENCE</span>
                </div>
                {knowledge.key_traps?.length ? (
                  <div className="insurer-traps">
                    {knowledge.key_traps.map((trap, index) => (
                      <article className="insurer-trap" key={`${index}-${trap}`}><span>{String(index + 1).padStart(2, '0')}</span><p>{trap.replace(/^[-\d.\s]+/, '')}</p></article>
                    ))}
                  </div>
                ) : <p className="companion-footnote">No gotcha list was extracted for this guide.</p>}
                {knowledge.official_portal && <a className="official-link" href={knowledge.official_portal} target="_blank" rel="noreferrer">IRDAI Bima Bharosa ↗</a>}
                <details className="insurer-source">
                  <summary>View full knowledge note</summary>
                  <pre>{knowledge.raw_content}</pre>
                </details>
              </>
            )}
          </div>
        </div>
      ) : <div className="history-empty">No insurer guides are available.</div>}
      {error && <div className="notice notice-error companion-error" role="alert">{error}</div>}
      <p className="companion-footnote">Reference notes are for claim preparation and are not a coverage decision. Confirm terms in your active policy schedule.</p>
    </section>
  );
}
