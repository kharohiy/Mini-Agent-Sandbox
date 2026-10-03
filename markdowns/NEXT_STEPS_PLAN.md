## Direct-callee evidence did not repair Qwen review - 2026-10-03

The controlled reordering experiment failed and was reverted. Retrieval already
supplies the required facts, and placing them immediately after the requested
method did not change the omission. Do not add more retrieval heuristics or
repeat the same Qwen call. A next decision should explicitly choose whether the
current concise answer is acceptable for this small local model or whether a
different offline verifier/model is required for deeper evidence tracing.

## Prompt-only Reviewer repair was insufficient - 2026-10-03

Do not spend more live calls retrying the same checklist. It removed unsupported
timing/praise but did not surface the available callee implementation. Any next
repair should improve deterministic evidence presentation for the named method
and its directly called project methods, then reuse the exact acceptance facts.
Do not change token limits, project isolation or code-task orchestration.

## Project-Q&A quality defect - 2026-10-03

Exact-file retrieval succeeded for `GtaSaViewModel.kt`, but Analyst and Reviewer
both omitted available refresh implementation details. The next repair must stay
inside project-Q&A answer completeness/review behavior; do not change retrieval,
model output limits, code-task contracts or GTA source based on this observation.

## Shared-book retrieval checkpoint - 2026-10-03

The bounded same-section continuation repair passed the real before/after Runner
check. Do not repeat the Compose slot-table question without a new regression.
The next user-gated live step remains project-selected GTA Q&A; it has not been
run as part of this repair.

## Current checkpoint - Phases 20–22 closed locally, 2026-10-02

Do not resume prose-scored security evals or automatic Regulator self-editing.
The behavioral manifest, advisory proposal gate and security-boundary matrix are
accepted locally. Full suite: 261 OK, 8 expected skips; Docker outbound socket
denial passed. Read the Phase 20–22 preparation and continuation records.

No new phase is authorized by this closure. The next separate candidates are
CLI exit codes for blocked tasks and a bounded successful code-task acceptance.
Neither is required to reopen Phases 20–22. The current code and documentation
changes are local and not yet committed/pushed.

## Earlier checkpoint - Phase 19 closed locally, 2026-10-02

The real offline Runner reached N+1 and stopped before call six, with five
persisted calls, breaker_blocked, a durable incident and actual resume rejection.
Read the final record in `CODEX_HANDOVER.md` and
`OFFLINE_ACCEPTANCE_20261002.md`. Do not repeat the passing breaker
or Navigation.kt runs without a new defect. Preserve their states and captures.

The output-budget and native tool-transport fixes are local and not yet
published. Further work needs its own agreed scope: full successful code-task
acceptance and CLI exit codes for blocked tasks remain separate unresolved
items. Historical duplicate-write observations are not silently declared fixed
by the transport change. No new phase or broader acceptance is inferred.

## Earlier checkpoint - output repair verified, 2026-10-02

Publication of the prior fixes is complete (870b2bc). The Navigation.kt output
repair passed one real offline Runner run: complete code block plus explanation,
both agents stop normally at 507 tokens, exit 0. The bounded limit is now 2048;
length termination is explicitly reported. See the latest handover/acceptance.
Do not repeat this successful run without a new defect. Book augmentation is
unchanged. Phase 19's separate live N+1 and code-task issues remain unresolved;
their earlier traces remain the starting point for any subsequent scoped work.

## Previous user-directed priority - 2026-10-02

1. Publish the accumulated offline fixes and this documentation checkpoint.
2. Then investigate project-Q&A output truncation: the user's Navigation.kt
   answer found the correct file but stopped mid-code, without the requested
   explanation. Inspect completion metadata/finish_reason and the existing
   200-output-token budget per agent before choosing a narrow repair. Do not
   infer the stop reason from the transcript alone or redesign agent contracts.
3. Keep project facts grounded in selected-project evidence; any future book
   augmentation provides separately labelled technical explanations. No corpus
   reindexing or GTA modification is justified by the observed truncation.

Phase 18 remains closed; Phase 19 live N+1 acceptance remains open. The earlier
code/breaker work below is still unresolved but follows this user-set priority.
No further model run is required merely to publish the documented fixes.

## Earlier next work after actual acceptance - 2026-10-02

QA routes completed; do not rework them based on prose-quality judgments.
Phase 18 remains closed. Phase 19 live N+1 acceptance and a successful full
code-task route remain open. Start with the code/breaker transcripts in
`data/offline-acceptance-20261002`: duplicate file writes and tool-shaped ordinary
content are recorded. Determine the narrow protocol/workflow defect before
changing prompts, tool parsing or orchestration. Do not execute assistant text
as tools or use GTA/Gradle to force a pass. The CLI's exit 0 for blocked tasks
is also recorded as a separate unresolved presentation issue. No new broad
model retry loop is prescribed. See `OFFLINE_ACCEPTANCE_20261002.md`.

## Active priority - actual offline orchestration acceptance

