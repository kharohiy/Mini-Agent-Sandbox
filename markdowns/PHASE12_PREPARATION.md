# Phase 12 Preparation — Deterministic session lifecycle

## Status

Completed on 2026-09-21. Phases 9, 10, and 11 (including the isolated
fresh-clone acceptance) are complete.

## Why this phase

Item 12 of `mini_agent_sandbox_analysis.md` correctly identified that session
state existed but did not originally drive the main loop. Phase 7 partially
addressed that finding: `runner.py --resume <user_id>` now restores only a
structurally valid `in_progress` state. The remaining gap is a documented,
deterministic lifecycle for a saved session.

The current `--clear` helper mutates a saved state directly, clears memory and
tool history, and marks it `in_progress`. It is neither an explicit reset nor a
validated resume transition. The phase must make this boundary observable and
safe before any future session-memory or RAG feature is considered.

## Objective

Define and implement the smallest deterministic lifecycle contract for
per-user session state:

```text
new session      -> creates a new task state only after explicit input
resume session   -> accepts only a valid interrupted state
reset session    -> requires an explicit destructive action and leaves no
                    resumable task state
```

The contract must preserve the separate tiers:

```text
project facts / verified knowledge -> structured project state
documents                           -> isolated project/global RAG stores
conversation and tool history       -> session state only
```

## First bounded increment

1. Inspect the current state schema, `run_agent_loop`, `_load_resumable_state`,
   CLI paths, and their existing tests without contacting a model service.
2. Write the exact allowed state transitions and failure behaviour before
   changing code.
3. Replace the ambiguous clear behaviour with one explicit reset contract,
   preserving project facts, knowledge cards, RAG collections, ledger evidence,
   snapshots, and all other user data.
4. Add focused deterministic tests for valid resume, malformed/non-interrupted
   refusal, new-session isolation, and reset non-resumability.
5. Update the canonical documentation with only observed results.

## Hard boundaries

- Do not re-enable LLM memory summarisation or add automatic summarisation.
- Do not send, embed, index, promote, train on, or otherwise feed session
  memory into project or global RAG.
- Do not alter project facts, knowledge-card verification/indexing, snapshots,
  RAG corpora/Chroma collections, the GTA profile, or the connected Android
  source.
- Do not change `roles.json`, provider routing, budgets, tool capability
  policy, patch/review/approval/validation orchestration, Docker, Gradle,
  Ollama models, or dependency manifests.
- Do not run local-model calls, broad suites, Docker, Gradle, PDF ingestion,
  or destructive data cleanup as exploration.
- Reset must be narrowly scoped to the specified user's session state. It must
  not call `purge_user_data` and must never delete vaults, facts, RAG data, or
  project records.

## Exit condition

Focused tests prove deterministic new, resume, and reset semantics; invalid
state fails closed; reset is explicit and cannot accidentally create a
resumable task. No live GTA, RAG, model, Docker, Gradle, or package state is
changed.

## Expected blockers

- A documented state field may have incompatible historic values. Do not
  silently coerce it; record the incompatibility and fail closed until a
  migration policy is explicitly approved.
- If proving reset safety requires touching preserved historical state, use
  temporary directories and mocks only. Do not test against `data/`.
- If implementation needs a new user-facing CLI spelling or API surface that
  changes established workflows, stop after documenting options and obtain
  direction rather than choosing one implicitly.

## Completion record — 2026-09-21

- `SandboxStorage.reset_session_state()` deletes only the selected user's
  `state.json`, rejects a symlink state file, and does not create a user
  directory when state is absent.
- The new `--reset <user_id>` command is explicit. Legacy `--clear <user_id>`
  remains a compatibility alias and prints a deprecation notice before applying
  the same session-only reset contract.
- `_new_session_state()` makes new-session isolation explicit; `--resume`
  retains its existing fail-closed validation.
- `test_session_lifecycle.py` passed 3/3 and the existing resume-state
  validation passed 1/1. The tests use temporary directories and prove that
  facts and a vault file survive reset and resume is refused afterward.
- Ruff passed for the new test. `ruff check runner.py` still reports 10
  pre-existing violations outside the Phase 12 edits; they were not changed in
  this bounded phase.
- No live session state, GTA data/source, RAG/Chroma, Ollama/model call,
  Docker, Gradle, or package state was used or changed.
