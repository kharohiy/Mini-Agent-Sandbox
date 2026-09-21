# Phase 11 Continuation Prompt — Reproducible dependency manifests

```text
Working directory:
C:\Users\AlSaintUk\Desktop\Mini Agent Sandbox

You are starting Phase 11. Phases 9 and 10 are complete. Read before changing:
1. AGENTS.md
2. CODEX_HANDOVER.md
3. README.md
4. NEXT_STEPS_PLAN.md
5. PROJECT_EVOLUTION_ROADMAP.md
6. TESTS.md
7. PHASE11_PREPARATION.md
8. mini_agent_sandbox_analysis.md
9. this file

Objective
---------
Create reproducible dependency manifests for runtime, optional PDF ingestion,
and development/test tooling. Preserve a compatible runtime installation entry
point. Every declared package must correspond to a direct import or documented
tool contract.

First task
----------
Audit direct third-party imports and installed versions without installing or
upgrading anything. Define the smallest requirements-file layout, add focused
manifest tests, and update documentation with observed package ownership.

Hard boundaries
---------------
- Do not install, upgrade, download, remove, or lock packages.
- Do not alter Python runtime behavior, models, provider policy, Chroma data,
  Android source, Docker, Gradle, vaults, or saved state.
- Do not use an LLM-proposed dependency without a direct-import or documented
  contract.
- Do not run broad suites or network-dependent installation checks.

Completion
----------
Phase 11 completes when manifests account for direct imports and focused tests
pass. A clean-environment install is a separately authorized external action.

Completion record — 2026-09-20
-------------------------------
- Runtime, ingestion, and development manifests now have distinct ownership.
- `requirements.txt` remains the compatible default entry point.
- Versions were pinned to the observed working environment; no package state
  was changed.
- Ruff and `test_dependency_manifests` passed 3/3.

Fresh-clone acceptance record — 2026-09-21
------------------------------------------
- A separate `E:` clone reached `3f7027f`; Python 3.11.9 installed the default
  and optional-ingestion manifests with Pip caching disabled.
- `pip check`, runtime imports, the full suite (166 tests; 17 expected skips),
  and the two ingestion tests passed.
- No Ollama, Chroma persistent store, PDF/RAG ingestion, or GTA source action
  occurred; generated test registry state was removed.

Phase 11 and its fresh-clone acceptance are complete.
```
