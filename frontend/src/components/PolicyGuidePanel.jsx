import React from 'react';

export default function PolicyGuidePanel({ guide }) {
  if (!guide) return null;

  return (
    <section className="policy-guide" aria-labelledby="policy-guide-title">
      <div className="policy-guide-heading">
        <div>
          <div className="eyebrow">DOCUMENT INSIGHTS{guide.page_count ? ` · ${guide.page_count} PAGES SCANNED` : ''}</div>
          <h3 id="policy-guide-title">Policy guide & claim traps</h3>
        </div>
        <span className="policy-guide-tag">{guide.source === 'gemma' ? 'GEMMA REVIEW' : 'KEYWORD SCAN'}</span>
      </div>
      <p className="policy-guide-summary">{guide.summary}</p>

      <div className="policy-guide-columns">
        <div>
          <h4>Policy highlights</h4>
          {guide.highlights?.length ? (
            <div className="policy-insight-list">
              {guide.highlights.map((item, index) => (
                <article className="policy-insight" key={`highlight-${index}`}>
                  <div className="policy-insight-title">
                    <strong>{item.title}</strong>
                    {item.page && <span>Page {item.page}</span>}
                  </div>
                  <p>{item.detail}</p>
                  <small><b>Next step:</b> {item.action}</small>
                </article>
              ))}
            </div>
          ) : <p className="policy-guide-empty">No specific clauses were confidently identified in the scanned text.</p>}
        </div>
        <div>
          <h4>Common claim traps</h4>
          <div className="policy-insight-list">
            {(guide.common_traps || []).map((item, index) => (
              <article className="policy-insight policy-trap" key={`trap-${index}`}>
                <div className="policy-insight-title"><strong>{item.title}</strong></div>
                <p>{item.detail}</p>
                <small><b>What to do:</b> {item.action}</small>
              </article>
            ))}
          </div>
        </div>
      </div>
      <small className="policy-guide-note">Guidance is for review; confirm coverage against your policy schedule and insurer.</small>
    </section>
  );
}
