# Phase 14.1 Preparation — Test-suite structure and project-RAG separation

## Objective

Move root-level Python tests into a discoverable `tests/` package without
mixing Mini Agent Sandbox tests with registered-project RAG contracts. This is
a structural-only phase: it must preserve test behaviour, fixtures, and the
read-only boundary around the connected GTA project.

## Target layout

```text
tests/
  sandbox/       API, core orchestration, policy, storage and validation tests
  project_rag/   generic registered-project snapshot/RAG/knowledge contracts
  integration/   explicitly opt-in local-Ollama and Docker tests
  fixtures/      synthetic Kotlin/Android fixture only; not GTA source
```

`project_rag` does not contain a copy of GTA Cheats. It tests generic project
isolation with temporary fixtures and read-only stored-profile contracts. Real
GTA acceptance stays an explicitly documented opt-in operation outside Git.

## Plan

1. Create package markers and move every root `test_*.py` using Git-aware
   renames; do not duplicate compatibility wrappers in the project root.
2. Repair only direct test-to-test imports and documented current commands.
3. Update `AGENTS.md`, `markdowns/TESTS.md`, `markdowns/README.md`, handover
   and next-steps records to use module paths and discovery from `tests`.
4. Run focused import/discovery checks after migration, then full deterministic
   suite. Do not run opt-in Ollama/Docker tests merely because they moved.
5. Keep `tests/fixtures/kotlin-android` intact. Do not read, copy, build or
   alter connected GTA source, live RAG collections, facts, knowledge or state.

## Acceptance

- `python -m unittest discover -s tests -t . -v` discovers the same ordinary
  deterministic suite without root test files.
- The documentation transition module still imports shared fixtures correctly.
- Local-Ollama and Docker modules remain opt-in/skip-safe.
- Git records renames rather than duplicated test logic; no generated data or
  project source enters the repository.

## Boundaries

- Do not change production behaviour, RAG retrieval, prompt/model policy,
  dependency manifests, Docker configuration, or validation semantics.
- Do not invent a GTA test corpus. A generic fixture must never be labelled
  GTA, and a real GTA profile must never be committed.
- Do not delete tests as a way to make discovery pass.

## Completion record — 2026-09-21

All 38 root-level `test_*.py` modules were moved with Git-aware renames into
the declared packages. The only repairs were package-qualified test imports and
one repository-root calculation used by manifest tests; no assertion or
production behaviour changed. `tests/fixtures/kotlin-android` remains the
existing synthetic fixture and no GTA source, snapshot, RAG store, model cache
or runtime data entered `tests/`.

`python -m unittest discover -s tests -t . -v` passed: 181 tests with 19
expected environment/opt-in skips. `python -m ruff check tests` passed. Docker
and local-Ollama integration tests were not activated for this structural
phase.
