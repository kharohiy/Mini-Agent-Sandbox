# Анализ проекта kharohiy/Mini-Agent-Sandbox

## 1. Для чего проект

Задача проекта — дать LLM несколько специализированных ролей:

**Coder → Reviewer → при тупике Arbitrator → финальный ответ**

Дополнительно вокруг этого стоят:

- RAG с ChromaDB;
- долгосрочные project facts;
- DataGuardrail для маскировки секретов;
- Vault для обратной подстановки;
- fallback между LLM;
- telemetry;
- adversarial evals;
- файловые tools;
- статические проверки Ruff/Semgrep.

Но фактически это скорее **agent pipeline / coding assistant**, чем sandbox в смысле изоляции недоверенного процесса.

---

# 2. Как реально работает

Основной entrypoint — `runner.py`. Цикл примерно такой:

```text
User task
   ↓
language_gateway()
   ↓
DataGuardrail
   ↓
state
   ↓
RAG query
   ↓
Coder
   ↓
tools
   ↓
Ruff + Semgrep
   ↓
Reviewer
   ↓
APPROVE ───────────────→ finish
   │
   └── REJECTED
          ↓
        Coder
          ↓
       повтор
          ↓
      deadlock
          ↓
      Arbitrator
          ↓
       Coder
          ↓
      forced finish
```

Фактический state machine находится в `run_agent_loop()`.

Каждый ход:

1. выбирается роль;
2. строится RAG-контекст;
3. добавляются project facts;
4. передаётся накопленная history;
5. LLM может делать tool calls;
6. tool calls логируются;
7. после Coder запускаются Ruff/Semgrep;
8. Reviewer решает `APPROVE/REJECTED`;
9. после завершения формируется финальный ответ.

---

# 3. Архитектура по компонентам

| Компонент | Что делает | Реальное состояние |
|---|---|---|
| `runner.py` | главный orchestrator | центральный и перегруженный |
| `roles.json` | system prompts + модели | сильно завязан на Android/Kotlin |
| `SandboxStorage` | state/facts/files | простой файловый storage |
| `rag_service.py` | Chroma + embeddings + reranking | работает как отдельный слой |
| `data_guardrail.py` | поиск и tokenization секретов | эвристический regex-based guardrail |
| `vault_registry.py` | хранение secret mapping | глобальный vault на весь процесс |
| `evals_pipeline.py` | security/e2e evals | тестирует в основном ожидаемые сценарии |
| `telemetry_aggregator.py` | собирает метрики | очень простой агрегатор |
| `ingest_knowledge.py` | PDF → chunks → Chroma | отдельный ingestion pipeline |
| `repo_pattern.yaml` | Semgrep rule | фактически правило для Python |

---

# 4. Настройка

## LLM

По умолчанию роли используют:

`ollama/qwen2.5:14b`

Cloud fallback:

```text
gemini/gemini-2.5-flash
gemini/gemini-3.5-flash
gemini/gemini-3.0-flash
```

Local fallback:

```text
ollama/qwen2.5:14b
```

Роутер блокирует provider при 429/NotFound и переключается дальше.

## RAG

Embeddings жёстко привязаны к:

```text
ollama/nomic-embed-text
localhost:11434
```

Chroma хранится в:

```text
data/chroma_db
```

Есть:

- per-user collection;
- общая `android_architecture_library`;
- FlashRank reranking.

## Guardrail

Правила определяются в `data_guardrail.py`:

- API key;
- email;
- IPv4;
- AWS access key;
- AWS secret.

Найденное значение заменяется на:

```text
__VAULT_SECRET_...__
```

и mapping сохраняется в encrypted vault.

---

# 5. Самая важная проблема: это не настоящий sandbox

Проект **не создаёт отдельный OS/process/container/VM sandbox**. Он не использует Docker, seccomp, namespaces, VM или аналогичный execution isolation.

Он ограничивает агента в основном:

- набором function tools;
- workspace directory;
- path check;
- отсутствием `execute_command`.

Это означает:

> система не запускает сгенерированный код как изолированный процесс.

