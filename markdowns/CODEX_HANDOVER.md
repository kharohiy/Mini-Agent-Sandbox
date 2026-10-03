## Direct-callee evidence experiment failed and was reverted - 2026-10-03

The exact GTA question was run once with project evidence reordered as requested:
`toggleFavorite`, then `loadFavoriteCodes`, then `getDescriptionForCode`, followed
by remaining file context. Explicit labels identified the requested method and
direct local callees. The prompt visibly contained the three missing facts.

Analyst and Reviewer still stopped at "calls loadFavoriteCodes" and omitted
`getFavoriteCheatCodesUseCase`, `uiMapper.mapFavorites`, and the assignment to
`_favoriteCodes.value`. Both stopped normally at 305/2048 tokens. The evidence
reordering code and its test were reverted because the live result showed no
measurable benefit and the change would alter retrieval semantics. This makes
local Qwen instruction-following/verification the primary remaining explanation,
not a proven universal cause. Do not repeat this identical run.

## Project Reviewer checklist experiment is only a partial fix - 2026-10-03

The same live GTA `GtaSaViewModel.kt` question was repeated after adding a
project-Reviewer-only checklist: cover every question part, trace available
method/state chains, remove unsupported timing claims, and return the corrected
answer without evaluating Analyst. Retrieval, Analyst, roles, limits and
code-task contracts were unchanged.

The checklist removed the unsupported "immediately" wording and the Reviewer no
longer praised the draft. It did not make Reviewer trace `loadFavoriteCodes`:
the final answer still omitted `getFavoriteCheatCodesUseCase`,
`uiMapper.mapFavorites`, and the `_favoriteCodes.value` assignment despite all
being present in evidence. Both calls stopped normally (242/2048 and 241/2048).
Prompt-only tuning is therefore not accepted as a complete repair; do not repeat
the run hoping for a random better sample.

## Project-Q&A chain check remains open - 2026-10-03

The GTA project-selected Runner was tested against indexed
`GtaSaViewModel.kt`. Deterministic retrieval assembled all eight current chunks,
including `toggleFavorite` and the full `loadFavoriteCodes` implementation.
Analyst correctly described add/remove selection but reduced refresh behavior to
"calls loadFavoriteCodes" and added an unsupported "immediately" claim. Reviewer
repeated both omissions instead of explaining the available
`getFavoriteCheatCodesUseCase -> uiMapper.mapFavorites -> _favoriteCodes.value`
chain. Output limits were not involved (284/2048 and 200/2048; both stop).

Project CLI now prints the existing Analyst draft before the Reviewer answer so
future live checks expose the complete chain. This is an observability change;
retrieval, prompts, roles and model limits are unchanged. Project Q&A is not
accepted as fully reviewed by this run, although exact-file retrieval succeeded.

## Shared-book continuation retrieval verified - 2026-10-03

A real no-project Runner comparison exposed a chunk-boundary defect: retrieval
selected the start of the Compose change-list explanation but omitted its direct
continuation, which contained the answer about when deferred changes execute.
General book retrieval now attaches at most one immediate successor only when it
belongs to the same PDF and header section. The result count remains capped at
three; agent prompts, roles and output limits are unchanged. New ingestion stores
`chunk_index`; the existing index uses its preserved insertion order.

The same real Runner question was repeated. RAG reported
`5dbcea86...` plus continuation `b8d4b3ee...`; Analyst then stated that changes
are deferred until Composition completes, and Reviewer preserved that fact in
the final answer. Both model calls completed and models unloaded. Project RAG
and GTA were not used. Verification: 15 focused tests, all 59 project-RAG tests,
focused Ruff and the real before/after Runner check passed.

## Phases 20–22 CLOSED locally - 2026-10-02

Security eval acceptance now comes from 10 named behavioral tests covering
filesystem, state, facts, network, tool dispatch and Vault effects. Model prose
is excluded from the result. A real Docker container failed its outbound socket
attempt, and Kotlin validation remained isolated from source fixtures.

Regulator telemetry now supplies payload-free evidence IDs. Proposals require
proposal/confidence/evidence/affected_rule and pass a deterministic admission
gate, but remain `auto_apply=false`; Regulator receives no tools and cannot edit
rules, roles, facts or capabilities. The independent-boundary audit is recorded
in `SECURITY_BOUNDARY_MATRIX.md`.

Verification: behavioral evals 10/10, focused Phase 20–22 tests 7/7, focused
Ruff passed, full discovery 261 tests OK with 8 expected skips. Two pre-existing
Docker integration modules had an incorrect doubled fixture path; correcting
only those paths allowed their 8 real container tests to pass. No Qwen, GTA,
project RAG, user-state reset, commit or push was used. Docker was stopped.

Known separate work remains: blocked tasks may return CLI exit 0, and a full
successful code-task route is not certified by these phases. Phase 19 evidence
and all historical states remain preserved.

## Phase 19 CLOSED locally - 2026-10-02

The live blocker was traced to LiteLLM's ollama completion transport: it puts
tools into a JSON prompt and recognizes only name/arguments; the saved Qwen
function/parameters response remained text. LiteLLMAdapter now uses ollama_chat
for non-empty tool requests only, reaching native /api/chat. The configured
model, local routing policy, roles, Runner and authorization are unchanged.
No parsing/execution of arbitrary assistant text was added.

29 focused tests and Ruff passed. One real Runner menu-3 run with the original
six-list_directory request processed exactly five calls in one Coder turn and
blocked call six. Durable status: breaker_blocked; incident records limit=5,
attempted=6, processed=5. No subsequent agent/regulator ran. Duration 61.25s;
CLI exit 0 is still a known presentation limitation, not task success.
Actual --resume rejected it (exit 1), preserving the live state. Reset behavior
and documentation-mode limit=3 are covered deterministically, not by a live
documentation run. All 19 historical states are unchanged; models unloaded.
Evidence: data/offline-acceptance-20261002/breaker-native (run, console, resume,
verification). Live evidence was not reset. See the preparation closure record.

Phase 18 remains closed. Phase 19 closure covers the breaker boundary, not
successful full code generation, Kotlin-answer accuracy or all agent workflows.
The native transport/output-budget follow-ups and these docs remain local.

## Project-Q&A output repair verified - 2026-10-02 (earlier checkpoint)

The previous fixes were published as 870b2bc. The follow-up now raises only the
project-Q&A output budget from 200 to 2048 tokens per agent, logs finish reason
and completion tokens, and reports provider length termination as incomplete
without retries. Roles, prompts, Runner and retrieval are unchanged.

19 focused project-Q&A tests and Ruff passed. A real offline Runner menu-2 run
of the user's Navigation.kt question completed in 104.09 seconds, exit 0:
Analyst and Reviewer each reported finish_reason=stop and 507 output tokens.
The final output contains the closed code block and navigation explanation.
Evidence: data/offline-acceptance-20261002/navigation-output-ready. Two earlier
connection-failure attempts are retained separately; Ollama was not running
until ollama ps started it. The old user run's finish_reason remains unknown.
Phase 19 live N+1 remains open; this is not full code-task acceptance.

## Publication checkpoint and next task - 2026-10-02 (historical)

The user authorized documenting and committing/pushing the accumulated offline
fixes before further implementation. This checkpoint supersedes historical
priorities below; it does not close Phase 19. Phase 18 remains closed within its
documented scope. See `OFFLINE_ACCEPTANCE_20261002.md` for actual run evidence.

The user's subsequent Navigation.kt run selected the correct source, but the
answer stopped inside `onNavigateToGtaV = { nav` and omitted the explanation.
Project Q&A currently requests max_tokens=200 for each agent and does not check
finish_reason for truncation. The limit is a plausible cause, not a confirmed
stop reason from that transcript. After publication, investigate this bounded
output defect first. No token-budget or agent-chain change is part of this
documentation checkpoint. Book augmentation is optional and disabled by default
for project Q&A; enabling books would not itself resolve output truncation.

Earlier statements that no commit/push occurred describe their own checkpoints.
Runtime evidence, vaults, indexes and user data remain local and outside Git.

## Subsequent named-file RAG repair - 2026-10-02

The user's CheatCodes.kt query exposed a source-ranking bug: the file already
exists in snapshot/Chroma, but general words displaced it before context reached
the agents. Explicit filenames now resolve against the selected snapshot first;
only their stored chunks are supplied, with existing hash checks retained.
Duplicate basenames require a relative path. No quotes are required in a normal
question. This changes project retrieval, superseding the earlier checkpoint's
statement that its source files were unchanged. No source/corpus reindexing,
role/status change or phase closure is involved. See the latest preparation
record and `data/offline-acceptance-20261002/project-filename` for acceptance.
The exact real Runner question passed: both local turns, the correct sole source,
exit 0, 81.65 seconds, models unloaded. Phase 19 live N+1 remains open.

### Runtime acceptance outcome - 2026-10-02

See `OFFLINE_ACCEPTANCE_20261002.md` and the captured real CLI evidence under
`data/offline-acceptance-20261002`. General QA, book QA after a bounded literal
retrieval fix, and explicitly selected GTA QA completed through both agents.
The code-task created the same file twice then stopped at `validation_blocked`
for a missing wrapper. The live breaker attempt returned tool-shaped text,
executed zero tools, and never reached N+1. Therefore Phase 18 remains closed
within its original scope; Phase 19 live acceptance remains OPEN. No full
successful code-task workflow is claimed. Process exit 0 is not task completion.
Final focused/adjacent tests: 14 + 35 = 49 passed; this was not a full suite.
All 19 historical states are unchanged; library counts remain 2,293 and 393;
models are unloaded. Generated-answer accuracy is outside runtime acceptance.

## Current scope correction and runtime acceptance - 2026-10-02

