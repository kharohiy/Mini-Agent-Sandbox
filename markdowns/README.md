## Актуальный статус — выполнение ограниченного контура 2026-09-16

- `phase7_quality_final` остаётся неизменяемым историческим неуспешным run
  (`in_progress`, фактические `agent_steps: 11`), без reset/edit/resume.
- Один автоматический preflight успешно поднял Docker Desktop и подтвердил
  Docker, native Ollama, `qwen2.5:14b`, `nomic-embed-text:latest` и FastAPI.
- Новая ограниченная `phase7_dispatch_guard` завершена после одного точечного
  dispatch fix и одного test (**1/1 passed**): невалидный documentation write
  отклоняется до записи без расхода отдельного шага.
- Один opt-in Ollama/Chroma run: **1/1 passed**. Один real offline
  documentation resume: **completed**, `agent_steps: 2`, Reviewer `APPROVE`.
- Финальный полный suite: **126 tests, OK (skipped=3), exit code 0**; после
  прогона нет загруженных Ollama-моделей или Docker-контейнеров.

**Phase 7 закрыта 2026-09-16. Исторический `phase7_quality_final` сохранён
без изменений как неуспешный run.**

### Операционный контур Phase 7

`phase7_operational_preflight.ps1` — единственный preflight-контур. Если
`docker info` недоступен, он сам находит Docker Desktop по установленному
Docker CLI, запускает Desktop скрыто и ждёт готовности daemon. Затем он
проверяет native Ollama endpoint и наличие `qwen2.5:14b` / `nomic-embed-text:latest`,
кратко поднимает FastAPI только на loopback и останавливает этот процесс.
Скрипт не загружает модели, не меняет Docker executor и не создаёт model storage.
Runner запускается отдельно как контролируемый процесс без внешнего короткого
timeout.

### Актуальная карта проекта

| Область | Основные компоненты |
|---|---|
| Orchestration | `runner.py`, `roles.json`, `model_router.py` |
| Documentation workflow | `documentation_policy.py`, `project_retrieval.py`, `test_documentation_*.py` |
| Project/RAG state | `project_registry.py`, `project_rag_ingestion.py`, `rag_service.py`, `data/projects/` |
| API and policy | `api.py`, `capability_policy.py`, `work_ledger.py` |
| Isolated validation | `validation_worker.py`, `sandbox_executor.py`, `Dockerfile.executor` |

Архитектурный backlog и P0/P1-границы описаны в
[`mini_agent_sandbox_analysis.md`](../mini_agent_sandbox_analysis.md). Этот файл
является исходной точкой для следующих доработок; Phase 7 не отменяет его
приоритеты по isolation, policy, vault, validation и state machine.

---

## Исторические статусы и справочные материалы

## Актуальный статус на конец сессии 2026-09-15

### Результат единственного resume — 2026-09-16

- Локальный Ollama endpoint восстановлен; opt-in Ollama/Chroma integration
  прошёл **1/1**.
- Единственный offline resume `phase7_quality_final` остановлен до
  evidence/reviewer проверки: Coder записал `# Overview` вместо обязательного
  `## Overview`. State: `in_progress`, `agent_steps=7`, без review verdict.
- Второй resume и prompt-подгонка не выполнялись. Phase 7 не закрыта.

### Обновление выполнения закреплённого плана — 2026-09-16

- Phase 7 получила минимальный детерминированный evidence gate: каждый
  retrieval-запрос с прямым совпадением требует один соответствующий реальный
  RAG source path. Сложная схема сопоставления цитат с фрагментами кода не
  возвращалась.
- Новый regression test и целевой набор прошли **52/52**. Полный suite:
  **126 run, 111 passed, 15 skipped**; Docker-тесты ожидаемо пропущены,
  потому что Docker Desktop не был запущен оператором.
- Opt-in Ollama/Chroma integration не дошёл до agent loop: embedding через
  `ollama/nomic-embed-text` завершился `APIConnectionError`. `ollama ps` затем
  завершился по тайм-ауту: Ollama не смог создать log в
  `%LOCALAPPDATA%\\Ollama` из-за `Access is denied`.
- `phase7_quality_final` не возобновлялась, сохранила `in_progress` и
  `agent_steps=6`. До внешнего восстановления Ollama service не запускать
  модели, не менять prompts/RAG и не сбрасывать задачу.

**Phase 7 не завершена. Работа и генерации остановлены по просьбе пользователя.**
Этот блок актуальнее всех прежних статусов и prompt ниже в документе.

- Сохранены проверки документационного артефакта в `documentation_policy.py`,
  изменения `runner.py` и точный поиск существующих Chroma-фрагментов в
  `project_retrieval.py`. Есть регрессионные тесты.
- Финальная версия упрощена: нужный Markdown, отсутствие лишних файлов,
  обязательные разделы и реальные пути из RAG; Reviewer возвращает
  `decision` и содержательный `reason`. Сложная схема сопоставления цитат
  документа с цитатами кода удалена. Ссылка в каждом разделе не обязательна.
  Наличие ссылок не является доказательством истинности всех утверждений.
- После упрощения целевые тесты: **51/51 прошли**. Последний полный прогон:
  **125 запущено, 122 прошли, 3 пропущены**, но он был ДО последнего упрощения.
  Полный прогон финального упрощённого кода и повтор opt-in Ollama/Chroma
  в этой части работы не выполнены. Старый результат opt-in 1/1 исторический.
