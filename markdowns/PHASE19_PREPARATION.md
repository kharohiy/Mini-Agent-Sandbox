# Phase 19 Preparation — Make the Tool Circuit Breaker a Hard Boundary

**Status:** Implementation and deterministic checks completed locally. Live N+1
acceptance remains OPEN after the 2026-10-02 attempt (zero native tool calls).
See `OFFLINE_ACCEPTANCE_20261002.md`. Not committed or pushed.

## Goal

Address analysis item 19 by making the per-turn tool-call breaker a deterministic
execution boundary rather than a workflow hint that hands control to another
agent. At the configured threshold, stop dispatching further calls, record a
structured incident, and place the task into an explicit, fail-closed recovery
state.

Threshold semantics: N is the maximum number of tool calls processed in one
agent turn. Calls 1 through N may be dispatched; an attempted call N+1 is
blocked before authorization or execution. In a multi-call response, calls
before N+1 remain processed, and the rest of the response is discarded. The
system records the attempted call number and processed-call count; it does not
claim to undo prior effects.

The intended contract is:

```text
tool_count > N
→ hard stop the task before dispatching call N+1
→ structured incident
→ explicit recovery state
```

This phase concerns the per-turn tool-call breaker only. It does not change the
separate global agent-step limit, emergency budget stop, tool authorization,
Vault policy, HITL patch-approval flow, model/provider routing, project Q&A, or
connected project/RAG data.

## Observed Starting Point

- `runner.py` sets `MAX_TOOL_CALLS_PER_TURN = 5` (documentation mode uses 3).
- The current condition prevents dispatch of call N+1 but does not define a
  terminal task state; Phase 19 will formalize that as the maximum-N contract.
- For ordinary tasks, the breaker adds a generic memory message, changes
  `current_turn` to `analyst`, then continues the outer loop. That is not a
  hard stop of the current task/agent execution.
- For documentation mode, the loop exits after saving metrics, but there is no
  explicit breaker recovery status or structured incident contract.
- A model response's full tool-call list is appended before individual calls
  are dispatched. Calls already dispatched before reaching the threshold are
  not rolled back. Phase work must state and test the exact boundary semantics;
  it must not imply rollback of side effects.
- `MAX_AGENT_STEPS` and emergency budget handling are distinct controls and
  must remain behaviorally independent.

## Execution Plan

1. **Specify the boundary.** Define whether N means the maximum number of
   dispatchable calls or the call that triggers the stop; define behavior for a
   response containing multiple calls, including suppression of calls at and
   beyond the threshold. Preserve already completed side effects and state that
   no rollback is promised.
2. **Define the incident and recovery contract.** Identify the structured
   incident fields and durable task status/state. Specify what the user sees,
   whether the task can be resumed, and what explicit action clears or resolves
   the breaker state. Fail closed on malformed or missing recovery metadata.
3. **Implement the smallest Runner change.** Stop the active turn at the
   boundary; do not transfer execution to Analyst as a substitute for stopping.
   Keep documentation mode and ordinary mode consistent unless a documented
   reason requires distinct presentation.
4. **Add deterministic regression tests.** Use fake model/tool responses and
   temporary state. Verify exactly N permitted dispatches, no dispatch at or
   after the stop boundary, no subsequent-agent execution, structured incident
   persistence, explicit recovery behavior, and unchanged global step/budget
   guards. Include multi-call responses and both task modes.
5. **Update canonical documentation.** Correct README/runtime claims and
   `TESTS.md`; record actual focused and full deterministic test results in
   handover and roadmap only after they have run.
6. **Review scope and state.** Inspect the diff and saved task-state effects;
   ensure no Vault, runtime user data, project source, RAG, or unrelated files
   changed. Do not commit or push without separate instruction.

## Potential Blockers and Risks

- **Persisted task-state compatibility:** an explicit recovery state may not
  fit existing resumable-task statuses. Inspect the storage schema and resume
  path before choosing a representation; do not silently make a stopped task
  runnable again.
- **Multi-call responses:** the current implementation receives several calls
  in one model response and dispatches them sequentially. Threshold behavior
  must be precise, with no off-by-one allowance and no execution after stop.