The user explicitly separated answer accuracy from Mini Agent Sandbox runtime
correctness and authorized auditing the diff, removing unnecessary ordinary-QA
contract changes, and running real isolated acceptance scenarios. The prior
"semantic acceptance failed" labels below are historical assistant assessments,
NOT failures of orchestration and NOT current phase acceptance criteria.

The added ordinary Reviewer JSON contract has been removed. Reviewer again
returns plain text/Markdown; code-task and project-patch review are unchanged.
Shared-book retrieval failure is visible but no longer blocks ordinary QA.
A real SlotTable query exposed irrelevant vector hits despite existing exact
book passages. The global reader now prioritizes up to two literal camel-case
identifier/spaced-name passages, excludes contents listings from that stage,
and fills remaining slots from vector retrieval. No corpus rebuild or project
RAG change is involved.

Current run evidence, baseline backup, diff decisions and exact acceptance
boundaries are in `OFFLINE_ACCEPTANCE_20261002.md`. Do not claim full acceptance
from targeted tests, process exit alone, or prose quality. Preserve all original
states and new acceptance profiles. No automatic rollback, role/model changes,
GTA writes/builds, or unrelated orchestration changes are authorized.

## Superseded review-quality framing (historical)

## Current offline Q&A repair — 2026-10-02

The user authorized review-quality repairs and clarified that ordinary questions
must have access to the shared three-book library without attaching GTA.
`question_answering.py` now validates a structured Reviewer result (decision,
corrections, uncertainties, answer). Invalid records stop without retry;
uncertainty is visible with exit 2. Runner no longer prints "Question answered"
merely because both model calls finished; compilation/tests remain explicitly
not run. These are model assessments, not correctness certificates.

`global_library_retrieval.py` opens only the existing
`data/knowledge/global/chroma_db` / `android_architecture_library` collection,
embeds locally, and supplies up to three bounded excerpts to both agents.
It never instantiates project/user RAG, selects a project, ingests PDFs, or
reindexes. Retrieval failure stops before completion. Console output identifies
book sources and chunk IDs. The previous blanket no-RAG statements below are
historical: only shared book access has been added.

13 focused tests passed; changed service/retrieval/test modules pass Ruff.
Runner retains nine pre-existing Ruff findings. The first live structured-review
run completed but Reviewer introduced the invalid `androidx.lifecycle.ViewModelScope`
import; answer correctness is still not accepted. The second live run with books also completed, but retrieved unrelated
reflection/DSL passages and produced lifecycleScope examples without the required
receiver/imports. Semantic acceptance failed in both runs. Final `ollama ps`
is empty. The exact records are consolidated later in this file and in
`OFFLINE_ACCEPTANCE_20261002.md`. Do not retry
blindly, equate retrieved chunks with relevant evidence, or claim Phase 19 closure.
Preserve new profiles `phase19-qa-review-20261002`, `phase19-qa-books-20261002`
and every prior profile. The original `user_123/state.json` hash is unchanged.

## Previous repair — ordinary Runner questions — 2026-10-01

The user supplied a real `python runner.py` transcript for
`kotlin language show function`: code-mode Coder attempted file writes, then
Shift-Left returned it to Coder for ten turns. The no-argument entry point
unconditionally entered code mode, whose role prompt requires actual files.
This establishes the wrong workflow for ordinary questions; it does not prove
a Qwen-only regression or that historical cloud runs worked.

The authorized repair introduces the default menu: general question without
a project, explicitly selected project Q&A, or explicitly selected code task.
General questions use `question_answering.py` for exactly Analyst then Reviewer,
with no tools, project/RAG access, validator, or regulator. Native tool calls,
tool-call JSON, empty responses and output-limit truncation fail visibly.
Role models/routing remain configured in `roles.json`; no provider permissions
were widened. State-save logs now contain status/step/tool counters; stdout is
line-buffered, and router logs expose actual dispatches and safe failures.
Code validation stops after two consecutive identical failures.

Historical `user_123` and probe states must be preserved. Ordinary Q&A does not
overwrite `state.json`; normal guardrail/Vault and telemetry operations still
occur in the completion facade. The temporary RAG helper experiment was
removed; no new RAG route or corpus change is part of this repair.

Three actual Git Bash CLI runs completed naturally with exit code 0: two
dispatcher-question runs (before/after review-prompt refinement) and the user's
original `kotlin language show function` entered directly at the menu. All
used two local Qwen agent turns, returned text and finished automatic unload.
Final `ollama ps` was empty; the saved `user_123/state.json` hash was unchanged.
The ordinary control-flow repair is evidenced. Reviewer still accepted missing
coroutine receivers and mislabelled an ordinary function as inline; semantic
answer correctness is NOT accepted. Full records are consolidated later in
this file. No unit-test suite was run; added regressions are
unexecuted. Phase 19's live breaker acceptance remains separately unproven.

## Phase 13 handover — completed 2026-09-21

Phase 13 is **deterministic context accounting**. The next open analysis item
is number 13: `ModelRequest.context_tokens` and runner window metrics use the
same undocumented `chars / 4` approximation. The phase may unify this into one
model-aware counter or proven conservative bound, but only after auditing
locally installed capabilities. It is not authorized to add a tokenizer,
download assets, or call Ollama.

Bounded audit result: with local-cost-map mode LiteLLM's counter is stable on a
fixed fixture but it is not Qwen-exact. Its installed source maps the Ollama
Qwen identifier to `gpt-3.5-turbo` and uses the OpenAI `cl100k_base` fallback;
its message framing is not proof of Ollama/Qwen framing. It must not replace
the current estimate. An initial import without local-cost-map mode attempted a
GitHub price-map refresh, which was refused; subsequent calls were local only.
No external request succeeded.

The former blocked path required an official Qwen tokenizer
dependency and clean-install acceptance, authorize an opt-in documented Ollama
tokenization integration, or retain the estimate. Do not guess exact counts or
change production code. Completion: approved Qwen assets on `E:` are
hash-verified through `MINI_AGENT_QWEN_TOKENIZER_DIR`; one real Ollama request
and offline rendering both counted 26 tokens. Runner/router exact mode covers
supported text chats; tool-bearing/unsupported shapes retain fallback. Focused
tests passed 28/28 and focused Ruff passed.

Do not change providers, models, roles, prompts, routing/budget policy,
dependencies, manifests, RAG/Chroma, facts, knowledge, session lifecycle,
vaults, GTA source/profile, Docker, Gradle, patch/review/approval/validation,
or live data. No LLM/model request, download, or installation is in scope.

## Phase 12 handover — completed 2026-09-21

Phase 12 is **deterministic session lifecycle hardening**. The historical
analysis item 12 is partially superseded: Phase 7 already added fail-closed
resume of a structurally valid interrupted state. The remaining bounded issue
is the lifecycle contract around new, resume, and reset: the current clear
helper mutates session state directly and is neither explicit reset nor
validated resume.

Completion: `SandboxStorage.reset_session_state()` removes only selected
`state.json`; it rejects symlink state files and does not create an absent user
directory. `--reset` is explicit; legacy `--clear` is a deprecated compatible
alias. `_new_session_state()` explicitly creates a clean envelope, while
existing resume validation remains fail-closed. Temporary-fixture tests passed
3/3 plus the existing resume validation 1/1; facts and a vault file survived
reset and resume was rejected afterward.

Do not enable LLM memory summarisation, conversation-to-RAG ingestion, or
learning. Do not change facts, knowledge cards, snapshots, RAG/Chroma, the GTA
profile/source, vaults, provider policy, roles, codegen/review/approval/
validation, Docker, Gradle, models, or dependencies. Reset must never call
`purge_user_data` or delete facts, vaults, project data, RAG, snapshots, or
ledger evidence.

Ruff passed for the new test. `ruff check runner.py` reports 10 pre-existing
findings outside this phase's edits. No live state, GTA, RAG/Chroma, model,
Docker, Gradle, or package state was changed.

# Phase 8 closed — 2026-09-17

GTA profile `gta-cheats--cc0fe5de` has 393 project-code chunks. `project_qa.py`
runs local Analyst → Reviewer Q&A over hybrid semantic plus snapshot/source
retrieval. Grounded manifest answer: `tools:targetApi="31"` from
`app/src/main/AndroidManifest.xml`. Connected Android source was not modified.

## Phase 9 handover — completed 2026-09-20

Phase 9 is **project-RAG quality and grounded native Q&A**. It was created
from the completed Phase 8 outcome because no prior Phase 9 file existed.
Start with `PHASE9_CONTINUATION_PROMPT.md` and `PHASE9_PREPARATION.md`.

Phase 9 uses a cascaded, isolated RAG design: project snapshot/project-code
evidence establishes GTA facts first; the shared Compose/Kotlin/architecture
library is an optional separately labelled technical reference for explanation
only. Do not mix their collections, rankings, or citations. Audit the one
canonical global-library Chroma storage route without rebuilding corpora. Any
future knowledge promotion must be explicit, evidence-gated, and human
approved; LLM answers never auto-enter RAG.

Audit result (2026-09-20): GTA project-code has 393 chunks, while both existing
global-library collections have zero. The user authorized one bounded ingestion
of the three PDFs already present in `docs/` into the canonical global library;
do not re-index or otherwise alter GTA RAG.

Completion record: the canonical global book library now contains 2,293 chunks
and GTA project-code remains 393. A stored-chunk lexical stage raises
`app/src/main/AndroidManifest.xml` first for the observed `tools:targetApi`
ranking miss. Books stay in the separately labelled `global-library` technical
reference stage; project facts come only from project-code. Two real local
Analyst -> Reviewer answers were grounded in that manifest:
`tools:targetApi="31"` and the `.MainActivity` `MAIN`/`LAUNCHER` declaration.
Focused Ruff and 4/4 focused tests passed. No Docker, Gradle, connected-source,
GTA-corpus, or preserved-state change occurred.

