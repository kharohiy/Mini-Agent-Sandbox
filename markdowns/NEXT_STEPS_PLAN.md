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

See `PHASE12_PREPARATION.md` and `PHASE12_CONTINUATION_PROMPT.md`.

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

## Актуальный статус — выполнение ограниченного контура 2026-09-16

- `phase7_quality_final` сохранён без изменений как исторический неуспешный
  run; фактический state: `in_progress`, `agent_steps: 11`.
- `phase7_operational_preflight.ps1` автоматически запускает Docker Desktop,
  затем подтверждает Docker, native Ollama, обе требуемые модели и отдельный
  FastAPI. Все проверки контура прошли.
- Новая ограниченная задача `phase7_dispatch_guard` создана в существующем
  storage. Один fix dispatch-path предотвращает списание отдельного шага за
  отклонённый до записи невалидный documentation `create_file`; точечный test
  прошёл **1/1**.
- Один opt-in Ollama/Chroma run прошёл **1/1**; один real offline resume новой
  задачи завершён: `completed`, `agent_steps: 2`, Reviewer `APPROVE`.
- Финальный полный suite подтверждён audit-логом: **126 tests, OK
  (skipped=3), exit code 0**; post-run `ollama ps` пуст, Docker-контейнеров нет.

**Phase 7 закрыта 2026-09-16. Не возобновлять и не нормализовать
`phase7_quality_final`; он остаётся историческим отказом.**

Для следующей фазы использовать [`README.md`](README.md) как карту текущего
контура и [`mini_agent_sandbox_analysis.md`](../mini_agent_sandbox_analysis.md)
как список архитектурных приоритетов. Preflight сам запускает Docker Desktop;
ручной запуск Docker оператором не требуется.

---

## Исторические планы и статусы

## Актуальный статус на конец сессии 2026-09-15

### Результат единственного resume — 2026-09-16

- Локальный Ollama endpoint восстановлен; opt-in Ollama/Chroma integration:
  **1/1 passed**.
- Единственный `MINI_AGENT_OFFLINE=1` resume `phase7_quality_final` сохранил
  отказ до evidence/reviewer проверки: Coder записал `# Overview` вместо
  обязательного `## Overview`. State: `in_progress`, `agent_steps=7`, без
  `documentation_review`.
- Второй resume и prompt-подгонка запрещены. Дефект зафиксирован для
  отдельного решения; Phase 7 не закрыта.

### Обновление выполнения закреплённого плана — 2026-09-16

- В `documentation_policy.py` добавлен минимальный детерминированный evidence
  gate: на каждый retrieval-запрос с прямым совпадением требуется один
  соответствующий реальный source path из RAG. Сложная проверка цитат с
  фрагментами кода не возвращалась.
- Новый regression test и целевой набор: **52/52 passed**. Полный suite:
  **126 run, 111 passed, 15 skipped**; Docker-тесты ожидаемо пропущены,
  потому что Docker Desktop не был запущен оператором.
- Opt-in Ollama/Chroma integration остановился до agent loop:
  `ollama/nomic-embed-text` вернул `APIConnectionError`. Команда `ollama ps`
  затем не смогла создать log в `%LOCALAPPDATA%\\Ollama` (`Access is denied`)
  и завершилась по тайм-ауту сервера.
- Это инфраструктурный отказ, а не дефект документационного gate. Не запускать
  `phase7_quality_final`, не сбрасывать state/`agent_steps=6` и не менять
  prompts/RAG. Продолжать только после внешнего восстановления Ollama и
  успешного `ollama ps`.

## Закреплённый порядок выполнения Phase 7

Этот порядок обязателен до закрытия Phase 7. Не расширять его исправлениями,
не относящимися к offline-документационному quality gate: такие находки только
записывать отдельно с точным симптомом и тестом.

1. Сохранить текущие состояния и проверить границы задачи без запуска моделей.
   Не изменять `user_123`, Android-исходники, legacy vault, зависимости,
   Docker-конфигурацию или `roles.json`.
2. Уточнить детерминированный контракт качества документации: он должен
   требовать реальные RAG-источники, покрывающие entry/navigation, состав
   модулей и поддержанные data-flow. Не возвращать удалённую сложную схему
   сопоставления цитат с фрагментами кода.
