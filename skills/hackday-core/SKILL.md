---
name: hackday-core
description: Agent skill for validating inputs using Gemma 4 perception and a deterministic engine.
version: 1.0.0
---

# Hack Day Core (Agent Skill)

## Intent
This skill allows agents to send prompts, optional image data, and rule constraints to the validation engine. It uses Gemma 4 for initial extraction (perception) and a local Python engine to enforce deterministic rules based on the provided settings.

## Setup Instructions
1. Install Python dependencies: `pip install -r backend/requirements.txt`.
2. Export your Gemini API key: `export GEMINI_API_KEY="your_key"`.
3. Run the validation engine: `uvicorn backend.main:app --reload`.

## Usage
Agents can invoke this skill by sending a `POST` request to `/api/process` with a prompt, optional file, domain mode, and JSON string of rule settings. The response provides a unified JSON containing metadata, perception, and deterministic verification results.
