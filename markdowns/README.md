## Project-Q&A chain visibility — 2026-10-03

The project-selected CLI prints both the Analyst draft and Reviewer final answer.
A live `GtaSaViewModel.kt` check confirmed exact-file retrieval but exposed an
open quality defect: both agents omitted the retrieved implementation details of
`loadFavoriteCodes()` and used an unsupported "immediately" description. This
run does not accept Reviewer correctness or complete project-Q&A behavior.

## Shared book chunk continuations — 2026-10-03

General no-project Q&A keeps the three-reference limit, but a selected book chunk
may now include one immediate continuation from the same PDF and the same header
section. Runner prints every included chunk ID. This prevents an explanation
split at a chunk boundary from losing its conclusion without mixing books or
project evidence. A real Compose slot-table/change-list question verified the
before/after behavior through Analyst and Reviewer. GTA project RAG remains
separate and was not used by this check.

## Phases 20–22 security boundary status — 2026-10-02

Phases 20–22 are closed locally. `evals_pipeline.py` now runs the deterministic
cases in `tests/security_behavioral_manifest.json`: filesystem, state, facts,
network, tool dispatch and Vault effects. It passed 10/10 without a model. A
real Docker test also confirmed an outbound socket cannot connect; full test
discovery passed 261 tests with 8 expected skips.

`tests/adversarial_prompts.json` is a model-quality corpus and does not create a
security score. Telemetry supplies bounded payload-free evidence IDs. Regulator
output requires proposal, confidence, cited evidence and affected rule, then a
deterministic gate may admit it only for human review. The Regulator has no tools
and always has `auto_apply=false`; it never rewrites roles, facts, capabilities
or policy. See `SECURITY_BOUNDARY_MATRIX.md` and Phase 20–22 preparation records.

The older Release 1.0 claims about a prose-derived 100% Security Score,
automatic self-evolution and Regulator fact/policy rewrites are superseded.

## Runner entry point — ordinary questions and explicit project selection

Phase 19 is closed locally (2026-10-02): a real offline Runner run processed
five tool calls and blocked the sixth, persisted breaker_blocked and its
incident, and rejected resume. The acceptance record is consolidated in
`CODEX_HANDOVER.md` and `OFFLINE_ACCEPTANCE_20261002.md`;
earlier inconclusive checkpoints below are historical. Blocked code tasks
still exit the CLI with 0; use the recorded task status, not exit code alone.

Local requests with tools use LiteLLM's native ollama_chat transport to Ollama
/api/chat. Configured ollama/model identifiers, local-only routing and tool
authorization are unchanged. Requests without tools retain their previous
completion transport. Assistant text is not converted into executable calls.

Run `python runner.py` to open the menu. Option **1** asks a general question
without selecting a project. Enter the question after selecting 1, or type it
directly at the menu prompt. Analyst drafts an answer and Reviewer returns the
final answer. General questions now retrieve up to three excerpts from the existing
shared `android_architecture_library` book collection. Both agents receive the
same excerpts, labelled as untrusted technical references; the console lists
book filenames and chunk IDs. This path has no filesystem tools, project lookup,
project/user RAG, code validation, or regulator call. It does not reset or resume saved code tasks.
It uses the existing Analyst/Reviewer models and routing settings from
`roles.json`, with conversation prompts rather than the code-generation prompts.

Actual CLI runs return answers and exit after the two agent turns. This
repairs the observed question-to-codegen loop. Reviewer returns ordinary
text/Markdown, not a mandatory JSON assessment. Empty, truncated or tool-call
responses still stop visibly. Exit 0 means this conversation route completed;
it does not certify generated code. Completion telemetry `Success` describes
only a successful model call.

The library reader opens only the existing global collection, never a project
registry or project collection, and uses local Nomic embeddings. Missing or
failed book retrieval is reported and the question continues without books.
It does not ingest PDFs or rebuild the index. For camel-case technical names,
up to two exact identifier/spaced-name passages precede vector hits, with table
of contents entries excluded from that literal stage. This addresses the
observed SlotTable ranking miss without changing project retrieval. Retrieved
passages remain candidates, not proof of correctness.

See `OFFLINE_ACCEPTANCE_20261002.md` for actual runtime results and unresolved
boundaries. Answer quality is distinct from orchestration acceptance.

Project-Q&A output repair (2026-10-02): the former 200-output-token budget is now
2048 per agent. A provider finish_reason of length stops the request with an
explicit incomplete-answer message, without an automatic retry or passing a
truncated Analyst draft to Reviewer. Completion reason and token count are
logged per agent. This is output-boundary handling, not a correctness check.
Project Q&A defaults to selected-project evidence only
(`include_technical_reference=False`); optional technical-book references are
not enabled by menu selection. Larger files can still exceed the bounded output
budget; separate the requested section and explanation if that happens.