- **Irreversible prior calls:** the breaker cannot undo tools that already ran.
  The incident must report this honestly; transactional rollback is out of
  scope unless existing tool semantics prove it is safe and necessary.
- **Task-mode differences:** documentation mode currently exits differently
  from ordinary mode. Tests must verify both without weakening documentation
  write guards or normal authorization.
- **Recovery semantics:** automatic retry or Analyst handoff could recreate the
  loop. Recovery must be explicit, bounded, and fail closed; if repository
  state cannot support this safely, stop and report the blocker rather than
  inventing a parallel state mechanism.
- **Existing test coverage:** `TESTS.md` describes Analyst interception, but
  this does not establish a security boundary. Replace that claim only when
  source and focused tests support the new contract.

## Out of Scope / Prohibitions

- Do not change `roles.json`, provider routing, tool capability policy,
  authorization rules, Vault contents, or HITL approval semantics.
- Do not modify connected project source, its RAG corpus, or user task/run
  evidence except the minimum state fields required by the approved contract.
- Do not run Ollama, network requests, Docker, Gradle, broad synthetic loops,
  or unrelated test suites to validate this deterministic control-flow change.
- Do not claim a hard stop, incident persistence, recovery behavior, passing
  tests, or phase completion without direct evidence.

## Acceptance Criteria

- The threshold is unambiguous and enforced without an N/N+1 discrepancy.
- No tool beyond the allowed boundary is dispatched, and the current agent
  cannot continue by handing off to Analyst.
- A structured incident and explicit fail-closed recovery state are persisted
  and presented consistently in ordinary and documentation task modes.
  `breaker_blocked` is not resumable; `python runner.py --reset USER` explicitly
  clears only the session state, while starting a new task replaces it.
- Prior side effects are reported accurately; no rollback is implied.
- Focused deterministic regression tests pass; the full deterministic suite is
  run only if focused results and scope justify it.
- README, TESTS, handover, and roadmap accurately reflect observed behavior;
  no unrelated or sensitive runtime data is included in the diff.

## Expected Outcome

The tool-call breaker is a testable control-flow/security boundary with
deterministic threshold semantics, a durable structured incident, and an
explicit recovery path. Users can distinguish a breaker stop from success,
ordinary model refusal, or a generic error. Any already-executed side effects
remain visible and are not represented as rolled back.

## Completion Record — 2026-10-01

`runner.py` now treats N as the maximum calls processed in one agent turn and
blocks attempted call N+1 before dispatch. The saved state receives
`status="breaker_blocked"` and a structured `breaker_incident` containing the
agent, mode, limit, attempted call number, processed-call count, recovery
instruction, and timestamp. Both ordinary and documentation modes exit without
Analyst handoff; the model-backed regulator is not triggered after a breaker
stop. Resume rejects this status with guidance to use `python runner.py --reset
USER` or start a new task. Earlier processed calls are explicitly reported as
not rolled back.

Focused tests: `python -m unittest tests.sandbox.core.test_tool_circuit_breaker
-v` passed 2 tests, including both task modes and session-only reset behavior.
Adjacent resume, documentation-transition, and session-lifecycle tests passed
11/11. No live model, network, Vault, RAG, Docker, or connected project was
used. The full suite was not run because focused and adjacent deterministic
tests directly exercise the changed contract.

### Live Runner Acceptance — inconclusive

Two local-only CLI attempts used `MINI_AGENT_OFFLINE=1` and disposable user
IDs. Neither reached the breaker:

- `phase19-live-20261001`: Runner dispatched two `read_file` calls against its
  isolated workspace, where `AGENTS.md` was absent. The model then returned a
  tool-call-shaped JSON string as ordinary content; Runner entered Shift-Left
  validation and reported `No supported source files found for validation`.
- `phase19-live-2-20261001`: Runner dispatched `create_file` for
  `breaker_probe.md`, then again returned the next tool-call-shaped JSON as
  ordinary content. The same validation error repeated; only the create call
  appears in saved tool executions. The run was interrupted at four agent
  steps, with the task still `in_progress` and no breaker incident.