Она просто даёт агенту файловые операции в каталоге.

Поэтому это **agent workspace isolation**, а не полноценная execution isolation.

**Решение:** если нужен реальный sandbox — отдельный subprocess/container/VM с deny-by-default filesystem, network, CPU, memory и syscall policy.

---

# 6. Критическая ошибка: path traversal protection реализована неправильно

Проверка построена через строковый `startswith()` для абсолютного пути. Это небезопасный способ проверки границы каталога.

Например логически:

```text
/data/user
/data/user_evil
```

второй путь начинается с первого.

Кроме того, остаётся проблема symlink traversal.

Ещё одна проблема: `user_id` непосредственно вставляется в `os.path.join(self.base_dir, user_id)` без нормализации.

### Решение

Использовать:

```python
base = Path(user_dir).resolve()
target = (base / raw_path).resolve()
target.relative_to(base)
```

и отдельно:

- запретить symlink;
- валидировать `user_id`;
- использовать UUID вместо произвольного `user_id`.

**Приоритет: P0.**

---

# 7. Project facts можно отравить

Tool `update_project_fact` напрямую меняет facts storage без отдельного authorization/policy layer.

Получается архитектурно слабая схема:

```text
LLM → решает, можно ли изменить security policy
```

вместо:

```text
LLM
 ↓
Policy validator
 ↓
allow/deny
 ↓
write
```

Тесты в adversarial pipeline в основном проверяют, что модель сама не согласилась на плохой факт.

### Решение

Для `project_facts`:

- allow-list категорий;
- immutable security rules;
- versioning;
- human approval для security facts;
- запрет LLM менять security-critical facts напрямую.

**P0.**

---

# 8. Reviewer можно обойти логикой оркестратора

Завершение определяется условием вида:

```python
if "APPROVE" in answer.strip():
    state["status"] = "completed"
```

Это substring-check.

Текст вроде:

```text
DO NOT APPROVE
```

тоже содержит `APPROVE`.

### Решение

Использовать structured output:

```json
{"decision":"APPROVE"}
```

и проверять:

```python
decision == "APPROVE"
```

а не substring.

**P0.**

---

# 9. Arbitrator фактически отключает финальную проверку

После Arbitrator устанавливается флаг `force_complete_next`.

Затем следующий Coder может завершить workflow без Reviewer approval.

Получается:

```text
Coder
 → Reviewer
 → reject
 → Arbitrator
 → Coder
 → COMPLETE
```

а должно быть:

```text
Coder
 → Reviewer
 → reject
 → Arbitrator
 → Coder
 → Reviewer
 → approve
```

### Решение

Arbitrator должен выдавать architectural decision, но **не иметь права завершать pipeline**.

После Arbitrator обязателен:

```text
Coder → Validator → Reviewer
```

**P0.**

---

# 10. Shift-Left validation не соответствует реальному проекту

В `roles.json` Coder ориентирован на Android/Kotlin/Jetpack Compose.

Но validation использует:

```text
Ruff
Semgrep
```

и Semgrep rule настроен на Python.

То есть система просит писать **Kotlin**, а статически проверяет **Python**.

Это видно и в evals: тестовый код — Python.

### Решение

Либо:

**Вариант A:** сделать sandbox language-agnostic и определять validator по проекту.

**Вариант B:** если проект Android — использовать:

```text
Gradle
ktlint
detekt
Android Lint
unit tests
```

**P0.**

---

# 11. `requirements.txt` неполный

Основной requirements содержит только базовые зависимости типа `litellm`, `ruff`, `semgrep`, но runtime импортирует также RAG/crypto-зависимости.

Отдельно есть `requirements-ingest.txt`.

Получается, простой `pip install -r requirements.txt` не описывает полный runtime.

### Решение

Разделить зависимости на:

```text
requirements-runtime.txt
requirements-ingest.txt
requirements-dev.txt
```

или перейти на `pyproject.toml`.

**P1.**

---

# 12. Memory architecture заявлена лучше, чем реализована

В `save_state()` вызов memory summarization временно отключён.

