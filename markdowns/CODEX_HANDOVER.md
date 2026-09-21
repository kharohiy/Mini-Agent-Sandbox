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

## Актуальный статус — выполнение ограниченного контура 2026-09-16

- `phase7_quality_final` сохранён как неизменяемый неудачный исторический run:
  фактический `state.json` содержит `in_progress`, `agent_steps: 11`. Он не
  сбрасывался, не редактировался и не возобновлялся.
- `phase7_operational_preflight.ps1` теперь сам запускает Docker Desktop при
  недоступном daemon и проверяет `docker info`, native Ollama endpoint,
  `qwen2.5:14b`, `nomic-embed-text:latest` и отдельный FastAPI. Контур прошёл.
- Создана новая ограниченная задача `phase7_dispatch_guard`; она не использует
  storage `phase7_quality_final`. Исправлен только documentation `create_file`:
  невалидная структура отклоняется до записи и не списывает отдельный шаг.
  Точечный dispatch-test: **1/1 passed**.
- Один opt-in Ollama/Chroma integration: **1/1 passed** (21.618 s). Один
  `MINI_AGENT_OFFLINE=1` documentation resume новой задачи: **completed**,
  `agent_steps: 2`, Reviewer: `APPROVE`.
- Финальный полный suite: **126 tests, OK (skipped=3), exit code 0**. После
  прогона `ollama ps` пуст и Docker-контейнеров нет.

**Phase 7 закрыта 2026-09-16. Основание: успешные preflight, один opt-in
Ollama/Chroma run и один новый real documentation resume. Исторический
`phase7_quality_final` остаётся сохранённым неуспешным run и не является
результатом закрытия.**

Новый session должен начинаться с [`README.md`](README.md) и
[`mini_agent_sandbox_analysis.md`](../mini_agent_sandbox_analysis.md): первый
содержит актуальный operational contour и карту модулей, второй — утверждённый
архитектурный backlog.

---

## Исторические статусы и handover-записи

## Актуальный статус на конец сессии 2026-09-15

### Результат единственного resume — 2026-09-16

- Локальный Ollama endpoint восстановлен; opt-in Ollama/Chroma integration
  прошёл **1/1** с уже установленными моделями.
- Единственный разрешённый `MINI_AGENT_OFFLINE=1` resume
  `phase7_quality_final` завершился сохранённым отказом: Coder записал
  `# Overview` вместо обязательного `## Overview`. Gate остановил задачу до
  evidence/reviewer проверки. State: `in_progress`, `agent_steps=7`, без
  `documentation_review`.
- Не выполнять второй resume и не подгонять prompt. Phase 7 не закрыта;
  дефект зафиксирован для отдельного решения после этой попытки.

### Обновление выполнения закреплённого плана — 2026-09-16

- Для Phase 7 добавлен минимальный детерминированный evidence gate: для каждого
  retrieval-запроса с прямым совпадением нужен один соответствующий реальный
  RAG source path; совпадение в пути имеет приоритет над случайным упоминанием
  в тексте. Это не восстанавливает сложное сопоставление цитат с кодом.
- Новый отрицательный regression test и целевой набор прошли: **52/52**.
  Полный `python -m unittest discover -v`: **126 запущено, 111 прошли,
  15 пропущены**; Docker-тесты ожидаемо пропущены, потому что Docker Desktop
  не был запущен оператором.
- Opt-in `test_offline_integration` не дошёл до agent loop: Chroma embedding
  через `ollama/nomic-embed-text` завершился `APIConnectionError`.
  Последующий `ollama ps` не вернул нормальный список: Ollama не смог создать
  log в `%LOCALAPPDATA%\\Ollama` из-за `Access is denied` и истёк тайм-аут
  ожидания сервера. Это зафиксированный инфраструктурный отказ Phase 7.
- `phase7_quality_final` не возобновлялась, её state и `agent_steps=6` не
  менялись; модели не были успешно загружены. Не исправлять этот отказ
  изменениями prompt, RAG или задач. Следующее действие только после внешнего
  восстановления локального Ollama service и успешного `ollama ps`.

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

### Минимальный контекст и порядок продолжения

Прочитать `documentation_policy.py`, документационные ветки `runner.py`,
`project_retrieval.py`, `test_documentation_policy.py`,
`test_documentation_transition.py`, `test_documentation_retrieval.py` и
`data/phase7_quality_final/state.json`. Не загружать весь репозиторий или Android-исходники.