3. Сначала добавить регрессионные тесты на отклонение: недостаточные или
   самоссылочные источники, DTO-описание вместо архитектуры и ложное
   `APPROVE` Reviewer. Добавить положительный компактный случай.
4. Внести минимальные изменения только в `documentation_policy.py`,
   документационные ветки `runner.py` и, если потребуется для точного поиска,
   `project_retrieval.py`; затем прогнать целевой набор тестов.
5. После зелёных целевых тестов один раз выполнить полный `unittest discover`
   и отдельно opt-in offline integration.
6. Выполнить ровно один resume сохранённой `phase7_quality_final` c
   `MINI_AGENT_OFFLINE=1`, не сбрасывая state или `agent_steps`. Зафиксировать
   только `completed` либо конкретный отказ; не подбирать промпты по кругу.
7. После работы выгрузить использованные модели, проверить `ollama ps` и
   обновить актуальные статусы в четырёх документах только результатами,
   которые действительно были получены.

Критерий закрытия: quality gate детерминированно отклоняет некачественный
документ; целевые, полный и opt-in тесты зелёные; единственный реальный
offline-resume подтверждён либо его конкретный отказ сохранён.

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

# План следующих шагов после P0 hardening

Этот план продолжает анализ `mini_agent_sandbox_analysis.md` и учитывает уже выполненные изменения:

- workspace path isolation и валидация `user_id`;
- tenant-scoped Vault (`data/<user_id>/.vault`);
- policy layer для `project_facts`;
- structured Reviewer verdict;
- обязательный Reviewer после Arbitrator;
- language-aware validation routing.

Цель следующей итерации — превратить оставшиеся архитектурные ограничения в проверяемые security boundaries, не смешивая их с prompt engineering, RAG и telemetry.

## Этап 0 — Зафиксировать security contract

**Зачем:** до контейнеризации нужно определить, что именно разрешено запускать и где проходит граница доверия.

1. Описать threat model: LLM и сгенерированный код считаются недоверенными; policy engine и runner — доверенными.
2. Завести capability manifest для tools: filesystem, network, secrets, subprocess, build/test.
3. Определить для каждой capability owner, scope, default (`deny`) и требуемое human approval.
4. Разделить два режима:
   - `plan_only` — агент читает/пишет workspace, но не запускает код;
   - `validated_execution` — build/test выполняется только в изолированной среде.

**Критерий готовности:** documented capability matrix и тест, доказывающий, что неизвестный tool/block запуска отклоняется по умолчанию.

## Этап 1 — Реальная execution sandbox

**Зачем:** текущая workspace isolation не защищает хост, если в будущем будет запускаться сгенерированный код или Gradle build.

1. Выбрать execution backend (решение владельца проекта):
   - Docker/Podman с Linux-изоляцией — рекомендуемый вариант для CI и Linux;
   - отдельная VM/Windows Sandbox — вариант для локальной Windows-разработки;
   - отдельный restricted subprocess — только временная мера, не эквивалент container/VM.
2. Создать `SandboxExecutor` adapter; `runner.py` не должен напрямую вызывать build tools.
3. В backend включить deny-by-default:
   - network disabled;
   - read-only base image и writable только user workspace;
   - CPU, memory, process и wall-clock limits;
   - non-root user;
   - без host mounts, кроме явно выделенной копии workspace.
4. Вынести результаты build/test в структурированный report: exit code, timeout, resource limit, stdout/stderr с masking секретов.
5. Добавить integration tests: network denied, host path unavailable, timeout, memory/process limit, workspace write allowed.

**Критерий готовности:** Kotlin/Python validation выполняется только через `SandboxExecutor`; тесты подтверждают отсутствие доступа к сети и host filesystem.

**Выбранное решение:** Docker — execution backend; FastAPI — API-слой проекта. Docker sandbox запускается из `C:\Users\AlSaintUk\Desktop\Mini Agent Sandbox`, но получает только выделенную копию user workspace, а не доступ ко всему host project directory.

## Этап 2 — Довести Kotlin/Android validation до реального integration flow

**Зачем:** сейчас route Kotlin → Gradle корректный, но проверен mock-ом, а не Android fixture.

