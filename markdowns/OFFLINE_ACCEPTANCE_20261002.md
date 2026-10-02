# Offline Runner acceptance - 2026-10-02

This is the user-authorized continuation of the Phase 19 follow-up, not a new
phase. Acceptance concerns orchestration, local routing, context isolation,
tool execution, durable state and completion. The assistant's opinion of the
generated Kotlin explanation is not a runtime acceptance criterion.

## Preserved baseline

`data/offline-acceptance-20261002/baseline` contains the pre-edit Git HEAD,
working-tree patch/status, copies and hashes of 17 changed source/documentation
files, and hashes of 19 historical `state.json` files. It excludes Vault
contents. No reset, checkout, commit, push or removal was performed.

## Diff audit and decisions

- Retain the explicit general/project/code menu: it addresses the reproduced
  defect where an ordinary question entered file-generation mode.
- Retain immediate tool-result persistence and safe error metadata: source
  and earlier saved runs establish the lost-progress failure.
- Retain the runtime Vault filename exclusion in Markdown workspace validation.
- Retain Phase 19's hard N+1 stop and its separate persisted incident/recovery
  semantics. Do not change limits to make a live test pass.
- Retain the bounded repeated-validation stop, local-routing diagnostics and
  line-buffered output from the previous CLI repair.
- Remove the newly imposed JSON review record and its semantic verdict/exit-2
  gate for ordinary questions. Reviewer again returns text/Markdown. Code-task
  and project-patch Reviewer contracts are unchanged.
- Make shared-book retrieval optional on failure, with a safe visible notice.
  Failure no longer prevents ordinary Analyst/Reviewer completion. Keep the
  separate book collection and existing project-selection boundary.
- Do not change roles, models, provider policy, GTA source, corpus contents,
  unrelated legacy-file deletions, or prior test/run evidence.

## Verification plan and interpretation

All live scenarios use the real `runner.py` CLI with `MINI_AGENT_OFFLINE=1`,
unchanged configured models and no injected completion responses. They run
sequentially through a capture helper. Inputs, complete output, process exit
and elapsed time are saved under `data/offline-acceptance-20261002`.

1. General question: menu 1, brief list/tuple question; observe two turns,
   final answer, no project selection and natural model unload.
2. Book context: menu 1, SlotTable question; observe existing global-library
   chunk IDs and the ordinary two-turn route. Do not grade prose correctness.
3. Project context: menu 2, explicitly select `gta-cheats--cc0fe5de`, use the
   documented manifest question. Only read-only project retrieval is allowed.
4. Code task: menu 3, a small isolated Kotlin file. The current validator
   requires a Gradle wrapper; the task explicitly excludes generating one.
   Therefore this checks actual tool dispatch and the failure/stop path, NOT
   a successful Kotlin build or a complete successful code-task workflow.
5. Breaker: ask for six read-only directory calls in one turn with the normal
   limit of five. Only an observed N+1 attempt and persisted incident can pass
   live acceptance. No altered limits, synthesized calls, or prompt retries.

The code-task scenario's known validation boundary is reported up front. No
available successful Kotlin build is implied. The connected Android project
must not be used to supply a wrapper or resolve this limitation.

## Deterministic checks

- Final Q&A and book-reader modules: 14 tests passed after simplification and the bounded retrieval fix (`qa-retrieval-tests.txt`).
- Phase 18 authorization/patch approval, Phase 19 breaker/persistence,
  documentation transition, session lifecycle and project-Q&A selection:
  35 focused/adjacent tests passed. Captured in `focused-tests.txt`.
- Focused Ruff for Q&A, book reader and their tests passed; diff check passed.
- These are deterministic checks using mocks/temporary fixtures. They are
  not the full test suite and not live end-to-end acceptance.

## Live results

| Scenario | Actual outcome | Duration |
| --- | --- | --- |
| General QA | Two local turns, final text, exit 0, automatic unload | 120.36 s |
| Books, before retrieval fix | Two turns completed, but selected introduction/contents instead of SlotTable evidence | 110.75 s |
| Books, after bounded retrieval fix | Two relevant slot-table passages supplied, both agents answered, exit 0, unload | 144.52 s |
| Explicit GTA project QA | Selected project in menu; two local turns; targetApi 31; snapshot 869a2a9e1d75; sources printed; exit 0 | 45.05 s |
| Isolated Kotlin code task | Two identical native create_file calls persisted; stopped at validation_blocked after the repeated missing-wrapper failure; Reviewer not reached | 138.26 s |
| Real breaker attempt | No native tool calls; model returned tool-shaped text twice; validation_blocked, no N+1 incident; live breaker NOT accepted | 93.13 s |

The code-task process returned exit 0 despite `validation_blocked`. Existing
CLI exit behavior is recorded, not silently redefined. The saved state and
absence of Reviewer completion establish that this is not successful code-task
acceptance. Both writes have the same content SHA-256. No Gradle wrapper was
created and no Gradle/Docker execution occurred in that scenario.

### Bounded retrieval fix and its limits