Use existing GTA profile `gta-cheats--cc0fe5de` and its 393 code chunks. Work
only on source-aware ranking, evidence selection, and local Analyst → Reviewer
answers for natural project questions. The connected Android source remains
read-only. Do not resume Phase 8 codegen runs, create patch proposals, modify
Android source, or run Docker/Gradle. Preserve all saved runs, ledger records,
and Phase 8 evidence as historical state.

## Previous generic handover

## Phase 11 handover — completed 2026-09-20

Phase 11 is **reproducible dependency manifests**. Its observed baseline is an
incomplete `requirements.txt`: it omits direct runtime imports such as ChromaDB
and Cryptography, while PDF ingestion has separate dependencies. On approval,
audit direct imports and installed versions, split runtime/ingestion/dev
manifests with a compatible runtime entry point, and add focused manifest
tests. Do not install, upgrade, download, remove, or lock packages; a fresh
environment install is separately authorized. Start from
`PHASE11_CONTINUATION_PROMPT.md` and `PHASE11_PREPARATION.md` only after the
user authorizes implementation.

Phase 11 completion: added pinned runtime, optional-ingestion, and development
manifests while preserving `requirements.txt` as the compatible default entry
point. The versions match the observed working environment. Focused manifest
tests passed 3/3 and Ruff passed. No package install, upgrade, download,
removal, lockfile resolution, model, RAG, Android, Docker, or Gradle state was
changed. A clean-environment install remains separately authorized.

Fresh-clone acceptance (2026-09-21): a separate `E:` clone finished at
`3f7027f`. Python 3.11.9 installed the default and optional-ingestion manifests
with Pip caching disabled. `pip check`, runtime imports, the full suite (166
tests; 17 expected skips), and the two ingestion tests passed. No Ollama,
Chroma persistent store, PDF/RAG ingestion, or GTA source was used.

Phase 11 recovery-first contract: preserve `requirements.txt` as the familiar
installation entry point, retain currently observed compatible versions unless
a direct import proves otherwise, and make only additive manifest changes until
focused checks pass. Do not delete dependency files, migrate packaging tools,
change Chroma/Ollama data or configuration, or run a network install. The goal
is to describe what already works reproducibly, not to upgrade or replace it.

## Phase 10 handover — completed 2026-09-20

Phase 10 is **evidence-gated knowledge promotion**. Start with
`PHASE10_CONTINUATION_PROMPT.md` and `PHASE10_PREPARATION.md`. It may build a
deterministic bridge from grounded project Q&A to a **draft** project knowledge
card only. A card requires same-project `project-code` source paths and current
snapshot/source hashes; books are technical-reference-only. Existing explicit
human verification remains the sole indexing path. Do not create any card in
the live GTA profile, train a model, auto-promote LLM output, alter GTA RAG, or
enter codegen/Docker/Gradle/approval/validation workflows.

Phase 10 completion: `grounded_knowledge_proposal.py` validates structured
same-project `project-code` source paths and hashes against the stored snapshot
and creates only a draft card. `project_qa.py` returns the required structured
evidence but cannot create, verify, or sync a card. Global, missing, stale, and
cross-project evidence are rejected. Focused Ruff and 11 focused
knowledge/retrieval/Q&A tests passed. No live GTA data, Docker, Gradle, model
call, or model-training operation occurred.

Start from `NEXT_STEPS_PLAN.md` and `PROJECT_EVOLUTION_ROADMAP.md`; do not
resume the old Phase 8 codegen runs, modify the connected Android source, or
repeat Phase 8 validation. The completed Phase 8 evidence is the registered
GTA profile, 393 project-code chunks, `project_qa.py`, hybrid retrieval, and
the grounded `tools:targetApi="31"` answer. Preserve all existing run and
ledger evidence as historical state.

## Phase 8 current increment — 2026-09-16

- Workspace policy is enforced at `WorkLedger.record_patch`, the shared path
  for API and worker candidates. Every parsed changed path must match
  `allowed_workspace_paths`; no policy or an empty list rejects the candidate
  before ledger persistence, review, approval, or validation.
- Project-scoped model calls now pass `model_providers` to `ModelRouter`.
  The router filters primary and fallback candidates before adapter dispatch;
  missing or empty policy permits no provider calls.
- The same pre-dispatch router gate now reserves input-context estimate plus
  requested output tokens and enforces both project budget fields. The runner
  passes task tokens already consumed within the task, including earlier calls
  in the active turn.
- Project-scoped payload-free telemetry is now connected to runner project
  flows. Successful and failed model calls record only event/outcome/provider
  and bounded tokens; retrieval records only event/outcome. Prompts, queries,
  retrieved content, model responses, source excerpts, secrets, and validation
  output do not enter this store.
- Validation telemetry remains written only after the trusted worker saves its
  report. FastAPI still cannot invoke Docker or execute generated code.
- Focused verification: targeted router and runner telemetry tests: **23
  passed**. They prove budget refusal occurs before adapter dispatch.
- Retention now has an explicit, project-scoped read-only preview at
  `GET /projects/{project_id}/retention/preview`. It reports only per-category
  retention days and total/expired counts for telemetry and policy-audit JSONL
  stores. Missing stores are empty; malformed events block the preview
  fail-closed. It neither deletes files nor reads knowledge, RAG, ledger,
  snapshots, or vault material.
- Do not claim auto-apply, graphical UI,
  destructive telemetry/audit cleanup, or destructive knowledge deletion. Each
  remains a separate Phase 8 security contract with regression tests.

## Bounded execution status — 2026-09-16

- `phase7_quality_final` was preserved as an immutable historical failed run:
  its actual `state.json` contains `in_progress` and `agent_steps: 11`. It was
  not reset, edited, or resumed.
- `phase7_operational_preflight.ps1` starts Docker Desktop when the daemon is
  unavailable and checks `docker info`, the native Ollama endpoint,
  `qwen2.5:14b`, `nomic-embed-text:latest`, and a separate FastAPI process. The
  workflow passed.
- A new bounded `phase7_dispatch_guard` task was created without using
  `phase7_quality_final` storage. The only fix affected documentation
  `create_file`: invalid structure is rejected before writing and does not
  consume a separate step. The focused dispatch test passed **1/1**.
- One opt-in Ollama/Chroma integration passed **1/1** in 21.618 seconds. One
  `MINI_AGENT_OFFLINE=1` documentation resume of the new task completed with
  `agent_steps: 2` and Reviewer verdict `APPROVE`.
- The final full suite reported **126 tests, OK (skipped=3), exit code 0**.
  After the run, `ollama ps` was empty and no Docker containers remained.

**Phase 7 was closed on 2026-09-16 based on the successful preflight, one
opt-in Ollama/Chroma run, and one new real documentation resume. The historical
`phase7_quality_final` failure remains preserved and was not closure evidence.**

New sessions should start with [`README.md`](README.md) for the current runtime
and module map, then use the canonical documents in this directory for the
approved architectural record.

---

## Historical status and handover records

## Status at the end of the 2026-09-15 session

### Result of the single resume — 2026-09-16

- The local Ollama endpoint was restored and the opt-in Ollama/Chroma
  integration passed **1/1** with the already installed models.
- The single permitted `MINI_AGENT_OFFLINE=1` resume of
  `phase7_quality_final` ended in a preserved rejection because Coder wrote
  `# Overview` instead of the required `## Overview`. The gate stopped the
  task before evidence and Reviewer checks. State remained `in_progress`, with
  `agent_steps=7` and no `documentation_review`.
- No second resume or prompt tuning was to be performed. Phase 7 remained open
  at this checkpoint and the defect was recorded for separate resolution.

### Pinned-plan execution update — 2026-09-16

- Phase 7 gained a minimal deterministic evidence gate. Every retrieval
  request with a direct match required one corresponding real RAG source path;
  a path match took precedence over an incidental text mention. This did not
  restore complex citation-to-code matching.
- The new negative regression and focused suite passed **52/52**. The full
  `python -m unittest discover -v` run executed **126 tests: 111 passed and 15
  skipped**; Docker tests were skipped because Docker Desktop had not been
  started by the operator.
- The opt-in `test_offline_integration` did not reach the agent loop. Chroma
  embedding through `ollama/nomic-embed-text` ended in `APIConnectionError`.
  `ollama ps` then could not create a log under `%LOCALAPPDATA%\\Ollama`
  (`Access is denied`) and timed out waiting for the server. This was recorded
  as a Phase 7 infrastructure failure.
- `phase7_quality_final` was not resumed; its state and `agent_steps=6` were
  unchanged and no models were loaded successfully. The failure was not to be
  addressed by changing prompts, RAG, or task state. Work would continue only
  after external restoration of Ollama and a successful `ollama ps`.

**At this historical checkpoint Phase 7 was not complete. Work and generation
were stopped at the user's request.** This checkpoint superseded the older
status and continuation prompt below it at that time.

- Documentation artifact checks in `documentation_policy.py`, the `runner.py`
  changes, and exact retrieval of existing Chroma fragments in
  `project_retrieval.py` were preserved with regression tests.
- The final design was simplified to require the intended Markdown file, no
  unexpected files, required sections, and real RAG paths. Reviewer returned a
  structured `decision` and meaningful `reason`. Complex citation-to-code
  matching was removed. Links were not required in every section and did not
  prove every claim.
- Focused tests passed **51/51** after simplification. The latest full run at
  that checkpoint ran **125 tests: 122 passed and 3 skipped**, but it preceded
  the final simplification. No full run of the final simplified code or repeat
  opt-in integration had yet been performed.
- A successful real offline run had not been demonstrated. `qwen2.5:14b` lost
  citations, and one Reviewer response cited the document itself as evidence.
  Those failures did not close tasks.
- `phase7_offline_test` was `completed` at step 6 with a known quality defect;
  `phase7_quality_test` was `in_progress` at step 11 with its limit exhausted;
  and `phase7_quality_final` was interrupted at step 6 and preserved.
