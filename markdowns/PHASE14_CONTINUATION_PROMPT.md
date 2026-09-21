# Phase 14 Continuation Prompt — Explicit document ingestion and isolated long-term RAG

## Status

Completed on 2026-09-21. Retain this file as the scope and safety record.

Read `AGENTS.md`, `CODEX_HANDOVER.md`, `README.md`, `NEXT_STEPS_PLAN.md`,
`PROJECT_EVOLUTION_ROADMAP.md`, `TESTS.md`, `mini_agent_sandbox_analysis.md`,
and `PHASE14_PREPARATION.md` before changing code.

The source objective is historical analysis item 14. Reconcile it with the
current cascade before acting: GTA project-code, verified project knowledge,
and global books already use separate paths and trust labels. The legacy
per-user collection is not permission to feed arbitrary content into the main
loop.

Implement only an explicit, project-bound supplemental-document ingestion path
after a source/ownership contract and temporary-fixture tests exist. Preserve
the class boundary:

```text
facts != session != project-code != project-document != verified knowledge != global library
```

Unknown project, source, metadata, type, size, checksum mismatch, or embedding
failure must fail closed and must not leave a successful-looking manifest.
Keep user documents in their own project collection with deterministic IDs.
Retrieved user documents require their own `project-document` scope/trust
label; they cannot establish project facts or be promoted automatically.

Do not touch live GTA/global RAG, re-index existing corpora, migrate/delete the
legacy user collection, ingest conversations/model answers/facts, train a
model, alter project source, or change providers, roles, policy, Docker,
Gradle, validation or approval flow. Use a real local Ollama/Chroma check only
as an opt-in final acceptance run on a temporary fixture.