Follow `OFFLINE_ACCEPTANCE_20261002.md`. The user authorized restoring ordinary
Reviewer text output, optional book failure handling, and actual CLI scenarios:
general QA, book QA, explicitly selected project QA, isolated code-task failure
handling, and the real per-turn tool breaker. Preserve all evidence. Generated
answer accuracy is a separate topic and is not a phase/runtime pass criterion.
Phase 18 is complete within its deterministic scope. Phase 19's live acceptance
must be judged from the recorded N+1 event, not from successful Q&A.

## Historical priorities below - superseded where they grade answer semantics

## Active priority — offline Q&A correctness and shared-book evidence

2026-10-02: structured model review and an isolated shared-book reader are
implemented. This restores book access for ordinary questions while keeping
project selection explicit. Thirteen focused tests pass. One real run without
books still produced an invalid import; model review is not a correctness gate.
The book-enabled run retrieved three irrelevant reflection/DSL excerpts for
the dispatcher question. All three original PDFs remain represented in the
2,293-chunk index. Two literal `Dispatchers` hits concern Compose in browsers,
not the requested Android dispatcher examples. Do not infer adequate coverage
from a non-empty retrieval or replace missing evidence with invented citations.
The book-enabled answer also remains incorrect (lifecycleScope context/imports);
both runs finished and models are unloaded. Read the latest preparation result before further work; no blind retries or
new corpus ingestion. Preserve all profiles and the original failed state.

## Previous priority — repair the ordinary Runner question/answer workflow

The user authorized repairing the CLI workflow and completing the actual
Runner run with `mobile kotlin coroutines. show few examples of dispatchers`.
General questions must have no project unless explicitly selected in the menu.
The new menu and bounded Analyst/Reviewer path completed actual CLI runs with
both user questions, final text, exit code 0 and automatic unload. The repeated
code-validation loop no longer occurs for general questions. Reviewer still
accepted incorrect coroutine snippets and terminology: semantic correctness
remains open. Do not turn this workflow result into an all-system success
claim or repeat blind model retries. See `CODEX_HANDOVER.md` and
`OFFLINE_ACCEPTANCE_20261002.md`. Preserve the user's failed `user_123` run.

## Previous priority — Phase 19 offline Ollama follow-up

The Phase 19 breaker implementation and deterministic tests are complete
locally, but live Runner acceptance is inconclusive. The user authorized
stepwise diagnosis and fixes. Step 1 (saved-trace comparison) is complete:
Phase 7 has a completed offline run and saved Ollama/Qwen telemetry, while both
Phase 19 attempts also used only Ollama/Qwen. The historical state aggregates
15 telemetry records over about an hour and does not preserve raw response
shapes or a run ID; it cannot establish whether those successful tool calls
used native `tool_calls`. The two failed states record 2 failed `read_file`
calls and 1 successful `create_file`; afterward tool-call-shaped JSON was
handled as ordinary assistant content. Neither run reached the breaker.
One approved Runner CLI probe created its expected artifact in a disposable
workspace with Ollama-only telemetry, but its saved state has zero tool-execution
records and remains `in_progress`. The confirmed Markdown validator defect
that counted `vault.enc`/`vault.key` as artifacts is fixed; focused tests pass
7/7. Source confirmed tool execution was saved only after the turn and caught
exceptions were not persisted. The exact exception from the live probe is
unrecoverable. Runner now saves each dispatch result immediately and persists
safe early-error metadata. The new interruption regression plus breaker,
documentation-transition, and validation tests passed 15/15. One offline
system-library Runner probe then generated a 1,560-byte answer citing *Jetpack
Compose Internals* but repeated `create_file` three times; the five-minute cap
stopped it before Reviewer/completion. The tool records persisted, but retrieval
hits are not saved, so grounding is unverified. Current step: inspect/fix
repeated-write turn behavior and retrieval provenance; do not resume either
probe profile or make another model request without approval. The historical
probe record and current status are consolidated in `CODEX_HANDOVER.md`.

## Current checkpoint — Phase 19 implementation complete locally

Phase 18 removed the unreachable mocked confirmation branch for unsupported
external tools, preserved exact-hash human approval for project patches, and
corrected the general-HITL documentation. The focused capability tests passed
6/6; the patch-approval API test passed 1/1. Ruff passed for the modified test
module; `runner.py` retains 10 pre-existing findings. The Phase 18 completion
record is consolidated in `CODEX_HANDOVER.md`. Phase 19's implementation
and deterministic acceptance are complete locally; live Runner acceptance is
inconclusive and needs separate diagnosis. Its later acceptance result is
consolidated in `CODEX_HANDOVER.md` and `OFFLINE_ACCEPTANCE_20261002.md`.

**Standalone approved task — Project Catalog and Project-Bound Q&A:** implemented
locally and recorded in `TASK_PROJECT_CATALOG_AND_QA.md`; this does not create
or activate Phase 19. The deterministic suite passed 225 tests with 20 expected
skips, and the exact saved GTA manifest question passed through the interactive
Runner with the expected `tools:targetApi="31"` answer. The live project
registry was migrated after separate backup-first approval, and the GTA row
now stores user-provided description, optional GitHub URL, and existing local
checkout path. Remote clone/fetch remains deferred.