Плюс `run_agent_loop()` создаёт новый state вместо нормального восстановления текущей persistent session.

Получается:

- persistent storage существует;
- но основной loop его фактически обходит;
- межсессионная working memory не является полноценной state machine.

### Решение

При старте:

```python
state = storage.get_current_state(user_id)
```

и отдельно сделать режимы:

```text
new session
resume session
reset session
```

**P1.**

---

# 13. Динамический context window почти декоративный

Есть грубая оценка вида `total_chars / 4` и большой `max_window_tokens`.

Это всего лишь approximation и не является реальным tokenizer-specific accounting.

### Решение

Использовать tokenizer конкретной модели либо детерминированно ограничивать сообщения по реальному token count.

**P2.**

---

# 14. RAG реализован частично

Есть две коллекции:

```text
user_<id>_local_nomic
android_architecture_library
```

Но основной agent loop не заполняет user collection через `add_document_chunks()`.

То есть:

- user vector collection существует;
- API загрузки есть;
- основной loop её фактически не использует для полноценного long-term user RAG.

Фактическая persistent memory в основном держится в `project_facts.json`.

### Решение

Чётко разделить:

```text
Facts → structured memory
Docs → vector RAG
Conversation → session memory
```

и сделать явную ingestion pipeline для каждого класса данных.

**P1.**

---

# 15. DataGuardrail довольно слабый

Guardrail — это regex + context check + tokenization, а не полноценная секретная/PII classification system.

Проблемы:

### Неполное покрытие секретов

Набор detector patterns ограничен известными форматами и не покрывает весь реальный secret space.

### Context check слабый

Проверки по substring/window дают ложные срабатывания и пропуски.

### HTML/XML sanitizer

Удаление отдельных `<image>`, `<script>`, `<system>` конструкций не является полноценной prompt-injection protection.

### Решение

Для secret detection:

```text
regex
+
entropy
+
provider-specific detectors
+
structured secret scanner
```

Prompt injection нужно рассматривать как отдельный класс угроз, а не как часть secret masking.

---

# 16. Vault архитектурно глобальный

`VaultRegistry` хранит vault/ключ в текущей рабочей директории.

Это единый vault для всех пользователей процесса.

В mapping нет полноценного tenant namespace.

### Решение

Использовать:

```text
data/<user_id>/vault.enc
data/<user_id>/vault.key
```

или единый KMS/secret store с user/session namespace.

**P0/P1.**

---

# 17. `resolve_secrets()` слишком мощный слой

Runner автоматически раскрывает tokenized secrets в tool arguments.

Это означает, что любой инструмент, которому попадёт аргумент, потенциально может получить plaintext secret.

Если позже появятся web/email/HTTP/MCP/shell tools, secret может автоматически уйти наружу.

### Решение

Не делать generic `resolve_every_string()`.

Использовать tool-specific secret capabilities: конкретный секрет может быть раскрыт только в разрешённом параметре конкретного trusted tool.

**P0.**

---

# 18. HITL заявлен, но фактически почти отсутствует

В runtime есть ветка для `send_email`, `access_calendar`, `web_search`, но этих tools нет в основном `AGENT_TOOLS`.

Следовательно, HITL-функциональность сейчас выглядит как мёртвый/незавершённый код.

### Решение

Либо реально добавить capability registry и tools, либо удалить неподдерживаемую ветку.

**P1.**

---

# 19. Circuit breaker работает, но не идеально

Есть лимит tool calls на ход и переход в Analyst при блокировке.

Но breaker в значительной мере остаётся workflow escape mechanism, а не security boundary.

### Решение

Сделать breaker deterministic:

```text
tool_count >= N
→ hard stop current agent
→ structured incident
→ explicit recovery state
```

---

# 20. Evals выглядят сильнее, чем фактическая проверка

Pipeline умеет завершаться с ошибкой при score ниже порога.

Но многие проверки в основном смотрят на текстовый output модели.

Это слабее реальной security verification.

Security test должен проверять не только ответ LLM, но и фактические side effects:

```text
filesystem side effect
state mutation
fact mutation
network access
tool execution
vault access
```