Option **2** opens the registered-project catalog; a project is attached only
after the user selects it there. Option **3** explicitly starts a code task.
`python runner.py USER` also opens the menu; the old direct code-task entry is
now `python runner.py --code USER`. `--project-qa`, `--resume`, and project-patch
commands remain available. `--help` prints usage without creating a task.

For Git Bash, ordinary local question answering is:

```bash
export MINI_AGENT_OFFLINE=1
python runner.py
```

Select **1**, then enter the question verbatim. The direct equivalent is
`python runner.py --ask 'mobile kotlin coroutines. show few examples of dispatchers'`.
Omitting the offline variable uses the configured routing policy; it does not
automatically authorize cloud access. Console output is line-buffered, and each
model dispatch reports its actual provider/model and any safe failure category.
Questions finish after the two agent turns or report a failure; they never
fall through to code generation. Runtime guardrail/Vault mappings and model
telemetry still use the normal completion facade.

Code-task validation reports its redacted reason and stops with
`validation_blocked` after two consecutive identical failures. This is separate
from the per-turn tool-call limit; it does not grant validation or approval.

## Phase 19 checkpoint — live breaker acceptance remains inconclusive

Phase 18 removed the unreachable mocked confirmation branch for unsupported
external tools and preserved exact-hash user approval for reviewed project
patches. Its verification record is consolidated in `CODEX_HANDOVER.md`.

Phase 19 makes the per-turn tool-call limit a hard stop: calls 1..N may be
processed and call N+1 is blocked before dispatch. The incident is persisted
with `status="breaker_blocked"`; the task cannot resume. Run
`python runner.py --reset USER` to clear only session state, or start a new
task. Calls processed before the block are not rolled back. Deterministic
verification is recorded in `CODEX_HANDOVER.md`. Live Runner acceptance
is not yet established. Follow-up hardens dispatch durability: each tool result
is saved before continuing the turn, and early errors persist redacted
category/type/stage metadata. A failure-injection regression and adjacent
tests pass 15/15. The preserved live probe remains incomplete and is not claimed
as acceptance. A system-library concept probe produced an answer artifact but
repeated Markdown writes until the five-minute cap; retrieval provenance is not
persisted. The exact probe record is consolidated in `CODEX_HANDOVER.md`.

The approved standalone Project Catalog and Project-Bound Q&A task is
implemented locally; it does not designate a new numbered phase. The
deterministic suite passed 225 tests with 20 expected skips. See
`TASK_PROJECT_CATALOG_AND_QA.md` for the design and verification.

For read-only Q&A over a registered project from the Runner CLI, run
`python runner.py --project-qa`, select a listed project by number or ID, then
enter the question. Catalog metadata is stored in `data/registry/projects.sqlite`;
project RAG remains isolated under `data/projects/<project-id>/rag`, outside
the connected source tree and legacy user RAG. Both Runner and the compatibility
`project_qa.py` entry point call `project_qa_service.py`. Project-Q&A has
separate Analyst/Reviewer settings in `roles.json` and still uses the normal
router and project provider policy.

When a project question names a file such as `CheatCodes.kt`, quotes are
optional: the reader resolves the filename against that project's saved snapshot
before generic search. It supplies that file's stored chunks rather than unrelated
neighbours. Multiple matching paths require a project-relative path. Missing
indexed evidence is not proof that the file is absent from the live checkout.

Before calling a model, Q&A validates retrieved project-code source paths and
file hashes against the registered project's saved snapshot and reports its
derived snapshot revision. Missing, stale, cross-project, or malformed evidence
fails closed. This validates provenance, not semantic entailment: a non-empty
model answer is not deterministic proof that every claim is true. The CLI
prints the Reviewer answer, snapshot revision, and evidence sources, then
unloads local completion and embedding models. The live registry has been
migrated backup-first. A repository URL is optional and stored separately from
the required local checkout path; the GTA entry currently has both. Cloning or
fetching remote repositories is not implemented. This mode does not start the general
code-task loop or project-patch workflow.

The Phase 7 material below is retained as historical operational context.

## Historical status — bounded execution on 2026-09-16

- `phase7_quality_final` remained an immutable historical failed run
  (`in_progress`, actual `agent_steps: 11`) with no reset, edit, or resume.
- One automated preflight successfully started Docker Desktop and confirmed
  Docker, native Ollama, `qwen2.5:14b`, `nomic-embed-text:latest`, and FastAPI.
- The bounded `phase7_dispatch_guard` task completed after one focused
  dispatch fix and one passing test (**1/1**): an invalid documentation write
  is rejected before persistence without consuming a separate step.