- All three tasks were bound to `gta-cheats--cc0fe5de`. `user_123`, Android
  sources, the legacy vault, dependencies, and Docker configuration were not
  changed. No commit was made. Switching to `qwen3.5:9b` was discussed only;
  it was not performed and `roles.json` was unchanged.
- After stopping, `qwen2.5:14b` and `nomic-embed-text` were unloaded. A repeat
  check showed an empty `ollama ps` and no Python or Ollama runner processes;
  only the Ollama application and background server remained. GPU use was not
  measured because `nvidia-smi` was not on `PATH`. Models were not to be run
  merely to check status.

### Minimal context and continuation order

Read `documentation_policy.py`, the documentation branches of `runner.py`,
`project_retrieval.py`, `test_documentation_policy.py`,
`test_documentation_transition.py`, `test_documentation_retrieval.py`, and
`data/phase7_quality_final/state.json`. Do not load the entire repository or
the Android source tree.

1. Inspect the saved simplified implementation without rewriting it. It
   preserved stopping Coder after the write, a read-only Reviewer, the real
   file in context, file and SHA-256 rechecks before completion, identical
   project context for author and Reviewer, and `in_progress` on limits or
   errors. Exact fragments came from existing Chroma entries selected by paths
   found in the snapshot; the original source tree was not read.
2. The focused tests were already green and were to be repeated after a code
   change, not in a loop. The command was
   `python -m unittest test_documentation_policy test_documentation_transition test_documentation_mode test_documentation_retrieval test_model_router test_arbitrator test_project_retrieval test_work_ledger -v`.
3. Any further real test was to use the existing `phase7_quality_final` with
   `MINI_AGENT_OFFLINE=1`, after checking its limits and last failure. State and
   `agent_steps` were not to be reset; `user_123` was not to be resumed. One
   bounded run would produce either `completed` or one concrete failure.
4. After finalizing code, run `python -m unittest discover -v` once with Docker
   daemon access, then run the opt-in
   `MINI_AGENT_RUN_OFFLINE_INTEGRATION=1` test separately. Docker could use
   only fixture copies under the existing restrictions.
5. Update the four status documents only with observed results. Phase 7 could
   close only after a real run, local routing/RAG, and safe failure were
   demonstrated. Model review of a document was not patch approval or
   knowledge verification.

### Location of the historical work artifacts

The project is `C:\Users\AlSaintUk\Desktop\Mini Agent Sandbox`. Helper copies,
the baseline, and logs were kept separately under
`C:\Users\AlSaintUk\Documents\Codex\2026-09-14\kharohiy-mini-agent-sandbox-1-llm\work\phase7\quality_gate`.
The Desktop code was the current implementation; the baseline was for
comparison only.

- `focused-tests.log`: the last **51/51** result after simplification.
- `full-tests.log`: **125 run / 122 passed / 3 skipped** before simplification.
- `offline-run-audit.json`: a negative `phase7_quality_test` run. The
  process-local network guard permitted loopback only and recorded real Ollama
  completion and embedding calls. This was not a successful acceptance test.
- `phase7_quality_final` was stopped, so its final audit could be absent. A
  missing report was not success, and `verify_run.py` was not to run before an
  actual `completed` state.
- `prepare_run.py`, `offline_runner_check.py`, and `verify_run.py` were
  investigation helpers rather than a production API. They were not to run
  automatically. `prepare_run.py` intentionally refused to create a task when
  its directory already existed.

If models were run again, the controlling Python process had to stop, only the
models used by the test had to be unloaded with `ollama stop <model>`, and
`ollama ps` had to be checked so the GPU was not left occupied.

### Short continuation prompt from that checkpoint

```text
Continue Phase 7 from the newest status at the top of CODEX_HANDOVER.md.
Inspect the saved simplified code and phase7_quality_final state first.
Do not restart the work, restore complex citation checks, change models, or run
the full suite after each prompt edit. Focused tests already passed 51/51; the
full simplified run and a successful real resume have not been demonstrated.
Limit the real experiment to one run and preserve failure honestly.
Do not touch user_123, prior test state, Android sources, vault files,
dependencies, or Docker configuration. Do not run nested codex exec or commit.
After stopping, unload the models used and check ollama ps.
```

---

## Previous session history — status below may be outdated

# Codex Handover — Mini Agent Sandbox

Date: 2026-09-15

## Objective

Build a safe, project-aware Android/Kotlin coding assistant: read-only project indexing, strictly scoped retrieval, evidence-gated knowledge, and Docker/Linux-only code validation.

## Non-negotiable constraints

- Do not modify/delete legacy `.vault` or `.vault_key`.
- Never run Gradle, generated code, or untrusted project code on Windows.
- Docker validates only a temporary copied workspace; never mount the original project.
- FastAPI gets no Docker socket/CLI.
- Docker must retain `network=none`, read-only root, non-root user, `cap_drop=ALL`, `no-new-privileges`, and CPU/RAM/PID/time limits.
- RAG is retrieval, not training. Never auto-promote LLM output to knowledge.
- The only vector RAG is existing ChromaDB + LiteLLM + local Ollama `nomic-embed-text`.
- Never mix state or retrieval across projects. No git commit without explicit user request.

## Verified environment

- Docker Desktop/WSL2 works through elevated Windows context.
- Ollama works locally; `nomic-embed-text:latest`, `qwen3.5:9b`, `qwen2.5:14b`, `qwen2.5:7b`, and `llama3:latest` are installed.
- ChromaDB 1.5.9 and LiteLLM imports work.

## Connected project

Read-only source: `E:\Android\AndroidStudioProjects\GtaCheatsApp-main`

Registered ID: `gta-cheats--cc0fe5de`

- Seven Gradle modules: `:`, `:app`, `:core`, `:data`, `:feature:gta_sa`, `:feature:gta_v`, `:feature:gta_vice_city`.
- 156 indexed files and 274 Kotlin/Java symbols.
- `:app` depends on core, data, and all feature modules; compileSdk 34, minSdk 24, targetSdk 34.
- Indexing/RAG did not write to the Android source.

## Canonical state

```text
data/registry/projects.sqlite
data/knowledge/global/global_knowledge.sqlite
data/knowledge/global/chroma_db/
data/projects/gta-cheats--cc0fe5de/
  snapshot/project_snapshot.sqlite
  snapshot/snapshot.json
  rag/chroma_db/
  knowledge/project_knowledge.sqlite
  runs/work_ledger.sqlite
  exports/
```

`data/project_snapshots/gta-cheats` is legacy/non-canonical; do not delete it without explicit approval.

## Completed work

### Phase 0 — Docker validation

`Dockerfile.executor`, `executor-entrypoint.sh`, `sandbox_executor.py`, fixtures and tests exist. Runtime uses:

```sh
HOME=/tmp/home
GRADLE_USER_HOME=/tmp/gradle
ANDROID_USER_HOME=/tmp/android
```

Real Docker positive fixture and negative compile/failing-test/missing-wrapper/source-immutability cases passed.

### Phase 1 — read-only project snapshot

`project_registry.py`, `project_manager.py`, `project_indexer.py`, and `project_search.py` provide SHA-256 incremental isolated snapshots.

### Phase 2 — RAG and knowledge

- `project_rag_ingestion.py` produces deterministic chunks from snapshot-listed files.
- Unchanged SHA-256 documents skip re-embedding; changed files replace only their chunks; removed sources are de-indexed.
- Real result: 156 documents and 393 project-code chunks; repeat ingestion skipped all 156 without duplicates.
- A real local Chroma/Ollama query returned project navigation source context.
- `knowledge_store.py` provides global/project cards, evidence, versions/audit; cards start draft.
- `knowledge_rag_sync.py` indexes only verified cards and de-indexes deprecated/archived ones.
- `api.py` exposes knowledge list/search/create/evidence/verify/retire/history.
- `project_retrieval.py` has a fixed order: snapshot → project code → verified project knowledge → verified global knowledge. Each hit has trust, scope, source, and module labels.

### Phase 3 — persistent work ledger

`work_ledger.py` persists project-scoped `Task`, `Plan`, `PlanStep`, `Patch`, `Review`, `ValidationReport`, `Run` in `runs/work_ledger.sqlite`.

- Plan steps require files, risks, validation and rollback before approval.
- Patch record requires approved plan; validation requires approved review.
- Successful validation moves patch/step/task to `validated`.
- Task inspection restores plans, diffs/hashes, reviews, reports and runs after restart.
- `api.py` exposes list/create/inspect tasks, create/approve plans, add steps, and patch/review/validation/run records.

## Tests passed this session

```powershell
python -m unittest test_project_rag_ingestion -v
python -m unittest test_knowledge_store test_knowledge_rag_sync test_api_security -v
python -m unittest test_project_retrieval test_project_rag_ingestion test_knowledge_rag_sync test_arbitrator -v
python -m unittest test_work_ledger test_api_security -v
```

Latest relevant results: RAG/retrieval regression 5/5 green; ledger/API regression 9/9 green.

Phase 4 verification: `python -m unittest discover -v` passed 59 tests with 2 expected skips, including Docker smoke and real Kotlin/Android executor integration. Focused patch-policy/ledger/API tests also passed after the hash-bound approval audit was added.

Phase 5 verification (2026-09-15): `python -m unittest discover -v` passed 74 tests with 2 expected skips. This includes real Docker smoke, the existing Kotlin/Android executor suite, and four Phase 5 worker integration cases using only copied `tests/fixtures/kotlin-android`. After the final ledger snapshot-transaction change, `python -m unittest test_work_ledger test_validation_worker test_validation_worker_docker.ValidationWorkerDockerTests.test_approved_positive_patch_passes_and_original_fixture_is_unchanged -v` passed 14/14.

