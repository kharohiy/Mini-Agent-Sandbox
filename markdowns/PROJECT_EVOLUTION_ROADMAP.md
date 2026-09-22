## Актуальный статус — выполнение ограниченного контура 2026-09-16

- Historical `phase7_quality_final` сохранён без изменений (`in_progress`,
  фактические `agent_steps: 11`); новый run не использовал его storage.
- Автоматический preflight поднял Docker Desktop и подтвердил Docker, native
  Ollama endpoint, `qwen2.5:14b`, `nomic-embed-text:latest` и FastAPI.
- В новой `phase7_dispatch_guard` исправлен один orchestration defect:
  невалидный documentation `create_file` отклоняется до записи без отдельного
  agent step. Единственный точечный test: **1/1 passed**.
- Единственный opt-in Ollama/Chroma run: **1/1 passed**. Единственный real
  documentation resume новой задачи: **completed**, 2 шага, Reviewer `APPROVE`.
- Финальный полный suite: **126 tests, OK (skipped=3), exit code 0**; модели
  выгружены, Docker-контейнеров после прогона нет.

**Phase 7 закрыта 2026-09-16; исторический `phase7_quality_final` сохранён
как неуспешная запись и не использовался для закрытия.**

### Операционный контур и дальнейшая база изменений

`phase7_operational_preflight.ps1` автоматически поднимает Docker Desktop при
недоступном daemon, после чего проверяет Docker, native Ollama, требуемые
локальные модели и отдельный loopback FastAPI. Он не запускает модель, не
меняет Docker executor и не создаёт второй model storage.

Следующие изменения проекта должны начинаться с
[`mini_agent_sandbox_analysis.md`](../mini_agent_sandbox_analysis.md): его P0
границы для filesystem/vault isolation, deterministic policy, Kotlin/Android
validation и корректной state machine остаются приоритетнее новых agent-фич.

---

## Исторические статусы и roadmap-записи

## Актуальный статус на конец сессии 2026-09-15

### Результат единственного resume — 2026-09-16

- Локальный Ollama endpoint восстановлен; opt-in Ollama/Chroma integration
  прошёл **1/1**.
- Единственный offline resume `phase7_quality_final` остановлен gate до
  evidence/reviewer проверки: Coder записал `# Overview` вместо обязательного
  `## Overview`. State: `in_progress`, `agent_steps=7`, без review verdict.
- Второй resume и prompt-подгонка не выполнялись. Phase 7 не закрыта.

### Обновление выполнения закреплённого плана — 2026-09-16

- Детерминированный evidence gate для Phase 7 теперь требует для каждого
  retrieval-запроса с прямым совпадением один реальный source path из RAG;
  сложное сопоставление цитат с фрагментами кода не возвращалось.
- Новый regression test и целевой набор прошли **52/52**. Полный suite:
  **126 run, 111 passed, 15 skipped**; Docker-тесты ожидаемо пропущены,
  потому что Docker Desktop не был запущен оператором.
- Opt-in Ollama/Chroma integration не дошёл до agent loop: embedding через
  `ollama/nomic-embed-text` завершился `APIConnectionError`. `ollama ps` не
  смог создать log в `%LOCALAPPDATA%\\Ollama` (`Access is denied`) и истёк по
  тайм-ауту ожидания сервера.
- `phase7_quality_final` сохранён без resume, со state `in_progress` и
  `agent_steps=6`. До внешнего восстановления локального Ollama service не
  запускать модели, не менять prompts/RAG и не сбрасывать задачу.

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

# Project Evolution Roadmap

## Vision

Turn Mini Agent Sandbox into a safe, project-aware mobile-development assistant.
It should understand a connected Android/Kotlin project, propose and implement
small reviewed changes, validate them only in a Docker/Linux sandbox, preserve
useful project knowledge, and keep operating in a reduced offline mode when
cloud-model quotas or network access are unavailable.

## Architectural Boundary

```text
Android/Kotlin repository
        |
        v
Project index + RAG snapshot <----> verified knowledge base
        |                                  ^
        v                                  |
Task / plan orchestrator -> model router -> cloud or local LLMs
        |
        v
analysis -> implementation -> review -> Docker validation
        |
        v
validated patch + validation report -> optional knowledge card
```

