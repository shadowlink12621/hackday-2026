import React from 'react';
import { getCalendarIcsUrl } from '../api';

function formatDate(value) {
  if (!value) return 'Date not extracted';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

export default function BenefitCalendar({ claims }) {
  return (
    <section className="card companion-card" aria-labelledby="calendar-title">
      <div className="card-heading">
        <div>
          <div className="eyebrow">CLAIM FOLLOW-UP</div>
          <h2 id="calendar-title">Benefit Calendar</h2>
        </div>
        <span className="companion-count">{claims.length} CLAIM{claims.length === 1 ? '' : 'S'}</span>
      </div>
      <p className="companion-intro">Add claim submission and follow-up reminders to your calendar. Each file includes the backend's claim-specific milestones.</p>

      {claims.length ? (
        <div className="calendar-claim-list">
          {claims.map((claim) => (
            <article className="calendar-claim" key={claim.id}>
              <div className="calendar-date-mark" aria-hidden="true"><span>CLAIM</span><strong>#{claim.id}</strong></div>
              <div className="calendar-claim-details">
                <strong>{claim.extracted_data?.provider_name || 'Claim follow-up'}</strong>
                <span>{claim.domain === 'health_insurance' ? 'Health insurance' : 'Corporate expense'} · {formatDate(claim.extracted_data?.date_extracted || claim.timestamp)}</span>
                <small>Includes filing deadline, insurer follow-up, and post-hospitalization reminders.</small>
              </div>
              <a className="secondary-button calendar-download" href={getCalendarIcsUrl(claim.id)} download={`claimguard_claim_${claim.id}.ics`}>
                Download .ics
              </a>
            </article>
          ))}
        </div>
      ) : (
        <div className="history-empty">Process a claim first to create its calendar reminders.</div>
      )}
      <p className="companion-footnote">Reminder dates follow the backend's default schedule. Check the applicable policy and insurer instructions for actual deadlines.</p>
    </section>
  );
}