### Решение

Для каждого security test добавить behavioral assertions по состоянию системы и побочным эффектам.

---

# 21. Telemetry слишком примитивная для заявленного self-learning

Telemetry в основном собирает token count, guardrail events и error count.

Если на основе этого Regulator предлагает изменения, получается слишком слабая доказательная база для автоматического изменения security policy.

### Решение

Regulator должен выдавать:

```text
proposal
confidence
evidence
affected rule
```

а само изменение проходить deterministic approval.

---

# 22. Ключевая концептуальная проблема: система сама себе доверяет

Проект пытается решить проблему «не доверяй LLM», но значительная часть safety всё равно построена на другой LLM-роль/другом prompt:

- Reviewer;
- Analyst;
- Arbitrator;
- Regulator.

Это нормально как quality-control, но недостаточно как единственная security boundary.

Правильнее:

```text
LLM = untrusted planner
             ↓
deterministic policy
             ↓
tool capability
             ↓
OS/container isolation
             ↓
observable side effect
```

а не:

```text
LLM
 ↓
другая LLM проверяет первую LLM
```

---

# 23. Самые критичные проблемы

| Приоритет | Проблема | Решение |
|---|---|---|
| **P0** | Path traversal check через `startswith()` | `Path.resolve()` + `relative_to()` + symlink protection |
| **P0** | Arbitrator bypasses Reviewer | После Arbitrator всегда Reviewer |
| **P0** | `APPROVE` определяется substring | structured decision |
| **P0** | Secret vault глобальный | per-user/session vault |
| **P0** | LLM может менять project facts | policy/authorization layer |
| **P0** | Нет настоящего execution sandbox | container/VM/subprocess isolation |
| **P0** | Kotlin agent проверяется Python tooling | Kotlin/Gradle/Detekt/Ktlint |
| **P1** | requirements неполные | нормальный dependency manifest |
| **P1** | session state фактически сбрасывается | resume/persist state |
| **P1** | user RAG collection практически не используется | нормальная ingestion архитектура |
| **P1** | HITL ветка для несуществующих tools | capability registry |
| **P1** | evals проверяют output, а не side effects | behavioral/security assertions |
| **P2** | context token estimation грубая | реальный tokenizer |
| **P2** | telemetry слишком простая | structured observability |

---

# 24. Что в проекте хорошего

Несмотря на проблемы, архитектурная идея сама по себе хорошая.

### 1. Разделение ролей

Coder и Reviewer действительно разделены, а Arbitrator вынесен отдельно.

### 2. Tool-based orchestration

Вместо shell-доступа агент работает через ограниченный набор tools.

### 3. Explicit state

`state.json`, `tool_executions`, metrics — правильное направление для auditability.

### 4. Tokenization секретов

Guardrail не только блокирует, но и умеет заменять секреты токенами с последующим контролируемым восстановлением.

### 5. Adversarial eval layer

Наличие `adversarial_prompts.json`, deadlock tests и circuit-breaker tests — хорошая база.

### 6. Разделение memory tiers

Идея разделять structured facts, RAG и session context — правильная, хотя реализация пока сырая.

---

# 25. Оценка проекта

```text
Архитектурная идея       8/10
Agent orchestration      7/10
Code organization        5/10
Security architecture    4/10
Actual sandbox isolation 2/10
Testing strategy         5/10
Production readiness     3/10
```

Главная ценность проекта сейчас — **исследовательский prototype multi-agent coding platform**.

Главная ошибка позиционирования — считать его уже **безопасным production sandbox**.

---

# 26. Что менять первым

Не нужно сразу переписывать весь проект.

Я бы сделал четыре последовательных изменения:

```text
1. Security boundary
   ↓
Path / user / vault isolation

2. Deterministic policy engine
   ↓
facts / secrets / tool authorization

3. Correct validation
   ↓
Kotlin/Android validators вместо Python validators

4. Correct agent state machine
   ↓
Coder → Validator → Reviewer
                     ↑
                 Arbitrator
```

После этого уже имеет смысл заниматься:

```text
RAG
Telemetry
Regulator
Prompt tuning
Few-shot
Cost optimization
```

Потому что сейчас часть «умных» функций построена поверх слабой security и orchestration boundary.

---

# Итог

Проект интересный и архитектурно амбициозный, но сейчас это **prototype multi-agent coding orchestrator с файловым workspace**, а не production-grade sandbox.

Самые опасные места — path isolation, доверие к LLM в policy decisions, обход Reviewer после Arbitrator, global vault и несоответствие Kotlin ↔ Python validation.

## Основные исходники

- https://github.com/kharohiy/Mini-Agent-Sandbox
- https://github.com/kharohiy/Mini-Agent-Sandbox/blob/main/runner.py
- https://github.com/kharohiy/Mini-Agent-Sandbox/blob/main/roles.json
- https://github.com/kharohiy/Mini-Agent-Sandbox/blob/main/rag_service.py
- https://github.com/kharohiy/Mini-Agent-Sandbox/blob/main/data_guardrail.py
- https://github.com/kharohiy/Mini-Agent-Sandbox/blob/main/vault_registry.py
- https://github.com/kharohiy/Mini-Agent-Sandbox/blob/main/evals_pipeline.py
# Scope of this analysis

This document is a security and architecture risk assessment for Mini Agent Sandbox. It does not redefine the product as a security sandbox: the product objective is an agentic code-generation tool. The identified boundaries exist to support the real-project workflow of retrieval, patch proposal, review, explicit approval, and isolated validation.
## Phase 8 implementation note

## Phase 9 implementation note — 2026-09-17

## Phase 10 implementation note — 2026-09-20

The historic analysis correctly identifies memory poisoning as a high-risk
area, but the current implementation already denies direct LLM
`update_project_fact` calls and provides evidence-gated versioned knowledge
cards. Phase 10 addresses the remaining integration gap: a deterministic
grounded-Q&A-to-draft-card bridge with same-project source/hash checks. It must
not automate verification or indexing, treat a global book as GTA evidence, or
train on model output. This narrows the remaining risk without reopening the
codegen or validation workflows.

## Phase 13 planning note — 2026-09-21

Item 13 remains applicable after the completed dependency and session phases.
`ModelRequest.context_tokens` falls back to `len(content) // 4`, and runner
separately derives window utilisation from the same approximation. Phase 13
will first audit whether an already installed, model-compatible local counter
exists for the configured Qwen route. Only a reproducible counter or proven
conservative bound may replace the approximation; no new tokenizer package,
asset download, or model request is authorized by this plan.

The phase must feed one result to the existing router and metric paths and test
budget refusal before provider dispatch. Unknown model identifiers cannot be
called exact. If a compatible counter cannot be established without changing
the Phase 11 dependency contract, that is a blocker and production code stays
unchanged.

Completion record (2026-09-21): approved official Qwen assets on `E:` are
hash-verified; exact offline rendering matched one actual Ollama count at 26.
Phase 13.1 subsequently inspected the installed Ollama 0.21.0 Modelfile and
debug-rendered prompt, then matched real local counts for declared tool schema
(135), assistant tool call (52), and tool response (76). The runner/router
exact path covers only these measured forms; unknown tool schemas and message
shapes retain explicit fallback.

Blocker record (2026-09-21): the local LiteLLM counter returned a stable value
for a fixed `ollama/qwen2.5:14b` fixture but is not model-compatible proof. Its
installed source maps the identifier to `gpt-3.5-turbo` and uses OpenAI
`cl100k_base` fallback with generic message framing. Therefore it must not
replace the approximation. No code changed; proceeding requires an approved
official-Qwen-tokenizer dependency/clean-install path, an authorized Ollama
tokenization integration, or retaining the current estimate.
The local package/cache audit found only generic `tokenizers`/`tiktoken` and a
non-Qwen `faster-whisper-tiny` cache; no Qwen tokenizer assets are available.

## Phase 12 planning note — 2026-09-21