The FastAPI service authorizes work but never executes it. A separate trusted
worker invokes Docker. Docker runs compilation and tests in Linux with no
network and constrained resources. The source project is copied to a temporary
workspace before validation; it is never mounted directly into the executor.

## Knowledge Rule

RAG supplies current context; it does not train a model. Knowledge cards are
added only after evidence exists: a reviewed patch, a successful validation
report, or an explicitly approved architectural decision. Each card must record
the problem, decision, evidence, affected modules, and creation date.

## Execution Plan

## Current implementation status (2026-09-15)

- **Phase 0 complete:** Kotlin/Android Gradle validation passes only in the locked-down Docker executor; compile errors, failing tests and a missing wrapper are rejected.
- **Phase 1 complete:** the read-only incremental snapshot of `GtaCheatsApp-main` is registered as `gta-cheats--cc0fe5de` (7 modules, 156 files, 274 symbols).
- **Phase 2 complete:** the canonical RAG pipeline is the existing ChromaDB + LiteLLM + local Ollama `nomic-embed-text` service. It uses physical per-project Chroma paths, separate code and verified-knowledge collections, deterministic incremental ingestion, and evidence-gated knowledge synchronization. A real project query returned indexed source context.

Project state is isolated outside project source:

```text
data/projects/<project-id>/snapshot/
data/projects/<project-id>/rag/chroma_db/
data/projects/<project-id>/knowledge/
data/projects/<project-id>/runs/
data/projects/<project-id>/exports/
```

Never create a parallel vector-store. Snapshot is regenerable inventory; ChromaDB is the sole retrieval store; knowledge cards remain evidence-gated records.

### Phase 2 completion record (2026-09-15)

- The registered project has 156 snapshot documents and 393 project-code chunks. Repeat ingestion skips unchanged documents and creates no duplicates.
- Ingestion uses deterministic IDs; changed sources replace only their chunks and sources removed from the snapshot are de-indexed.
- Only evidence-backed verified cards enter RAG. Deprecated and archived cards are de-indexed.
- The FastAPI knowledge editor supports list/search, draft creation, append-only evidence, verification, retirement, versions and audit history.
- Selected-project planning retrieval is ordered: snapshot, project code, verified project knowledge, then verified global knowledge. It attaches trust, scope, source and module labels.

**Phase 3 complete:** the project-scoped SQLite work ledger and API persist `Task`, `Plan`, `PlanStep`, `Patch`, `Review`, `ValidationReport` and `Run`. Plans require inspectable files, risks, validation and rollback before approval; validation requires an approved patch review. A task can be reopened from disk with its plan, patch, review, validation evidence and runs intact.

**Phase 4 proposal/review gate complete:** candidates are stored as validated text unified diffs; all diff paths must match the approved `PlanStep` and project source policy. Reviewer decisions persist independently from user approval. The user must approve the exact diff SHA-256 before the ledger permits validation. The API does not apply diffs or invoke Docker.

**Phase 5 complete (2026-09-15):** the trusted validation worker applies hash-approved diffs only to temporary copies, supports up to three sequential allowlisted Gradle profiles, and stores bounded redacted stage evidence including executor image identity and Docker settings. The connected source remains unmodified and is never mounted.

**Phase 6 complete (2026-09-15):** `model_router.py` defines provider-neutral completion and embedding contracts, deterministic task/quality preferences, context and budget gates, default-deny cloud privacy policy, request quotas, expiring provider health, bounded retry, and explicit fallback. The LiteLLM adapter retains Ollama and supported Gemini/OpenAI model IDs without adding SDK dependencies. `safe_llm_completion` remains the compatibility facade; per-role routing options are optional, so existing `roles.json` files continue to load. Both embedding call sites use the fixed local `ollama/nomic-embed-text` contract. Telemetry records only bounded operational fields. Fake-based router and compatibility tests passed; full suite: 90 tests passed, 2 expected skips. Docker Kotlin/Android executor integrations passed against the copied fixture. No connected Android source was read for model context, mounted or modified. The next phase is Phase 7: offline local-model mode.