**Status:** Phases 13/13.1 were committed and pushed as `ffd0fd0`; Phase 14
was committed and pushed as `c563cd4`; and Phase 14.1 was committed and pushed
as `dfae390` on 2026-09-21. Phase 15 plus the bounded Phase 9 retrieval
hotfix were committed and pushed as `1b0a402` on 2026-09-22. Phase 16 was
reviewed, committed and pushed as `ae15081` on 2026-09-22; `main` is
synchronized with `origin/main`.

**Phase 17 — completed locally:** analysis item 17's P0 tool-secret capability
boundary now uses an empty default-deny production registry. `runner.py`
authorizes a tool before capability-scoped resolution; current agent-visible
tools retain opaque tokens. Focused tests passed 5/5 and the deterministic
suite passed 202 tests with 20 expected skips; the completion is retained here
and in the roadmap. The standalone Phase 17 files were removed.

**Phase 16 scope — completed:** analysis item 16 was reconciled with the
existing tenant factory and completed with an explicit canonical
`data/<user_id>/vault.enc` / `vault.key` contract. Complete legacy hidden
pairs are validated then non-destructively copied only when canonical files are
absent; incomplete, malformed, symlinked or divergent pairs fail closed.
Focused Vault/guardrail tests passed 17/17 with one expected Windows real-
symlink fixture skip; a separate deterministic mock test covers symlink
refusal without Windows privileges. The full deterministic suite passed 197
tests with 20 expected skips. No KMS, dependency, model, RAG, GTA, Docker or
Gradle work occurred.

**Phase 15 scope — completed:** secret/PII classification is separated from prompt-injection
handling. Structured findings, provider detectors and context-gated entropy
preserve masking compatibility. Markup sanitisation remains a separately
labelled limited boundary, not a claim of complete injection protection.
Focused tests passed 10/10; after the Phase 9 hotfix the full deterministic
suite passed 190 tests with 19 expected skips. External scanner adoption
remains a separate dependency decision.

**Post-phase live result:** real local Ollama/Chroma component integration
passed 1/1. A separate actual offline `runner.py` loop in a disposable `E:`
copy correctly masked its synthetic GitHub-shaped token before state persistence
but remained `in_progress` after three turns and ten tool executions. It was
stopped and the entire copy deleted. Do not claim full runtime acceptance or
attribute this loop nondeterminism to Phase 15 without a separate diagnosis.

**Correct GTA baseline validation:** the saved read-only Analyst→Reviewer
`tools:targetApi="31"` manifest question passed. The saved `MainActivity`
`MAIN`/`LAUNCHER` question initially failed closed: both manifest chunks exist
in Chroma, but only the `LAUNCHER` tail was supplied. The bounded Phase 9
source-assembly correction keeps the selected literal source's stored chunks
through fusion; the same real question now passes with `.MainActivity`.
No corpus re-indexing or connected-source access occurred.

**Phase 14.1 structure — completed:** all Python test modules now reside under
`tests/`: `sandbox/` for the Sandbox itself, `project_rag/` for generic
registered-project/RAG contracts, and `integration/` for Docker or opt-in
local-Ollama checks. `tests/fixtures/` remains synthetic only. The deterministic
discovery suite passed 181 tests with 19 expected skips, and Ruff passed for
`tests/`. No production code, GTA source, live RAG, Docker, Gradle, model, or
package state changed.

**Phase 14 scope:** close the still-relevant historical user-document
RAG gap through an explicit project-bound supplemental-document ingestion
pipeline. It must preserve the existing cascade: GTA project-code is evidence,
verified cards are human-approved knowledge, and global books are technical
reference only. The legacy user collection is audited, not automatically fed,
migrated, or deleted.

**Phase 14 acceptance — completed:** isolated temporary-fixture tests prove explicit
project ownership, deterministic idempotent replacement, no cross-project or
legacy leakage, failure-safe ingestion records, and labelled retrieval. No
supplemental document may establish a project fact or self-promote into
knowledge.

**Observed completion:** approved hash-verified Qwen assets on `E:` yielded an
offline count of 26, matching one real Ollama `prompt_eval_count=26`. The shared
runner/router path is exact for measured text, declared-tool schema,
assistant-tool-call, and tool-response formats (26/135/52/76). Unmeasured
tool schemas and message shapes retain fallback. Focused tests passed 33/33;
the full deterministic suite passed 178/178 with 15 expected skips; focused
Ruff and `git diff --check` passed.

**Out of scope:** providers/models/roles/prompts/privacy/fallbacks/budget
values; package or manifest changes; downloads; Ollama; RAG/Chroma; facts,
knowledge, session state, vaults; GTA; Docker; Gradle; and patch/review/
approval/validation workflows.

The obsolete standalone Phase 14 planning files were intentionally removed;
its historical completion and constraints remain recorded in the roadmap and
analysis.

