import React, { useEffect, useMemo, useState } from 'react';
import {
  askPolicy,
  createCase,
  getCase,
  getCaseDocumentUrl,
  getCases,
  getModelStatus,
  getPolicy,
  generatePolicySummary,
  uploadCaseDocument,
} from '../api';

const EMPTY_PATIENT = {
  patient_name: '',
  age: '',
  weight_kg: '',
  blood_group: '',
  medical_conditions: '',
  admission_date: '',
  discharge_date: '',
};

const STEPS = [
  { id: 'case', label: '1. Patient case' },
  { id: 'policy', label: '2. Policy' },
  { id: 'documents', label: '3. Medical documents' },
  { id: 'review', label: '4. Summary & questions' },
];

export default function PolicyNavigator() {
  const [cases, setCases] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [caseData, setCaseData] = useState(null);
  const [policyData, setPolicyData] = useState(null);
  const [patient, setPatient] = useState(EMPTY_PATIENT);
  const [step, setStep] = useState('case');
  const [modelStatus, setModelStatus] = useState(null);
  const [category, setCategory] = useState('lab_report');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [generatedSummary, setGeneratedSummary] = useState(null);
  const [cloudConsent, setCloudConsent] = useState(false);
  const [reminderDate, setReminderDate] = useState('');
  const [reminderConfirmed, setReminderConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const policyDocument = useMemo(
    () => caseData?.documents?.find((document) => document.category === 'policy' && document.policy_id),
    [caseData],
  );
  const canReview = Boolean(policyDocument && policyData);

  const refreshCase = async (caseId) => {
    const [record, list] = await Promise.all([getCase(caseId), getCases()]);
    setCaseData(record);
    setCases(list);
    setSelectedId(String(record.case_id));
    setReminderDate(localStorage.getItem(`claimguard-reminder-${record.case_id}`) || '');
    setReminderConfirmed(localStorage.getItem(`claimguard-reminder-confirmed-${record.case_id}`) === 'true');
    const linkedPolicy = [...record.documents].reverse().find((doc) => doc.category === 'policy' && doc.policy_id);
    if (linkedPolicy) setPolicyData(await getPolicy(linkedPolicy.policy_id));
    else setPolicyData(null);
  };

  useEffect(() => {
    let active = true;
    Promise.all([getCases(), getModelStatus()])
      .then(([list, status]) => {
        if (!active) return;
        setCases(list);
        setModelStatus(status);
        const savedId = localStorage.getItem('claimguard-selected-case');
        const first = list.find((item) => String(item.case_id) === savedId) || list[0];
        if (first) return refreshCase(first.case_id);
      })
      .catch((err) => active && setError(err.message));
    return () => { active = false; };
  }, []);

  const handleSelectCase = async (event) => {
    const id = event.target.value;
    setSelectedId(id);
    setError('');
    setNotice('');
    setMessages([]);
    setCloudConsent(false);
    setGeneratedSummary(null);
    if (!id) {
      setCaseData(null);
      setPolicyData(null);
      setStep('case');
      return;
    }
    setBusy(true);
    try {
      await refreshCase(id);
      localStorage.setItem('claimguard-selected-case', id);
      setStep('case');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleCreateCase = async (event) => {
    event.preventDefault();
    if (!patient.patient_name.trim()) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const payload = {
        patient_name: patient.patient_name.trim(),
        ...(patient.age !== '' && { age: Number(patient.age) }),
        ...(patient.weight_kg !== '' && { weight_kg: Number(patient.weight_kg) }),
        ...(patient.blood_group.trim() && { blood_group: patient.blood_group.trim() }),
        medical_conditions: patient.medical_conditions
          .split(/[,\n]/).map((value) => value.trim()).filter(Boolean),
        additional_details: {
          ...(patient.admission_date && { admission_date: patient.admission_date }),
          ...(patient.discharge_date && { discharge_date: patient.discharge_date }),
        },
      };
      const created = await createCase(payload);
      await refreshCase(created.case_id);
      localStorage.setItem('claimguard-selected-case', String(created.case_id));
      setPatient(EMPTY_PATIENT);
      setStep('policy');
      setNotice('Case saved locally. Add the policy document to continue.');
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleUpload = async (event, uploadCategory) => {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file || !caseData) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      if (uploadCategory === 'policy') {
        setCloudConsent(false);
        setGeneratedSummary(null);
        setMessages([]);
      }
      const response = await uploadCaseDocument(caseData.case_id, file, uploadCategory);
      await refreshCase(caseData.case_id);
      if (uploadCategory === 'policy') {
        setPolicyData(response.policy);
        setStep('review');
        setNotice(`Indexed ${response.policy?.page_count ?? 0} policy pages locally. Original file is saved only in this local demo.`);
      } else {
        setNotice('Document saved to this case locally. Medical interpretation is not available yet.');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleQuestion = async (event) => {
    event.preventDefault();
    const prompt = question.trim();
    if (!prompt || !policyDocument || busy) return;
    setMessages((previous) => [...previous, { role: 'user', text: prompt }]);
    setQuestion('');
    setBusy(true);
    setError('');
    try {
      const response = await askPolicy(policyDocument.policy_id, prompt, cloudConsent);
      setMessages((previous) => [...previous, { role: 'assistant', ...response }]);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleSummary = async () => {
    if (!policyDocument || !cloudConsent || busy) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const summary = await generatePolicySummary(policyDocument.policy_id, true);
      setGeneratedSummary(summary);
      if (summary.model_used === 'retrieval_only') setNotice(summary.detail);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const saveReminderDate = (value) => {
    setReminderDate(value);
    setReminderConfirmed(false);
    if (caseData) {
      localStorage.setItem(`claimguard-reminder-${caseData.case_id}`, value);
      localStorage.removeItem(`claimguard-reminder-confirmed-${caseData.case_id}`);
    }
  };

  const confirmReminderDate = (checked) => {
    setReminderConfirmed(checked);
    if (caseData) localStorage.setItem(`claimguard-reminder-confirmed-${caseData.case_id}`, String(checked));
  };

  const selectStep = (id) => {
    if (id !== 'case' && !caseData) return;
    if (id === 'review' && !canReview) return;
    if (id === 'documents' && !policyDocument) return;
    setStep(id);
    setError('');
  };

  const modelLabel = !modelStatus
    ? 'Checking runtime…'
    : modelStatus.active_backend === 'cloud_gemma'
      ? `Cloud configured · ${modelStatus.cloud_model}`
      : modelStatus.active_backend === 'local_ollama'
        ? `Local Ollama · ${modelStatus.local_models?.[0] || 'online'}`
        : 'Offline · retrieval only';

  return (
    <section className="case-workflow">
      <header className="card case-toolbar">
        <div>
          <div className="eyebrow">LOCAL CLAIM WORKSPACE</div>
          <h2>Patient cases</h2>
        </div>
        <label className="case-picker">
          <span>Open case</span>
          <select value={selectedId} onChange={handleSelectCase} aria-label="Open patient case">
            <option value="">New case</option>
            {cases.map((item) => <option key={item.case_id} value={item.case_id}>{item.patient_name} · #{item.case_id}</option>)}
          </select>
        </label>
        <div className="model-state" title="Runtime configuration only; successful live inference is confirmed per response.">
          <span className={modelStatus?.active_backend === 'offline_mock' ? 'state-dot state-offline' : 'state-dot'} />
          <span>{modelLabel}</span>
        </div>
      </header>

      <nav className="workflow-steps" aria-label="Case workflow">
        {STEPS.map((item) => {
          const disabled = (item.id !== 'case' && !caseData)
            || (item.id === 'documents' && !policyDocument)
            || (item.id === 'review' && !canReview);
          return (
            <button key={item.id} type="button" className={step === item.id ? 'workflow-step active' : 'workflow-step'} disabled={disabled} onClick={() => selectStep(item.id)}>
              {item.label}
            </button>
          );
        })}
      </nav>

      {error && <div className="notice notice-error" role="alert">{error}</div>}
      {notice && <div className="notice notice-success" role="status">{notice}</div>}
      {busy && <div className="workflow-progress" role="status">Working…</div>}

      {step === 'case' && (
        <section className="card workflow-panel">
          <div className="eyebrow">STEP 1 · CASE DETAILS</div>
          <h2>{caseData ? `Case for ${caseData.patient_name}` : 'Register a patient case'}</h2>
          {caseData ? (
            <div className="case-facts">
              <p>Case data is stored locally on this machine. Optional health details come from you and are not inferred from documents.</p>
              <dl>
                <div><dt>Name</dt><dd>{caseData.patient_name}</dd></div>
                <div><dt>Age</dt><dd>{caseData.patient_details.age ?? 'Not provided'}</dd></div>
                <div><dt>Weight</dt><dd>{caseData.patient_details.weight_kg ? `${caseData.patient_details.weight_kg} kg` : 'Not provided'}</dd></div>
                <div><dt>Blood group</dt><dd>{caseData.patient_details.blood_group || 'Not provided'}</dd></div>
                <div><dt>Conditions provided</dt><dd>{caseData.patient_details.medical_conditions?.join(', ') || 'None provided'}</dd></div>
                <div><dt>Admission date · user entered</dt><dd>{caseData.patient_details.additional_details?.admission_date || 'Not provided'}</dd></div>
                <div><dt>Discharge date · user entered</dt><dd>{caseData.patient_details.additional_details?.discharge_date || 'Not provided'}</dd></div>
              </dl>
              <button type="button" className="secondary-button" onClick={() => { setCaseData(null); setPolicyData(null); setSelectedId(''); setPatient(EMPTY_PATIENT); }}>Register another case</button>
            </div>
          ) : (
            <form className="case-form" onSubmit={handleCreateCase}>
              <label>Patient name<input required maxLength={120} value={patient.patient_name} onChange={(e) => setPatient({ ...patient, patient_name: e.target.value })} autoComplete="name" /></label>
              <label>Age (optional)<input type="number" min="0" max="120" value={patient.age} onChange={(e) => setPatient({ ...patient, age: e.target.value })} /></label>
              <label>Weight in kg (optional)<input type="number" min="1" max="500" step="0.1" value={patient.weight_kg} onChange={(e) => setPatient({ ...patient, weight_kg: e.target.value })} /></label>
              <label>Blood group (optional)<input maxLength={8} value={patient.blood_group} onChange={(e) => setPatient({ ...patient, blood_group: e.target.value })} placeholder="e.g. O+" /></label>
              <label className="wide-field">Known conditions the patient chooses to share<textarea rows="3" value={patient.medical_conditions} onChange={(e) => setPatient({ ...patient, medical_conditions: e.target.value })} placeholder="Optional. Separate items with commas." /></label>
              <label>Admission date (optional)<input type="date" value={patient.admission_date} onChange={(e) => setPatient({ ...patient, admission_date: e.target.value })} /></label>
              <label>Discharge date (optional)<input type="date" value={patient.discharge_date} onChange={(e) => setPatient({ ...patient, discharge_date: e.target.value })} /></label>
              <p className="wide-field muted-copy">No smoking/lifestyle answer is assumed. The policy wording and your chosen workflow determine whether extra questions are relevant.</p>
              <button className="primary-button wide-field" type="submit" disabled={busy}>Save case locally</button>
            </form>
          )}
        </section>
      )}

      {step === 'policy' && caseData && (
        <section className="card workflow-panel">
          <div className="eyebrow">STEP 2 · POLICY SOURCE</div>
          <h2>Upload the policy schedule and wording</h2>
          <p>Text-based PDF, up to 20 MB. It is indexed page by page and linked to this case. Scanned PDFs need OCR and will be rejected if no text can be read.</p>
          <label className="file-action">{policyDocument ? 'Replace policy PDF' : 'Choose policy PDF'}
            <input type="file" accept="application/pdf,.pdf" onChange={(event) => handleUpload(event, 'policy')} disabled={busy} />
          </label>
          {policyDocument && <p className="muted-copy">Current: {policyDocument.filename}. Uploading the same PDF again reuses its indexed policy record.</p>}
        </section>
      )}

      {step === 'documents' && caseData && (
        <section className="card workflow-panel">
          <div className="eyebrow">STEP 3 · SUPPORTING EVIDENCE</div>
          <h2>Keep medical documents with this case</h2>
          <p>A blood report is optional. For hospitalization, bills, prescriptions, diagnostic reports, and a discharge summary can support a readiness review. Files are saved locally; medical-result interpretation is not enabled yet.</p>
          <div className="upload-row">
            <label>Document type<select value={category} onChange={(event) => setCategory(event.target.value)}>
              <option value="lab_report">Lab / blood report</option>
              <option value="discharge_summary">Discharge summary</option>
              <option value="bill">Hospital bill</option>
              <option value="prescription">Prescription</option>
              <option value="other">Other document</option>
            </select></label>
            <label className="file-action">Add document<input type="file" accept="application/pdf,image/jpeg,image/png,.pdf,.jpg,.jpeg,.png" onChange={(event) => handleUpload(event, category)} disabled={busy} /></label>
          </div>
          <DocumentList documents={caseData.documents} caseId={caseData.case_id} />
        </section>
      )}

      {step === 'review' && policyData && policyDocument && (
        <div className="review-grid">
          <div className="review-column">
            <section className="card workflow-panel">
              <div className="eyebrow">POLICY SUMMARY · SOURCE-DERIVED</div>
              <h2>{policyData.insurer || 'Insurer not identified'}</h2>
              <dl className="policy-meta">
                <div><dt>Document</dt><dd>{policyData.filename}</dd></div>
                <div><dt>Pages</dt><dd>{policyData.page_count}</dd></div>
                <div><dt>Imported</dt><dd>{new Date(policyData.imported_at).toLocaleString()}</dd></div>
                <div><dt>Profile facts found</dt><dd>{policyData.profile?.length || 0}</dd></div>
              </dl>
              {modelStatus?.active_backend === 'cloud_gemma' && (
                <label className="consent-line"><input type="checkbox" checked={cloudConsent} onChange={(event) => setCloudConsent(event.target.checked)} />
                  I consent to cloud processing when I request a generated answer or outline. Questions send relevant redacted passages; a full outline sends the redacted text of the entire policy, which may still contain sensitive details.
                </label>
              )}
              {modelStatus?.active_backend === 'cloud_gemma' && (
                <button type="button" className="primary-button" onClick={handleSummary} disabled={!cloudConsent || busy}>
                  Generate cited policy outline
                </button>
              )}
              <p className="muted-copy">Only indexed passages are shown below. A missing topic means it was not found by retrieval, not that the policy has no such term.</p>
              {generatedSummary && <GeneratedSummary result={generatedSummary} />}
            </section>
            <section className="policy-facts" aria-label="Policy evidence topics">
              {policyData.profile?.length ? policyData.profile.map((fact) => (
                <article className="card policy-fact" key={fact.topic}>
                  <div className="fact-heading"><h3>{fact.topic}</h3><span className={fact.status === 'conflict_review' ? 'status-pill pill-review' : 'status-pill pill-pending'}>{fact.status === 'conflict_review' ? 'Verify source' : 'Source found'}</span></div>
                  {fact.pages.map((page, index) => (
                    <div className="source-excerpt" key={`${fact.topic}-${page}-${index}`}>
                      <a href={`${getCaseDocumentUrl(caseData.case_id, policyDocument.document_id)}#page=${page}`} target="_blank" rel="noreferrer">PDF page {page}</a>
                      <p>{fact.evidence[index]}</p>
                    </div>
                  ))}
                </article>
              )) : <div className="card empty-state">No policy passages were retrieved. Review the uploaded PDF manually.</div>}
            </section>
            <section className="card workflow-panel reminder-panel">
              <div className="eyebrow">OPTIONAL REMINDER</div>
              <h3>Set a confirmed follow-up date</h3>
              <p>Enter a deadline you verified in the policy or with the insurer. ClaimGuard does not infer statutory or policy deadlines.</p>
              <label>Confirmed date<input type="date" value={reminderDate} onChange={(event) => saveReminderDate(event.target.value)} /></label>
              <label className="consent-line"><input type="checkbox" checked={reminderConfirmed} onChange={(event) => confirmReminderDate(event.target.checked)} disabled={!reminderDate} /> I verified this date for this case.</label>
              <button type="button" className="secondary-button" disabled={!reminderDate || !reminderConfirmed} onClick={() => downloadCaseReminder(caseData.patient_name, reminderDate)}>
                Download calendar reminder (.ics)
              </button>
            </section>
          </div>

          <section className="card policy-chat">
            <div className="eyebrow">POLICY Q&A</div>
            <h2>Ask about this document</h2>
            <p className="muted-copy">Answers use retrieved clauses and show their PDF pages. They are not a coverage decision.</p>
            {modelStatus?.active_backend === 'cloud_gemma' && <p className="runtime-note">Cloud processing runs only while consent is enabled above.</p>}
            {modelStatus?.active_backend !== 'cloud_gemma' && <p className="runtime-note">No cloud model is active. This workspace will return relevant source text without generated answers unless a local model is selected.</p>}
            <div className="chat-log" aria-live="polite">
              {messages.map((message, index) => (
                <article className={`chat-message ${message.role}`} key={`${message.role}-${index}`}>
                  <strong>{message.role === 'user' ? 'You' : (message.model_used || 'Source retrieval')}</strong>
                  <p>{message.text || message.answer}</p>
                  {message.citations?.map((citation) => <details key={`${index}-${citation.page}`}><summary>PDF page {citation.page}</summary><p>{citation.excerpt}</p></details>)}
                </article>
              ))}
            </div>
            <form className="chat-form" onSubmit={handleQuestion}>
              <input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about a clause, limit, date, or member" aria-label="Question about policy" />
              <button type="submit" className="primary-button" disabled={busy || !question.trim()}>Ask</button>
            </form>
          </section>
        </div>
      )}
    </section>
  );
}

function GeneratedSummary({ result }) {
  if (!result.summary) return <p className="runtime-note">{result.detail || 'No generated summary returned.'}</p>;
  const sourceMap = new Map((result.sources || []).map((item) => [item.page, item.text]));
  const items = Object.entries(result.summary).flatMap(([group, value]) => {
    if (!value) return [];
    const facts = Array.isArray(value) ? value : [value];
    return facts.filter((fact) => fact?.fact).map((fact, index) => ({ group, index, ...fact }));
  });
  return (
    <div className="generated-summary">
      <h3>Model outline · {result.model_used}</h3>
      {items.map((item) => (
        <article key={`${item.group}-${item.index}-${item.fact}`}>
          <strong>{item.group.replaceAll('_', ' ')}</strong>
          <p>{item.fact}</p>
          {item.pages.map((page) => <details key={page}><summary>PDF page {page}</summary><p>{sourceMap.get(page) || 'Source text unavailable.'}</p></details>)}
          {item.uncertainty && <small>Needs verification: {item.uncertainty}</small>}
        </article>
      ))}
      <p className="muted-copy">AI-extracted outline; verify every item against the cited policy wording and active schedule.</p>
    </div>
  );
}

function downloadCaseReminder(patientName, date) {
  const start = date.replaceAll('-', '');
  const [year, month, day] = date.split('-').map(Number);
  const nextDay = new Date(Date.UTC(year, month - 1, day + 1));
  const end = nextDay.toISOString().slice(0, 10).replaceAll('-', '');
  const escapeIcs = (value) => value.replaceAll('\\', '\\\\').replaceAll(';', '\\;').replaceAll(',', '\\,').replaceAll('\n', '\\n');
  const content = [
    'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//ClaimGuard//Case Reminder//EN', 'CALSCALE:GREGORIAN',
    'BEGIN:VEVENT', `UID:${crypto.randomUUID()}@claimguard.local`, `DTSTAMP:${new Date().toISOString().replaceAll('-', '').replaceAll(':', '').replace(/\.\d{3}/, '')}`,
    `DTSTART;VALUE=DATE:${start}`, `DTEND;VALUE=DATE:${end}`,
    `SUMMARY:${escapeIcs(`Claim follow-up: ${patientName}`)}`,
    `DESCRIPTION:${escapeIcs('User-confirmed reminder date. Verify the applicable policy and insurer requirements; this is not a coverage decision.')}`,
    'END:VEVENT', 'END:VCALENDAR', '',
  ].join('\r\n');
  const url = URL.createObjectURL(new Blob([content], { type: 'text/calendar;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'claimguard-case-reminder.ics';
  link.click();
  URL.revokeObjectURL(url);
}

function DocumentList({ documents = [], caseId }) {
  if (!documents.length) return <p className="muted-copy">No supporting documents added to this case.</p>;
  return (
    <ul className="document-list">
      {documents.map((document) => (
        <li key={document.document_id}>
          <span><strong>{document.filename}</strong><small>{document.category.replaceAll('_', ' ')} · {(document.size_bytes / 1024).toFixed(0)} KB</small></span>
          <a href={getCaseDocumentUrl(caseId, document.document_id)} target="_blank" rel="noreferrer">Open</a>
        </li>
      ))}
    </ul>
  );
}