The second validation result is consistent with the checked-in validator:
Markdown-only detection treats files other than its explicit metadata allowlist
as artifacts, while the disposable user directory also contains `vault.enc`
and `vault.key`. That allowlist omission was not changed in Phase 19.

Both states and their generated runtime artifacts were preserved. No project
source was touched. The Runner's final automatic unload was interrupted; a
manual unload then succeeded and `ollama ps` was empty. These attempts do not
establish live end-to-end breaker behavior. A separate diagnosis is needed for
the observed model/Runner turn progression and workspace validation. No further
live retries were made.

## Active follow-up — offline Ollama/Runner compatibility

**Status:** Active; user authorized stepwise diagnosis and focused fixes.

Establish why local Qwen returned tool-call-shaped JSON as ordinary content,
compare it with the successful offline Phase 7 run, and fix only a confirmed
protocol/Runner defect. Do not infer that all offline mode is broken or that
arbitrary JSON text should execute as a tool call.

### Ordered steps

1. **Compare preserved traces.** Inspect `data/phase7_offline_test/state.json`
   and both `phase19-live-*` states using redacted structure only: status,
   task mode, agent steps, executed tool names/counts, message roles, whether
   content parses as exact tool-call JSON, and whether native `message.tool_calls`
   entries were recorded. Do not print prompts, file bodies, argument values,
   or Vault contents/keys. Establish historical model/provider where saved
   evidence permits.
2. **Trace the source path.** Follow the completion response through
   `LiteLLMAdapter` → `safe_llm_completion` → Runner message-history assembly
   → tool dispatch. Compare current logic with successful-run records/revision.
   Do not modify code in this step.
3. **State a diagnosis before patching.** Distinguish provider formatting,
   history serialization, prompt-induced plain-text JSON, and workspace
   validation. If evidence does not distinguish them, propose one bounded
   local-only reproduction; do not launch it without separate approval.
4. **Apply the smallest confirmed fix.** Preserve offline-only policy, exposed
   tool allowlists, normal argument authorization, workspace isolation, and
   fail-closed handling. Never execute arbitrary JSON, fenced/partial JSON, or
   unknown tool names from assistant text. Keep the Markdown-only Vault-metadata
   validation issue separate unless it blocks the confirmed scenario.
5. **Test the fix.** Add focused deterministic tests for native calls, the
   confirmed Qwen shape, malformed/unknown text refusal, tool-result pairing,
   and the Phase 19 N/N+1 breaker. Then run one bounded CLI acceptance with
   `MINI_AGENT_OFFLINE=1`, an isolated synthetic workspace, and a disposable
   user ID. No cloud fallback, GTA source/RAG, Docker, Gradle, or broad retries.
6. **Close evidence and docs.** Record observed behavior, test results,
   remaining blockers, and final Ollama process state. Preserve test states;
   do not commit or push unless separately requested.

### Step 1 result — saved-trace comparison

The saved Phase 7 state is `completed` in documentation mode with six agent
steps and five successful `create_file` executions. Its telemetry contains 15
records for `ollama/qwen2.5:14b` over about an hour and an old breaker note;
the state does not identify a single run or preserve raw completion response
shapes. It proves historical offline tool execution, but not whether native
`message.tool_calls` or text-shaped calls were used in the final successful
run.

Both Phase 19 attempts used only `ollama/qwen2.5:14b` under offline routing.
The first saved two failed `read_file` executions; the second saved one
successful `create_file`. Both then stored tool-call-shaped JSON as ordinary
assistant content and entered Shift-Left validation. Neither reached the
breaker or completed. The distinct workspace validation failure is also
observed; it is not evidence of the cause of the response-shape discrepancy.

Conclusion: saved evidence confirms offline routing worked in both periods and
that historical tool execution succeeded, but cannot establish a regression or
distinguish a provider response-format change from prompt/history effects. No
prompts, file bodies, arguments, Vault content, or keys were inspected. No code
was changed and no model request was made for this comparison.

### Current step

Step 2: trace `LiteLLMAdapter` through `safe_llm_completion`, message-history
assembly, and Runner tool dispatch; compare with available historical source
evidence. Do not modify code or launch another model request during this step.