**Observed blocker:** LiteLLM's installed `token_counter` is deterministic on
a fixed fixture but maps `ollama/qwen2.5:14b` to `gpt-3.5-turbo` and falls back
to OpenAI `cl100k_base`; it is not a Qwen-exact tokenizer or proved Ollama chat
framing. It cannot replace the estimate. The next decision is: approve an
official Qwen tokenizer/dependency and clean-install acceptance, authorize an
opt-in documented Ollama tokenization run, or retain the estimate.
The local environment has generic `tokenizers`/`tiktoken` but no Qwen tokenizer
assets (and no `transformers` or `sentencepiece`), so it supplies no alternate
exact counter.

## Phase 12 — completed 2026-09-21

**Status:** completed on 2026-09-21.

**Scope:** formalize and harden the per-user session lifecycle: explicit new
session, fail-closed resume of an interrupted valid state, and an explicit
session-only reset that cannot leave an accidental resumable task. The analysis
item about resume is partially addressed already by Phase 7; Phase 12 concerns
the remaining lifecycle and reset contract, not a new memory feature.

**Acceptance:** focused fixture-based tests cover valid resume,
malformed/non-interrupted refusal, new-session isolation, and reset
non-resumability. All state changes are deterministic and no live saved state
is used as test input.

**Out of scope:** LLM summarisation; session-to-RAG ingestion, indexing,
promotion, or training; project facts; knowledge cards; snapshots; RAG/Chroma;
GTA source/profile; vaults; providers; roles; patch/review/approval/validation
workflows; Docker; Gradle; models; dependency changes; broad suites. Reset may
never call `purge_user_data` or remove non-session user data.

The former Phase 12 preparation and continuation files were removed after
completion; its historical contract and observed results remain recorded here
and in `CODEX_HANDOVER.md`.

**Observed completion:** `--reset` deletes only the selected session
`state.json`; `--clear` remains a deprecated compatibility alias. New-session
state construction is explicit and resume retains its fail-closed validation.
Temporary-fixture lifecycle tests passed 3/3, existing resume validation passed
1/1, and the new test passes Ruff. Facts and a vault file survived reset; no
live state, RAG, GTA, model, Docker, Gradle, or package state was changed.
`runner.py` retains 10 pre-existing Ruff findings outside this phase's edits.

# Phase 8 closed — 2026-09-17

GTA project RAG Q&A is complete: 393 project-code chunks, local Analyst →
Reviewer through `project_qa.py`, and hybrid semantic plus snapshot/source
retrieval. Grounded manifest answer: `tools:targetApi="31"` from
`app/src/main/AndroidManifest.xml`.

## Current Phase 8 continuation — 2026-09-16

## Phase 11 — completed 2026-09-20

**Scope:** make dependency manifests reproducible by auditing direct imports
and separating runtime, PDF-ingestion, and development/test packages. Preserve
a compatible runtime installation entry point and add focused manifest tests.

**Hard boundary:** no package installation, download, upgrade, removal,
lockfile resolution, model/provider change, Chroma/Android/Docker/Gradle
action, or broad test run. A clean-environment install is a separate user
authorization.

See `PHASE11_CONTINUATION_PROMPT.md` and `PHASE11_PREPARATION.md`.

**Observed completion:** added `requirements-runtime.txt`,
`requirements-ingest.txt`, and `requirements-dev.txt` with observed working
versions. `requirements.txt` remains a compatible default entry point. Ruff and
the focused dependency-manifest suite passed 3/3. No package state, model, RAG,
Android, Docker, or Gradle state changed; clean-environment installation remains
separately authorized.

**Fresh-clone acceptance (2026-09-21):** completed in an isolated `E:` clone
at `3f7027f`. Python 3.11.9 installed the default and optional-ingestion
manifests; `pip check`, runtime imports, the full suite (166 tests; 17 expected
skips), and the two ingestion tests passed. No RAG corpus, Chroma persistent
store, Ollama, PDF processing, or GTA source was used.

## Phase 10 — completed 2026-09-20

**Scope:** implement a deterministic proposal bridge from grounded project Q&A
to a draft project knowledge card. A GTA fact must retain same-project
`project-code` source paths and snapshot/source hashes. Global books remain
technical-reference-only. Draft creation must not verify or index the card;
the existing explicit human verification path remains the only promotion path.

**Out of scope:** model training, automatic LLM knowledge promotion, live GTA
knowledge-card creation, Android-source/GTA-corpus changes, codegen, patches,
Docker, Gradle, provider policy, dependencies, vaults, and broad test runs.

See `PHASE10_CONTINUATION_PROMPT.md` and `PHASE10_PREPARATION.md`.

**Observed completion:** `grounded_knowledge_proposal.py` validates structured
same-project `project-code` paths and hashes against the stored snapshot and
creates only a draft knowledge card. `project_qa.py` exposes this structured
evidence without creating a card. Global-library, missing, stale, and
cross-project evidence are rejected; only the existing verified-card path may
index. Focused Ruff and 11 focused knowledge/retrieval/Q&A tests passed. No
live GTA data, Docker, Gradle, model call, or model-training operation occurred.

## Phase 9 — completed 2026-09-20

