# ClaimGuard Sample Policy UI Profile

This is a redacted UI fixture based on the locally supplied 59-page SBI General Group Mediclaim policy PDF. It contains no policyholder identity, address, contact information, policy/certificate number, or other personal identifier. It is for interface and retrieval acceptance tests, not a coverage decision.

## Safe Display Profile

- Insurer: SBI General Insurance
- Product label: Group Mediclaim Policy; schedule names Arogya Advanced
- Policy period: show only after parsing and user confirmation; do not copy the personal schedule dates into this public fixture.
- Base cover: schedule includes a ₹5,00,000 family-floater entry. Confirm which schedule row applies before presenting it as the user's active benefit.
- Source document: 59 pages; source page numbering matches the printed page labels for the citations below.
- Review status: “Illustrative extraction; verify with the active schedule and complete policy wording.”

## Eye Treatment Findings

### Cataract

- Finding: the Customer Information Sheet lists a 12-month specific waiting period for cataract, with an accident exception noted in the wording.
- Citation: printed page 9.
- UI state: “Waiting period found” with a link to page 9.
- Do not display a fixed cataract payout. The reviewed schedule/CIS text does not establish a single cataract-specific payout amount.

### Refractive Error

- Finding: refractive error is listed as an exclusion on printed page 4. Detailed wording on printed page 35 describes exclusion for eyesight correction due to refractive error below 7.5 dioptres.
- Citations: printed pages 4 and 35.
- UI state: “Exclusion wording found; check exact treatment and policy version.”
- Do not generalize this to every eye procedure or to all insurer products.

### OPD and Optical Items

- Finding: one schedule entry lists OPD cover of ₹3,000 per family on printed page 3.
- Finding: wording on printed page 25 says lenses, including contact lenses, are excluded in the relevant benefit context.
- Citations: printed pages 3 and 25.
- UI state: “Limit found; optical expense eligibility needs clause-level review.”
- Do not imply the ₹3,000 OPD amount pays for every eye test, frame, or lens.

### Room Rent

- Finding: printed page 3 contains both a room-rent limit entry and a “no room rent capping” entry in different schedule blocks.
- Citation: printed page 3.
- UI state: “Conflicting schedule text; verify the applicable plan/schedule before calculation.”
- Do not choose a cap or advertise an automatic proportional deduction from this extracted text alone.

## UI Card Fixture

```json
{
  "policy_label": "SBI General Group Mediclaim - redacted sample",
  "source_pages": 59,
  "review_state": "illustrative_verify_source",
  "facts": [
    {"topic": "Cataract", "summary": "12-month specific waiting period is listed.", "pages": [9], "status": "source_found"},
    {"topic": "Refractive error", "summary": "Exclusion listed; detailed text refers to correction below 7.5 dioptres.", "pages": [4, 35], "status": "source_found"},
    {"topic": "OPD / optical", "summary": "Schedule lists ₹3,000 per family; lens wording needs contextual review.", "pages": [3, 25], "status": "verify_scope"},
    {"topic": "Room rent", "summary": "Schedule entries conflict; do not infer a limit.", "pages": [3], "status": "conflict_review"}
  ]
}
```

All patient names, dates, bills, chat prompts, and reminder dates shown in screenshots or test data must be fictional. Never take identifiers from the source PDF.

## Chat Test Cases

1. Question: “What does the wording say about cataract?” Expected: mention the 12-month specific waiting period and cite page 9; state that this alone does not establish coverage or payout.
2. Question: “Is eyesight correction covered?” Expected: summarize the refractive-error exclusion and cite pages 4 and 35; do not apply it to unrelated ophthalmic procedures.
3. Question: “What is the room-rent cap?” Expected: say that the schedule text is contradictory and cite page 3; request visual/user confirmation instead of selecting a number.
4. Question: “Will this hospital pay my entire eye bill?” Expected: say the indexed wording does not establish a guaranteed payout; ask for procedure, active schedule and claim facts.
5. Unrelated question with no matching clause: expected “not found in the indexed excerpts,” with no invented answer.

## Acceptance Checks for the UI

- Every coverage card displays one or more printed page references.
- Clicking a page reference opens the PDF at that page when the browser supports it, otherwise it displays the excerpt.
- Conflicting and unconfirmed content uses a review label, never a green coverage guarantee.
- The UI distinguishes a source fact from an AI explanation and labels demo/sample data.
- Local-only mode remains useful without network access and says when no model generated the answer.
