# Task — Project Catalog and Project-Bound Q&A

## Status

Implemented locally on 2026-10-01; this is not a numbered phase. The live
registry was migrated backup-first, and GTA catalog metadata was populated from
user-provided values. Repository network access and remote clone/fetch remain
out of scope.

## Goal

Make project selection and read-only Q&A a maintainable, auditable workflow:

- Runner lists real registered projects in a readable format, with stored
  project name, description, source type/location, and project-RAG status.
- The selected project's own snapshot and RAG are the only project evidence
  used for its question; no legacy user-RAG fallback or substituted project.
- Q&A retrieval and Analyst → Reviewer logic live in one service, separate
  from the general code-task orchestration.
- The answer either cites retrieved project evidence or clearly refuses when
  evidence is missing, stale, cross-project, or unusable.
- Local/cloud model routing is explicit and follows the existing router and
  project provider policy; it does not silently change general agent routing.

## Proposed catalog and RAG boundary

- Keep `data/registry/projects.sqlite` as the single operational source of
  truth. Do not add a competing editable JSON catalog. JSON may be considered
  later for import/export only, with explicit conflict rules.
- Preserve current project IDs, source paths, snapshots, RAG collections, runs,
  and evidence. Add metadata with a backward-compatible migration.
- Store name, description, local checkout path, and optional repository URL
  separately; the repository URL is not required. Store source kind and—where applicable—
  configured ref and resolved revision. Existing local projects retain their
  current paths and IDs.
- Keep project RAG in application-owned per-project state (currently
  `data/projects/<project-id>/rag`), outside connected source checkouts. Tie
  the indexed corpus to an identifiable project snapshot/revision.
- Phase/task scope covers local registered projects and a remote-ready catalog
  schema only. Remote clone/fetch/update and network access are deferred to a
  separately approved task. A remote URL alone is not query-ready evidence.

## Plan of execution

1. **Read-only audit:** inspect registry consumers, schema assumptions, source
   snapshot and revision metadata, RAG metadata, and all Q&A callers. Record
   current schema and project counts without opening connected source files.
2. **Data contract:** finalize catalog fields, local/remote source semantics,
   stable project ID behavior, RAG-to-snapshot identity, stale-index behavior,
   and whether Q&A settings belong in `roles.json` or a dedicated config.
3. **Migration design:** add a backward-compatible migration and test it on a
   temporary copy of the old schema. Prove IDs, records, and derived project
   state paths remain unchanged. Live DB migration requires a separate
   backup-first approval.
4. **Service extraction:** move project retrieval, evidence preparation,
   Analyst/Reviewer calls, and result validation into one Q&A service. Keep
   Runner responsible for interactive selection and readable rendering;
   preserve `project_qa.py` compatibility if existing callers rely on it.
5. **Catalog UX and errors:** render only stored metadata; show whether a
   project has usable RAG and which indexed revision it represents. Return
   clear errors for no project, invalid selection, no evidence, stale evidence,
   malformed/empty model output, and provider failure.
6. **Deterministic regression tests:** use temporary SQLite databases and
   synthetic project fixtures for migration, selection binding, cross-project
   isolation, evidence failures, model failures, and model unload. Do not use
   the connected GTA source as a fixture.
7. **Bounded end-to-end acceptance:** run the exact saved GTA manifest
   question once through the interactive Runner with the registered GTA
   project selected. Confirm the expected answer, project-code source path and
   hash, and empty `ollama ps` afterward. Do not use an unbound generic Runner
   task as a RAG test.
8. **Documentation and handoff:** update canonical docs with only observed
   outcomes. Keep the task open if any acceptance check fails; do not tune
   prompts or repeat model calls until a desired answer appears.

## Pitfalls and controls

- **Two sources of truth:** SQLite plus an independently edited JSON file can
  diverge. Choose one operational catalog; current recommendation is SQLite.
- **Identity drift:** recomputing existing IDs from a changed path or name can
  orphan project state. Preserve IDs and use additive migrations.
- **RAG/source mismatch:** a valid project ID does not prove its RAG reflects
  the current source. Record snapshot revision and fail/report stale state
  rather than implying freshness.
- **Cross-project leakage:** retrieval must always receive the selected
  `project_id`; test with at least two isolated synthetic projects and ensure
  legacy user RAG is never queried as fallback.
- **False confidence from Reviewer/citations:** a second LLM pass or a source
  list is not deterministic semantic proof. Validate source membership and
  revision mechanically; describe semantic limits honestly and abstain on
  insufficient evidence.
- **Shared role side effects:** reusing general Analyst/Reviewer model fields
  for Q&A can change code-task routing unintentionally. Isolate Q&A settings
  and continue enforcing project provider policy.