### Phase 0 — Finish the execution foundation

**Goal:** a real Kotlin/Android fixture passes in the locked-down executor.

Tasks:

1. Give AAPT2 only the writable temporary locations it demonstrably needs
   (`/tmp`, runtime home/cache and, if needed, constrained shared memory).
2. Keep root read-only, network disabled, non-root execution, capabilities
   dropped, no-new-privileges, resource limits, and the temporary workspace
   copy.
3. Capture the exact AAPT2 failure with Gradle `--stacktrace --info` if the
   first adjustment does not pass.
4. Run successful, compilation-error, failing-test, missing-wrapper and
   workspace-immutability integration tests.

Deliverables: green Docker Kotlin test suite, documented executor contract.

Exit criteria: `./gradlew --offline test` succeeds only in the Docker executor;
all negative fixtures are rejected.

### Phase 1 — Project inventory and indexing

**Goal:** create a deterministic, refreshable representation of an Android
project without sending every source file to a model.

Tasks:

1. Define a project manifest schema: Gradle modules, SDK versions, plugins,
   dependencies, source roots, manifests, tests and generated-file exclusions.
2. Build a read-only indexer for Kotlin, Java, Gradle, XML and Markdown.
3. Extract symbols and lightweight relationships: package, class, function,
   imports, test-to-production references and Gradle module dependencies.
4. Store a content hash per file and re-index only changed files.
5. Add fixture repositories and tests for multi-module Android projects.

Deliverables: `ProjectSnapshot` JSON/SQLite data model and indexer CLI/API.

Exit criteria: one command produces the same snapshot for unchanged input and
incrementally updates it after a source change.

### Phase 2 — Local RAG and knowledge base

**Goal:** retrieve relevant project context and verified historical decisions.

Tasks:

1. Select local storage: SQLite for metadata plus a local vector index.
2. Chunk source by semantic boundaries where possible; retain file path, symbol,
   module, hash and line-range metadata.
3. Index architecture docs, ADRs, Gradle configuration, selected source and
   validated test reports separately.
4. Implement hybrid retrieval: module/path filters, keyword search and semantic
   similarity.
5. Implement immutable evidence-linked `KnowledgeCard` records and a review
   gate before insertion.

Deliverables: snapshot search API, knowledge-card schema, retrieval tests.

Exit criteria: a query about a module returns relevant sources and decisions
with paths and evidence, without exposing unrelated project files.

### Phase 3 — Work-item and planning model

**Goal:** make agent work explicit, resumable and auditable.

Tasks:

1. Define `Task`, `Plan`, `PlanStep`, `Patch`, `Review`, `ValidationReport` and
   `Run` schemas.
2. Introduce statuses: proposed, approved, running, blocked, validated, rejected
   and superseded.
3. Require each plan step to identify files, risks, expected validation and
   rollback approach.
4. Persist state locally so a task survives model quota failures or restarts.
5. Build an API endpoint to inspect a plan before code changes are allowed.

Deliverables: persistent work ledger and plan/review API.

Exit criteria: a task can be stopped and resumed with its plan, evidence and
current validation state intact.

### Phase 4 — Safe patch generation and review workflow

**Goal:** turn a plan into minimal, reviewable changes.

Tasks:

1. Give the implementation agent only the task, retrieved context and approved
   plan step.
2. Require unified diffs and prohibit direct writes outside the connected repo.
3. Add a reviewer agent/checklist for correctness, Android conventions,
   security, scope and test coverage.
4. Apply patches only after explicit user approval, or use a separately enabled
   low-risk auto-apply policy.
5. Record the patch hash and reviewer decision in the work ledger.

Deliverables: patch proposal/review pipeline and adversarial scope tests.

Exit criteria: every applied change has a linked plan step, diff and review
record; rejected patches never reach validation as accepted work.

### Phase 5 — Docker validation pipeline (implemented 2026-09-15)

**Goal:** validate each accepted candidate patch only in isolated Linux.

Tasks:

1. Add command allowlists for Gradle tasks such as `test`, `lint`, and targeted
   module tests.
2. Copy the repository to a temporary workspace, apply the candidate patch there
   and invoke the executor.
3. Capture bounded stdout/stderr, exit status, duration, image digest and
   security settings in `ValidationReport`.
4. Support staged validation: fast unit test, relevant module test, then broader
   project checks.
5. Reject reports when Docker is unavailable rather than falling back to host
   execution.

Implementation note: `validation_worker.py` exposes only symbolic `test`,
`lint`, and snapshot-registered `module_test` profiles. One to three unique
profiles can run in order against a fresh temporary copy; any failure stops
the sequence. The worker rechecks reviewer and hash-bound user approval before
copying and before each stage. FastAPI does not load this trusted Docker worker.

Deliverables: validation worker, report schema and Docker integration suite.

Exit criteria: validation reports prove container image, command, resource
limits and result; Windows-host Gradle execution is impossible by design.

### Phase 6 — Model router and cloud providers

**Goal:** use cloud models efficiently without coupling the system to one
provider.

Tasks:

1. Define provider-neutral requests for planning, coding, review and embeddings.
2. Add adapters for approved providers such as OpenAI and Gemini; keep API keys
   outside the repository and Docker image.
3. Route by task class, estimated context size, privacy policy, quality need,
   budget and remaining quota.
4. Add retries, provider health state and explicit fallback rules.
5. Log only operational metadata; never persist provider secrets or unnecessary
   source excerpts.

Deliverables: model-router interface, provider adapters and deterministic router
tests using fakes.

Exit criteria: the same plan can proceed through a secondary provider after a
primary-provider quota/error response.

### Phase 7 — Offline local-model mode

**Status (2026-09-15):** implementation underway; the real local-model check
covers persisted task data, local Chroma retrieval and Ollama completion, while
the runner's resume path is tested separately with a fake completion adapter.
A single real-model run through the full CLI orchestration remains unverified.
The first change adds process-start
`MINI_AGENT_OFFLINE=1`, which restricts completion routing to Ollama even when
cloud is otherwise eligible. `runner.py --resume <user_id>` restores valid
interrupted state, and an opt-in integration test has exercised the persisted
work ledger, local Chroma embeddings/retrieval and real Ollama completion with
only Ollama calls recorded. Phase 6 already provides the LiteLLM routing boundary,
local Ollama completion configuration, and local `ollama/nomic-embed-text`
embeddings. Phase 7 should complete and prove disconnected operation using
these existing components before considering a new runtime or model.

**Goal:** retain useful, bounded operation without internet access, with clear
capability limits and no hidden cloud fallback.

Tasks:

1. Audit the existing Ollama completion and embedding routes, health handling,
   model availability, and failure behavior. Keep Ollama and the current local
   embedding model unless these checks reveal a concrete blocker.
2. Define and document capability levels for project search/RAG, summaries,
   continuing persisted plans, small patch proposals, review, and validation.
   Local model output must never count as reviewer/user approval or validation.
3. Ensure missing/unhealthy local models fail clearly and never trigger cloud
   fallback when the request is local-only or cloud is disallowed. Preserve the
   router's default-deny privacy and budget rules.
4. Exercise resume from persisted task/plan state with local RAG and local
   completion while external network access is blocked. Use fakes for
   deterministic policy tests and a separately marked local integration check
   for an installed Ollama model; tests must not require cloud credentials.
5. Keep model weights, Ollama caches, secrets and telemetry outside the repo
   and executor image. Keep validation's Docker `network=none` boundary and the
   FastAPI/worker separation unchanged.

Reading scope for implementation: `CODEX_HANDOVER.md`, this Phase 7 section,
`README.md`, then `model_router.py`, `runner.py`, `roles.json`,
`rag_service.py`, `ingest_knowledge.py`, `test_model_router.py`, and relevant
runner/ledger tests. Read dependency and Docker files only to verify local model
assets and credentials are excluded from images; expand the scope only when
call-site/configuration search finds another affected file.

