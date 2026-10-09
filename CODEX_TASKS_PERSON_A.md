# Codex Tasks for Person A (Backend & AI Parallel Stream)

Here are the 2 tasks you can run immediately on Codex to work in parallel on Person A's backend stream.
For each task, the exact model to select is listed to maximize intelligence while conserving credits!

---

## TASK 1: Insurer Knowledge Corpus Integrity Validator
- **Recommended Model:** `5.6 Luna` (Strong Python scripting & domain understanding, highly credit-efficient)
- **Branch:** `feat/core-ai`
- **Target File:** `backend/scripts/validate_insurer_knowledge.py`

### Prompt to copy into Codex:

```text
Role: Senior Backend Engineer on ClaimGuard.
Task: Create an automated integrity validator for the local insurer knowledge base.
File: `backend/scripts/validate_insurer_knowledge.py`
Branch: `feat/core-ai`

OBJECTIVE:
Write an idempotent Python script `backend/scripts/validate_insurer_knowledge.py` that checks the health and completeness of all insurer policy files in `backend/knowledge/`.

REQUIREMENTS:
1. Scan `backend/knowledge/*.md`.
2. For each insurer markdown file, verify:
   - File exists and is non-empty (> 500 bytes).
   - Contains Section 1: Plan Overview.
   - Contains Section 2: Key Sub-limits & Mandatory Policy Conditions.
   - Contains Section 3: Real-World Claim Repudiation Traps (at least 3 actionable traps).
   - Contains Section 4: Statutory IRDAI Grievance Escalation with reference to Bima Bharosa.
3. Test fuzzy matching using `get_insurer_knowledge(query)` from `backend.knowledge_loader`:
   - Test queries: "hdfc", "star", "bupa", "care", "icici", "sbi".
4. Print a clean, formatted terminal summary table with emoji indicators (✅ Passed / ❌ Failed).
5. Exit with code 0 if all 6 insurers pass; exit with code 1 if any insurer file is missing or invalid.
6. Support `--verbose` CLI flag to print the exact traps parsed for each insurer.

VERIFICATION:
Run: `python backend/scripts/validate_insurer_knowledge.py --verbose`
Verify all 6 insurers pass with code 0.
```

---

## TASK 2: Hybrid AI Benchmark Utility (Cloud Gemma vs Local Ollama vs Mock)
- **Recommended Model:** `5.6 Terra` (Fastest, ultra-low credit cost, ideal for benchmark & test harnesses)
- **Branch:** `feat/core-ai`
- **Target File:** `backend/scripts/benchmark_gemma.py`

### Prompt to copy into Codex:

```text
Role: Senior Backend & AI Engineer on ClaimGuard.
Task: Build a multi-tier benchmark utility for the AI extraction engine.
File: `backend/scripts/benchmark_gemma.py`
Branch: `feat/core-ai`

OBJECTIVE:
Create a standalone CLI benchmarking tool `backend/scripts/benchmark_gemma.py` that evaluates the latency, connectivity, and response schema adherence of:
1. Google Cloud Gemma 4 (via `GEMINI_API_KEY`)
2. Local Ollama Gemma (via `http://localhost:11434`)
3. Deterministic Offline Mock Fallback

REQUIREMENTS:
1. Read runtime status using `get_model_status()` from `backend.gemma_client`.
2. Generate a synthetic test document payload (synthetic health bill bytes).
3. Test `extract_form_data()` under:
   - Default configured backend
   - Local Ollama backend (`USE_LOCAL_LLM=1`)
   - Mock fallback (`FORCE_MOCK=1` or empty keys)
4. Record latency in milliseconds and validate that the output adheres to `ClaimExtraction` Pydantic model.
5. Print an ASCII comparison table:
   - Backend Name
   - Connection Status (Online / Offline)
   - Latency (ms)
   - Schema Valid (Yes/No)
   - Confidence Score
6. Add `--runs <N>` CLI option (default: 1) to average latency over multiple iterations.

VERIFICATION:
Run: `python backend/scripts/benchmark_gemma.py`
Verify the script executes cleanly, prints the table, and exits with code 0.
```
