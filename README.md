# DocuGuard (Agent Skill)
**Hacktoberfest Hack Day Bengaluru × IEEE CIS (October 9, 2026)**

DocuGuard is an open-source visual accessibility and document validation engine. It uses **Gemma 4** for multimodal form extraction (perception) and a **deterministic rules engine** to validate those findings mathematically (logic).

This project targets two prize categories simultaneously:
1. **Best Use of Gemma 4:** Uses Gemma 4 Multimodal for high-accuracy document parsing.
2. **Best Open-Source AI Project:** Built as a compliant **Agent Skill** following the [Agent Skills open standard](https://agentskills.io/specification).

## Architecture
- **Perception (AI):** Gemma 4 extracts fields, signatures, and stamps from raw images/PDFs into a strict JSON schema.
- **Verification (Deterministic):** A standalone Python engine mathematically verifies the AI's output against strict local rules (e.g. "date must be valid", "signature must be present") to prevent hallucination.

## Setup
*(Instructions to run the frontend and backend will go here)*

## License
Apache 2.0
