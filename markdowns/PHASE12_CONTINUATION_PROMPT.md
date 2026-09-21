# Phase 12 Continuation Prompt — Deterministic session lifecycle

```text
Working directory:
C:\Users\AlSaintUk\Desktop\Mini Agent Sandbox

You are starting Phase 12. Phases 9, 10, and 11 are complete. Read before
changing:
1. AGENTS.md
2. CODEX_HANDOVER.md
3. README.md
4. NEXT_STEPS_PLAN.md
5. PROJECT_EVOLUTION_ROADMAP.md
6. TESTS.md
7. PHASE12_PREPARATION.md
8. mini_agent_sandbox_analysis.md
9. this file

Objective
---------
Establish a narrow, deterministic lifecycle for per-user session state:
explicit new session, fail-closed resume of an interrupted valid state, and an
explicit narrowly scoped reset that cannot leave an accidental resumable task.

First task
----------
Inspect the existing state schema and the `run_agent_loop`,
`_load_resumable_state`, and clear/reset paths. Record the allowed transitions
and add focused temporary-directory tests before changing the state mutation.

Hard boundaries
---------------
- Do not enable LLM summarisation, retrieval ingestion, or learning from
  conversation memory.
- Do not touch RAG, project facts, knowledge cards, snapshots, ledger evidence,
  live GTA data, connected Android source, vaults, providers, models, Docker,
  Gradle, dependency manifests, or codegen/review/approval/validation policy.
- Do not run Ollama, broad suites, Docker, Gradle, or destructive cleanup.
- Never use `purge_user_data` for reset. Reset may affect only the selected
  user's session state and must be covered with a regression test.
- For unknown or malformed persisted state, refuse resume; do not guess or
  silently repair it.

Completion
----------
Completion record — 2026-09-21
-------------------------------
- `--reset` now removes only the selected `state.json`; `--clear` remains a
  deprecated compatibility alias with the same session-only semantics.
- New-session construction is explicit and resume continues to fail closed.
- Temporary-fixture lifecycle tests passed 3/3; existing resume validation
  passed 1/1. No live data or external service was used.
- Ruff passed for `test_session_lifecycle.py`. `runner.py` retains 10
  pre-existing Ruff findings outside this phase's edits.

Phase 12 is complete.
```