- One opt-in Ollama/Chroma run passed **1/1**. One real offline documentation
  resume completed with `agent_steps: 2` and Reviewer verdict `APPROVE`.
- The final full suite reported **126 tests, OK (skipped=3), exit code 0**;
  no Ollama models or Docker containers remained loaded after the run.

**Phase 7 was closed on 2026-09-16. The historical `phase7_quality_final`
failed run was preserved unchanged.**

### Phase 7 operational workflow

`phase7_operational_preflight.ps1` is the single preflight workflow. If
`docker info` is unavailable, it locates Docker Desktop through the installed
Docker CLI, starts it hidden, and waits for the daemon. It then checks the
native Ollama endpoint and the presence of `qwen2.5:14b` and
`nomic-embed-text:latest`, briefly starts FastAPI on loopback only, and stops
that process. The script does not load models, change the Docker executor, or
create model storage. Runner is started separately as a controlled process
without a short external timeout.

### Current project map

| Area | Main components |
|---|---|
| Orchestration | `runner.py`, `roles.json`, `model_router.py` |
| Documentation workflow | `documentation_policy.py`, `project_retrieval.py`, `test_documentation_*.py` |
| Project/RAG state | `project_registry.py`, `project_rag_ingestion.py`, `rag_service.py`, `data/projects/` |
| API and policy | `api.py`, `capability_policy.py`, `work_ledger.py` |
| Isolated validation | `validation_worker.py`, `sandbox_executor.py`, `Dockerfile.executor` |

The architectural priorities carried forward from this period are isolation,
deterministic policy, vault separation, real validation, and a correct state
machine. Their current implementation and remaining boundaries are described
in the canonical documents in this directory.

---

## Historical status and reference material

## Status at the end of the 2026-09-15 session

### Result of the single resume — 2026-09-16

- The local Ollama endpoint was restored and the opt-in Ollama/Chroma
  integration passed **1/1**.
- The single offline resume of `phase7_quality_final` stopped before evidence
  and Reviewer checks because Coder wrote `# Overview` instead of the required
  `## Overview`. State remained `in_progress`, with `agent_steps=7` and no
  review verdict.
- No second resume or prompt tuning was performed. Phase 7 was still open at
  this checkpoint.

### Pinned-plan execution update — 2026-09-16

- Phase 7 gained a minimal deterministic evidence gate: each retrieval request
  with a direct match required one corresponding real RAG source path. The
  complex citation-to-code matching design was not restored.
- The new regression test and focused suite passed **52/52**. The full suite
  ran **126 tests: 111 passed and 15 skipped**; Docker tests were skipped
  because Docker Desktop had not been started by the operator.
- The opt-in Ollama/Chroma integration did not reach the agent loop. Embedding
  through `ollama/nomic-embed-text` returned `APIConnectionError`, and
  `ollama ps` timed out because Ollama could not create a log under
  `%LOCALAPPDATA%\\Ollama` (`Access is denied`).
- `phase7_quality_final` was not resumed and retained state `in_progress` with
  `agent_steps=6`. Until Ollama was restored externally, models, prompts, RAG,
  and task state were not to be changed.

**At this historical checkpoint Phase 7 was not complete. Work and generation
were stopped at the user's request.** This record superseded the older status
and continuation prompt below it at that time.

- Documentation artifact checks in `documentation_policy.py`, the `runner.py`
  changes, and exact retrieval of existing Chroma fragments in
  `project_retrieval.py` were preserved with regression tests.
- The final design was simplified to require the intended Markdown file, no
  unexpected files, required sections, and real RAG paths. Reviewer returned a
  structured `decision` and meaningful `reason`. Complex citation-to-code
  matching was removed. A link was not required in every section, and links
  were not treated as proof that every claim was true.
- Focused tests passed **51/51** after simplification. The latest full run at
  that checkpoint ran **125 tests: 122 passed and 3 skipped**, but it preceded
  the final simplification. The final simplified code had not yet received a
  full run or repeat opt-in integration.
- A successful real offline run of the simplified version had not been shown.
  `qwen2.5:14b` lost citations, and one Reviewer response cited the document
  itself as evidence. These failures did not close any new task.
- `phase7_offline_test` was `completed` at step 6 with a known quality defect;
  `phase7_quality_test` was `in_progress` at step 11 with its limit exhausted;
  and `phase7_quality_final` was interrupted at step 6 and preserved.