After bounded Docker pipe capture, cidfile-based timeout cleanup and whole-fixture immutability assertions, a focused worker/ledger/Docker check passed 15/15, including a real positive fixture validation. Subsequent module-profile and ledger-read refinements passed worker/ledger tests 14/14. The full suite was run immediately before the final timeout-cleanup additions and passed 74 tests with 2 expected skips.

## Phase 4 — safe patch proposal and review workflow

Implemented in the current session:

1. Candidates must be text unified diffs with valid file/hunk headers. Each old/new path is checked against the approved step's exact file list and project source policy; traversal, excluded directories, protected files and binary diffs are rejected.
2. Reviewer decisions persist in `Review`. A positive reviewer decision leaves a candidate at `review_approved` and cannot start validation.
3. The user calls `POST /projects/{project_id}/patches/{patch_id}/approve` with the candidate SHA-256. This records hash-bound approval and is the only transition to `approved`.
4. Validation records require explicit user approval. The API does not apply diffs or invoke Docker.
5. Legacy unvalidated patches previously marked `approved` are migrated to `review_approved` and require explicit approval under this contract.

Phase 4 proposal/review/approval is complete. **Phase 5 worker implementation is complete (2026-09-15).** It applies only hash-approved diffs to a fresh temporary copy, supports up to three sequential allowlisted validation profiles, and records bounded evidence. The worker never writes to or mounts `E:\Android\AndroidStudioProjects\GtaCheatsApp-main`.

The trusted host-side entry point is `validation_worker.run_validation(project_id, patch_id, profile="test")`. Allowed profiles are `test`, `lint`, and `module_test`; staged runs pass a list of up to three unique profile names. `module_test` also requires a module present in that project's snapshot. FastAPI does not import the worker and has no Docker CLI/socket. The user must inspect and explicitly approve the exact diff SHA-256 through `POST /projects/{project_id}/patches/{patch_id}/approve` before any validation copy is created; reviewer approval alone is insufficient.

The worker re-reads the patch, approved plan step, persisted reviewer decision and user approval before copying and before each Docker stage. It rejects hash drift, rejected/superseded candidates, malformed/out-of-scope diffs, links/junctions, and disallowed profiles. It excludes known secret and generated-state paths from the copy, applies the diff only there, and invokes the existing executor. Reports include patch hash, commands and per-stage results, exit status, duration, bounded redacted output, image ID/digest when available, and the exact Docker security settings. The executor retains bounded stdout/stderr tails in memory, attempts to stop timed-out containers using their temporary CID file, and keeps the network, filesystem, privilege, and resource limits.

Worker unit tests cover rejected/missing approvals, hash drift, malformed/path-escape patches, command allowlisting, staged runs, output redaction/limits, source immutability, and cleanup after success, exception and timeout. Docker worker tests use only `tests/fixtures/kotlin-android`; the connected Android source was not validated.

## Documentation

- `PROJECT_EVOLUTION_ROADMAP.md` is canonical roadmap/status.
- `NEXT_STEPS_PLAN.md` contains legacy material plus authoritative current status.
- `README.md` has current project-aware safety status; older claims are historical.

## Phase 6 implementation status (2026-09-15)

Phase 6 is implemented. `model_router.py` defines provider-neutral completion and embedding requests/results, a LiteLLM adapter, deterministic task and quality preferences, context and budget checks, privacy gating, provider quota and expiring health state, bounded retries, and explicit fallback eligibility. `safe_llm_completion` preserves the existing LiteLLM response shape. Optional per-role `routing` settings are read from `roles.json`; legacy role files remain valid. Cloud calls require both `privacy_policy="cloud_allowed"` and `cloud_eligible=true`, plus a positive budget. The default is local-only.

The two embedding call sites use `EmbeddingRequest`, fixed to local `ollama/nomic-embed-text`; no vector store, model, dimension, collection, or persisted embedding changed. LiteLLM remains the only provider integration; credentials come from external runtime configuration. Telemetry accepts only bounded provider/task/quality/attempt/fallback metadata and excludes prompts, retrieved content, secrets and responses.

Verification in an isolated copy: `python -m unittest discover -v` passed 90 tests with 2 expected skips; Docker Kotlin/Android executor integrations passed against the copied fixture. Focused router and compatibility tests passed 14/14. No connected Android source or legacy `.vault` / `.vault_key` was changed. No dependencies were added. Phase 7 (offline local-model mode) is next.

## Phase 7 handoff — offline local-model mode

Phase 7 implementation is underway; offline continuation is not yet validated
end to end. Phase 6 already routes completion through
LiteLLM with local Ollama available and fixes RAG embeddings to the existing
`ollama/nomic-embed-text` model. Begin by auditing those paths and their runtime
health/model-availability behavior. Keep this runtime and embedding contract
unless a reproducible local test shows a concrete blocker. Do not migrate
ChromaDB, change embedding dimensions, or re-embed collections.

Before editing, search all model call sites and settings, then read the listed
handoff files plus only additional files found by that search. Start with
`model_router.py`, `runner.py`, `roles.json`, `rag_service.py`,
`ingest_knowledge.py`, `test_model_router.py`, and relevant runner/work-ledger
tests. Inspect dependency and Docker definitions only as needed to verify that
model weights, caches and credentials are not copied into the repository or
executor image.

The implementation should prove that a persisted task can continue using
local project RAG and a local completion route when external network access is
unavailable. Document the reduced local capability set (search/RAG,
summaries, continuation and any safe small-patch proposals). Model output never
grants reviewer approval, hash-bound user approval, or validation status. A
missing or unhealthy local model must produce an actionable failure and must
not trigger a cloud call when the task is local-only or cloud is disallowed.
Preserve default-deny cloud privacy/budget policy, the Docker validator's
`network=none`, the rule that the original Android project is read-only, and
FastAPI's separation from the trusted validation worker.

Test deterministically with injected provider fakes and no cloud credentials;
block external networking at the model-router/integration boundary for the
offline test. If an installed-Ollama test is added, label it as an optional
local integration check. Keep model files, Ollama caches, secrets and telemetry
outside the repository and Docker executor. Phase 7 is complete only when tests
prove local task continuation, documented capability limits, clear failure
without disallowed fallback, and no accidental transition to approved or
validated work.

The Phase 7 implementation adds an explicit process-start setting:
`MINI_AGENT_OFFLINE=1` (PowerShell: `$env:MINI_AGENT_OFFLINE = "1"`). The
default router then excludes every non-Ollama completion route, even if a role
allows cloud use. An unavailable local model surfaces a redacted provider
failure; it cannot fall through to a cloud adapter. Invalid setting values fail
router initialization. Start or resume an interrupted CLI task with
`python runner.py --resume <user_id>` after setting the environment variable.
Resume accepts only a saved `in_progress` state with a task, valid memory,
metrics and known agent turn; the cumulative agent-step limit is persisted.

Verification so far: the full suite passes in an isolated copy (96 tests run,
3 skipped, including the opt-in local integration test; Docker integrations
passed). An opt-in local
integration test also passed against the installed Ollama `qwen2.5:7b` and
`nomic-embed-text:latest`: it restored a SQLite work-ledger task, embedded and
retrieved project context in temporary Chroma, and completed through an
Ollama-only router. It required no cloud credentials; recorded adapter calls
were all Ollama. A separate runner resume test verifies that the actual
orchestration loop consumes saved state and invokes project retrieval. The
original Android project was not used or modified. Re-run the opt-in check with
`$env:MINI_AGENT_RUN_OFFLINE_INTEGRATION = "1"; python -m unittest test_offline_integration -v`.

## Next Codex CLI session — dedicated Phase 7 run

The user chose to create a separate test task. Do not resume or modify the
existing `data/user_123/state.json`: it is `in_progress`, has 11 memory items,
and has no `project_id`, so it is unrelated to the registered Android project.
Use the dedicated runner user ID `phase7_offline_test`; its state and generated
files belong under `data/phase7_offline_test/`. Link the synthetic state to
registered project `gta-cheats--cc0fe5de` so retrieval uses that project's
snapshot and RAG. The source `E:\Android\AndroidStudioProjects\GtaCheatsApp-main`
remains read-only: do not open it directly, mount it, or validate against it.

Ollama is already running in the Windows tray. `ollama list` confirmed
`qwen2.5:7b` and `nomic-embed-text:latest`; the local API answered at
`http://localhost:11434`. `ollama ps` showed no model loaded, so the first
inference may cold-load weights. Do not start a second `ollama serve` unless
the local API check fails. Set `MINI_AGENT_OFFLINE=1` before Python starts so
the singleton model router is initialized in offline mode. The repository's
opt-in integration command is:

```powershell
$env:MINI_AGENT_RUN_OFFLINE_INTEGRATION = "1"
python -m unittest test_offline_integration -v
Remove-Item Env:MINI_AGENT_RUN_OFFLINE_INTEGRATION
```

For the full runner check, create a separate, clearly synthetic `in_progress`
state for `phase7_offline_test`, with `project_id="gta-cheats--cc0fe5de"`, a
bounded task asking for a Markdown architecture summary in the dedicated
sandbox workspace, a valid Coder turn, metrics and memory. Resume it only with
this process environment:

```powershell
$env:MINI_AGENT_OFFLINE = "1"
python runner.py --resume phase7_offline_test
```

Verify the task's RAG retrieval is labelled for the registered project, every
completion call is Ollama, the generated file stays under
`data/phase7_offline_test/`, and no approval/validation status is inferred from
model output. Test unavailable-local-model behavior with an injected failing
adapter; do not stop the user's Ollama service to simulate failure. Confirm
the task remains `in_progress` and no cloud adapter is called. Keep the
synthetic state as a separate test artifact; do not alter `user_123`, legacy
vault files, or other user workspaces. Do not commit.

Docker Desktop is already running and Docker CLI is installed at
`C:\Users\AlSaintUk\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe`.
`docker info` reported Docker Desktop 29.8.0 / `docker-desktop` when run with
daemon permission. A restricted command context may get access denied to the
Docker named pipe; the Ollama/RAG check does not need Docker. Use Docker CLI
only if running executor validation, and retain `network=none` and all
existing executor limits.