- Успешный реальный offline-проход финальной упрощённой версии НЕ подтверждён.
  Модель `qwen2.5:14b` теряла ссылки; одна версия Reviewer ошибочно цитировала
  сам документ как доказательство. Ошибочные результаты не закрыли новые задачи.
- `phase7_offline_test`: `completed`, шаг 6, старый результат с известным
  дефектом качества; сохранить. `phase7_quality_test`: `in_progress`, шаг 11,
  лимит исчерпан; не сбрасывать. `phase7_quality_final`: `in_progress`, шаг 6,
  прерван; это последняя задача, которую можно рассмотреть для продолжения.
- Все три задачи связаны с `gta-cheats--cc0fe5de`. `user_123`, исходники
  Android, legacy vault, зависимости и Docker-конфигурация не изменялись.
  Коммитов не было. Смена на `qwen3.5:9b` только обсуждалась: НЕ выполнена;
  `roles.json` не менялся.
- После остановки отдельно выгружены `qwen2.5:14b` и `nomic-embed-text`.
  Повторная проверка: `ollama ps` пуст, Python и Ollama runner процессов нет;
  остались приложение Ollama и фоновый сервер. Показатель GPU не измерен:
  `nvidia-smi` отсутствует в PATH. Не запускать модели ради проверки статуса.

**Продолжение завтра:** сначала прочитать новый верхний блок `CODEX_HANDOVER.md`.
Не повторять длительные циклы подбора промптов, не менять модели автоматически,
не возвращать сложное «доказательство» качества текста. Проверить сохранённые
изменения, затем один ограниченный реальный проход; если он не проходит,
зафиксировать конкретный дефект и остановиться, не подгонять тест до успеха.

---

## Исторические материалы

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
- **Multimodal & MCP Isolation**: Protection against hidden commands in images (OCR Attack Protection) and strict directory isolation (Path Traversal Protection). A Human-in-the-loop (HITL) mechanism is built-in for critical tool calls. **Protection against The Agentic Shift vector:** Agents are hardware-restricted from direct access to the system shell at the tool level (tools like `execute_command` are absent). This completely eliminates the risk of Install-time execution (automatic downloading and installation of malicious dependencies), ensuring the system remains under the operator's full control.
- **Tool Circuit Breaker**: Protection against agent looping (Excessive Requests) with a hard limit (`MAX_TOOL_CALLS_PER_TURN = 5`). If exceeded, execution is interrupted (`SECURITY BLOCK`).

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

  1. Hardened Evals Pipeline (CI/CD Security Check)
  The `evals_pipeline.py` script uses a dataset of attack vectors (`tests/adversarial_prompts.json`).
  👉 **A detailed description of all attacks, testing scenarios (including Tool Abuse, Memory Poisoning, and Shift-Left Validation), and behavior rules are described in a special guideline: [TESTS.md](TESTS.md).**

  • The pipeline simulates the debate cycle and validates that DataGuardrail or the Reviewer successfully blocked the attack. It returns a strict Security Score (target value: 100%). If the Score is below 100%, the script issues `sys.exit(1)`, interrupting the hypothetical CI/CD process and protecting against the deployment of vulnerable roles.

  2. Telemetry Aggregation & System Regulator (Self-learning)
  Instead of raw logs, the `telemetry_aggregator.py` script is used, which mathematically compresses `telemetry.json` into `incident_summary.json`.
  • **Regulator Agent**: Every 10 sessions, a special super-agent "Regulator" is launched. It analyzes dry incident statistics (without access to raw user prompts, which completely eliminates *Data Poisoning*) and automatically generates improvements for `roles.json` or the facts database.
  • **Evolutionary Facts**: To avoid endless memory bloat (`project_facts.json`), the Regulator uses semantic consolidation — it merges similar facts and removes unused ones using the LRU algorithm, strictly maintaining the limit (no more than 15 facts).

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
  - **Hardened Evals**: ✅ Security Score 100% against injections (Indirect, Multimodal, Role-play, Exfiltration).
  - **Regulator Trigger**: ✅ Self-evolution is enabled: every 10 sessions, the system rewrites its facts and strengthens security based on telemetry metadata, protecting against Data Poisoning.
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

  Run the local integration check with `MINI_AGENT_RUN_OFFLINE_INTEGRATION=1` set before `python -m unittest test_offline_integration -v`. The check uses the installed `qwen2.5:7b` and `nomic-embed-text:latest` models; normal unit tests do not contact a model service.

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
See [PHASE8_PREPARATION.md](PHASE8_PREPARATION.md) for scope and remaining
increments, and [PHASE8_RUNBOOK.md](PHASE8_RUNBOOK.md) for backup, export, and
knowledge-removal procedures.
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

## Latest Phase 8 codegen status

The project-patch bridge accepts only bounded Coder proposals and recovers
recognized local-Qwen proposal envelopes through the same unified-diff,
approved-path, policy and ledger checks. Current GTA search candidates were
Reviewer-rejected; no Android source change, user SHA approval, Docker run or
temporary-copy validation has occurred. The next target is the observed local
provider stall before first response, not weaker policy or auto-apply.