- All three tasks were bound to `gta-cheats--cc0fe5de`. `user_123`, Android
  sources, the legacy vault, dependencies, and Docker configuration were not
  changed. No commit was made. A switch to `qwen3.5:9b` was discussed only;
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

  🚀 Architecture and Design of the "Mini Agent Sandbox" Project
  The Mini Agent Sandbox project is a custom, locally deployable sandbox operating on the principles of an LLM-OS (LLM-based Operating System). It is designed
  for autonomous resolution of engineering tasks through the interactive collaboration of several specialized AI agents, equipped with their own multi-level memory and
  tools for interacting with the environment.
  Below is a detailed breakdown of the architecture, patterns, and tools embedded in the project.
  ──────
  ## 💡 Concept and Idea
  Instead of relying on a single prompt to a large language model, the system uses the concept of Multi-Agent Debate.
  The process is divided into roles. Currently, three basic ones are implemented:

  1. Feature Developer (Coder): Writes code based on the user's task and architectural context.
  2. Tech Lead Reviewer: A strict critic who checks the code for memory leaks, errors, and code-style compliance.
  3. Data Analyst (Analyst / Predictive Architect-Diagnostician): Analyzes session logs and generates Few-Shot instructions to fix the output.
  4. Architectural Arbitrator (Judge): Steps in in case of a deadlock between the Coder and Reviewer. Analyzes the logs of their debates and delivers a final, unappealable architectural verdict.

  Agents communicate in a loop until the Tech Lead is convinced of the solution's quality and issues an APPROVE verdict.
  ──────
  ## 🏗 System Architecture (Enterprise AI Pipeline)

The project's architecture is built around a 4-stage data processing pipeline that meets Enterprise AI standards:

### 1. Ingestion & Validation
- **Vector Database & Advanced RAG (ChromaDB)**: The knowledge base runs on the local `ollama/nomic-embed-text` model. The context is isolated by user.
  - *Knowledge Ingestion Pipeline*: Automatic conversion of PDF books to Markdown, semantic chunking, and vectorization.
  - *Query Expansion & Dynamic Context*: Query expansion with synonyms and dynamic substitution of architectural rules into prompts. Acts as **Restating Binding Constraints**, forcibly reminding agents of global rules on every turn.
- **Shift-Left Validation**: Static code analysis (Ruff, Semgrep) runs *before* passing the code to the Reviewer Agent. Errors are caught at an early stage, returning the code to the Coder with a detailed report, saving time and tokens. Linter execution is hardware-isolated via `subprocess` with strict timeouts (10s/15s) to prevent hangs.

### 2. Security & Anonymization
- **Mini Presidio (Layered DataGuardrail)**: Three-tier serverless leak protection: Regex, Contextual Validation, and Tokenization Engine (two-way obfuscation with substitution by tokens like `__VAULT_SECRET_...__`). Includes a Deobfuscation Vault (VaultRegistry) that encrypts the key map (Fernet AES-128) and unpackages tokens (Runner-Interceptor) on the fly before local code execution.
- **Prompt Injection Protection**: Includes Affirmative Reframing (CBSI framework), RAG Isolation (escaping extracted facts with XML tags), and Output Integrity Guardrails.
- **Tool and patch boundaries**: Unregistered tools, including external email, calendar, and web-search tools, are rejected by default. For project patches, a positive Reviewer decision is followed by explicit user approval bound to the exact diff SHA-256 before trusted validation. There is no general-purpose console HITL for arbitrary critical tools. Agents also have no direct system-shell tool.
- **Tool Circuit Breaker**: Processes at most `MAX_TOOL_CALLS_PER_TURN = 5` calls per ordinary agent turn (3 in documentation mode). Attempt N+1 is blocked before dispatch; a structured incident is saved and the task becomes non-resumable until session reset or a new task.

### 3. AI Analysis & Orchestration
- **Multi-Agent Debate**: Coder, Reviewer, Analyst, and Arbitrator debate until the `APPROVE` status is reached. The Reviewer Agent is reinforced with strict protocols: **SIX-DIMENSIONAL AUDIT METHOD** (code analysis across 6 vectors: dependencies, logic, access rights, etc.) and **AUDIT WORKFLOW** (a 4-step check with mandatory Unit test requirements and Slopsquatting protection). Built-in Arbitrated Debate & Graceful Abandonment safeguard (forced loop termination at step 8). A hard session reset is a defense against **Long-Session Failure (Silent Context Loss)**, preventing agents from forgetting initial requirements when logs grow excessively.
- **Provider-neutral Model Router**: `safe_llm_completion` preserves the LiteLLM response shape while a deterministic router applies task, context, privacy, quality, budget, quota, health, retry, and fallback policy. Cloud routes require both explicit cloud eligibility and a cloud-allowed privacy policy; defaults are local-only.
- **Tiered Memory Architecture**:
  - *Tier-1 (Working Memory)*: `state.json` stores the Session State. Includes the Orchestrator Tool Tracking mechanism for strict logging of tool calls and eliminating hallucinations.
  - *Tier-2 (Long-term Knowledge Base)*: `project_facts.json` for storing global architectural rules.
- **Dynamic Token Limiting**: Hard output token limits (1000 for Coder, 150 for Reviewer).