### Step 2 result — current source path

`LiteLLMAdapter.complete` passes LiteLLM's completion response through without
normalizing its message or tool-call shape. `ModelRouter.complete` returns that
response in `ModelResult`; `safe_llm_completion` sanitizes message content and
returns the same response object. Runner dispatches only when
`response.choices[0].message.tool_calls` is present. Otherwise it assigns
`message.content` as the answer and exits the tool loop; it does not parse
assistant text as tool instructions. Native tool-call messages are serialized
into conversation history with `message.model_dump()`, and tool results are
appended with the matching call ID.

The saved Phase 7 state has no raw completion messages, so it cannot be compared
to this response-handling path. The implementation explains the observed
behavior once a response contains tool-shaped JSON only in `content`, but does
not establish why Qwen/LiteLLM produced that shape in those two attempts. The
missing `vault.enc`/`vault.key` metadata allowlist in Markdown-only validation
is a separate observed workspace-validation defect; do not conflate it with
the absence of native `tool_calls`.

### Step 3 result — bounded protocol probe

With the user's approval, one `ModelRouter` completion was sent to
`ollama/qwen2.5:14b` under `MINI_AGENT_OFFLINE=1`, local-only privacy, no cloud
fallback, and zero retries. It returned one native `list_directory`
`tool_call`, with no assistant content. The tool was not dispatched and no
workspace was used. Ollama was stopped afterward; `ollama ps` was empty.

This confirms that the installed local model/router combination can return a
native tool call for a small tool-enabled request. It does not reproduce the
failed Runner prompt/history, prove that LiteLLM always preserves the shape, or
identify why the two earlier attempts returned content-only JSON. Therefore
no protocol parser or orchestration change is justified; arbitrary assistant
text remains non-executable.

The separate workspace blocker is confirmed in code: Markdown-only validation
counted `vault.enc` and `vault.key` as artifacts. The validator now excludes
those exact runtime filenames, and focused validation tests pass 7/7,
including acceptance of Markdown plus empty runtime-file markers and rejection
of runtime files alone. No Vault contents or keys were read.

### Current step

The confirmed validator defect is fixed and focused-tested. A full CLI Runner
acceptance and reproduction of the original content-only response remain
unproven; the one-shot probe was not end-to-end acceptance. Do not make a
protocol fix without evidence from the actual Runner request path. Preserve the
failed states and ask before any additional model request beyond the approved
Runner probe below.

### Bounded Runner probe — 2026-10-01

With user approval, one `runner.py` CLI run used the new isolated profile
`phase19-runner-probe-20261001`, `MINI_AGENT_OFFLINE=1`, and a 180-second
per-request Ollama timeout. The task asked the agent to create one Markdown
probe file only inside its assigned workspace. The process ended within the
five-minute wall-clock cap. Telemetry contains three records, all for
`ollama/qwen2.5:14b` / provider `ollama` (one planning and two coding records);
no cloud provider appears. The disposable workspace contains the expected
175-byte `runner_probe.md` artifact.

The saved task state is still `in_progress`, `current_turn=coder`,
`agent_steps=1`, with only the original user memory and **zero saved tool
executions**. The file itself was not read. In the current Runner source the
only path that writes workspace files is tool dispatch, and that branch is
entered only for native `message.tool_calls`; this is strong evidence the
Runner dispatched a native tool call, but the saved state does not preserve
that execution as evidence. The exact reason the run stopped before the turn
state was persisted is not established. Thus the probe supports the hypothesis
that native calls can reach Runner dispatch, but it is not a passing end-to-end
acceptance and does not explain the earlier content-only JSON responses.

The Ollama model and embedder were explicitly stopped; final `ollama ps` was
empty. The state and artifact are preserved. No project source/RAG, Vault
contents/keys, or other user profile was accessed.

### System RAG concept probe — 2026-10-01