Deliverables: verified local-runtime readiness and no-cloud fallback behavior,
a documented capability matrix, and offline policy/integration tests.

Exit criteria: with external network access unavailable, an interrupted task
can resume from persisted local state, retrieve project-scoped local RAG
context, and complete only the documented local capabilities. Tests prove no
cloud request or credential is needed, local-model failure is reported without
disallowed fallback, and no validation or approval state is inferred from model
output. The local integration test uses real installed models and records only
Ollama adapter calls; keep it opt-in for environments without Ollama.

### Phase 8 — User experience, governance and operational hardening

**Goal:** make autonomous work understandable and controllable.

**Current checkpoint (2026-09-16):** the read-only operations and metrics API,
default-deny policy storage and audit metadata, validation-profile enforcement,
backup/export runbook, and payload-free project telemetry are implemented.
Runner project flows now record model and retrieval outcomes without prompts,
queries, retrieved context, model output, source excerpts, validation output,
or secrets. Workspace paths are enforced at candidate-patch persistence with a
default-deny per-project allowlist. Project-scoped model providers are filtered
by policy before adapter dispatch, including fallbacks; the same path enforces
per-request and cumulative task token budgets before dispatch. Auto-apply,
graphical UI, and destructive knowledge deletion remain separate unimplemented
contracts.

The retention increment provides only a project-scoped, metadata-only preview
for telemetry and policy-audit events. Missing stores are empty and malformed
events block the preview. No cleanup is implemented; knowledge, RAG, ledger,
snapshots, vaults, and source trees are outside its scope.

Tasks:

1. Provide a dashboard/API view for current task, plan, retrieved context,
   proposed diff, validation output and knowledge-card candidates.
2. Add per-project policies: allowed directories, validation commands, model
   providers, budgets and auto-apply level.
3. Add audit logging, redaction and retention policies.
4. Add metrics for task success, validation failure categories, retrieval quality
   and token/cost usage.
5. Write backup/export procedures for the work ledger and knowledge base.

Deliverables: operational UI/API, policy file, audit model and runbook.

Exit criteria: a developer can understand why a patch was proposed, approve or
reject it, reproduce its validation and remove/export project knowledge.

## Recommended Order

Execute phases strictly in this order: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8.
Phases 6 and 7 may share interfaces, but local-model installation should wait
until project context, planning and validation have stable contracts.

## Non-negotiable Safety Constraints

- Never run Gradle, generated code or untrusted project code directly on Windows.
- Do not mount the original project directory into the executor.
- Do not give the FastAPI container a Docker socket or Docker CLI.
- No network during validation runtime; fetch dependencies only while building a
  controlled executor image.
- Never auto-promote model output to knowledge without evidence and review.
- Preserve `.vault` and `.vault_key`; do not place secrets in snapshots, prompts,
  images, logs or knowledge cards.

**Workspace verification (2026-09-15):** Real Ollama/temporary-Chroma check passed 1/1; focused tests passed 31/31; full suite passed 98 tests with 3 expected skips. The offline adapter now preserves Ollama tool schemas, and Markdown-only output is handled without code execution. The actual `phase7_offline_test` resume used project ID `gta-cheats--cc0fe5de` and created a summary in its isolated workspace, but the generic Android agent review cycle did not complete and created unrelated `.kt` artifacts there. CLI end-to-end completion remains unverified; Phase 7 stays in progress.

The run also recorded an `update_project_fact` tool call that wrote a canonical fact into the synthetic user's `project_facts.json`. That generated file was removed from the isolated test workspace; blocking unsupported model-driven knowledge promotion remains an open safety item.

## Phase 7 latest verification and remaining gate (2026-09-15)

The full suite passes **103 tests with 3 skips** and the opt-in real Ollama/temporary-Chroma integration passes **1/1**. The latest `phase7_offline_test` run is not complete: project-scoped state is `in_progress` for `gta-cheats--cc0fe5de`; local telemetry shows Ollama only, and one Markdown summary was written, but three repeated `create_file` calls triggered the circuit breaker. The next CLI task is to enforce a single successful documentation write followed by read-only review, add a regression test, and rerun this saved task offline. Phase 7 remains in progress until the real resume completes and all exit criteria pass. Detailed scope and paste-ready prompt are in the latest section of `CODEX_HANDOVER.md`.


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
# Product orientation