### 4. Output Delivery
- **Cross-lingual Communication (Language Gateway)**: A two-way language gateway. The user's request is translated into English (accelerates inference and saves tokens by 3-4 times), and the final response is translated back into the user's native language.
- **Output Formatting Pattern**: Hiding the agents' internal debates from the user. Only a clean, final response is outputted after task completion.

  ──────
  ## ⚙️ Key Mechanisms and Design Patterns

  The project uses classic engineering patterns:

  1. State Machine
  The `run_agent_loop` operation cycle is implemented as a state machine: `status: "in_progress" | "completed"` and `current_turn: "coder" | "reviewer"`. The state machine guarantees
  clear context transfer between agents without human intervention.
  2. Repository & Adapter Pattern
  The `SandboxStorage` class encapsulates all file system operations. Agents and functions do not touch files directly, but request or save state through
  a storage adapter.
  3. Function Calling & Orchestrator Tracking (Agent Tools)
  Agents are "hardwired" with the tools `read_project_facts`, `update_project_fact`, `create_file`, `read_file`, and `list_directory`.
  The Supersession mechanism (Rule Replacement) is used to update facts.
  Each tool call is recorded in the `tool_executions` array of the state machine, forming a verifiable, deterministic log (Orchestrator Tracking). Agents receive this log in context and are obligated to rely only on the actual tool execution results, not their own guesses.
  4. Chain of Responsibility
  The compatibility facade (`safe_llm_completion`) routes eligible requests through configured adapters and returns the existing LiteLLM response shape. Provider failures are surfaced with secret-safe errors after bounded retries and explicit fallback checks.
  ──────
  ## 🧪 Testing and Monitoring (LLMOps)
  The project includes built-in mechanisms for evaluating agent quality and monitoring costs:

  1. Historical Hardened Evals Pipeline (superseded)
  The `evals_pipeline.py` script uses a dataset of attack vectors (`tests/adversarial_prompts.json`).
  👉 **A detailed description of all attacks, testing scenarios (including Tool Abuse, Memory Poisoning, and Shift-Left Validation), and behavior rules are described in a special guideline: [TESTS.md](TESTS.md).**

  • Historical behavior: the pipeline inferred security from model/guardrail prose and produced a percentage score. Phase 20 replaced this with named behavioral assertions over observable side effects; missing, skipped, or failing assertions now fail the pipeline.

  2. Historical Regulator description (superseded)
  Instead of raw logs, `telemetry_aggregator.py` creates a bounded report with aggregate counters and payload-free evidence records.
  • **Regulator Agent**: Every 10 telemetry records, the Regulator may propose a change when actionable evidence exists. A deterministic gate checks the exact JSON schema, confidence bounds, affected rule and evidence references. Accepted output is queued only for human review.
  • **Fact and policy safety**: The Regulator receives no tools and has no path that writes `project_facts.json`, `roles.json`, `capabilities.json` or policy modules. Normal deterministic approval and implementation workflows remain mandatory.

  3. Drift Metrics (Drift Control)
  After running automatic tests, the pipeline analyzes the average number of agent debate rounds. If solving a single task takes on average more than 3 iterations, the system issues a WARNING about context drift, signaling the need for prompt calibration or facts review.

  4. Prompt Engineering & Few-Shot Prompting (Prompt Tuning)
  The system allows flexible management of review quality through the configuration of system instructions (`roles.json`). The use of strict acceptance criteria (Guardrails) and the introduction of `Few-Shot` examples (providing specific code templates with errors and the expected reaction) forms a powerful semantic anchor for the LLM's Attention mechanism. This forces the language model to more accurately identify architectural violations and push the agents' Accuracy to high values.
  • **UI State Observation Guardrails**: The role is hardcoded with strict Anti-patterns for Jetpack Compose: the use of infinite `while(true)` loops inside `LaunchedEffect` is prohibited. The Reviewer is trained to uncompromisingly reject such solutions and demand safe methods for subscribing to state.
  • **Predictive Architect Diagnostics**: The Analyst agent is endowed with an auto-recovery mechanism. If the base models start outputting empty responses or the session loops, the Analyst intercepts the log and forcibly generates a strict instruction on the output format (for example, demanding to wrap the code in markdown), saving the pipeline from crashing.
  ──────
  ## 🛠 Tech Stack and Tooling

  The project is written in Python with a minimal number of external dependencies to maintain lightweightness:

  • LiteLLM (`litellm`): The main driver of the system. A powerful library that unifies API calls to 100+ providers (Google, OpenAI, Anthropic) under a single input-
  output standard (OpenAI API Format).
  • Ollama: A local engine for running open-source LLMs on the user's desktop. Acts as a guarantor of autonomy and free inference if the clouds stop responding.
    - **AMD GPU Support**: To activate hardware acceleration on AMD (Radeon) graphics cards, before starting the pipeline, you must start the Ollama server in a separate terminal window with a special environment variable:
      ```cmd
      set HSA_OVERRIDE_GFX_VERSION=10.3.0
      ollama serve
      ```
  • Python Standard Library (`json`, `os`, `shutil`, `datetime`): Used for managing the file system, facts lifetime metrics, and state serialization.
  • Logging (`logging`): Targeted logger configuration blocks garbage output from libraries, leaving the console clean and transparent for observing the agents' thoughts.

  ### Summary

  Mini Agent Sandbox is a fault-tolerant, confidential, and autonomous system. It is able to survive under the harsh limits of a free API, shifting tasks
  from the cloud to a local graphics card, while teaching AI agents to negotiate with each other to write perfect code.

  ──────
  ## 🚀 Release 1.0 (Production-Ready)

  The system has successfully passed all tests and is locked as the stable Version 1.0:
  - **Self-Healing & RAG**: ✅ Agents autonomously extract architectural rules and apply them. The Analyst successfully intercepts infinite loops.
  - **Mini Presidio Guardrail**: ✅ Absolute interception of AWS keys, API tokens, and PII through a 3-layer system (Regex + Contextual Validation).
  - **Historical Evals claim (superseded)**: the former 100% score described prose-based scenarios and is not accepted as security verification after Phase 20.
  - **Regulator**: advisory only. Every ten telemetry records it may emit an evidence-bound proposal for human review; it has no tools and cannot rewrite facts or policy.
  - **Two-Way Obfuscation (Deobfuscation Vault)**: ✅ Successfully implemented the tokenization and interception model. Sensitive data is substituted with tokens (`__VAULT_SECRET_...__`), and transparently deobfuscated via `Runner-Interceptor` before actual code execution. The key map is stored outside the working directory and is encrypted.

  ──────
  ## 🔮 Future Roadmap

  - **Offline Model Mode (Phase 7 — in progress)**: Continue verifying bounded task operation with the already-configured Ollama/local RAG path when external network access is unavailable. End-to-end task continuation is not yet validated.

  ## Current project-aware status (2026-09-15)

  The historical overview above is not the operational safety contract. The current implementation has a registered Android/Kotlin project with an isolated snapshot, canonical project-scoped Chroma RAG, evidence-gated knowledge cards, and a FastAPI knowledge editor.

  - RAG uses the existing ChromaDB + LiteLLM + local Ollama `nomic-embed-text` pipeline only; it is retrieval, not model training.
  - Project code and knowledge are isolated under `data/projects/<project-id>/`; no cross-project retrieval is performed.
  - Planning retrieval order is snapshot → project code → verified project knowledge → verified global knowledge. Context includes source, module, scope and trust labels.
  - Gradle, generated code and untrusted project code run only in the locked-down Docker/Linux executor. The original project is copied to a temporary workspace for validation and is never mounted directly.
  - FastAPI authorizes work but receives neither a Docker socket nor Docker CLI.
  - Knowledge cards require evidence before verification; draft/proposed cards are never indexed, and deprecated/archived cards are removed from RAG.

  - Phase 6 adds `model_router.py` contracts and a LiteLLM adapter for completion and embedding calls. Optional per-role `routing` settings in `roles.json` can set `task_class`, `privacy_policy`, `cloud_eligible`, `quality`, context and budget bounds, fallback models, and retry limits. Existing role files remain valid and default to local-only routing.
  - `rag_service.py` and `ingest_knowledge.py` keep embeddings on `ollama/nomic-embed-text`; no vector database, model, dimensions, or collection layout changed. API keys remain in external runtime configuration. Telemetry stores bounded operational metadata only.

  Phase 6 implementation status: router and compatibility tests pass; the full suite passed 90 tests with 2 expected skips in an isolated copy, including the Docker Kotlin/Android executor integrations. The connected Android project remains read-only.

  ## Phase 7 — in progress: offline local-model mode

  Ollama completion routing and local `ollama/nomic-embed-text` embeddings are already present. Set `MINI_AGENT_OFFLINE=1` before starting the application to restrict all completion calls to Ollama, including roles otherwise eligible for cloud routing. An unavailable local model fails clearly without a cloud request; invalid setting values fail startup. Resume an interrupted CLI task with `python runner.py --resume <user_id>`; only valid saved `in_progress` tasks are accepted, and the cumulative step limit is retained. The opt-in integration test exercises a persisted work-ledger task, local Chroma embeddings/retrieval and real Ollama completion; all recorded calls use Ollama. No ChromaDB migration or embedding re-indexing is planned. Model output cannot substitute for reviewer approval, explicit user approval, or isolated Docker validation. Model files, caches, credentials and telemetry stay outside the repository and executor image.

  Run the local integration check with `MINI_AGENT_RUN_OFFLINE_INTEGRATION=1` set before `python -m unittest tests.integration.local_ollama.test_offline_integration -v`. The check uses the installed `qwen2.5:7b` and `nomic-embed-text:latest` models; normal unit tests do not contact a model service.

  Phase 3 is complete. Phase 4's patch proposal gate is implemented: candidates are unified diffs scoped to approved PlanStep files, reviewer decisions are recorded separately, and a user must approve the exact diff hash before validation can be recorded. Phase 5 is implemented by the separate trusted `validation_worker.py`: it rechecks both approvals, applies diffs only in a temporary copy, and runs up to three allowlisted Gradle profiles through the isolated Docker executor. FastAPI does not import the worker or access Docker. Each report records bounded redacted output, stage status, image identity/digest when available, and enforced Docker settings. The connected source is never mounted or modified by validation.

  **Phase 7 workspace verification (2026-09-15):** The real Ollama/temporary-Chroma check passed 1/1; focused tests passed 31/31; the full suite passed 98 tests with 3 expected skips. Offline Ollama tool schemas are preserved and Markdown-only workspace validation is supported. The dedicated CLI resume created `data/phase7_offline_test/architecture_summary.md` but remained `in_progress` after the generic Android review loop created unrelated Kotlin artifacts. This file is isolated test output and is not linked to the repository docs. Phase 7 remains in progress.