1. Просмотреть сохранённую упрощённую реализацию; не переписывать её заново.
   Сохранены: остановка Coder после записи, read-only Reviewer, реальный файл
   в контексте, повторная проверка файла и SHA-256 перед завершением,
   одинаковый проектный контекст для автора и Reviewer, сохранение in_progress
   при лимитах/ошибках. Точные фрагменты берутся из существующего Chroma по
   пути, найденному в snapshot; оригинальный source tree не читается.
2. Целевые тесты уже зелёные; повторять их после изменения кода, а не по кругу.
   Команда: `python -m unittest test_documentation_policy test_documentation_transition test_documentation_mode test_documentation_retrieval test_model_router test_arbitrator test_project_retrieval test_work_ledger -v`.
3. Если продолжать реальный тест, использовать существующий
   `phase7_quality_final` с `MINI_AGENT_OFFLINE=1`. Проверить сначала его лимиты
   и последний отказ; не заменять state и не сбрасывать agent_steps.
   Не возобновлять `user_123`, не создавать бесконечную цепочку новых задач.
   Один ограниченный запуск, затем явный результат: completed либо конкретный отказ.
4. Только после фиксации финального кода — один полный прогон
   `python -m unittest discover -v` с доступом к Docker daemon, затем отдельно
   opt-in `MINI_AGENT_RUN_OFFLINE_INTEGRATION=1` / `test_offline_integration`.
   Docker использует только копии fixtures с прежними ограничениями.
5. Обновить эти четыре документа фактическими результатами. Phase 7 закрывать
   только после подтверждённого реального прохода, локального routing/RAG и
   безопасного отказа. Не выдавать модельное ревью документа за одобрение патча
   или верификацию знания.

### Где лежат результаты этой работы

Проект: `C:\Users\AlSaintUk\Desktop\Mini Agent Sandbox`.
Вспомогательные копии, baseline и логи находятся в отдельной рабочей папке:
`C:\Users\AlSaintUk\Documents\Codex\2026-09-14\kharohiy-mini-agent-sandbox-1-llm\work\phase7\quality_gate`.
Рабочий код на Desktop — актуальная реализация; baseline — только для сравнения.

- `focused-tests.log`: последний результат 51/51 после упрощения.
- `full-tests.log`: 125 / 122 passed / 3 skipped до упрощения.
- `offline-run-audit.json`: отрицательный прогон phase7_quality_test;
  process-local сетевой guard разрешал только loopback, записаны реальные
  Ollama completion/embedding вызовы. Это НЕ успешный acceptance-тест.
- `phase7_quality_final` был остановлен; его финальный audit может отсутствовать.
  Не трактовать отсутствие отчёта как успех и не запускать `verify_run.py`
  до фактического completed.
- Скрипты `prepare_run.py`, `offline_runner_check.py`, `verify_run.py` являются
  вспомогательными инструментами этого расследования, а не новым production API.
  Не запускать их автоматически. В `prepare_run.py` создание новой задачи
  намеренно запрещено, если её каталог уже существует.

Если снова запускались модели, в конце завершить свой Python-процесс,
выгрузить только использованные тестом модели командой `ollama stop <model>`
и проверить `ollama ps`. Не оставлять GPU занятой после сообщения об остановке.

### Короткий prompt для следующей сессии

```text
Продолжи Phase 7 с верхнего актуального блока CODEX_HANDOVER.md.
Сначала просмотри сохранённый упрощённый код и состояние phase7_quality_final.
Не начинай заново, не возвращай сложную схему проверки цитат, не меняй модели
и не гоняй полные тесты после каждой правки промпта. Целевые 51/51 уже прошли;
полный прогон упрощённой версии и её успешный реальный resume ещё не доказаны.
Ограничь реальный эксперимент одним проходом, сохрани неуспех честно.
Не трогай user_123, прежние тестовые состояния, Android source, vault,
зависимости и Docker-конфигурацию. Не запускай вложенный codex exec и не коммить.
После остановки обязательно выгрузи свои модели и проверь ollama ps.
```

---

## История предыдущих сессий — нижние статусы могут быть устаревшими

﻿# Codex Handover вЂ” Mini Agent Sandbox

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