This roadmap develops Mini Agent Sandbox as an agentic code-generation tool for real projects. Governance work is valuable only insofar as it makes the core workflow reliable: project-scoped retrieval, bounded patch proposal, review, explicit approval, and isolated validation. GTA Cheats (`gta-cheats--cc0fe5de`) is the canonical live Android profile. Its saved retrieval evidence includes `MainActivity.kt`, `settings.gradle.kts`, and `gradle.properties`; that is not a claim of a connected-source Gradle run.
## Phase 9 — Project-RAG quality and grounded native Q&A

**Status:** completed on 2026-09-20 after Phase 8 closure.

Phase 9 improves source-aware ranking and evidence choice for the existing
read-only local Analyst → Reviewer Q&A path. Its acceptance result is a small,
meaningful set of natural project answers that name supporting source paths and
do not claim facts absent from them. It does not edit the connected Android
source, create patches, or run Docker or Gradle. See
`PHASE9_CONTINUATION_PROMPT.md`.

The Phase 9 retrieval architecture is cascaded: project snapshot/project-code
evidence is selected first and is the sole proof for GTA-project facts; the
shared Compose/Kotlin/architecture library is a separately labelled optional
technical-reference stage for explanations. The stages retain distinct Chroma
paths, quotas, and citations and are never mixed into an unlabelled ranking.
The global-library ingestion/retrieval path must be audited and made canonical
without rebuilding corpora. Future approved knowledge cards remain a separate,
evidence-gated feature; model answers never auto-promote into RAG.

Audit result (2026-09-20): both pre-existing global-library collections had
zero chunks, while the GTA project-code collection had 393. The user authorized
one bounded ingestion of the three existing PDF books into the canonical global
library only; GTA RAG remains untouched.

Completion record: the canonical global library contains 2,293 book chunks;
GTA project-code remains 393 chunks. A minimal stored-chunk lexical stage
brings `app/src/main/AndroidManifest.xml` first for the observed
`tools:targetApi` ranking miss. The optional global-library stage remains
technical-reference-only. Two local Analyst -> Reviewer answers were grounded
in that manifest (`tools:targetApi="31"` and the `.MainActivity`
`MAIN`/`LAUNCHER` declaration). Focused Ruff and 4/4 focused tests passed.

## Phase 8 live-codegen gate

The project-patch bridge persists only bounded, policy-checked proposals and
can recover constrained local-model envelopes without extra authority. Current
GTA candidates are rejected and have no user approval or validation. The next
gate is reliable local-provider completion for a grounded proposal; it is not
dashboard, auto-apply, destructive cleanup, or knowledge deletion work.

## Phase 10 — Evidence-gated knowledge promotion

**Status:** completed on 2026-09-20.

Phase 10 adds only a deterministic draft-proposal bridge from a grounded
project Q&A result to the existing project knowledge-card store. A proposal
must retain same-project `project-code` source paths and snapshot/source hashes.
Shared books are technical-reference-only and cannot prove a project fact. The
bridge cannot verify or index a card: existing explicit human verification is
the sole promotion path. The phase uses temporary fixtures and does not create
or change live GTA knowledge, source, snapshot, or RAG data.

Completion record: `grounded_knowledge_proposal.py` validates same-project
`project-code` paths and hashes against the stored snapshot, then creates only
a draft card. Q&A now exposes the structured evidence required by that bridge.
Global-library, missing, stale, and cross-project evidence are rejected; the
existing verified-card path remains the only indexing path. Focused Ruff and 11
focused tests passed. No live GTA data, Docker, Gradle, model call, or training
operation occurred.

## Phase 13 — Deterministic context accounting

**Status:** completed on 2026-09-21.

Historical analysis item 13 remains open: both the router fallback and runner
metrics calculate context through `chars / 4`. Phase 13 first audits locally
installed counting capabilities and all consumers of this value. It may unify
the counter only when model mapping and message framing are reproducible; the
result must state whether it is exact or a conservative bound.