The run also recorded an `update_project_fact` tool call that wrote a canonical fact into the synthetic user's `project_facts.json`. That generated file was removed from the isolated test workspace; blocking unsupported model-driven knowledge promotion remains an open safety item.

## Phase 7 latest status (2026-09-15)

The full suite passed **103 tests with 3 skips**; the opt-in real Ollama/temporary-Chroma integration passed **1/1**. Offline router failure policy and documentation-mode safety are covered by tests. The latest isolated `phase7_offline_test` resume used Ollama only and created its Markdown summary, but remains `in_progress` because repeated model tool calls triggered the circuit breaker. Phase 7 is still in progress pending a single-write documentation-loop fix and a successful real resume/review. See `CODEX_HANDOVER.md` for the continuation prompt and strict scope.


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

## Current Phase 8 status (2026-09-16)

This section supersedes the older Phase 7 progress notes above for current
operational planning. Phase 7 is closed; its historical
`phase7_quality_final` run is immutable and must not be reset or resumed.

Phase 8 now provides a bounded read-only operations view at
`GET /projects/{project_id}/operations`, versioned default-deny project policy
storage with redacted audit metadata, and aggregate project metrics at
`GET /projects/{project_id}/metrics`. The API remains unable to start Docker or
execute generated code.

Validation profiles are default-deny. The separate trusted
`ValidationWorker` runs Docker validation only when every requested profile is
explicitly listed in that project's persisted `validation_profiles`; a missing
policy allows no profiles. It records a validation telemetry outcome only after
the report is saved.