One approved `runner.py` offline run used a new profile
`phase19-coroutines-rag-run-20261001` and asked about Kotlin `suspend`,
`CoroutineScope`, structured concurrency, and cancellation. It made four
completion calls (one planning, three coding), all
`ollama/qwen2.5:14b` / provider `ollama`; no cloud provider appears. Retrieval
hits are not persisted by this Runner path, so the generated book citation
does not independently prove which global-library chunks were retrieved.

The assistant stopped the run at an imposed five-minute cap; the user later
explicitly objected to that cutoff. Runner successfully
dispatched `create_file` **three times** to the same `coroutines_rag_probe.md`
path. All three tool records are present in state, confirming dispatch-result
persistence works. The 1,560-byte Markdown answer discusses suspend functions,
`CoroutineScope`, and structured cancellation and cites *Jetpack Compose
Internals*. State remains `in_progress`, `current_turn=coder`,
`agent_steps=1`; no Reviewer verdict or completed task exists. The response was
not independently validated against saved retrieval hits; this is **not** a
passing RAG/Runner acceptance. The code-mode Runner repeated successful
Markdown writes instead of ending the turn after the first write. Ollama was
stopped and final `ollama ps` was empty. Profile and artifact are preserved;
no retry was made.

### Persistence diagnosis — source-confirmed

Runner appends the tool execution record to the in-memory state and then
appends the tool reply to in-memory message history. Durable
`update_state_metrics`/`save_state` occurs only after the agent turn finishes.
The surrounding exception handler prints `Error during LLM call: ...` and
breaks without saving the in-memory state or exception. Therefore an exception
after the file write but before the end-of-turn save leaves an orphan workspace
artifact beside the old `in_progress` state. This save boundary is confirmed
in source and matches the observed divergence.

The exact exception for this run is **not recoverable**: it was not written to
a durable log, and the captured CLI output did not retain it. No specific
exception (including a missing tool-call ID) is claimed. The evidence confirms
the durability gap, not the exact instruction that threw.

### Persistence fix — 2026-10-01

Runner now saves each normal tool-execution record immediately after dispatch,
before appending the tool reply to in-memory message history. The
documentation-path rejection branch also persists its record before
continuing. An early turn exception now persists `last_runner_error` with a
safe category, exception class, stage, agent, task mode, and timestamp; raw
exception text is neither persisted nor printed. The task remains
`in_progress`, and no success is implied.

`tests/sandbox/core/test_runner_tool_persistence.py` injects a failure at the
next model completion after a successful file dispatch. It verifies the file
and execution record survive, the safe error metadata is saved, and the raw
exception message is absent. The persistence, breaker, documentation
transition, and workspace-validation modules passed **15/15** tests. Ruff
passed for the new test module. Runner-wide Ruff still reports the existing
unrelated findings; no model request was used for these tests.

### Current step

The dispatch durability/error-recording fix is deterministically tested. The
live system-RAG concept probe also stopped incomplete after repeated writes;
its profile is preserved and must not be resumed. Next inspect and fix
code-mode repeated-write/turn-completion behavior and retrieval provenance
before another live acceptance. No further model request without approval. The
earlier content-only Qwen response cause remains unproven; do not claim Phase 19
live acceptance.

## User-authorized CLI repair — ordinary questions — 2026-10-01

The user supplied a complete real run of `python runner.py` with
`kotlin language show function`. It entered Coder, attempted file creation,
then repeated Shift-Left correction for ten steps before the global stop.
Repeated storage log lines were saves, not agent steps. Source inspection
confirmed that the no-argument entry point always started a code task; the
Coder role explicitly requires file creation. The project-Q&A menu was only
reachable through `--project-qa`. This evidence does not establish that Qwen
alone regressed or that historical cloud-provider runs succeeded.

The approved repair changes ordinary startup to a menu. General question
answering selects no project, supplies no tools, performs no RAG retrieval or
code validation, and uses exactly Analyst then Reviewer. Registered-project
Q&A requires explicit menu selection. Code generation requires menu option 3
or `--code`. The role models/routing are reused with conversation prompts.
Provider permissions, project source, corpora and saved task states are not
changed. Normal completion guardrails, Vault mapping and telemetry remain.