No tokenizer package, asset download, model invocation, dependency-manifest
change, or routing/prompt/budget-policy change is implied. A missing proven
counter for the local Qwen model blocks implementation rather than permitting a
guessed exact result. RAG, knowledge, session, vault, GTA, Docker, Gradle, and
proposal/validation paths remain out of scope.

Completion record: official Qwen assets on `E:` are revision/hash verified and
produced the same 26-token count as one real Ollama request. Phase 13.1 then
proved the installed Ollama 0.21.0 tool template against fixed local fixtures:
declared schema 135, assistant tool call 52, and tool response 76. Shared
accounting is exact only for those measured forms; unmeasured schemas/messages
fall back explicitly. Focused tests passed 33/33; the full deterministic suite
passed 178/178 with 15 expected skips; focused Ruff and `git diff --check`
passed.

Historical blocker record: the installed LiteLLM `token_counter` is locally stable on a
fixed fixture but does not provide Qwen evidence. Its source maps the Ollama
Qwen identifier to `gpt-3.5-turbo` and falls back to OpenAI `cl100k_base` with
generic message framing. It cannot replace the estimate. Continuing requires
an approved official-Qwen-tokenizer dependency plus clean-install acceptance,
an opt-in documented Ollama tokenization integration, or a decision to retain
the estimate.

## Phase 12 — Deterministic session lifecycle

**Status:** completed on 2026-09-21.

The historical analysis's item 12 found that persistent state was bypassed by
the primary loop. Phase 7 subsequently implemented a fail-closed `--resume`
path for structurally valid interrupted state, so Phase 12 does not re-solve
that completed part. It closes the remaining lifecycle ambiguity: new session,
resume session, and reset session must have explicit deterministic semantics.

The phase may replace the current ambiguous clear helper only after a written
transition contract and focused temporary-fixture tests exist. Reset is a
session-state operation only: it may not purge user data or alter project
facts, verified knowledge, RAG collections, snapshots, ledgers, or vaults.
Malformed or incompatible historic state must fail closed, not be silently
repaired. LLM summarisation, conversation ingestion, and all RAG/model/
provider/codegen/validation/Docker/Gradle/dependency work are excluded.

Completion record: `SandboxStorage.reset_session_state()` removes only a
selected user's `state.json`, rejects state-file symlinks, and leaves an absent
user directory absent. `--reset` is explicit; `--clear` is a deprecated
compatibility alias. `_new_session_state()` makes a clean new-session envelope
explicit and existing resume validation remains fail-closed. Temporary-fixture
lifecycle tests passed 3/3 and existing resume validation passed 1/1. No live
state, RAG, GTA, model, Docker, Gradle, or package state changed.

## Phase 11 — Reproducible dependency manifests

**Status:** completed on 2026-09-20.

The architecture analysis identifies an incomplete dependency declaration:
current direct runtime imports include packages absent from `requirements.txt`,
and PDF ingestion has a separate partial manifest. Phase 11 will audit direct
imports and installed versions, define runtime/ingestion/development manifests,
preserve a compatible runtime entry point, and add focused manifest tests. It
does not install or resolve packages; a clean-environment installation is a
separately authorized external action.

Completion record: manifests now separate direct runtime, PDF-ingestion, and
development tooling dependencies while retaining `requirements.txt` as a
compatible default entry point. Versions match the observed working environment.
Focused Ruff and 3/3 manifest tests passed. No package, model, RAG, Android,
Docker, or Gradle state changed; clean-environment installation remains a
separate authorized action.

Fresh-clone acceptance (2026-09-21): completed in an isolated `E:` clone at
`3f7027f`. Python 3.11.9 installed the default and optional-ingestion manifests
with Pip caching disabled. `pip check`, runtime imports, the full suite (166
tests; 17 expected skips), and the two ingestion tests passed. No RAG corpus,
Chroma persistent store, Ollama, PDF processing, or GTA source was used.
## Phase 14 — Explicit project-document ingestion and long-term RAG boundaries

**Status:** completed on 2026-09-21.

