# Phase 14.1 Continuation Prompt — Test-suite structure and project-RAG separation

Read `AGENTS.md`, the current `markdowns/` handover, `TESTS.md`,
`PHASE14_1_PREPARATION.md`, and this file before moving test files.

Move test modules into `tests/` packages in the planned categories. Preserve
all test names and assertions. Update direct imports to package-qualified
paths. Use `python -m unittest discover -s tests -t . -v` as the new ordinary
suite command; local Ollama and Docker modules remain opt-in or skip-safe.

Keep `tests/fixtures/kotlin-android` as a synthetic validation fixture and do
not introduce real GTA source into Git. Do not alter production code, live
RAG, project data, Docker, Gradle, dependencies, policy, or model routing.

## Completion — 2026-09-21

This structural migration is complete. Do not resume it by moving tests back
to the root or by adding compatibility wrappers. Use the package-qualified
commands in `AGENTS.md` and `TESTS.md` for any future focused test run.
