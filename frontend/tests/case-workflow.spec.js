import { expect, test } from '@playwright/test';

test('creates a patient case, links a policy, and asks with source citations', async ({ page }) => {
  let savedCase = null;
  let policyAttached = false;
  await page.route('http://localhost:8000/api/health', (route) => route.fulfill({ json: { status: 'ok', authentication_required: false } }));
  await page.route('http://localhost:8000/api/claims', (route) => route.fulfill({ json: [] }));
  await page.route('http://localhost:8000/api/model/status', (route) => route.fulfill({ json: {
    active_backend: 'cloud_gemma', cloud_gemma_configured: true, cloud_model: 'test-model', local_ollama_online: false,
  } }));
  await page.route('http://localhost:8000/api/model/check', (route) => route.fulfill({ json: { ok: true, model: 'test-model' } }));
  await page.route('http://localhost:8000/api/cases', async (route) => {
    if (route.request().method() === 'POST') {
      const payload = route.request().postDataJSON();
      savedCase = { case_id: 7, patient_name: payload.patient_name, patient_details: payload, documents: [] };
      return route.fulfill({ status: 201, json: savedCase });
    }
    return route.fulfill({ json: savedCase ? [{ case_id: 7, patient_name: savedCase.patient_name }] : [] });
  });
  await page.route('http://localhost:8000/api/cases/7', (route) => route.fulfill({ json: savedCase }));
  await page.route('http://localhost:8000/api/cases/7/reminder', async (route) => {
    savedCase.reminder_date = route.request().postDataJSON().confirmed_date;
    savedCase.reminder_confirmed_at = savedCase.reminder_date ? '2026-10-09T00:00:00Z' : null;
    return route.fulfill({ json: { case_id: 7, confirmed_date: savedCase.reminder_date } });
  });
  await page.route('http://localhost:8000/api/cases/7/documents', async (route) => {
    policyAttached = true;
    savedCase.documents = [{
      document_id: 11, category: 'policy', filename: 'user-policy.pdf', content_type: 'application/pdf',
      size_bytes: 1200, policy_id: 23,
    }];
    return route.fulfill({ status: 201, json: {
      ...savedCase.documents[0],
      policy: {
        policy_id: 23, insurer: 'Example Insurer', filename: 'user-policy.pdf', page_count: 2,
        imported_at: '2026-10-09T00:00:00Z', profile: [{
          topic: 'Waiting period', pages: [2], evidence: ['Example clause from the user-uploaded test document.'], status: 'source_found',
        }],
      },
    } });
  });
  await page.route('http://localhost:8000/api/policies/23', (route) => route.fulfill({ json: {
    policy_id: 23, insurer: 'Example Insurer', filename: 'user-policy.pdf', page_count: 2,
    imported_at: '2026-10-09T00:00:00Z', profile: [{
      topic: 'Waiting period', pages: [2], evidence: ['Example clause from the user-uploaded test document.'], status: 'source_found',
    }],
  } }));
  await page.route('http://localhost:8000/api/policies/23/summary', async (route) => {
    expect(route.request().postDataJSON().allow_cloud_processing).toBe(true);
    return route.fulfill({ json: {
      model_used: 'cloud_gemma (test-model)', detail: null,
      summary: { policy_name: { fact: 'Example Plan', pages: [2], uncertainty: null } },
      sources: [{ page: 2, text: 'Example clause from the user-uploaded test document.' }],
    } });
  });
  await page.route('http://localhost:8000/api/policies/23/chat', async (route) => {
    const body = route.request().postDataJSON();
    expect(body.allow_cloud_processing).toBe(false);
    return route.fulfill({ json: {
      answer: 'The test clause gives a waiting period [page 2].', model_used: 'retrieval_only',
      citations: [{ page: 2, excerpt: 'Example clause from the user-uploaded test document.' }],
    } });
  });

  await page.goto('/');
  await page.getByRole('button', { name: /Patient Cases & Policy/ }).click();
  await expect(page.getByRole('heading', { name: 'Register a patient case' })).toBeVisible();
  await expect(page.getByLabel('Patient name')).toHaveValue('');
  await page.getByLabel('Patient name').fill('Fictional Test Person');
  await page.getByRole('button', { name: 'Save case locally' }).click();
  await expect(page.getByText('Case saved locally. Add the policy document to continue.')).toBeVisible();
  await page.locator('input[type="file"]').setInputFiles({
    name: 'user-policy.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF test'),
  });
  await expect.poll(() => policyAttached).toBe(true);
  await expect(page.getByRole('heading', { name: 'Example Insurer' })).toBeVisible();
  await expect(page.getByText('Example clause from the user-uploaded test document.')).toBeVisible();
  await page.getByRole('button', { name: 'Test AI connection' }).click();
  await expect(page.getByText('Connected · test-model')).toBeVisible();
  const summaryButton = page.getByRole('button', { name: 'Generate cited policy outline' });
  await expect(summaryButton).toBeDisabled();
  const consent = page.getByLabel(/I consent to cloud processing/);
  await consent.check();
  await summaryButton.click();
  await expect(page.getByText('Example Plan')).toBeVisible();
  await page.getByLabel('Confirmed date').fill('2027-01-15');
  await page.getByLabel('I verified this date for this case.').check();
  const reminderDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download calendar reminder (.ics)' }).click();
  expect((await reminderDownload).suggestedFilename()).toBe('claimguard-case-reminder.ics');
  await consent.uncheck();
  await page.getByRole('textbox', { name: 'Question about policy' }).fill('What is the waiting period?');
  await page.getByRole('button', { name: 'Ask' }).click();
  await expect(page.getByText('The test clause gives a waiting period [page 2].')).toBeVisible();
  await expect(page.locator('summary', { hasText: 'PDF page 2' }).first()).toBeVisible();
});