Project telemetry is isolated per project and stores only event type, outcome,
provider, bounded token/cost counters, and a timestamp. Metrics expose
aggregates, not telemetry payloads. Prompts, source excerpts, RAG text, model
responses, validation stdout/stderr, and secrets are excluded by design.

`GET /projects/{project_id}/retention/preview` is an explicit metadata-only
preview for telemetry and policy-audit retention. It reports retention days and
total/expired event counts only; it accepts no filesystem paths, treats absent
stores as empty, and blocks malformed event data without modifying anything.
It does not inspect or remove knowledge, RAG data, work-ledger records,
snapshots, vault material, or source files.

Destructive telemetry/audit cleanup, auto-apply, a graphical UI, and destructive
knowledge deletion are deliberately not enabled. Each needs a separate safe
contract, review, and regression coverage before it can expand any authority.
The historical scope and remaining increments are consolidated in
`CODEX_HANDOVER.md` and `PROJECT_EVOLUTION_ROADMAP.md`; backup, export, and
knowledge-removal actions still require their separately approved procedures.
# Product direction — agentic code-generation tool

Mini Agent Sandbox is an agentic code-generation tool, not a policy or telemetry demonstration. Its useful path is: a real project profile supplies snapshot/RAG context; Coder proposes a bounded patch; Reviewer evaluates that proposal; a human approves its exact hash; and the trusted worker validates it only in a temporary Docker workspace. Policies, telemetry, the ledger and redaction make this workflow controllable and reproducible; they are not the product by themselves.