### Copy/paste prompt for Codex CLI

```text
Continue Phase 7 in C:\Users\AlSaintUk\Desktop\Mini Agent Sandbox.
Read CODEX_HANDOVER.md and the files listed below first. Run the task under the
separate user_id phase7_offline_test; do not run or change user_123.

Goal: verify a real offline runner.py --resume flow with local Ollama and RAG
for the registered project gta-cheats--cc0fe5de. Create only a separate
synthetic task state with status in_progress, bind it to that project_id, and
ask the agent to prepare a short Markdown architecture overview in its isolated
sandbox workspace. Set MINI_AGENT_OFFLINE=1 before the run. Confirm that
retrieval is scoped to project_id, every completion call goes only to Ollama,
and files appear only under data/phase7_offline_test/. Do not open, mount, or
modify E:\Android\AndroidStudioProjects\GtaCheatsApp-main.

Separately test Ollama unavailability through a failing fake adapter without
stopping Ollama Desktop. The call must end in a safe error, task state must
remain in_progress, and no cloud calls may occur. The existing
test_offline_integration.py used real qwen2.5:7b and nomic-embed-text:latest;
do not replace its responses with fakes, and rerun it with the command from the
handover. Use the fake only for deterministic failure-policy verification.

Docker Desktop is already running. Docker CLI is available, although named-pipe
access may require an authorized context. Docker is not needed for the
Ollama/RAG step. If executor validation is run, use only the Docker worker, a
temporary copy, and the existing network=none and resource limits. Do not run
Gradle on Windows.

Afterward, run the focused and full tests and update CODEX_HANDOVER.md,
NEXT_STEPS_PLAN.md, PROJECT_EVOLUTION_ROADMAP.md, and README.md with observed
results. Mark Phase 7 complete only if the real resume flow, project-scoped
RAG, Ollama-only routing, and safe failure are demonstrated. Do not add
dependencies or make a Git commit.
```

### Minimal context file list for Codex CLI

Read first:

- `CODEX_HANDOVER.md`
- `PROJECT_EVOLUTION_ROADMAP.md` (Phase 7)
- `NEXT_STEPS_PLAN.md` (canonical current status)
- `README.md` (current project-aware status)

Implementation and test context:

- `model_router.py`, `runner.py`, `roles.json`
- `rag_service.py`, `project_retrieval.py`, `project_registry.py`
- `work_ledger.py`
- `analyst_agent.py`, `evals_pipeline.py`, `ingest_knowledge.py` (model-call-site audit)
- `test_model_router.py`, `test_offline_integration.py`, `test_arbitrator.py`
- `test_project_retrieval.py`, `test_work_ledger.py`

Only if executor validation is needed: `validation_worker.py`,
`sandbox_executor.py`, `Dockerfile.executor`, and the relevant Docker tests.
Do not load the whole repository or source Android project into context.
## Phase 7 workspace rerun (2026-09-15)

The real Ollama/temporary-Chroma opt-in check passed 1/1 after the local adapter and validator changes. The focused router/runner/retrieval/ledger/RAG/validation set passed 31/31; full `python -m unittest discover -v` passed 98 tests with 3 expected skips, including Docker checks on copied fixtures. No Android project source was validated.

A separate CLI resume was run as `phase7_offline_test` with `MINI_AGENT_OFFLINE=1` and project ID `gta-cheats--cc0fe5de`. Telemetry records completion calls through Ollama, and the task created `data/phase7_offline_test/architecture_summary.md`. The standard Android Coder/Reviewer/Analyst loop did not finish this documentation task: it also created three unrelated Kotlin files and the state remains `in_progress` (step 3 when stopped). These artifacts remain confined to the dedicated test workspace; no approval or validation status was recorded. The generated summary is a test artifact, not linked from the project documentation.

Two concrete blockers were fixed and covered by tests: Ollama completions now preserve tool schemas, and a Markdown-only workspace passes the no-code validation branch. The CLI integration gate remains open because the generic Android review cycle does not reliably complete bounded documentation tasks. Keep Phase 7 in progress.

The run also recorded an `update_project_fact` tool call that wrote a canonical fact into the synthetic user's `project_facts.json`. That generated file was removed from the isolated test workspace; blocking unsupported model-driven knowledge promotion remains an open safety item.

## Phase 7 handoff update — latest verified state (2026-09-15)

This update supersedes earlier Phase 7 run notes in this file. Verification completed after the latest documentation-mode and offline-router changes:

- `python -m unittest discover -v`: **103 tests passed, 3 skipped** (two environment/integration skips and the opt-in Ollama test).
- `$env:MINI_AGENT_OFFLINE = "1"; $env:MINI_AGENT_RUN_OFFLINE_INTEGRATION = "1"; python -m unittest test_offline_integration -v`: **1/1 passed** using installed Ollama and temporary Chroma.
- The saved `data/phase7_offline_test/state.json` belongs to `phase7_offline_test`, links to `gta-cheats--cc0fe5de`, and is currently `in_progress`, `task_mode=documentation`, `current_turn=coder`. Latest runner telemetry records only `ollama/qwen2.5:14b` completion calls. The resume created `data/phase7_offline_test/architecture_summary.md` but the model repeated `create_file` three times and the circuit breaker stopped the turn. It did not complete. The old unrelated Kotlin artifacts were removed from this dedicated test directory; do not recreate them. No `user_123` state or Android source was used or modified.
- The safe-failure policy is covered by `test_offline_local_failure_never_attempts_cloud_fallback`; the documentation-mode tests cover Markdown-only tools/paths, denied model fact mutation, and no automatic fact ingestion. Rerun these after any code changes.

### Immediate continuation for the Codex CLI session

1. Inspect the current `runner.py`, documentation-mode tests, saved `phase7_offline_test` state and telemetry. Do not reset or replace the saved state unless a structural defect makes it unresumable.
2. Fix the loop at the orchestration boundary: once a documentation-mode `create_file` succeeds for the requested `.md` artifact, stop requesting more coder tool calls and continue to the documentation reviewer. The reviewer should have read/list tools only. Add a regression test proving one successful write is sufficient to advance; repeated model tool calls must not create repeated files or invoke the generic Analyst path.
3. Resume only this ID with `MINI_AGENT_OFFLINE=1`. Confirm project-scoped retrieval for `gta-cheats--cc0fe5de`, only Ollama completion telemetry, a completed documentation review, and no approval/validation fields or fact mutations. Confirm the only deliverable in the dedicated workspace is `architecture_summary.md` (besides runner state/telemetry/key files).
4. Rerun focused tests, the opt-in local integration, and the full suite. Update this file, `NEXT_STEPS_PLAN.md`, `PROJECT_EVOLUTION_ROADMAP.md` and `README.md` with the new observed result. Keep Phase 7 **in progress** unless the real resume and all handover exit criteria pass.

Do not run another `codex exec` from this task: the user already has the Codex CLI open in a terminal. Do not change `data/user_123`, `.vault`/`.vault_key`, the registered Android source, dependencies, or Docker configuration. Do not commit. The workspace contains existing uncommitted/untracked project files; do not use broad reset/restore/cleanup commands.

Prompt to paste into the already-open CLI if it needs a steering message:

```text
Continue Phase 7 using the latest “Phase 7 handoff update — latest verified state” in CODEX_HANDOVER.md. Work in this repository with the local model configured for this CLI session. Do not start another codex exec. First inspect the current documentation-mode runner and tests. The dedicated state is data/phase7_offline_test/state.json (project gta-cheats--cc0fe5de); its last real runner resume used Ollama only but remained in_progress after three repeated create_file calls. Fix the orchestration boundary so the first successful create_file in documentation mode ends the coder tool loop and proceeds to a read-only reviewer; add a regression test. Then resume only phase7_offline_test with MINI_AGENT_OFFLINE=1, verify RAG project scope and local-only telemetry, no model fact mutation, no approval/validation, and only the requested Markdown deliverable. Run focused tests, opt-in Ollama/Chroma integration and full unittest suite. Update the four status documents only with verified results. Do not touch user_123, Android source, vault files, dependencies, Docker configuration, or make a commit.
```


## Phase 7 continuation result — 2026-09-15, 17:38 UTC

This section supersedes earlier continuation instructions and test counts.

The repeated-create_file orchestration bug is fixed. In documentation mode the
first successful write ends the Coder turn, including any remaining calls in
the same model response. Reviewer tools are read/list only and this restriction
is enforced at dispatch. The runner supplies the actual bounded Markdown file
to the Reviewer because the first real review incorrectly claimed it did not
exist without reading it. Documentation rejection never enters Arbitrator.
Step/budget exhaustion now preserves in_progress instead of claiming completion.

The existing phase7_offline_test state was resumed without resetting it, with
MINI_AGENT_OFFLINE=1. The final run completed at agent_steps=6; the saved final
Reviewer response is {"decision": "APPROVE"}. All completion telemetry is
ollama/qwen2.5:14b with provider=ollama. The saved project ID remains
gta-cheats--cc0fe5de. A separate real retrieval check returned project-code
hits from this project's local Chroma collection; retrieval reads the snapshot
and collection, not the Android source tree. This run used offline routing;
the opt-in integration separately blocks external networking at its boundary.

The only deliverable is data/phase7_offline_test/architecture_summary.md.
Other files are state.json, telemetry.json, the existing .vault_key, and the
runner-generated incident_summary.json. There is no project_facts.json and no
approval/validation field in saved state. The documentation verdict does not
approve a code patch or establish validated knowledge. No user_123 or Android
source changes were made; no dependencies, Docker settings or commits changed.