**Scope:** improve project-RAG evidence quality and the native, read-only
Analyst → Reviewer Q&A path for the registered GTA profile. Begin from
`PHASE9_CONTINUATION_PROMPT.md` and `PHASE9_PREPARATION.md`.

**Cascaded-RAG decision (2026-09-20):** retrieve GTA snapshot/project-code
evidence first; use the shared Compose/Kotlin/architecture library only as a
separately labelled optional technical reference. A book cannot establish a
fact about GTA Cheats. Audit the global-library ingestion/retrieval storage
route and retain one canonical path without rebuilding either corpus. Future
knowledge promotion must remain explicit, evidence-gated, and human-approved;
LLM answers never auto-enter RAG.

**Observed exception (2026-09-20):** the two existing global-library
collections contained zero chunks, while GTA project-code contained 393. The
user authorized exactly one ingestion of the three existing `docs/*.pdf` books
into the canonical global-library path. GTA RAG must not be re-indexed or
otherwise altered.

**Observed completion:** the canonical global library has 2,293 chunks
(326 Compose, 859 Kotlin in Action, 1,108 Software Architecture with Kotlin);
GTA project-code remains 393. Project retrieval now uses a stored-chunk lexical
stage before semantic fusion, returning `app/src/main/AndroidManifest.xml`
first for `tools:targetApi`. The optional book stage stays
`global-library`/technical-reference only. Two real local Analyst -> Reviewer
answers were grounded in that manifest: `tools:targetApi` is `"31"`, and
`.MainActivity` is the `MAIN`/`LAUNCHER` activity. Focused Ruff passed and the
focused test suite passed 4/4. No Docker, Gradle, connected-source, GTA-corpus,
or preserved-Phase-8-state changes occurred.

**Out of scope:** connected Android-source changes, codegen/patch workflow,
Docker, Gradle, model-provider policy changes, and broad test generation.

The project-scoped telemetry store is now connected to runner model and
retrieval flows. It records only event, outcome, provider, bounded tokens/cost,
and timestamp; retrieval queries and hits, prompts, source text, model output,
validation stdout/stderr, and secrets are excluded. This does not grant the
runner, API, or telemetry store any execution capability.

Workspace policy is now enforced at patch-candidate creation: every changed
path must be inside `allowed_workspace_paths`, while no policy or an empty list
rejects the candidate before persistence. Project-scoped model provider policy
and token budgets are also enforced before adapter dispatch, including
fallbacks. The retention contract now provides only an explicit read-only
preview for one project: metadata-only counts for telemetry and policy audit
events, with malformed input blocked fail-closed. It does not clean up files.
The next Phase 8 candidates are separately approved telemetry/audit cleanup,
auto-apply, a graphical UI, and destructive knowledge deletion. Do not begin
them without a narrowly defined contract and regression tests that preserve the
FastAPI/Docker boundary and default-deny behavior.

## Bounded execution status — 2026-09-16

- `phase7_quality_final` was preserved unchanged as a historical failed run;
  its actual state is `in_progress`, with `agent_steps: 11`.
- `phase7_operational_preflight.ps1` starts Docker Desktop automatically, then
  confirms Docker, native Ollama, both required models, and a separate FastAPI
  process. All workflow checks passed.
- A new bounded `phase7_dispatch_guard` task was created in the existing
  storage. One dispatch-path fix prevents a rejected invalid documentation
  `create_file` request from consuming a separate step; the focused test
  passed **1/1**.
- One opt-in Ollama/Chroma run passed **1/1**. One real offline resume of the
  new task completed with `agent_steps: 2` and Reviewer verdict `APPROVE`.
- The audit log confirmed the final full suite: **126 tests, OK (skipped=3),
  exit code 0**. After the run, `ollama ps` was empty and no Docker containers
  remained.

**Phase 7 was closed on 2026-09-16. Do not resume or normalize
`phase7_quality_final`; it remains a historical failure.**

For later work, use [`README.md`](README.md) as the map of the current runtime
and the canonical documents in this directory as the architectural record.
The preflight starts Docker Desktop itself; the operator does not need to
start it manually.

---

## Historical plans and status

## Status at the end of the 2026-09-15 session

### Result of the single resume — 2026-09-16

- The local Ollama endpoint was restored and the opt-in Ollama/Chroma
  integration passed **1/1**.
- The single `MINI_AGENT_OFFLINE=1` resume of `phase7_quality_final` preserved
  a rejection before evidence and Reviewer checks because Coder wrote
  `# Overview` instead of the required `## Overview`. State remained
  `in_progress`, with `agent_steps=7` and no `documentation_review`.
- A second resume and prompt tuning were prohibited. The defect was recorded
  for separate work; Phase 7 was still open at this checkpoint.

### Pinned-plan execution update — 2026-09-16

- `documentation_policy.py` gained a minimal deterministic evidence gate: each
  retrieval request with a direct match requires one corresponding real RAG
  source path. The complex citation-to-code matching design was not restored.
- The new regression test and focused suite passed **52/52**. The full suite
  ran **126 tests: 111 passed and 15 skipped**; Docker tests were skipped
  because Docker Desktop had not been started by the operator.
