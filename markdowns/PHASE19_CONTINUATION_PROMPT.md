## Latest continuation checkpoint - 2026-10-02

The user requested documentation, commit and push first; project-Q&A answer
truncation is the next implementation task afterward. Follow NEXT_STEPS_PLAN.md.
The named-file retrieval repair passed one actual offline Runner run. A later
user-run Navigation.kt query found its source but ended mid-code. The configured
200 output tokens per agent suggest truncation; finish_reason has not confirmed
that diagnosis. Do not claim book RAG is the cause, reindex, change agent roles,
or repeat model requests without a scoped diagnostic need.

Phase 19 live N+1 remains OPEN. Ordinary Reviewer uses plain text/Markdown;
historical structured-review and semantic-acceptance instructions below are
superseded. Preserve all historical task states and acceptance profiles.

## Earlier user-authorized runtime acceptance - 2026-10-02

Start from `OFFLINE_ACCEPTANCE_20261002.md` and its latest results. The user
rejected changes based solely on assistant judgments of Qwen answer quality.
The current authorized work audits the diff, removes ordinary Reviewer JSON
requirements, makes book failure non-blocking, and exercises actual CLI routes.
This supersedes the review-quality instructions below. Full output and inputs
must be preserved; focused tests are never called full runtime acceptance.
Code-task/project Reviewer, roles, model policy and historical task states must
not be rewritten to force success. No GTA write, build or corpus reindexing.

# Phase 19 Continuation Prompt — harden the per-turn tool breaker

## Current follow-up — 2026-10-02

The user authorized fixing ordinary offline answer review, then clarified that
general questions should use the existing shared PDF book library while GTA
RAG remains project-bound. The earlier blanket no-RAG restriction below is
superseded only for shared book retrieval. `global_library_retrieval.py` opens
only the existing global library; no registry, project RAG, ingestion or source
tree is involved. Both agents receive the same labelled excerpts. Reviewer
returns structured corrections/uncertainties/final answer; this is a model
assessment, not code validation. Read the latest preparation record before
any more model requests. Preserve both new QA profiles and all older evidence.

## Latest user-authorized follow-up — ordinary Runner questions

The user explicitly authorized fixing the ordinary CLI question/answer chain
and a complete real Runner verification. Project context must exist only after
explicit menu selection. `python runner.py` now offers general questions,
project Q&A, and code tasks; general questions invoke Analyst then Reviewer
without code tools, RAG, project lookup, validation, or regulator execution.
Read the current handover and latest acceptance record in
`PHASE19_PREPARATION.md` before continuing. Older no-model restrictions below
describe earlier checkpoints, not this explicitly authorized run. Do not
resume or reset the user's failed run or the old probe profiles.

Actual CLI verification is now recorded: both supplied questions reached
Analyst then Reviewer and a final answer, exited with code 0, and unloaded
Ollama. The user state was preserved. Reviewer still accepted incorrect
examples/terminology, so answer correctness and overall phase closure remain
open. Do not rerun the same dispatcher question without a justified change,
substitute canned answers, or claim these Q&A runs exercised the tool breaker.

## Earlier checkpoint

Phase 19's breaker implementation and deterministic tests are complete
locally; live Runner acceptance is inconclusive. The user authorized a
stepwise offline-Ollama diagnosis and focused fixes. This is now the active
follow-up. Read `PHASE19_PREPARATION.md` and execute its ordered steps. Step 1
is complete: historical Phase 7 state proves successful offline tool
executions but lacks per-run IDs/raw response shapes; both failed Phase 19
runs routed only to local Ollama and treated tool-call-shaped JSON as ordinary
assistant content. The evidence does not establish regression or root cause.
Step 2 source tracing is complete: the adapter/router pass the response through;
`safe_llm_completion` sanitizes content but does not normalize tool calls; the
Runner dispatches only native `message.tool_calls` and treats content-only
JSON as an answer. One approved local-only ModelRouter probe returned a native
tool call, but did not reproduce the full Runner request or explain the earlier
content-only responses. One approved CLI probe created its expected artifact
in a new disposable workspace with Ollama-only telemetry, but the saved task
state remained `in_progress` with zero tool-execution records. Source indicates
the artifact can only be written through native tool dispatch, yet the state
does not durably confirm it; exact stop cause is unknown. The confirmed
Markdown validator omission for `vault.enc`/`vault.key` is fixed; focused tests
pass 7/7. The persistence gap is fixed: each dispatch record is saved before
tool-result message pairing, and early exceptions save category/type/stage
without raw exception text. A focused failure-injection test plus breaker,
documentation-transition, and validation tests passed 15/15. One offline
system-library concept probe then created an answer artifact but repeated
`create_file` three times and hit the five-minute cap before Reviewer/completion.
Tool records persisted; retrieval hits did not. Current step: inspect/fix
code-mode repeated-write turn behavior and retrieval provenance. Do not resume
either probe profile or make another model request without approval. Never
inspect Vault contents.

The original Phase 19 contract remains: N is the maximum number of calls
processed in one turn: allow calls 1..N and block N+1 before
dispatch. In multi-call responses, discard calls after N+1. Persist the
structured incident and a non-resumable `breaker_blocked` status. The explicit
`--reset USER` session reset is the recovery action; a new task replaces the
old state. Do not route a breaker event to Analyst or trigger a model-backed
post-session action. Preserve already-executed side effects and do not claim
rollback.

Do not alter provider policy, roles, tool authorization, Vault, HITL patch
approval, connected project/RAG data, or unrelated saved evidence. Use focused
deterministic tests with mocked model/tool responses. No model, network,
Docker, Gradle, or broad retry loops are authorized by this phase plan.

Report actual changes, tests and results, remaining blockers, and the final
diff. Update canonical documentation only with observed facts. Do not commit
or push unless separately requested. Mark Phase 19 complete only after every
acceptance criterion in `PHASE19_PREPARATION.md` is evidenced.