Console stdout is line-buffered so progress does not accumulate behind stderr
logs in Git Bash. State-save messages show actual counters rather than an
unchanging list of keys; model dispatches and safe failure categories are
visible. Explicit ordinary code tasks stop at two consecutive identical
validation failures with `validation_blocked`; documentation and project-patch
validation workflows retain their existing retry behavior.

### First actual CLI run after repair

Git Bash ran `python runner.py`, menu option 1, under
`MINI_AGENT_OFFLINE=1`, with the exact supplied question:
`mobile kotlin coroutines. show few examples of dispatchers`.
Both Analyst and Reviewer used `ollama/qwen2.5:14b`; the process completed
naturally with exit code 0, without tool calls or a code-validation loop.
Automatic model unload finished and `ollama ps` was empty. The preserved
`data/user_123/state.json` SHA-256 remained
`52600fb65bd9d00b96ed735c06a02c9b7e405d9501640a09eac1cdec595cf2a7`.

The final answer was **not accepted as correct**: Reviewer copied the draft,
including undefined `launch` receivers and `updateUI(data)` against a declared
zero-argument `updateUI()`. This run proves the ordinary control flow returned
an answer, not the correctness of that answer. The review instructions were
then corrected to inspect declarations, scope, signatures and assumptions,
and the draft is now followed by an explicit review request. The same supplied
question was rerun through the same CLI. No broad/unit-test suite was run during
this repair.

### Subsequent actual CLI results

The second dispatcher run used the same Git Bash command, offline flag, menu
option and verbatim question after the prompt change. It again finished with
two Ollama/Qwen agent turns, a visible final answer, exit code 0 and automatic
unload. Reviewer still incorrectly accepted snippets that call `launch(IO)`
and `launch(Default)` without a declared `CoroutineScope` receiver. Thus the
prompt change did not solve this answer-quality defect. No further dispatcher
retries were made.

The user's original failure case was then reproduced with the repaired CLI:
Git Bash ran plain `python runner.py`, with `MINI_AGENT_OFFLINE` unset and the
question `kotlin language show function` typed directly at the menu prompt.
The existing role policy selected `ollama/qwen2.5:14b` for both turns. It returned
three function examples, including:

```kotlin
fun greet(name: String): String {
    return "Hello, $name!"
}
```

The process exited naturally with code 0 after Analyst and Reviewer, with no
tool dispatch, Shift-Left loop or project selection. Its explanation still
incorrectly called an ordinary `sayGoodbye` function "inline" and described
the order of a Kotlin function declaration imprecisely. Reviewer is therefore
not a reliable correctness gate, even though the original infinite-correction
symptom is absent and a concrete function answer is delivered.

After all three runs, `ollama ps` was empty and the preserved `user_123` state
hash remained unchanged. No project source or corpus was used. Runtime
completion telemetry and normal Vault mappings were allowed through the usual
facade. The temporary RAG helper has no remaining diff. New regression source
covers menu isolation, rejection of unexpected tools, explicit project
selection and repeated code-validation failure; these unit tests were not run.
Syntax parsing passed, Ruff passed on the new service/router/regression module,
and `git diff --check` passed. Runner-wide Ruff reports nine existing findings.

**Current result:** ordinary CLI workflow and visible completion are repaired
and exercised through the actual Runner. Semantic answer quality remains open;
do not claim all-system acceptance, correct dispatcher examples, tested code
generation, or Phase 19 live breaker acceptance. Preserve these observations
instead of repeating model calls or adding a question-specific canned answer.


## Offline review and shared-library repair ? 2026-10-02

The user's new `kotlin coroutine` transcript shows Reviewer adding a
`job.join()` suspend call inside ordinary `fun main()`, although Analyst had
not produced that example. Source audit confirms the original question and
complete draft reach Reviewer, but free-form output was accepted without a
separate review record. Existing scope/signature instructions did not prevent
this. It is not evidence of a transport failure or of compiler validation.

The authorized repair adds a structured model assessment with concrete
corrections, uncertainties and answer. The parser refuses invalid, incomplete
or inconsistent records without model retry; unresolved issues are displayed
with CLI exit 2. Both completed model calls and `code_validation=not_run` are
separate service result fields. CLI exit 0 is successful conversation protocol,
not proof of semantic correctness. Completion telemetry `Success` is unchanged
and still describes only the model call. Reviewer is instructed to audit its
own revised examples, explain specific defects and avoid unsupported examples.

