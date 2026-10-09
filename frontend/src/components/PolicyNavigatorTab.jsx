import React, { useState } from 'react';
import CaseRegistration from './CaseRegistration';
import PolicyUpload from './PolicyUpload';
import PolicyOverview from './PolicyOverview';
import PolicyFacts from './PolicyFacts';
import CoverageSections from './CoverageSections';
import NetworkHospitals from './NetworkHospitals';
import ExclusionsPanel from './ExclusionsPanel';
import DeadlinesCalendar from './DeadlinesCalendar';
import CaseChat from './CaseChat';
import { createCase, uploadPolicy, getPolicy } from '../api';

export default function PolicyNavigatorTab() {
  const [caseId, setCaseId] = useState(null);
  const [policy, setPolicy] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRegister = async (data) => {
    setLoading(true);
    try {
      const res = await createCase(data);
      setCaseId(res.case_id || 'mock_case_123'); // Fallback to mock if API fails
    } catch (e) {
      console.warn("Using mock case ID");
      setCaseId('mock_case_123');
    }
    setLoading(false);
  };

  const handleUpload = async (file) => {
    setLoading(true);
    try {
      const response = await uploadPolicy(caseId, file);
      const newPolicyId = response.policy_id;
      // Wait a moment then fetch
      setTimeout(async () => {
        const report = await getPolicy(newPolicyId);
        setPolicy(report);
        setCaseId(newPolicyId); // update caseId so chat hits the real backend
        setLoading(false);
      }, 1500);
    } catch (e) {
      console.warn("Upload failed, fetching mock");
      const report = await getPolicy(caseId);
      setPolicy(report);
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {!caseId && !policy && (
        <CaseRegistration onRegister={handleRegister} />
      )}
      
      {caseId && !policy && !loading && (
        <PolicyUpload onUpload={handleUpload} />
      )}

      {loading && (
        <div className="card" style={{ padding: '40px', textAlign: 'center', color: '#fff' }}>
          <div className="inline-loading">Processing...</div>
          <p style={{ marginTop: '16px', color: '#8d9ba8' }}>Reading pages... Extracting coverage... Please wait.</p>
        </div>
      )}

      {policy && !loading && (
        <>
          {policy.source?.is_fallback && (
            <div style={{ background: '#f39c12', color: '#000', padding: '8px 16px', borderRadius: '8px', fontWeight: 'bold', textAlign: 'center' }}>
              DEMO CACHE
            </div>
          )}
          {policy.warnings?.length > 0 && (
            <div style={{ background: '#e67e22', color: '#fff', padding: '12px 16px', borderRadius: '8px', borderLeft: '4px solid #d35400' }}>
              <strong>Warnings:</strong> {policy.warnings.map((w, i) => <div key={i}>{w}</div>)}
            </div>
          )}
          
          <PolicyOverview summary={policy.summary} />
          <PolicyFacts facts={policy.facts} />
          <CoverageSections sections={policy.sections} />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
            <NetworkHospitals network={policy.network} />
            <ExclusionsPanel exclusions={policy.exclusions} />
          </div>
          <DeadlinesCalendar caseId={caseId} />
          <CaseChat caseId={caseId} />
        </>
      )}
    </div>
  );
}