- **Remote repository risk:** do not clone/fetch while asking a question.
  Remote registration requires separate policy for allowed URL schemes,
  credentials, pinned refs/commits, checkout isolation, updates, and re-indexing.
- **Unsafe verification scope:** do not edit/browse/build the connected GTA
  project; do not run Docker or Gradle. Preserve all live RAG, Vault, run,
  ledger, and retrieval evidence.
- **Overstated acceptance:** one exact GTA question verifies one known path,
  not all orchestration or all projects. Keep deterministic contract tests
  separate from the single opt-in real-model check.

## Expected deliverables

- A single canonical catalog contract and tested, backward-compatible schema
  migration that preserves existing project identity and state.
- A project-Q&A service used by both Runner and the compatibility CLI, with
  no duplicated retrieval/orchestration implementation.
- A formatted project menu showing stored catalog metadata and project-RAG
  storage state. Directory presence is not proof of an indexed or current
  corpus; query-time evidence checks enforce provenance.
- Explicit, readable abstention/failure behavior and source-bearing answers;
  no generic-RAG substitution or unsupported claim of semantic certainty.
- Focused tests for migration, selection, isolation, stale/missing evidence,
  model failures, and unloading, plus the exact historical GTA manifest check.
- Updated canonical documentation recording actual behavior and test results.
- A separately scoped remote-ingestion follow-up if remote repositories are
  still required after the local catalog/Q&A contract is stable.

## Decisions and remaining gated action

1. Implemented SQLite as the single operational catalog; no second live JSON
   source was added.
2. Remote clone/fetch is deferred; remote URL metadata alone is not query-ready.
3. Implemented a separate `project_qa` section in `roles.json`; general agent
   model settings remain unchanged.
4. Q&A reports a revision derived from the saved snapshot and validates RAG
   evidence against that snapshot. It does not claim the snapshot equals the
   current connected source.
5. The live migration and metadata population are complete with explicit
   backup-first approval and user-provided project values.

## Explicitly out of scope

- Remote clone/fetch/update implementation or any network access.
- Connected project edits, dependency-tree exploration, Gradle, or Docker.
- Rebuilding or mutating live project/global RAG, facts, knowledge, Vault,
  saved runs, ledger, or historical evidence.
- Changes to general code-generation orchestration, patch approvals,
  validation boundaries, or provider policy.
- Commit or push.

## Completion record

- Added backward-compatible catalog metadata fields and an explicit
  `migrate_metadata_schema()` method. Existing-schema reads and local
  registration remain compatible; migration is not automatic.
- Added metadata support for descriptions, local/git source identity, HTTPS
  repository URL, configured ref, and resolved commit hash. Storing git
  metadata does not clone, fetch, or contact a repository.
- Extracted shared Q&A behavior into `project_qa_service.py`; Runner and the
  compatibility CLI delegate to it. Q&A has separate Analyst/Reviewer
  settings in `roles.json`.
- Before either model call, Q&A validates source paths, snapshot membership,
  file hashes, and hashes for assembled chunks. It reports the derived
  snapshot revision and refuses absent, stale, malformed, or cross-project
  evidence. This is provenance validation, not semantic entailment proof.
- Ollama unload uses the correct API field and enumerates configured local
  primary/fallback models plus the embedding model.
- Verification: 225 deterministic tests passed with 20 expected skips.
  Focused Ruff checks passed for changed modules and tests; `runner.py` retains
  9 pre-existing Ruff findings outside this task. The exact historical GTA
  manifest question returned `tools:targetApi="31"` from
  `app/src/main/AndroidManifest.xml`; snapshot revision prefix was
  `869a2a9e1d75`. Final `ollama ps` was empty after the successful run.
- The live registry was migrated on 2026-10-01 after separate approval.
  `data/registry/projects.sqlite` was backed up to
  `data/registry/backups/projects-20261001T165819Z.sqlite`; backup integrity,
  schema, and row contents matched the source before migration. The live schema
  gained all five metadata columns; integrity remained `ok`, and the existing
  ID, name, source path, and timestamps were unchanged.
- The GTA row now stores the user-provided description
  `Android application cheats gta vice city, gta san andreas and gta V`, the
  optional repository URL `https://github.com/kharohiy/GtaCheatsApp`, and the
  existing local checkout path `E:\Android\AndroidStudioProjects\GtaCheatsApp-main`.
  The Runner displays the repository URL and checkout separately. No branch or
  resolved revision was supplied, so those values remain empty. Metadata
  storage did not clone, fetch, or contact GitHub.
- Remote checkout/fetch, semantic answer verification, connected-source
  modification, RAG rebuild, Docker, and Gradle were not performed.