Verification: focused suite 33/33 passed; real opt-in Ollama/temporary-Chroma
integration 1/1 passed. Final full unittest suite: 107 tests run, 104 passed,
3 skipped, including Docker checks on copied fixtures. New regression tests
cover the single-write transition, denied reviewer writes, actual artifact
context, local-model failure preserving in_progress with no cloud calls, and
step/budget exhaustion preserving in_progress.

Phase 7 remains in progress for a documented quality gate: despite the real
resume completing, the final Markdown summarizes DTO structures and omits the
requested source-path citations. The model Reviewer accepted it anyway. The
runtime continuation gate passed; evidence-grounded documentation review is
not yet reliable. Do not present the Markdown or the generated terminal summary
as a verified architecture reference. Next work should enforce evidence/source
checks at the orchestration boundary and test rejection of uncited output.
The saved test task is now completed, so ordinary --resume will reject it;
do not silently reset it. Preserve it as evidence of this run.
# Product priority — agentic code generation

The sandbox is being developed as an agentic code-generation tool. Its canonical integration profile is `gta-cheats--cc0fe5de`, registered for `E:\\Android\\AndroidStudioProjects\\GtaCheatsApp-main`. Existing saved retrieval evidence includes `MainActivity.kt`, `settings.gradle.kts`, and `gradle.properties`; it is real project context, not a synthetic fixture.

Do not confuse that evidence with a real Gradle run on the connected source: the source remains unmodified and Docker evidence is fixture-only. The runner now binds a project-code task to an approved plan step through `--project-patch <project-id> <approved-step-id> <user-id>`: Coder has only `propose_patch`, which persists a unified diff through `WorkLedger`; a structured Reviewer approval records review only. The next product proof is a bounded GTA run through explicit user approval and temporary-copy Docker validation. Do not spend the next increment on a graphical frontend, auto-apply, destructive cleanup, or destructive knowledge deletion.
## Phase 8 codegen recovery status (latest)

`runner.py` now has a bounded project-patch bridge: Coder can only propose a
diff; policy and WorkLedger validate it before persistence; Reviewer records no
user approval or apply. Native tool calls, JSON diffs and narrowly parsed
malformed Qwen envelopes pass through the same checks. Focused tests last
passed 26/26.

The GTA task `task_3cf6b6422d16432da3133cdd9d016d2a` is bound only to
`feature/gta_v/src/main/java/com/gamescheats/feature/gta_v/screen/GtaVCheatCodesScreen.kt`.
Three candidates were Reviewer-rejected; none has approval or validation. The
next blocker is a local `qwen2.5:14b` completion stall before first response.
Diagnose that boundary without fake proposals, direct Android writes, apply, or
pre-approval validation.
## Phase 13.1 handover — completed 2026-09-21

Phase 13.1 completed the deliberately deferred Qwen/Ollama tool-message
accounting. `context_token_accounting.py` now uses the verified external Qwen
tokenizer asset only with `MINI_AGENT_QWEN_TOKENIZER_DIR` and both SHA-256
checks. The supported exact formats are fixed text chat (26 tokens), declared
basic function schema (135), assistant tool call (52), and tool response (76).
All other model identifiers, unmeasured message forms, and unfamiliar tool
schema extensions remain visibly `legacy-estimate`; they are not labelled exact.

The installed `qwen2.5:14b` Modelfile and Ollama 0.21.0 debug render were
inspected. Its tool template prints a Go function structure rather than the
incoming JSON verbatim. A one-token difference between that debug-rendered
schema and the standalone tokenizer asset is calibrated only for the declared
tool-schema path, against a real local `prompt_eval_count=135`; it does not
apply to text or tool history. The runner creates `turn_tools` once and passes
it to both the counter and completion call; `ModelRequest` forwards declared
tools to the same counter.

No RAG/Chroma, GTA source/profile, facts, knowledge, session data, Docker,
Gradle, model weights, or tokenizer files in `E:` were changed. Verification:
33 focused counter/router/manifest tests and the full deterministic suite
(178 tests, 15 expected skips) passed; focused Ruff and `git diff --check`
passed. A clean installation was not rerun: the direct
`tokenizers` pin is manifest-covered, while the intentionally external model
asset is optional and its absence safely selects fallback. Do not remove or
replace the external asset; do not widen exact mode without new measured local
fixtures.

Phases 13/13.1 were committed and pushed as `ffd0fd0` on 2026-09-21.

## Phase 14 historical planning record — superseded by completion

The authoritative historical finding was that legacy per-user vector RAG had
an append helper but no explicit main-loop
document ingestion contract. The current system is richer than that historical
snapshot: project-code RAG, verified project knowledge, and global books are
already separate. Phase 14 may add only an explicit project-bound supplemental
document collection and pipeline; it must not turn the old legacy collection
into a catch-all memory.

This record predates the completed implementation below. The obsolete Phase 14
preparation/continuation files were intentionally removed; use the completion
record, roadmap and analysis for historical detail. Its original boundaries
remain: no corpus re-indexing, conversation/model-output ingestion, automatic
knowledge promotion, connected-source changes, or policy/Docker/Gradle/provider
workflow changes.

## Phase 14 handover — completed 2026-09-21

The legacy user-RAG finding from analysis item 14 is closed by a separate,
explicit project-document pipeline, not by mixing memory tiers. New
`project_document_ingestion.py` accepts only confirmed request-body text or
Markdown for a registered project; it refuses arbitrary file paths, unknown
projects, invalid sources, unsupported types, oversized input, and unconfirmed
writes/removals. It stores only manifest metadata plus checksum/chunk IDs and
uses a distinct `project_*_documents` collection.

Project retrieval returns active supplemental documents with their own
`project-document` scope/trust label after project-code and verified knowledge.
They do not satisfy Phase 10 project-code evidence and cannot create facts or
knowledge cards. Focused tests passed 26/26, focused Ruff passed, and the full
deterministic suite passed 185/185 with 19 expected skips. A real local
Ollama/Chroma fixture run retrieved only its own document; its complete
`data/phase14_integration` fixture was deleted. GTA/global corpora, connected
source, facts, knowledge, session data, Docker and Gradle remain untouched.

## Phase 14.1 handover — completed 2026-09-21

The Python test suite now lives under `tests/`: `sandbox/` for Mini Agent
Sandbox contracts, `project_rag/` for generic registered-project/RAG contracts,
and `integration/` for Docker or opt-in local-Ollama checks. The existing
`tests/fixtures/kotlin-android` remains synthetic; GTA Cheats source, snapshots,
RAG stores, model caches and runtime data are not test fixtures and must never
be committed.

All 38 root test modules were Git-renamed without deleting tests or changing
production code. The ordinary command is now
`python -m unittest discover -s tests -t . -v`; it passed 181 tests with 19
expected skips. `python -m ruff check tests` passed. Docker and local-Ollama
checks were intentionally not activated. Do not restore root-level compatibility
wrappers; use fully-qualified module paths documented in `AGENTS.md` and
`TESTS.md`.

## Phase 15 handover — in progress 2026-09-22

Phase 15 addresses analysis item 15: `DataGuardrail` currently combines a
small regex/context secret masker with tag deletion. The work separates these
threat classes. The permitted implementation is a standard-library structured
SecretScanner with provider rules and context-gated entropy, plus a separately
named, compatibility-only prompt-injection boundary. Preserve
`DataGuardrail.run()` and existing vault token persistence.

Do not install or invoke an external scanner, scan live data, run local models
or evals, touch RAG/GTA/Docker/Gradle, alter vault paths, log plaintext values,
or change `resolve_secrets()`/tool authority. Prompt-injection protection must
not be described as complete. This planned handover is historical; the phase
completion record follows.

## Phase 15 handover — completed 2026-09-22

`secret_scanner.py` replaces the single pass with plaintext-free structured
findings, provider-first overlap selection, provider detectors, generic
credential assignment detection and context-gated Shannon entropy. Existing
OpenAI-style/AWS/email/IPv4 masking remains, while GitHub, GitLab, Slack,
Stripe and private-key blocks are now bounded provider rules.

`prompt_injection.py` separately owns the legacy paired-tag removal. It is a
compatibility boundary only, creates no vault mappings, and is not claimed as
general prompt-injection prevention. `DataGuardrail.run()` and tenant-scoped
vault token persistence remain compatible. Focused guardrail/vault tests passed
10/10; the full deterministic suite passed 188 with 19 expected skips; Ruff
and diff checks passed. No dependency, model/evals, Docker, RAG/GTA, Gradle or
live vault data was used. Do not add an external scanner or widen provider
patterns without a new reviewed dependency/scope decision.

Post-phase real integration (2026-09-22): real temporary Ollama/Chroma
component integration passed 1/1. An actual offline `runner.py` process in a
new disposable `E:` copy masked a synthetic GitHub-shaped token before its
`state.json` write, but remained `in_progress` after 3 turns and 10 tool
executions, producing unnecessary isolated workspace files. It was terminated;
the whole copy (including state/vault/artifacts) was deleted and loaded models
were explicitly unloaded. Full agent-loop completion is not accepted. Treat
the observed loop nondeterminism as an operational blocker requiring a separate
bounded diagnosis, not as evidence to weaken security/tool limits.

Correct GTA baseline validation (2026-09-22): use only the saved Android/GTA
RAG questions, not a generic Python task. The real local Analyst→Reviewer
`tools:targetApi="31"` manifest question passed. The `MainActivity`
`MAIN`/`LAUNCHER` manifest question did not. Read-only Chroma audit found two
adjacent manifest chunks: one contains `.MainActivity` and `MAIN`, the other
contains `LAUNCHER`; current retrieval supplied only the latter. Analyst and
Reviewer correctly declined to infer a fact absent from their evidence. Treat
this as historical fail-closed evidence. The bounded Phase 9 correction is now
implemented and accepted: literal selection assembles only that selected
source's stored chunks, and fusion preserves the assembly over a semantic tail
chunk. The same real Android question now names `.MainActivity` in both
answers. Do not weaken grounding, edit the connected source, re-index the
corpus, or expand source assembly beyond its bounded selected-source contract
without separate scope and acceptance tests. The full deterministic suite
passed 190 tests with 19 expected skips; changed retrieval files pass Ruff.
All temporary output was removed after the run.