- The opt-in Ollama/Chroma integration stopped before the agent loop:
  `ollama/nomic-embed-text` returned `APIConnectionError`. `ollama ps` then
  failed to create a log under `%LOCALAPPDATA%\\Ollama` (`Access is denied`)
  and timed out while waiting for the server.
- This was an infrastructure failure, not a documentation-gate defect.
  `phase7_quality_final` was not to be run, its state and `agent_steps=6` were
  not to be reset, and prompts/RAG were not to be changed until Ollama was
  restored externally and `ollama ps` succeeded.

## Pinned Phase 7 execution order

This order remained mandatory until Phase 7 closure. It was not to be expanded
with fixes unrelated to the offline documentation quality gate; such findings
were to be recorded separately with their exact symptom and test.

1. Preserve current state and inspect task boundaries without invoking models.
   Do not change `user_123`, Android sources, the legacy vault, dependencies,
   Docker configuration, or `roles.json`.
2. Define the deterministic documentation-quality contract. It must require
   real RAG sources covering entry/navigation, module composition, and
   supported data flow. Do not restore the removed complex citation-to-code
   matching design.
3. Add rejection regressions first: insufficient or self-referential sources,
   a DTO description presented as architecture, and a false Reviewer
   `APPROVE`. Add one compact positive case.
4. Make the minimum changes in `documentation_policy.py`, the documentation
   branches of `runner.py`, and, only if exact retrieval needs it,
   `project_retrieval.py`; then run the focused tests.
5. After the focused tests pass, run `unittest discover` once and run the
   opt-in offline integration separately.
6. Resume the saved `phase7_quality_final` exactly once with
   `MINI_AGENT_OFFLINE=1`, without resetting state or `agent_steps`. Record
   either `completed` or the concrete failure; do not tune prompts in a loop.
7. Afterward, unload models used by the run, check `ollama ps`, and update the
   four status documents only with results that actually occurred.

Closure required the quality gate to reject a poor document deterministically,
green focused/full/opt-in tests, and either a confirmed single real offline
resume or a preserved concrete failure.

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
  Those failed results did not close tasks.
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

The continuation instruction at that checkpoint was to read the newest status
at the top of `CODEX_HANDOVER.md`, avoid repeated prompt-tuning loops or model
changes, inspect saved work, run one bounded real attempt, and record any
failure without tuning the test to pass.

---

## Historical material

# Next steps after P0 hardening

This historical plan assumed the following changes had already been completed:

- workspace path isolation and `user_id` validation;
- a tenant-scoped vault at `data/<user_id>/.vault`;
- a policy layer for `project_facts`;
- a structured Reviewer verdict;
- a mandatory Reviewer step after Arbitrator;
- language-aware validation routing.

The goal of the next iteration was to turn the remaining architectural
constraints into testable security boundaries without mixing them with prompt
engineering, RAG, or telemetry.

## Stage 0 — Define the security contract

**Reason:** before containerization, define what may run and where the trust
boundary lies.

1. Document the threat model: the LLM and generated code are untrusted; the
   policy engine and runner are trusted.
2. Create a capability manifest for filesystem, network, secrets, subprocess,
   and build/test tools.
3. Define each capability's owner, scope, default (`deny`), and required human
   approval.
4. Separate two modes:
   - `plan_only`: the agent reads and writes its workspace but does not execute code;
   - `validated_execution`: build and test run only in the isolated environment.

**Completion criterion:** a documented capability matrix and a test proving
that an unknown tool or execution block is denied by default.

## Stage 1 — Real execution sandbox

**Reason:** workspace isolation alone does not protect the host if generated
code or a Gradle build is executed later.

1. Choose the execution backend as a project-owner decision:
   - Docker/Podman with Linux isolation for CI and Linux;
   - a separate VM or Windows Sandbox for local Windows development;
   - a restricted subprocess only as a temporary measure, not as an equivalent
     to a container or VM.
2. Create a `SandboxExecutor` adapter; `runner.py` must not invoke build tools
   directly.
3. Configure the backend as deny-by-default: no network, read-only base image,
   only the user workspace writable, CPU/memory/process/wall-clock limits, a
   non-root user, and no host mounts except an explicitly copied workspace.
4. Return build/test results as a structured report containing exit code,
   timeout, resource-limit status, and secret-masked stdout/stderr.
5. Add integration tests for denied network, unavailable host paths, timeout,
   memory/process limits, and allowed workspace writes.

**Completion criterion:** Kotlin/Python validation runs only through
`SandboxExecutor`, and tests demonstrate no network or host-filesystem access.

**Selected design:** Docker is the execution backend and FastAPI is the API
layer. The Docker sandbox starts from the repository but receives only a
dedicated copy of the user workspace, never the full host project directory.

## Stage 2 — Complete a real Kotlin/Android validation flow

**Reason:** at this checkpoint the Kotlin-to-Gradle route was correct but had
only been checked with mocks, not an Android fixture.

1. Add a minimal Kotlin/Android fixture with a Gradle wrapper under
   `tests/fixtures/`.