The first actual offline Runner run used the menu and the exact question
`mobile kotlin coroutines. show few examples of dispatchers` in the new profile
`phase19-qa-review-20261002`. Both local Qwen calls completed, structured review
parsed, exit was 0 and automatic unload completed. Reviewer replaced GlobalScope
examples but introduced `import androidx.lifecycle.ViewModelScope`, with missing
ViewModel/launch imports. This answer is NOT accepted as correct. Transcript:
`data/phase19-qa-review-20261002/console.txt`.

During that run the user clarified the intended shared-book RAG. Source audit
confirmed general Q&A had no RAG, whereas the old global-reference helper required
a project ID and instantiated project RAG. A new separate book-only reader now
opens the existing `android_architecture_library` collection directly, never
`ProjectRegistry`, project collections, legacy user RAG or `get_or_create_collection`.
It uses local Nomic embeddings, supplies the same at-most-three excerpts to
both agents, reports filenames/chunk IDs, and labels excerpts untrusted technical
reference data. Missing/failed retrieval stops before completion; an empty
collection reports zero excerpts. PDFs are not reingested and no project source
is accessed. This changes the prior blanket no-RAG rule only for shared books.

Focused deterministic command:
`python -m unittest tests.sandbox.core.test_question_answering tests.project_rag.test_global_library_retrieval -v`
with `LITELLM_LOCAL_MODEL_COST_MAP=True` and `MINI_AGENT_OFFLINE=1`: **13 passed**.
Tests use mocked completion/embedding/Chroma, not actual model answers. Focused
Ruff passed on the two services and two test modules; Runner-wide Ruff reports
nine existing findings outside these edits. `git diff --check` passed.

The one book-enabled Runner run uses `phase19-qa-books-20261002` and the same
question/menu/offline flag. It selected these actual existing chunks:
- `1c01d135-2773-44ec-bbd5-dde0dbcafe2a`
- `89f8d256-f6a6-4d2c-b89e-f073a4f91258`
- `43a34bf3-22c8-4e81-85a7-941f25dae1af`

All three are from `Kotlin In Action.pdf`; inspection shows reflection and DSL
text, not dispatcher guidance. Their stored excerpts and SHA-256 values were
saved separately in `data/phase19-qa-books-20261002/book_references.json` by ID
lookup without an additional model/embedding request. The index still contains
2,293 chunks: Compose Internals 326; Kotlin In Action 859; Software Architecture
with Kotlin 1,108. A bounded literal lookup found two `Dispatchers` chunks in
Compose Internals, both about Compose in a browser and JS Main, not the requested
Android Main/IO/Default examples. This is insufficient evidence for the question;
do not claim the entire books lack coroutine information or that RAG guarantees
correctness. No corpus contents were changed.


### Completed book-enabled live result and remaining boundary

The book-enabled run completed naturally with exit 0 and automatic unload.
Both telemetry entries are `ollama/qwen2.5:14b` / provider `ollama`: planning
99.42 seconds, review 132.20 seconds. The earlier no-book run recorded planning
103.57 seconds and review 92.47 seconds. These `Success` records only establish
completed model calls. No further model retries were made.

Reviewer returned `revised` and identified GlobalScope and an undefined readFile,
but its final snippets use `lifecycleScope` in top-level functions without an
Activity/Fragment receiver, import `androidx.lifecycle.coroutineScope` instead
of the required lifecycleScope extension, omit launch/withContext imports and
leave textView undeclared. The readFile implementation is still absent, although
labelled as assumed elsewhere. The answer also does not explicitly distinguish
its general knowledge from the irrelevant retrieved book excerpts. This is a
FAILED semantic acceptance, despite valid structured review and CLI exit 0.
Transcript: `data/phase19-qa-books-20261002/console.txt`.

