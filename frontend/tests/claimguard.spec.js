import { expect, test } from '@playwright/test';

const expenseResponse = {
  claim_id: 101,
  metadata: {
    model_used: 'cloud_gemma (gemma-4-26b-a4b-it)',
    is_fallback_mock: false,
    latency_ms: 42,
    timestamp: '2026-10-09T10:00:00Z',
    domain: 'expense',
  },
  perception: {
    structured_data: {
      provider_name: 'Cafe Bengaluru',
      patient_or_employee_name: 'Asha Rao',
      date_extracted: '2026-10-09',
      currency: 'INR',
      items: [{ description: 'Team lunch', amount: 850, category: 'meals' }],
      total_extracted: 850,
      confidence_score: 0.98,
    },
    confidence: 0.98,
  },
  validation: {
    is_valid: true,
    final_amount_inr: 850,
    results: [
      { rule_name: 'Duplicate receipt check', passed: true, message: 'Receipt hash is unique.' },
      { rule_name: 'Expense limit', passed: true, message: 'Amount is within the configured limit.' },
    ],
  },
};

const healthResponse = {
  claim_id: 202,
  metadata: {
    model_used: 'cloud_gemma (gemma-4-26b-a4b-it)',
    is_fallback_mock: false,
    latency_ms: 58,
    timestamp: '2026-10-09T10:05:00Z',
    domain: 'health_insurance',
  },
  perception: {
    structured_data: {
      provider_name: 'City Care Hospital',
      patient_or_employee_name: 'Ravi Kumar',
      date_extracted: '2026-10-09',
      currency: 'INR',
      items: [
        { description: 'Room rent', amount: 15000, category: 'room_rent' },
        { description: 'Consultation', amount: 1200, category: 'consultation' },
      ],
      total_extracted: 16200,
      confidence_score: 0.94,
    },
    confidence: 0.94,
  },
  validation: {
    is_valid: false,
    final_amount_inr: 16200,
    results: [
      { rule_name: 'Room Rent Cap', passed: false, message: 'Room rent exceeds standard cap of ₹10,000.' },
      { rule_name: 'Consumables Excluded', passed: true, message: 'No excluded consumables found.' },
    ],
  },
};

async function mockBackend(page, { response } = {}) {
  await page.route('http://localhost:8000/api/health', (route) =>
    route.fulfill({ json: { status: 'ok', service: 'ClaimGuard Validation Engine' } }),
  );
  await page.route('http://localhost:8000/api/claims', (route) => route.fulfill({ json: [] }));
  if (response) {
    await page.route('http://localhost:8000/api/validate', (route) => {
      expect(route.request().postData()).toContain(`name="domain_mode"\r\n\r\n${response.metadata.domain}`);
      return route.fulfill({ json: response });
    });
  }
}

async function uploadClaim(page, domainMode) {
  await page.getByRole('combobox').selectOption(domainMode);
  await page.locator('input[type="file"]').setInputFiles({
    name: domainMode === 'expense' ? 'expense.png' : 'medical-bill.png',
    mimeType: 'image/png',
    buffer: Buffer.from('mock image bytes'),
  });
  await page.getByRole('button', { name: 'Process Claim' }).click();
}

test('analyzes a corporate expense and shows approved validation', async ({ page }) => {
  await mockBackend(page, { response: expenseResponse });
  await page.goto('/');

  await uploadClaim(page, 'expense');

  await expect(page.getByText('SYSTEM APPROVED')).toBeVisible();
  await expect(page.getByText('Cafe Bengaluru')).toBeVisible();
  await expect(page.getByText('Expense limit')).toBeVisible();
  await expect(page.getByText('Team lunch')).toBeVisible();
});

test('flags health insurance when room rent exceeds its cap', async ({ page }) => {
  await mockBackend(page, { response: healthResponse });
  await page.goto('/');

  await uploadClaim(page, 'health_insurance');

  await expect(page.getByText('FLAGGED / MANUAL REVIEW')).toBeVisible();
  await expect(page.getByText('Room Rent Cap')).toBeVisible();
  await expect(page.getByText('Room rent exceeds standard cap of ₹10,000.')).toBeVisible();
});

test('exports the audit CSV as a browser download', async ({ page }) => {
  await mockBackend(page);
  await page.route('http://localhost:8000/api/export.csv', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'text/csv',
      headers: { 'content-disposition': 'attachment; filename=claimguard_audit.csv' },
      body: 'ID,Domain,Total_INR\n101,expense,850\n',
    }),
  );
  await page.goto('/');

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export CSV' }).click();
  const download = await downloadPromise;

  expect(download.suggestedFilename()).toBe('audit_report.csv');
});

test('shows a backend validation error for an oversized upload', async ({ page }) => {
  await mockBackend(page);
  await page.route('http://localhost:8000/api/validate', (route) =>
    route.fulfill({
      status: 400,
      contentType: 'application/json',
      json: { detail: 'File exceeds the 5 MB upload limit.' },
    }),
  );
  await page.goto('/');
  await page.locator('input[type="file"]').setInputFiles({
    name: 'oversized-receipt.png',
    mimeType: 'image/png',
    buffer: Buffer.alloc(6 * 1024 * 1024),
  });

  await page.getByRole('button', { name: 'Process Claim' }).click();

  await expect(page.getByText('Connection Error')).toBeVisible();
  await expect(page.getByText('File exceeds the 5 MB upload limit.')).toBeVisible();
});