2. Run `gradlew --offline lint test` in the sandbox.
3. Run optional `detekt` and `ktlintCheck` checks only when those Gradle tasks
   are declared; otherwise report `not configured`.
4. Add negative fixtures for compilation failure, a failing unit test, an
   Android lint violation, and a missing wrapper.
5. Define mixed-language workspace rules through explicit validator chains or
   reject the workspace.

**Completion criterion:** the real fixture passes lint/test in isolation and
each negative fixture blocks transition to Reviewer.

## Stage 3 — Complete symlink and TOCTOU coverage

**Reason:** the code blocked symlink traversal, but the Windows test
environment could not create a symlink.

1. Add a Linux CI job where symlinks are available without special privilege.
2. Test an internal symlink escaping the workspace, a symlink to an external
   file, a symlink to an internal directory, and replacement of a regular file
   with a symlink between validation and open (TOCTOU).
3. For writes, use a platform no-follow primitive where available or create
   files through the trusted executor in an isolated filesystem.
4. Document the Windows prerequisite for local symlink tests and permit skips
   only with an explicit reason.

**Completion criterion:** a mandatory CI test demonstrates that symlinks cannot
escape the workspace; a local skip does not hide missing CI coverage.

## Stage 4 — Migrate and remove the legacy vault

**Reason:** root `.vault` and `.vault_key` files were no longer used at runtime
but could contain old secrets.

1. Add a read-only `vault_migration --dry-run` that checks the root legacy
   `.vault` and `.vault_key` files and reports only file presence and token
   count, never secret values.
2. Add an opt-in migration where the user explicitly supplies the target
   `user_id`; create an encrypted backup and atomically write the new tenant
   vault under `data/<user_id>/.vault`.
3. Verify decryption before switching and preserve an audit record without
   plaintext.
4. Delete legacy files only through a separately confirmed command after
   successful migration and backup verification.
5. Test successful migration, wrong key, corrupt vault, rollback, and absence
   of cross-tenant token leakage.

**Completion criterion:** legacy secrets are either safely migrated to one
selected tenant vault or left untouched; no automatic deletion occurs.

**Clarification:** `user_id` is a safe technical tenant/workspace identifier,
such as `local_owner`, rather than a Windows path or project folder name. The
legacy files predate tenant isolation and contain no owner identity. A
single-user installation can migrate them into one explicitly selected
namespace. Deletion requires a separate user command after backup verification.

## Stage 5 — Strengthen behavioral security evaluations

**Reason:** an LLM's textual response does not prove the absence of side
effects.

1. For every adversarial case, check state mutation, tool execution, fact
   mutation, vault access, and filesystem diff.
2. Add an evaluation where an agent tries to change a security fact; require a
   deterministic policy denial and no write.
3. Add an evaluation where Reviewer returns `DO NOT APPROVE`; require the
   workflow to remain incomplete.
4. Add an evaluation where Arbitrator issues a decision; require the final
   Reviewer to run anyway.
5. Add failure reports with machine-readable reason codes and evidence links.

**Completion criterion:** the security score is based on observable side
effects, not only model-response text.

## Execution order

```text
Stage 0 → choose backend → Stage 1 → Stages 2 and 3 in parallel → Stage 4 → Stage 5
```

RAG, telemetry, and Regulator were not to be expanded before Stages 1–5 were
complete because they cannot replace an execution boundary or behavioral
assertions.
# Current evolution status — 2026-09-15

- Docker Kotlin/Android validation is real and confined to a Linux executor.
- `GtaCheatsApp-main` is registered as `gta-cheats--cc0fe5de`; its state lives only under `data/projects/gta-cheats--cc0fe5de/`.
- Canonical RAG is the existing ChromaDB + LiteLLM + local Ollama `nomic-embed-text` pipeline; a project-scoped real embedding/query passed.
- Completed after this historical plan: deterministic project ingestion, verified-card-only knowledge synchronization, knowledge editor/API, and project-scoped planning retrieval.
- Phases 3–6 are complete. Phase 6 provider-neutral model routing is implemented and tested; Phase 7, offline local-model mode, is active and in progress.

## Canonical current status (2026-09-15)

Docker-only validation, project snapshot/indexing, canonical project RAG, knowledge-card verification, project-scoped retrieval and the persistent work ledger are complete and tested. Phase 4 validates unified-diff paths against the approved PlanStep, persists reviewer decisions, and requires hash-bound explicit user approval before validation records are accepted. Phase 5 is complete: the trusted worker rechecks both approvals, applies diffs only to a temporary copy, supports staged allowlisted Gradle profiles, and records bounded validation evidence from the locked-down Docker executor. Phase 6 adds provider-neutral routing behind the existing completion facade, default-deny cloud policy, explicit budget/context/quota/health and fallback rules, and a local-only embedding contract. Router tests use fakes; telemetry excludes prompts, source excerpts, secrets and responses; no provider SDK or dependency was added. Full suite: 90 passed, 2 expected skips; Docker Kotlin/Android executor integrations passed against the copied fixture. The original Android source was not run, mounted or modified. Phase 7 should verify full offline task continuation on the already-configured Ollama/local embedding path; it must not assume that the Phase 6 routing tests prove disconnected end-to-end operation.