`gta-cheats--cc0fe5de` is the canonical real Android project profile. It represents `E:\\Android\\AndroidStudioProjects\\GtaCheatsApp-main`, a small multilingual GTA cheat-code application. Saved project-scoped retrieval evidence in `data/phase7_dispatch_guard/state.json` includes `app/src/main/java/com/gamescheatsapp/MainActivity.kt`, `settings.gradle.kts`, and `gradle.properties`. This proves real-project snapshot/RAG retrieval; it does not claim that Gradle ran against the connected source tree. Docker validation evidence remains fixture-only until a user-approved GTA proposal is validated against a fresh temporary copy.

Phase 8 now has a `--project-patch <project-id> <approved-step-id> <user-id>` runner mode and a non-interactive `--project-patch-task <project-id> <approved-step-id> <user-id> <task...>` variant for orchestration. Coder can submit only one unified diff through `propose_patch`; the existing ledger checks the approved step and workspace policy before persistence, and a positive structured Reviewer verdict records review only. The next proof is a bounded live GTA Cheats run through explicit user approval and temporary-copy Docker validation. This remains higher priority than new dashboards, auto-apply, destructive cleanup, or knowledge deletion.
## Phase 9 complete (2026-09-20)

Phase 8 closed with a read-only GTA project-RAG answer grounded in
`app/src/main/AndroidManifest.xml`: `tools:targetApi="31"`. Phase 9 completed
the project-RAG quality and grounded native Q&A work recorded in
`PHASE9_CONTINUATION_PROMPT.md`; it did not authorize Android-source edits,
codegen proposals, Docker, or Gradle.

Phase 9 uses a cascaded RAG contract: project snapshot/project-code evidence
first establishes GTA facts and source paths; the shared Compose/Kotlin/
architecture library is an optional, separately labelled technical reference
for explanation only. The two corpora must not be mixed into one unlabelled
ranking. Any future knowledge-card promotion requires evidence and explicit
human approval; LLM answers never automatically enter RAG.

The 2026-09-20 audit found 393 GTA project-code chunks but zero chunks in both
pre-existing global-library collections. The user authorized one bounded
ingestion of the three existing PDF books into the canonical global library;
the GTA corpus remains unchanged.

The canonical global library now contains 2,293 chunks. Phase 9 added a
stored-chunk lexical stage that returns `app/src/main/AndroidManifest.xml`
first for the observed `tools:targetApi` ranking miss, while keeping books in a
separate optional technical-reference stage. Real local Analyst -> Reviewer
answers grounded `tools:targetApi="31"` and the `.MainActivity`
`MAIN`/`LAUNCHER` declaration in that manifest. Focused Ruff and 4/4 focused
tests passed; no Docker, Gradle, or connected-source action occurred.

## Phase 10 complete (2026-09-20)

Phase 10 will add a deterministic, evidence-gated draft knowledge-card proposal
from grounded project Q&A. It will retain project source paths and hashes,
reject global-library evidence for GTA facts, and require the existing explicit
human verification before indexing. This is not model training and does not
authorize automatic promotion, live GTA knowledge changes, codegen, Docker, or
Gradle.

The completed bridge in `grounded_knowledge_proposal.py` validates same-project
source paths and snapshot hashes and creates only a draft. `project_qa.py`
returns structured evidence but cannot create or promote a card. Invalid
global/missing/stale/cross-project evidence fails closed; existing explicit
verification remains the only indexing path. Focused Ruff and 11 focused tests
passed without live GTA, Docker, Gradle, model-call, or training activity.

## Phase 11 complete (2026-09-20)

Phase 11 will make dependency manifests reproducible. It addresses the
observed gap between `requirements.txt` and direct runtime/PDF-ingestion
imports, while preserving a compatible runtime installation entry point. It is
documentation and manifest work only: package installation, upgrades, lockfile
resolution, and clean-environment installation checks require separate user
authorization.

Runtime, PDF-ingestion, and development dependencies now have distinct pinned
manifests, while `requirements.txt` remains the compatible default entry point.
Focused Ruff and 3/3 manifest tests passed. No package state changed; a
clean-environment installation remains separately authorized.

Fresh-clone acceptance completed on 2026-09-21 in an isolated `E:` clone at
`3f7027f`: Python 3.11.9 installed the default and optional-ingestion manifests
with Pip caching disabled. `pip check`, runtime imports, the full suite (166
tests; 17 expected skips), and the two ingestion tests passed. No RAG corpus,
Chroma persistent store, Ollama, PDF processing, or GTA source was used.

## Latest Phase 8 codegen status

The project-patch bridge accepts only bounded Coder proposals and recovers
recognized local-Qwen proposal envelopes through the same unified-diff,
approved-path, policy and ledger checks. Current GTA search candidates were
Reviewer-rejected; no Android source change, user SHA approval, Docker run or
temporary-copy validation has occurred. The next target is the observed local
provider stall before first response, not weaker policy or auto-apply.
