# Phase 15 Continuation Prompt — Secret/PII detection and prompt-injection separation

Read `PHASE15_PREPARATION.md`, `TESTS.md`, `CODEX_HANDOVER.md`, and item 15
of `mini_agent_sandbox_analysis.md` before changes.

Implement only the standard-library deterministic SecretScanner and the
separate compatibility prompt-injection boundary described in the preparation
file. Preserve `DataGuardrail.run()` and vault token persistence. Add focused
tests before changing call sites. Never log a plaintext match, never make
entropy alone sufficient, and do not claim complete prompt-injection defence.

No dependency install/download, live model/evals run, RAG ingestion, GTA
access, Docker/Gradle activity, vault-path change, generic secret resolution,
or role/policy/orchestration modification is authorised.

## Completion — 2026-09-22

This phase is complete. Retain the provider-first overlap rule and the
requirement that entropy has credential context. Do not expand provider
patterns or add an external scanner without a separately reviewed scope and
dependency decision.
