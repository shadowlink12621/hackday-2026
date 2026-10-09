import React from 'react';
import ChatInterface from './ChatInterface';
import AnalyticsChart from './AnalyticsChart';

export default function ResultsDashboard({ result, loading }) {
  return (
    <section className="card results-card">
      <div className="card-heading">
        <div>
          <div className="eyebrow">STEP 2</div>
          <h2>Validation Results</h2>
        </div>
        {result && result.metadata && result.metadata.is_fallback_mock && (
          <div className="mock-tag">OFFLINE · NOT EXTRACTED</div>
        )}
      </div>
      
      {!result && !loading && (
        <div className="empty-state">
          <div className="empty-icon">▨</div>
          <strong>No Active Claim</strong>
          <p>Upload a receipt image to see the configured model result and deterministic checks.</p>
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

          {result.claim_id && (
            <div style={{ margin: '12px 0 16px', display: 'flex', gap: '10px' }}>
              <a
                href={`http://localhost:8000/api/claims/${result.claim_id}/calendar.ics`}
                download={`claimguard_deadline_${result.claim_id}.ics`}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '6px',
                  textDecoration: 'none',
                  padding: '8px 14px',
                  borderRadius: '6px',
                  fontSize: '13px',
                  fontWeight: '500',
                  background: 'rgba(56, 189, 248, 0.12)',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  color: '#38bdf8',
                  transition: 'background 0.2s',
                }}
              >
                📅 Add Claim Deadlines to Calendar (.ics)
              </a>
            </div>
          )}

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
          
          <AnalyticsChart items={result.perception.structured_data.items} />
          
          <div style={{ marginTop: '32px' }}>
             <ChatInterface claimId={result.claim_id} />
          </div>
        </>
      )}
    </section>
  );
}
