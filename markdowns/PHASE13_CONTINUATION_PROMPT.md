# Phase 13 Continuation Prompt — Deterministic context accounting

```text
Working directory:
C:\Users\AlSaintUk\Desktop\Mini Agent Sandbox

You are starting Phase 13. Phases 9 through 12 are complete. Read before
changing:
1. AGENTS.md
2. CODEX_HANDOVER.md
3. README.md
4. NEXT_STEPS_PLAN.md
5. PROJECT_EVOLUTION_ROADMAP.md
6. TESTS.md
7. PHASE13_PREPARATION.md
8. mini_agent_sandbox_analysis.md
9. this file

Objective
---------
Replace duplicated, undocumented `chars / 4` context accounting only when a
reproducible model-aware counter or a proven conservative bound is available.
The existing router context/request/task-budget gates and runner metrics must
consume one deterministic result with explicit exact-versus-bound semantics.

First task
----------
Audit the locally installed, already declared packages and trace every current
producer/consumer of context counts. Do not install, download, invoke Ollama,
or change code until the available counting mechanism and model mapping are
observed and recorded.

Hard boundaries
---------------
- Do not change providers, models, roles, prompts, privacy policy, fallbacks,
  budgets, completion payloads, or routing behaviour beyond the proven counter.
- Do not install packages, download tokenizer/model assets, alter manifests, or
  create a lockfile.
- Do not use Ollama, RAG/Chroma, live session/project data, GTA source, Docker,
  Gradle, or external services.
- Do not change facts, knowledge, vaults, session lifecycle, patch/review/
  approval/validation flows, or source-project state.
- Unknown models must not be labelled exact. If no safe counter is available,
  record the blocker and leave production behaviour unchanged.

Completion
----------
Phase 13 completes only with focused fake-based tests proving consistent router
and metric accounting plus fail-closed budget refusal. If a reproducible local
counter cannot be established without a new dependency or download, report the
blocker and do not substitute an unverified tokenizer.

Blocker record — 2026-09-21
---------------------------
The installed LiteLLM counter is locally deterministic but not Qwen-exact:
its source maps the Ollama Qwen identifier to `gpt-3.5-turbo` and falls back to
the OpenAI `cl100k_base` tokenizer. It returned 21 on a fixed two-message
fixture, but that is not acceptable evidence of Qwen token or chat-framing
equivalence. The safe options are an explicitly
approved official Qwen-tokenizer dependency/clean-install path, a separately
authorized documented Ollama-tokenization integration run, or retaining the
current estimate. Do not proceed without a new decision.

Completion record — 2026-09-21
-------------------------------
User-authorized Qwen assets on `E:` are hash-verified through
`MINI_AGENT_QWEN_TOKENIZER_DIR`. One real Ollama request and offline rendering
both counted 26 tokens for the same fixed text chat. Phase 13.1 additionally
proved declared tool-schema (135), assistant tool-call (52), and tool-response
(76) formats. Runner/router use those measured exact paths; unknown shapes
retain fallback. Focused tests passed 33/33 and focused Ruff passed.
```