Historical item 12 is only partially current. Phase 7 already added a
fail-closed `--resume` path that restores a structurally valid interrupted
session instead of unconditionally starting a fresh one. The remaining
observed gap is lifecycle ambiguity: the current `--clear` helper directly
mutates stored state, clears history, and marks the session `in_progress`.

Phase 12 was therefore limited to deterministic `new`, `resume`, and explicit
session-only `reset` semantics with focused fixture-based tests. It must not
enable LLM summarisation, memory ingestion, RAG promotion, or learning from
conversation. Reset must not purge user data or affect facts, knowledge cards,
RAG, snapshots, ledgers, vaults, or project source. Unknown historic state must
fail closed; no migration or repair is implied by this plan.

Completion record (2026-09-21): the session reset removes only selected
`state.json`, rejects a symlink state file, and leaves an absent user directory
absent. The explicit `--reset` command was added; `--clear` is a deprecated
compatibility alias. New session construction is explicit and the existing
resume path remains fail-closed. Temporary-fixture lifecycle tests passed 3/3,
with existing resume validation 1/1; no live state, RAG, GTA, model, Docker,
Gradle, or package state was used.

## Phase 11 planning note — 2026-09-20

Item 11 of this historical analysis remains applicable: `requirements.txt`
does not currently enumerate every direct runtime import, while PDF ingestion
has a separate partial manifest. Phase 11 will establish an auditable
runtime/ingestion/development dependency layout and focused manifest tests. It
will not install, upgrade, or resolve packages until separately authorized.

Completion record (2026-09-20): pinned runtime, PDF-ingestion, and development
manifests now account for observed direct imports while preserving the default
`requirements.txt` entry point. Focused manifest tests passed 3/3. No package
state changed; a clean-environment install remains separately authorized.

Fresh-clone acceptance (2026-09-21): completed in an isolated `E:` clone at
`3f7027f` with Python 3.11.9. Default and optional-ingestion manifests
installed with Pip caching disabled; `pip check`, runtime imports, the full
suite (166 tests; 17 expected skips), and the two ingestion tests passed. No
RAG corpus, Chroma persistent store, Ollama, PDF processing, or GTA source was
used.

Completion record (2026-09-20): the deterministic bridge validates structured
same-project project-code paths and hashes against the snapshot before creating
only a draft card. Global-library, missing, stale, and cross-project evidence
is rejected. Existing explicit verification remains the sole indexing path.
Focused Ruff and 11 focused tests passed; no live GTA knowledge, model training,
or execution workflow was used.

Phase 8 established a read-only project corpus and one grounded natural
answer. Phase 9 is the bounded retrieval-quality follow-up: improve the
selection and ranking of project evidence before the existing local Analyst →
Reviewer Q&A chain answers a natural question. It must remain read-only and
must not reopen the codegen, approval, or validation workflow.

Phase 9 additionally adopts a cascaded RAG boundary: project snapshot/code
retrieval is the only evidentiary source for claims about GTA Cheats. The
shared Compose/Kotlin/architecture library is retrieved separately and may
provide technical explanation only. Collections, trust labels, result quotas,
and citations must remain distinct. A future project-knowledge-card capability
may accept only explicitly approved, evidence-backed material; no model output
may self-promote into retrieval memory.

Audit result (2026-09-20): GTA project-code has 393 chunks; both legacy and
canonical global-library collections had zero. The user authorized one bounded
ingestion of the three existing PDF books into the canonical global library.
This exception does not authorize any change to GTA project RAG.

Completion record (2026-09-20): the canonical global library has 2,293 chunks
and GTA project-code remains 393. A separate stored-chunk lexical project stage
corrected the observed `tools:targetApi` source-selection miss without reading
the connected source tree. Global results remain technical-reference-only; two
real local Analyst -> Reviewer answers were grounded in
`app/src/main/AndroidManifest.xml`. Focused Ruff and 4/4 focused tests passed.

Recognized local-model proposal formats now pass through existing unified-diff,
path-policy and ledger controls. This compatibility layer grants no exception.
The remaining risk is local completion stalling before first output; resolution
must preserve default-deny providers, budgets, explicit approval, read-only
source and temporary-copy validation.