### Phase 0 вЂ” Docker validation

`Dockerfile.executor`, `executor-entrypoint.sh`, `sandbox_executor.py`, fixtures and tests exist. Runtime uses:

```sh
HOME=/tmp/home
GRADLE_USER_HOME=/tmp/gradle
ANDROID_USER_HOME=/tmp/android
```

Real Docker positive fixture and negative compile/failing-test/missing-wrapper/source-immutability cases passed.

### Phase 1 вЂ” read-only project snapshot

`project_registry.py`, `project_manager.py`, `project_indexer.py`, and `project_search.py` provide SHA-256 incremental isolated snapshots.

### Phase 2 вЂ” RAG and knowledge

- `project_rag_ingestion.py` produces deterministic chunks from snapshot-listed files.
- Unchanged SHA-256 documents skip re-embedding; changed files replace only their chunks; removed sources are de-indexed.
- Real result: 156 documents and 393 project-code chunks; repeat ingestion skipped all 156 without duplicates.
- A real local Chroma/Ollama query returned project navigation source context.
- `knowledge_store.py` provides global/project cards, evidence, versions/audit; cards start draft.
- `knowledge_rag_sync.py` indexes only verified cards and de-indexes deprecated/archived ones.
- `api.py` exposes knowledge list/search/create/evidence/verify/retire/history.
- `project_retrieval.py` has fixed order: snapshot в†’ project code в†’ verified project knowledge в†’ verified global knowledge. Each hit has trust, scope, source and module labels.

### Phase 3 вЂ” persistent work ledger

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

## Phase 4 вЂ” safe patch proposal and review workflow

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
Продолжи Phase 7 в репозитории C:\Users\AlSaintUk\Desktop\Mini Agent Sandbox.
Сначала прочитай CODEX_HANDOVER.md и указанные ниже файлы. Выполни задачу
отдельно под user_id phase7_offline_test; не запускай и не изменяй user_123.

Цель: проверить реальный offline-проход runner.py --resume с локальным Ollama и
RAG зарегистрированного проекта gta-cheats--cc0fe5de. Создай только отдельное
синтетическое состояние задачи со статусом in_progress, привяжи его к этому
project_id, попроси агента подготовить краткий Markdown-обзор архитектуры в
его изолированной sandbox workspace. Перед запуском установи
MINI_AGENT_OFFLINE=1. Подтверди, что retrieval scoped к project_id, все
completion вызовы идут только в Ollama, а файлы появились только в
data/phase7_offline_test/. Исходник
E:\Android\AndroidStudioProjects\GtaCheatsApp-main не открывай, не монтируй и
не изменяй.

Отдельно проверь отсутствие Ollama через failing fake adapter, не останавливая
Ollama Desktop: вызов должен завершиться безопасной ошибкой, состояние задачи
остаться in_progress, облачных вызовов быть не должно. Уже существующий тест
test_offline_integration.py запускался с настоящими qwen2.5:7b и
nomic-embed-text:latest; не подменяй его fake-ответами и повтори его командой из
handoff. Fake используй только для детерминированной проверки failure policy.

Docker Desktop уже запущен. Docker CLI доступен, но доступ к named pipe может
требовать разрешённого контекста. Для Ollama/RAG шага Docker не нужен. Если
запускаешь executor validation, используй только Docker worker, временную
копию и сохранённые network=none/resource limits. Не запускай Gradle на
Windows.

После выполнения запусти целевые и полные тесты, обнови CODEX_HANDOVER.md,
NEXT_STEPS_PLAN.md, PROJECT_EVOLUTION_ROADMAP.md и README.md фактическими
результатами. Отметь Phase 7 завершённой только если реальный resume-проход,
project-scoped RAG, Ollama-only routing и безопасный отказ доказаны. Не
добавляй зависимости и не делай git commit.
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
passed 25/25.

The GTA task `task_3cf6b6422d16432da3133cdd9d016d2a` is bound only to
`feature/gta_v/src/main/java/com/gamescheats/feature/gta_v/screen/GtaVCheatCodesScreen.kt`.
Three candidates were Reviewer-rejected; none has approval or validation. The
next blocker is a local `qwen2.5:14b` completion stall before first response.
Diagnose that boundary without fake proposals, direct Android writes, apply, or
pre-approval validation.
