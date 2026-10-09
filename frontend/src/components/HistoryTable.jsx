import React from 'react';

export default function HistoryTable({ claimsHistory, handleDecision, handleExportCsv, actionLoadingId }) {
  return (
    <section className="card history-card">
      <div className="card-heading history-heading">
        <h2>Recent Claims</h2>
        <button className="secondary-button" onClick={handleExportCsv}>
          Export CSV
        </button>
      </div>
      
      {claimsHistory.length > 0 ? (
        <div className="table-wrap">
          <table className="history-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Submitted</th>
                <th>Type</th>
                <th>AI Check</th>
                <th>Manager Status</th>
                <th>Amount</th>
                <th className="right">Action</th>
              </tr>
            </thead>
            <tbody>
              {claimsHistory.map(claim => (
                <tr key={claim.id}>
                  <td className="claim-id">#{claim.id}</td>
                  <td>{claim.timestamp ? new Date(claim.timestamp).toLocaleDateString() : '—'}</td>
                  <td>{claim.domain === 'health_insurance' ? 'Health' : 'Expense'}</td>
                  <td>
                    <span className={`status-pill ${claim.is_valid ? 'pill-valid' : 'pill-review'}`}>
                      {claim.is_valid ? 'Valid' : 'Flagged'}
                    </span>
                  </td>
                  <td>
                    <span className={`status-pill ${claim.status === 'Approved' ? 'pill-valid' : (claim.status === 'Rejected' ? 'pill-review' : 'pill-pending')}`}>
                      {claim.status || 'Pending'}
                    </span>
                  </td>
                  <td>₹{claim.total_inr}</td>
                  <td className="right">
                    {(!claim.status || claim.status === 'Pending') && (
                      <div className="action-buttons" style={{ justifyContent: 'flex-end' }}>
                        <button disabled={actionLoadingId === claim.id} onClick={() => handleDecision(claim.id, 'Approved')}>
                          {actionLoadingId === claim.id ? 'Saving…' : 'Approve'}
                        </button>
                        <button className="reject-button" disabled={actionLoadingId === claim.id} onClick={() => handleDecision(claim.id, 'Rejected')}>Reject</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="history-empty">
          No claims processed yet.
        </div>
      )}
    </section>
  );
}