The first live SlotTable request retrieved introduction and contents passages.
A direct lookup in the same existing index found actual slot-table prose.
The reader now recognizes camel-case identifiers in the request, looks up the
literal identifier and its spaced lower-case form (up to three identifiers,
32 candidate chunks), excludes contents headings, and prioritizes up to two
literal passages before the existing semantic results. No project reader or
corpus is modified. This is not a general relevance guarantee, especially for
queries without such identifiers.

The corrected run supplied chunks `00ec9f35-08d3-4749-8797-3cdd32720bd8` and
`43153c1f-52de-4070-807c-1db160bf458f`, which explain groups/slots and the gap
buffer, plus one semantic fallback chunk. Actual excerpts and hashes are saved
in the run directory. This demonstrates context retrieval/transfer; it is not
an external accuracy grade of the model answer.

Book-reader tests passed 5/5 after the new regression cases. An initial standalone
test invocation failed because a broad Path.is_file mock affected Chroma's lazy
import of dependency resources; importing Chroma before that mock fixed the test
isolation problem. The failed invocation was not a production retrieval failure.



## Earlier six-run checkpoint

Six actual CLI processes were captured: general, books-before-fix,
books-after-fix, project, code and breaker-attempt. Every captured completion
route was Ollama/Qwen under the offline flag. Successful QA routes do not imply
successful code-task or breaker acceptance. No full unittest discovery suite
was run; final focused/adjacent coverage is 14 + 35 = 49 tests, all passing.
Focused Ruff passed. Runner-wide Ruff retains nine pre-existing findings.

The breaker attempt returned ordinary content shaped as
`{"function":"list_directory","parameters":{"dirpath":""}}`, not native
`message.tool_calls`. Runner did not execute it. The preserved state contains
zero tool executions, no breaker incident, two steps and `validation_blocked`.
It therefore cannot close Phase 19 live acceptance. No synthesized tool calls,
changed limits, state resets or prompt-only repeats were used.

Final checks: all 19 historical state hashes are unchanged, including the
original `user_123` failure. QA profiles have no task state. The existing global
book collection remains 2,293 chunks and GTA project-code remains 393 chunks.
`ollama ps` is empty. Configured roles/provider policy and project-QA/retrieval
source files were not changed. No connected source write, Gradle, Docker,
installation, corpus reingestion, commit or push occurred.

## Phase status and unresolved work

- Phase 18: closed locally in its documented narrow scope; its six authorization
  tests and exact-SHA patch-approval test passed again. It never claimed full
  runtime acceptance of all tools or agents.
- Phase 19: hard-stop implementation and deterministic checks pass. Live N+1
  acceptance remains OPEN because the real request never produced tool calls.
- General/book/project QA: the specified real routes completed. Optional book
  failure continuation is covered deterministically, not by breaking live RAG.
- Code task: actual creation and durable dispatch are evidenced; duplicate
  writes and text shaped like tool protocol also occurred. The standalone
  Kotlin validator requires a wrapper. Full successful Coder -> Reviewer ->
  completed code-task acceptance is NOT established.
- CLI exit 0 on blocked code tasks is an observed presentation/automation
  ambiguity. It was documented, not used as a task-success criterion, and not
  silently changed during this audit.

Further code-tool protocol work must start from these traces, with a scoped
repair justified by a reproduced defect. Do not automatically execute JSON from
assistant prose, relax validation, substitute a canned model answer, or alter
roles/orchestration to make an acceptance record green.


### Named-file real Runner acceptance - completed (seventh captured CLI run)

The exact user question completed through real menu option 2 and explicit GTA
selection under MINI_AGENT_OFFLINE=1. Both configured Ollama/Qwen agent calls
completed. Runner confirmed the file, described `CheatCodes.groups` as
`List<CheatCodeGroup>`, and printed only
`core/src/main/java/com/gamescheats/core/domain/model/CheatCodes.kt` as its source.
Snapshot revision remains `869a2a9e1d75`; process exit 0; elapsed 81.65 seconds.
Final `ollama ps` is empty. All 19 preserved historical task hashes are unchanged.
No corpus reindexing, GTA source write/build, role/status change, commit or push
occurred. Phase 19's separate live N+1 acceptance remains open.

## Publication checkpoint and user-reported follow-up

The user subsequently reported improved general and project Q&A and supplied
this separate project query:
`could u show file Navigation.kt ? and answer how navigation work with compose?`
The displayed source was
`app/src/main/java/com/gamescheatsapp/navigation/Navigation.kt`, snapshot
`869a2a9e1d75`. Output stopped at `onNavigateToGtaV = { nav`, without finishing
the code or explaining navigation. This is a user-run transcript, not an eighth
captured acceptance process. It confirms relevant source selection, not complete
fulfilment of the two-part question.

Code inspection confirms max_tokens=200 per project-Q&A agent and no
finish_reason truncation check there. Output-budget exhaustion is a hypothesis
until response metadata confirms it. Project Q&A defaults to project evidence
only; book augmentation is optional and not enabled by the menu. Missing book
augmentation alone does not explain an answer stopping mid-token/code.

The user requested documentation and publication of existing fixes first, then
investigation of truncation. No truncation implementation or new model run was
performed for this publication checkpoint. Phase 18 remains closed within its
scope; Phase 19 live N+1 remains open. Earlier no-commit/no-push statements are
historical. Runtime captures, indexes, vaults and user state are not published.