## Active next phase — Phase 7: offline local-model mode

Phase 7 implementation is underway. An explicit process-start
`MINI_AGENT_OFFLINE=1` setting now prevents every non-Ollama completion route,
even when cloud use is otherwise eligible. Missing-local-model behavior is
covered by focused tests. `runner.py --resume <user_id>` now restores only an
interrupted, valid `in_progress` state and retains the cumulative step count.
An opt-in integration check has exercised a persisted work-ledger task, local
Chroma retrieval/embedding and a real local Ollama completion; all recorded
completion/embedding calls used Ollama. The initial model call-site/settings
search is complete; it found the expected routed completion sites in `runner.py`,
`analyst_agent.py`, and `evals_pipeline.py`, and local embedding calls in
`rag_service.py` and `ingest_knowledge.py`. The reviewed implementation touched
`model_router.py`, `runner.py`, and their router/orchestration tests. Ollama
completion and `ollama/nomic-embed-text` are already
present; retain them unless runtime evidence identifies a blocker. Do not
migrate ChromaDB, change embedding dimensions, or re-embed existing collections.

Phase 7 completion must demonstrate persisted task continuation with local RAG
and local completion while external network access is blocked. The optional
real-model check has exercised persisted work-ledger state, temporary Chroma
retrieval and actual Ollama completion; a full CLI-resume run with actual
models remains the final integration gate. Document which
tasks remain available locally, fail safely when a local model is unavailable,
prove no disallowed cloud fallback occurs, and keep model files/caches outside
the repository and Docker executor. Model output cannot grant patch approval,
review approval, or validation status. Preserve Docker `network=none` and the
FastAPI/validation-worker boundary. Router policy tests should use fakes; any
installed-Ollama integration check must be separately identified and must not
need cloud credentials.

Set `MINI_AGENT_OFFLINE=1` before starting the application to activate offline
routing; unset it (or use `0`) to retain normal Phase 6 policy. Resume from the
CLI with `python runner.py --resume <user_id>`. The local integration check is
opt-in: set `MINI_AGENT_RUN_OFFLINE_INTEGRATION=1` when running
`python -m unittest test_offline_integration -v`; it uses installed local
Ollama models and no cloud credentials.

Workspace rerun (2026-09-15): real Ollama/temporary-Chroma integration passed 1/1; focused router, runner-resume, retrieval, ledger, RAG and validation tests passed 31/31; full suite passed 98 tests with 3 expected skips. Ollama tool schemas and Markdown-only validation are now covered. The dedicated real CLI resume created `data/phase7_offline_test/architecture_summary.md` but did not complete: the generic Android agent loop produced unrelated Kotlin files and remained `in_progress`. Keep the full CLI completion gate open.

The run also recorded an `update_project_fact` tool call that wrote a canonical fact into the synthetic user's `project_facts.json`. That generated file was removed from the isolated test workspace; blocking unsupported model-driven knowledge promotion remains an open safety item.

## Phase 7 current handoff (2026-09-15)

Latest verification: full suite **103 passed, 3 skipped**; opt-in installed-Ollama/temporary-Chroma integration **1/1 passed**. The actual saved resume for `phase7_offline_test` / `gta-cheats--cc0fe5de` used only Ollama completion telemetry and created `architecture_summary.md`, but remains `in_progress`: the documentation coder repeated `create_file` three times and hit the circuit breaker. A regression-protected orchestration fix and one final real resume are still required. Keep Phase 7 in progress until that run completes and is reviewed. Continue from the latest instructions in `CODEX_HANDOVER.md`; the user already has Codex CLI open in a terminal. Do not launch another CLI process, touch `user_123` or Android source, add dependencies, modify Docker configuration, or commit.


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
## Product objective and next real integration

The product objective is an agentic code-generation tool for real codebases, not a collection of independent policy endpoints. `gta-cheats--cc0fe5de` is the canonical Android profile: snapshot/RAG retrieval has saved evidence for `MainActivity.kt`, `settings.gradle.kts`, and `gradle.properties`. It is the real context on which the tool must be developed.

The runner-to-ledger proposal bridge is implemented through `--project-patch <project-id> <approved-step-id> <user-id>`. Coder submits only a unified diff via `propose_patch`; the existing ledger enforces the approved step and workspace policy before persistence, and Reviewer approval records review only. Next, run one bounded GTA Cheats task through project retrieval, proposal, review, explicit approval, and Docker validation on a temporary copy. Do not claim a real connected-source Gradle run until that last step is actually performed. Dashboard/frontend work, auto-apply, retention cleanup, and destructive knowledge deletion are not the next product priority.
## Immediate codegen priority — local provider recovery

The proposal-format boundary is verified by 25 focused tests. Existing GTA
search proposals are rejected, not approved. Diagnose the reproducible
`qwen2.5:14b` stall before its first response, then create one grounded proposal
using the existing GTA V toolbar/view-model search flow. Stop at Reviewer and
require explicit user SHA approval before temporary-copy validation.