## Phase 16 handover — planned 2026-09-22

Phase 16 addresses analysis item 16: persistent Vault isolation must be
explicit and tenant-scoped. Reconciliation already found that the checked
source has `get_user_vault(user_id)` with validated IDs and separate
`data/<user_id>/.vault` / `.vault_key` files. Do not treat the historical
global-vault description as authorization to rename or migrate live data.

This planned handover is historical; the phase completion record follows.
Audit every constructor and persistence call first. Any filename migration to the desired
`vault.enc` / `vault.key` layout must be same-user, conflict-fail-closed,
verified, and non-destructive; live migration needs separate operational
approval. Use temporary fixtures only. Do not log/decrypt live secrets, add a
KMS/dependency, change secret-resolution authority, or touch RAG/GTA/Docker/
Gradle/models/policy/roles/approval/validation/task state/facts.

## Phase 16 handover — completed, committed and pushed 2026-09-22

Commit `ae15081` (`Isolate tenant vault persistence`) is on `main` and
synchronized with `origin/main`. The audit confirmed that production Runner
and Guardrail call sites use `get_user_vault()`; no direct production `VaultRegistry` construction was
found. Canonical tenant files are now `vault.enc` and `vault.key`. Complete
legacy hidden pairs are first decrypted, then copied only when canonical files
are absent; they are not deleted. A same-key canonical mapping may extend the
legacy mapping, but divergent pairs, incomplete pairs, invalid file types and
symlinks fail closed. Existing encrypted vaults cannot be silently re-keyed.

Focused Vault/guardrail tests passed 17/17 with one expected Windows real-
symlink fixture skip; a deterministic mock independently covers symlink
refusal without Windows privileges. The full deterministic suite passed 197
tests with 20 expected skips. No live vault/RAG/GTA/model/Docker/Gradle data
was touched. Do not run a live migration or delete legacy files without a
separate backup-first operational approval.

## Phase 17 handover — completed locally 2026-09-27

Phase 17 addresses analysis item 17, not Vault persistence. The new
`secret_capabilities.py` registry is static and empty in production; Runner
tool authorization occurs before any capability-scoped Vault lookup. The
former generic resolver and token logging are removed, and current file,
directory, fact, and patch arguments retain opaque tokens.

Focused tests passed 5/5; the deterministic suite passed 202 tests with 20
expected skips. Ruff passed for the new module/tests; `runner.py` has 10
pre-existing findings outside this phase. An initial unit-test import attempted
LiteLLM's remote cost-map refresh, which the sandbox refused; no external
request succeeded. Subsequent verification used `LITELLM_LOCAL_MODEL_COST_MAP=True`.
No live vault, model, RAG/GTA, Docker, or Gradle operation occurred. Do not add
a plaintext capability or restore generic deobfuscation
without a separately approved trusted tool, exact parameter, and regression
coverage.

## Phase 18 handover — completed locally 2026-10-01

Analysis item 18 is narrowed by current-source inspection. The runtime has a
mock confirmation branch for `send_email`, `access_calendar`, and `web_search`,
but these tools are absent from `AGENT_TOOLS`; authorization rejects them
before the branch, and its success path is mocked. A distinct human approval
flow exists for project patches and binds approval to the reviewed diff
SHA-256 before validation.

Phase 18 removed the unreachable mock branch, added focused fail-closed tests,
and corrected broad HITL claims in `README.md` and `TESTS.md`. The capability
suite passed 6/6 and the exact-SHA patch-approval API test passed 1/1. Ruff
passed for the changed test module; `runner.py` retains 10 pre-existing
findings. No external tools or RAG work occurred. The completion record is
consolidated in this handover.

## Standalone Project Catalog and Q&A task — implemented locally 2026-10-01

The user approved `TASK_PROJECT_CATALOG_AND_QA.md`; this is a standalone task,
not Phase 19. Catalog metadata fields and an explicit migration method are in
`project_registry.py`. The live SQLite database was migrated backup-first on
2026-10-01 after separate approval. Remote repository clone/fetch remains out
of scope.

`project_qa_service.py` is the single project-Q&A implementation used by
Runner and the compatibility CLI. It binds retrieval to the selected project,
checks retrieved source paths and hashes against the saved project snapshot,
reports a derived snapshot revision, and refuses stale, malformed, missing, or
cross-project evidence. These checks prove evidence provenance, not semantic
entailment. Q&A role settings are isolated in `roles.json`; local primary and
fallback Ollama models are discovered for unload from configured roles.

Verification: 225 deterministic tests passed with 20 expected skips. The exact
historical GTA manifest question returned `tools:targetApi="31"` from
`app/src/main/AndroidManifest.xml`; final `ollama ps` was empty. Focused Ruff
checks passed. `ruff check runner.py` still reports 9 pre-existing findings
outside task edits. No remote repository access, GTA source edit, RAG rebuild,
Docker, or Gradle operation occurred. The LiteLLM metadata-map
refresh was disabled for deterministic tests with
`LITELLM_LOCAL_MODEL_COST_MAP=True`.

After migration, the registry backup is
`data/registry/backups/projects-20261001T165819Z.sqlite`. Its integrity,
schema, and rows were verified against the source before migration. The live
database integrity is `ok`; the existing GTA project ID, name, checkout path,
and timestamps are unchanged. Its user-provided description and optional
GitHub URL are stored separately from the local checkout path. No branch or
resolved revision was provided. No GitHub access, source edit, RAG rebuild,
commit, or push occurred.

## Scoped project_qa Vault orphan recovery — 2026-10-01

`get_user_vault()` now repairs only the `project_qa` key-only orphan state:
it verifies a unique backup of the preserved key before writing an encrypted
empty mapping. Invalid keys, missing keys, conflicting or symlinked paths, and
other users' incomplete pairs still fail closed. Focused Vault/Guardrail tests
passed 20 tests with one expected Windows symlink skip. The live
`data/project_qa` files were not changed in this verification; metadata-only
inspection found both canonical and legacy pairs already present.

## Phase 19 handover — completed locally 2026-10-01

`runner.py` now allows at most N tool calls per turn and blocks attempted call
N+1 before dispatch. The saved `breaker_blocked` state contains a structured
incident and is not resumable. The user-facing recovery actions are
`python runner.py --reset USER` or starting a new task. No Analyst handoff or
model-backed regulator action follows the stop. Earlier calls are not rolled
back. `python -m unittest tests.sandbox.core.test_tool_circuit_breaker -v`
passed 2 tests; 11 adjacent resume, documentation-transition, and
session-lifecycle tests passed. The full suite was not run because focused and
adjacent deterministic coverage directly exercises the changed contract. Two
local-only live Runner attempts did not reach the breaker: after valid tool
dispatch, Qwen returned a tool-call-shaped JSON string as ordinary content and
Shift-Left validation stopped on `No supported source files found for
validation`. Both disposable test states were preserved; no project source was
changed. The Markdown-only validator also counts the disposable user's
`vault.enc` and `vault.key` as artifacts; this adjacent behavior was not changed.
Manual Ollama unload succeeded and `ollama ps` was empty. Live
end-to-end acceptance remains unproven and needs separate diagnosis. No commit
or push was made. The later acceptance result is consolidated above.

## Active Phase 19 offline follow-up — 2026-10-01

The user authorized a pinned, stepwise diagnosis and focused fixes. Step 1
comparison is complete: historical Phase 7 state records five successful
`create_file` executions and Ollama/Qwen telemetry, but aggregates 15 records
over about an hour without per-run IDs or raw response shapes. Both failed
Phase 19 attempts used only Ollama/Qwen; their saved executions show two failed
`read_file` calls in one run and one successful `create_file` in the other,
followed by tool-call-shaped JSON treated as ordinary assistant content.
Neither reached the breaker. This does not establish regression or root cause.
Source-path tracing is complete: `LiteLLMAdapter` and `ModelRouter` pass the
completion response through; `safe_llm_completion` sanitizes content without
normalizing tool calls; Runner dispatches only native `message.tool_calls` and
treats content-only JSON as an answer. Historical state has no raw responses,
so this explains the handling but not why Qwen returned that shape. Current
one approved Runner CLI probe in `phase19-runner-probe-20261001` created the
expected workspace artifact. All three telemetry records were local
`ollama/qwen2.5:14b`; no cloud provider appears. The saved state nevertheless
remains `in_progress` with zero tool-execution records and only user memory.
The source only writes such a file via native tool dispatch, but the missing
saved record and unexplained early stop mean end-to-end acceptance is not
proven. Source confirmed the save boundary: tool records were volatile until
turn completion, and caught exceptions were not persisted. The exact exception
from that run was not logged and is unrecoverable. Runner now saves each tool
execution immediately and records only safe exception category/type/stage
metadata on early exit. A failure-injection test plus breaker,
documentation-transition, and validation tests passed 15/15; Ruff passed for
the new test module. The confirmed validator bug that counted
`vault.enc`/`vault.key` as artifacts is fixed (7/7 focused tests). One offline
system-library question created a 1,560-byte answer citing *Jetpack Compose
Internals*, but code-mode Runner repeated `create_file` three times and was
stopped at five minutes before Reviewer/completion. The three tool records
persisted; retrieved global-library chunks are not persisted, so grounding is
unverified. Ollama was stopped and `ollama ps` was empty. Current step:
inspect/fix repeated-write turn behavior and retrieval provenance; preserve both
probe profiles and do not make another model request without approval. Do not
inspect Vault contents. The subsequent acceptance result and current
instructions are consolidated at the top of this handover.