Final `ollama ps` is empty. Neither new QA profile contains `state.json`.
The preserved original `data/user_123/state.json` SHA-256 remains
`52600fb65bd9d00b96ed735c06a02c9b7e405d9501640a09eac1cdec595cf2a7`.
No GTA/project source or RAG was read or changed, no PDF reingestion, compiler,
Gradle, Docker, provider/model configuration, role policy or historical task
state change occurred. No commit/push was made. The console captures and
book-reference inspection records are runtime evidence, not source fixtures.

Implemented: separate review protocol/statuses and shared-library access.
NOT solved: reliable semantic/code correctness, retrieval relevance/adequate
question coverage, or Phase 19 live tool-breaker acceptance. Do not claim that
RAG or a schema validates Kotlin. The next decision must address this evidence
boundary explicitly (appropriate offline references and/or separately authorized
isolated snippet validation), not another prompt-only retry or GTA build.


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


## Named-file project retrieval repair - 2026-10-02

The user supplied the real question:
`does project gta cheats app have file CheatCodes.kt? If yes answer, what in this file CheatCodes.kt ?`
The saved snapshot and project Chroma both already contain
`core/src/main/java/com/gamescheats/core/domain/model/CheatCodes.kt`, with matching
SHA-256 `b870f825f173e91d8a3c43bef09421cb4edefa5e96e430364d46b6a7edd1f489`.
The stored chunk defines `data class CheatCodes(val groups: List<CheatCodeGroup>)`.
No connected source read or reindexing was needed to establish this.

Deterministic replay of the old helpers selected four unrelated snapshot paths
and four generic lexical hits including Gradle/XML. The quota was four matching
sources, NOT four words from the question. Generic words were processed before
the explicit filename, and text scoring did not prioritize source names. A
short `CheatCodes.kt` lookup found the correct snapshot entry first.

The bounded correction recognizes explicit source filenames/relative paths,
resolves whole path components in the selected project's snapshot before generic
matching, and retrieves only those files' existing chunks. Named-file questions
no longer substitute generic vector/lexical neighbours. Missing files/chunks
remain missing evidence, without claiming absence from the live checkout.
Duplicate basenames raise a visible path-clarification error before model calls.
Normal questions without an explicit filename retain the previous hybrid path.
Chunk hashes from direct source retrieval now also pass through the existing
project-QA consistency checks; mismatched chunks are not accepted by snapshot
hash alone. No role prompt, model, provider, task status or agent chain changed.

Verification: the retrieval/project-QA modules passed 25 tests, followed by the
additional ambiguity-message test (1/1). Focused Ruff passed for both production
modules and both test modules. These are deterministic results, not live proof.
The exact original question was subsequently checked once through the real
offline Runner menu, with GTA explicitly selected (result below). Capture directory:
`data/offline-acceptance-20261002/project-filename`.


### Named-file real Runner acceptance - completed

The exact user question completed through real menu option 2 and explicit GTA
selection under MINI_AGENT_OFFLINE=1. Both configured Ollama/Qwen agent calls
completed. Runner confirmed the file, described `CheatCodes.groups` as
`List<CheatCodeGroup>`, and printed only
`core/src/main/java/com/gamescheats/core/domain/model/CheatCodes.kt` as its source.
Snapshot revision remains `869a2a9e1d75`; process exit 0; elapsed 81.65 seconds.
Final `ollama ps` is empty. All 19 preserved historical task hashes are unchanged.
No corpus reindexing, GTA source write/build, role/status change, commit or push
occurred. Phase 19's separate live N+1 acceptance remains open.

### Publication checkpoint and deferred truncation investigation

The user authorized documenting and publishing the accumulated fixes before
further implementation. The subsequent user-run Navigation.kt question retrieved
the correct source but stopped mid-code and omitted the requested explanation.
This transcript is separate from the seven captured CLI processes recorded in
OFFLINE_ACCEPTANCE_20261002.md. Project Q&A uses max_tokens=200 for each agent;
finish_reason is not checked there. The limit is a plausible, unconfirmed cause.
No output-limit fix, new model run, book/project context merger or phase closure
is claimed. After publication, start with this bounded truncation issue as
specified in NEXT_STEPS_PLAN.md. Preserve the earlier evidence and state.