The historical analysis found a legacy user vector collection that is not fed
by a clear main-loop ingestion contract. The solution is not to merge it with
the post-Phase-9 cascade. Phase 14 will define an explicit, project-bound,
idempotent supplemental-document pipeline and a separate `project-document`
retrieval scope. Project-code remains the evidence source for project facts;
verified cards remain human-approved knowledge; global books remain optional
technical reference.

The phase excludes corpus rebuilds, legacy migration/deletion, conversation or
model-output ingestion, automatic knowledge promotion/training, and changes to
GTA source, models, policies, Docker, Gradle, validation or approval. See
`PHASE14_PREPARATION.md` for blockers and acceptance evidence.

Completion record: explicit request-body text/Markdown ingestion is bounded,
confirmed, checksum-backed and project-bound; its separate document collection
and metadata-only manifest cannot contaminate project-code or knowledge.
Focused tests passed 26/26; the full suite passed 185/185 with 19 expected
skips. A real local Ollama/Chroma temporary-fixture run retrieved only its own
`project-document` hit and was deleted afterward. No live corpus changed.

## Phase 14.1 — Test-suite structure and project-RAG separation

**Status:** completed on 2026-09-21; awaiting commit and push.

All 38 Python test modules were Git-renamed from the repository root into the
`tests/` package. `tests/sandbox/` holds Mini Agent Sandbox unit/contract tests;
`tests/project_rag/` holds generic registered-project RAG contracts; and
`tests/integration/` holds bounded Docker/local-Ollama checks. The only Android
fixture remains synthetic under `tests/fixtures/kotlin-android`; no GTA source
or generated RAG/runtime data belongs in Git.

The supported deterministic command is
`python -m unittest discover -s tests -t . -v`. It passed 181 tests with 19
expected skips, and `python -m ruff check tests` passed. This phase changes no
production behaviour and does not activate Docker or Ollama integration.

## Phase 15 — Structured secret/PII detection and prompt-injection separation

**Status:** completed locally on 2026-09-22; awaiting commit and push.

The historical analysis correctly identifies that the current DataGuardrail is
a five-rule regex/context masker, not comprehensive secret classification and
not prompt-injection protection. Phase 15 introduces a deterministic,
standard-library structured finding layer: bounded provider-specific detectors,
credential-context checks and entropy as corroborating signal. The public
masking/vault contract remains compatible.

Prompt injection is a distinct threat class. Existing tag-only handling will
be placed behind a separately named compatibility boundary and will not be
represented as complete protection. External structured-scanner adoption is a
later explicit dependency decision. No model/evals, RAG, GTA, Docker, Gradle,
vault-path or secret-resolution authority changes are authorised.

Completion record: `secret_scanner.py` supplies plaintext-free structured
findings, provider-first overlap handling, existing and bounded new provider
rules, generic credential detection and context-gated Shannon entropy.
`prompt_injection.py` holds the legacy tag-only compatibility boundary. Focused
guardrail/vault tests passed 10/10; the full deterministic suite passed 188
tests with 19 expected skips. No external scanner dependency, model/evals,
RAG/GTA, Docker, Gradle or live vault data was used.

Post-phase live evidence: real Ollama/Chroma component integration passed 1/1.
An actual offline runner loop in a disposable `E:` copy masked its synthetic
GitHub-shaped token before state persistence but remained `in_progress` after
three turns and ten tool executions. The process and entire copy were removed.
The deterministic Phase 15 contract remains complete; full model-driven agent
loop acceptance is blocked by this observed nondeterminism and must not be
claimed.

Correct GTA baseline validation after Phase 15 found a separate existing-style
acceptance issue: the real local `tools:targetApi="31"` Analyst→Reviewer answer
passed, but the `MainActivity` `MAIN`/`LAUNCHER` answer initially failed closed.
Chroma contains both facts in adjacent manifest chunks while retrieval supplied
only the `LAUNCHER` chunk. The bounded Phase 9 correction assembles only the
already selected literal source and preserves it through fusion. The same real
question now passes with `.MainActivity`; no source access or corpus
re-indexing occurred.
