# Phase 14 Preparation — Explicit document ingestion and isolated long-term RAG

## Status

Completed on 2026-09-21.

## Source and current-state reconciliation

The authoritative motivation is item 14 in `mini_agent_sandbox_analysis.md`:
the historical legacy `user_<id>_local_nomic` collection has an append helper
but no explicit, auditable ingestion route in the main loop. That finding is
still relevant for user-supplied documents, but its described two-collection
layout is no longer the complete current architecture.

Phases 9 and 10 already established separate persistent scopes:

```text
registered project snapshot -> project-code RAG (GTA evidence)
three approved books        -> global-library RAG (technical reference only)
verified project card       -> project-knowledge RAG (human-verified only)
session state               -> temporary conversation memory
project_facts.json          -> structured facts, not vector memory
legacy user collection      -> existing compatibility store; no new automatic ingestion
```

Phase 14 must preserve those boundaries. It is not a rebuild of Phase 9 and
does not re-index the 393 GTA code chunks or 2,293 global-book chunks.

## Objective

Introduce a small, explicit ingestion contract for **user-supplied,
project-bound supplemental documents** while keeping every memory class
separate:

```text
Facts        structured, evidence/policy-gated state
Conversation session-only state, removable by reset
Project code snapshot-derived project-code RAG
User docs    explicit project-supplemental-document RAG
Knowledge    verified project knowledge cards
Books        separately labelled global technical reference RAG
```

The proposed supplemental collection must be distinct from both project code
and verified knowledge. A user document never becomes a GTA project fact just
because it is retrievable.

## Proposed bounded implementation

1. Audit the legacy `add_document_chunks()` call sites and API surface. Record
   whether any active route writes to `user_<id>_local_nomic`; do not populate,
   migrate, or delete it during the audit.
2. Define a project-bound ingestion request with explicit `project_id`, source
   label, content type, SHA-256, size/chunk limits, and user confirmation. A
   request without a registered project must be refused; no implicit fallback
   to the legacy per-user collection.
3. Store accepted supplemental documents in a dedicated collection under that
   project's existing RAG directory, with deterministic document/chunk IDs and
   metadata including `scope=project-document`, source, checksum, and status.
   It must never share the `project_*_code` or `project_*_knowledge` collection.
4. Add a deterministic replacement/removal policy by explicit source/checksum
   so retries do not duplicate chunks and a failed embedding leaves no falsely
   successful ingestion record. Keep a bounded manifest/audit record without
   document body duplication.
5. Extend project retrieval only after ingestion isolation is tested. Return
   supplemental hits with their own scope/trust label, ordered after
   snapshot/project-code evidence and before optional global technical
   reference only when relevant. Project facts may be established only from
   project-code evidence under the existing policy.
6. Keep the existing Phase 10 knowledge-card flow unchanged: LLM answers,
   conversations, retrieved book passages, and supplemental documents cannot
   auto-create, verify, or index knowledge cards. A future promotion rule is a
   separate phase and requires explicit human review.

## Acceptance evidence

- Temporary-directory tests prove project A's documents cannot be listed,
  retrieved, overwritten, or deleted through project B or a legacy user route.
- Tests prove duplicate retry is idempotent; changed content replaces only its
  own source; malformed metadata, oversized input, unknown project, and failed
  embedding fail closed without misleading manifest state.
- Retrieval tests show source/scope/trust labels and prove global books cannot
  satisfy a project-fact evidence requirement.
- Existing Phase 9 retrieval, Phase 10 knowledge-card, and session-reset tests
  continue to pass. A real Ollama/Chroma run is opt-in only and uses a temporary
  project fixture, never live GTA data.

## Hard boundaries

- Do not ingest conversations, model answers, `project_facts.json`, vaults,
  telemetry, saved tasks, or arbitrary workspace files.
- Do not auto-train, fine-tune, or treat RAG indexing as model training.
- Do not mix supplemental docs with GTA project-code, verified knowledge,
  global books, or another project's documents in collection, ranking, or
  citation output.
- Do not re-index, migrate, delete, or inspect full contents of live GTA/global
  collections as part of this phase. Do not change their embedding model,
  dimensions, paths, or existing chunk IDs.
- Do not modify connected Android source, run Gradle/Docker, change provider,
  model, role, approval, validation, or fact policy.
- Do not enable opaque background ingestion. Every write must be an explicit,
  attributable user action with bounded input and a visible outcome.

## Expected blockers and decisions

1. **No safe source/ownership contract for uploaded files.** Keep the phase at
   audit/design only; do not expose a generic path-based upload API.
2. **Ollama embedding unavailable.** Deterministic validation can run, but a
   true Chroma acceptance run is blocked. Do not queue partial live ingestion
   or retry indefinitely.
3. **A desired input exceeds agreed size/type limits.** Refuse it and request a
   smaller explicit document; do not silently split an arbitrary disk tree.
4. **Need to preserve legacy user-RAG content.** Inventory it read-only first.
   Migration or deletion requires a separately approved, reversible plan and
   cannot be combined with this phase.

## Completion condition

Phase 14 is complete only when supplemental project-document ingestion has an
explicit, isolated, idempotent and tested path, and the original Phase 9/10
trust boundaries remain intact. Otherwise record the observed blocker and
leave live collections unchanged.

## Completion record

- Added `project_document_ingestion.py`: explicit request-body ingestion for a
  registered project only, bounded text/Markdown input, source validation,
  SHA-256, deterministic chunk IDs, idempotent retry, metadata-only manifest,
  and explicit removal. It never reads a supplied disk path.
- Added a distinct `project_*_documents` Chroma collection. It is queried only
  as `scope=project-document` / `trust=user supplied project document`, after
  snapshot/code and verified knowledge; it cannot satisfy the existing
  project-code evidence gate used for fact/knowledge proposals.
- Added metadata-only API endpoints: `GET`/`POST`/`DELETE`
  `/projects/{project_id}/documents`. Ingestion/removal require `confirmed`.
- Temporary-fixture tests cover idempotency, replacement, project isolation,
  legacy/unknown-project refusal, path-shaped source refusal, explicit
  confirmation, pending-cleanup on embedding failure, retrieval labels, and
  request-body-only API behavior.
- Verification: focused suite 26/26 passed; focused Ruff passed. Full suite
  passed 185/185 with 19 expected skips. One real local Ollama/Chroma run on a
  new isolated fixture indexed one document and retrieved only
  `project-document / owner-notes.md`; the fixture was then deleted. No GTA,
  global-library, live knowledge, or connected source data changed.