1. Добавить минимальный Kotlin/Android fixture с Gradle wrapper в `tests/fixtures/`.
2. Запускать в sandbox последовательность `gradlew --offline lint test`.
3. Добавить optional checks `detekt` и `ktlintCheck` только при явно объявленных Gradle tasks; при их отсутствии report должен сообщать `not configured`, а не симулировать прохождение.
4. Добавить отрицательные fixtures: ошибка компиляции, failing unit test, Android lint violation, отсутствующий wrapper.
5. Определить правила для mixed-language workspace: отдельный manifest с validator chains либо reject, как сейчас.

**Критерий готовности:** реальный fixture проходит lint/test в изолированной среде; каждая отрицательная fixture блокирует переход к Reviewer.

## Этап 3 — Закрыть symlink/TOCTOU coverage

**Зачем:** код блокирует symlink traversal, но Windows не позволил создать symlink в текущем тестовом окружении.

1. Добавить Linux CI job, где symlink разрешены без special privilege.
2. Выполнить tests для:
   - symlink внутри workspace, ведущего наружу;
   - symlink на файл вне workspace;
   - symlink на каталог внутри workspace;
   - замены обычного файла на symlink между validation и open (TOCTOU).
3. Для записи использовать платформенный no-follow primitive, где он доступен, либо создавать файлы через trusted executor в isolated filesystem.
4. На Windows документировать prerequisite для локального symlink теста (Developer Mode или необходимая privilege) и оставлять skip только с явной причиной.

**Критерий готовности:** обязательный CI test доказывает, что выход через symlink невозможен; локальный skip не маскирует отсутствие CI coverage.

## Этап 4 — Миграция и удаление legacy vault

**Зачем:** корневые `.vault` и `.vault_key` больше не используются runtime, но могут содержать старые секреты.

1. Добавить read-only `vault_migration --dry-run`, который проверяет legacy файлы `C:\Users\AlSaintUk\Desktop\Mini Agent Sandbox\.vault` и `.vault_key` и показывает только metadata: наличие файлов и число tokens. Значения секретов никогда не печатать.
2. Добавить opt-in миграцию: пользователь явно задаёт target `user_id`; tool создаёт encrypted backup и атомарно пишет новый tenant vault в `data/<user_id>/.vault`.
3. Проверить корректность расшифровки до переключения и сохранить audit record без plaintext.
4. Удалять legacy файлы только отдельной подтверждённой командой после успешной миграции и backup verification.
5. Добавить тесты: successful migration, wrong key, corrupt vault, rollback, no cross-tenant token leakage.

**Критерий готовности:** legacy secrets либо безопасно мигрированы в один выбранный tenant vault, либо остаются нетронутыми; автоматического удаления нет.

**Пояснение:** `user_id` — это безопасный технический идентификатор tenant/workspace (например, `local_owner`), а не путь Windows и не имя папки проекта. Старые `.vault` и `.vault_key` появились до tenant-isolation и поэтому не содержат информации о владельце. Для single-user локального проекта их можно мигрировать в один явно выбранный namespace, например `local_owner`. Удаление legacy файлов — только после вашей отдельной команды и успешной проверки backup.

## Этап 5 — Усилить behavioral security evals

**Зачем:** текстовая реакция LLM не доказывает отсутствие side effect.

1. Для каждого adversarial case проверять state mutation, tool execution, facts mutation, vault access и filesystem diff.
2. Добавить eval, в котором agent пытается изменить security fact; ожидание — deterministic policy deny и отсутствие записи.
3. Добавить eval, в котором Reviewer возвращает `DO NOT APPROVE`; ожидание — workflow не завершён.
4. Добавить eval, в котором Arbitrator вынес решение; ожидание — финальный Reviewer всё равно вызывается.
5. Добавить failure reports с machine-readable reason code и evidence links.

**Критерий готовности:** security score основан на observable side effects, а не только на содержимом ответов модели.

## Порядок выполнения

```text
Этап 0 → выбор backend → Этап 1 → Этап 2 и 3 параллельно → Этап 4 → Этап 5
```

RAG, telemetry и Regulator не следует расширять до завершения Этапов 1–5: они не компенсируют отсутствие execution boundary и behavioral assertions.
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
