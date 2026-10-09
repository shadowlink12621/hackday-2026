const API_ORIGIN = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '');
const API = `${API_ORIGIN}/api`;

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, options);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = body.detail || body.message || message;
    } catch {
      // Keep the HTTP status message when the server response is not JSON.
    }
    throw new Error(message);
  }
  return response;
}

export async function processDocument(file, domainMode) {
  const healthMode = domainMode === 'health_insurance';
  const form = new FormData();
  form.append('file', file);
  form.append('domain_mode', domainMode);
  form.append('prompt', healthMode
    ? 'Extract the Indian health insurance claim details, itemized amounts, patient and provider information, and relevant dates. Return the requested structured claim data.'
    : 'Extract the corporate expense receipt details, itemized amounts, employee and merchant information, and relevant dates. Return the requested structured claim data.');
  form.append('rule_settings', '{}');
  const response = await request('/validate', { method: 'POST', body: form });
  return response.json();
}

export async function getHealth() {
  const response = await request('/health');
  return response.json();
}

export async function getClaims() {
  const response = await request('/claims');
  return response.json();
}

export async function saveDecision(claimId, decision) {
  const response = await request(`/claims/${encodeURIComponent(claimId)}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision }),
  });
  return response.json();
}

export async function getAuditCsv() {
  const response = await request('/export.csv');
  return response.blob();
}

export async function sendChat(claimId, question) {
  const response = await request('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ claim_id: claimId, question }),
  });
  return response.json();
}

export async function checkScamMessage(messageText) {
  const response = await request('/scamcheck', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message_text: messageText }),
  });
  return response.json();
}

export async function getInsurers() {
  const response = await request('/insurers');
  return response.json();
}

export async function getInsurerDetails(insurerKey) {
  const response = await request(`/insurers/${encodeURIComponent(insurerKey)}`);
  return response.json();
}

export async function getModelStatus() {
  const response = await request('/model/status');
  return response.json();
}

export function getCalendarIcsUrl(claimId) {
  return `${API}/claims/${encodeURIComponent(claimId)}/calendar.ics`;
}
