# Phase 13 Preparation — Deterministic context accounting

## Status

Completed on 2026-09-21. Phases 9 through 12 are complete.

## Why this phase

Item 13 of `mini_agent_sandbox_analysis.md` remains open. `ModelRequest`
falls back to `len(content) // 4`; `runner.py` independently computes the same
approximation for window utilisation and passes it into the router gate. That
number is not tokenizer-specific and can undercount or overcount the actual
local Qwen request.

This is not a RAG, memory, or provider-routing phase. It narrows the
deterministic input to the existing context and task-budget gates so that their
decision and their recorded utilisation use one auditable counter.

## Objective

Establish one explicit context-counting contract for completion requests:

```text
messages + declared completion reserve
        -> deterministic counter for the selected model family
        -> router context/request/task-budget decision
        -> bounded telemetry metric using the same count
```

The counter must identify whether its value is exact for the configured model
or a documented conservative bound. It must never silently claim a character
heuristic is exact tokenizer output.

## First bounded increment

1. Audit locally installed, already declared capabilities for counting messages
   for `ollama/qwen2.5:14b` and any existing routed model identifiers. Do not
   install a tokenizer, download model files, or call a model service.
2. Trace every producer and consumer of `estimated_context_tokens`,
   `max_context_tokens`, `max_request_tokens`, and window-utilisation metrics.
3. Specify one small pure counter interface and an explicit model-identifier
   mapping. It must include message role/content framing and the requested
   output-token reserve.
4. Add deterministic fake-based tests for boundary acceptance/refusal,
   consistent metrics, unknown-model behaviour, and preservation of the
   default-deny provider/budget gates.
5. Change production behaviour only if the audit proves a reproducible counter
   is available for the configured local model. Otherwise record the blocker
   and retain the current implementation unchanged.

## Implementation options

1. **Existing local counter — preferred.** Reuse an already installed,
   deterministic model-aware counter only after tests prove its model mapping
   and message framing. No network or model invocation is permitted.
2. **Conservative deterministic bound.** If an exact local tokenizer is not
   available, use a clearly named conservative byte/character bound only if it
   can be mathematically justified for the configured model contract and avoids
   undercounting. It must be reported as a bound, not exact tokens.
3. **Separate dependency decision — blocked by default.** A model-specific
   tokenizer dependency or downloaded tokenizer assets need a separate approved
   dependency and clean-install phase; do not add it opportunistically here.

## Hard boundaries

- Do not change model/provider selection, privacy policy, fallback rules,
  completion prompts, role configuration, budget values, or request payloads.
- Do not contact Ollama, download models/tokenizers, install/upgrade packages,
  alter manifests, or create a lockfile.
- Do not modify RAG/Chroma, ingestion, knowledge cards, project facts, session
  storage, vaults, GTA source/profile, Docker, Gradle, patch/review/approval,
  or validation workflows.
- Do not use live prompts, saved session memory, or model output as test data.
- Unknown model identifiers must fail closed or retain an explicitly documented
  existing contract; they must never receive a guessed "exact" token count.

## Exit condition

The implementation has one tested source of context accounting for the router
and metrics, proves no provider dispatch occurs after a budget refusal, and
documents exact-versus-bound semantics. If no reproducible local counter is
available without new dependencies or downloads, Phase 13 ends blocked with
the code unchanged and the evidence recorded.

## Expected blockers

- The installed dependencies may not include a tokenizer that is demonstrably
  compatible with `qwen2.5:14b` message framing.
- Tokenizers can require model-specific assets or silently fall back to another
  encoding; neither is acceptable as proof of exact local counting.
- Adding a tokenizer can change the reproducible dependency contract validated
  by Phase 11. That action needs separate authorization and a clean-install
  acceptance plan.

## Blocker record — 2026-09-21

- With `LITELLM_LOCAL_MODEL_COST_MAP=True`, the already installed LiteLLM
  `token_counter(model="ollama/qwen2.5:14b", messages=...)` is stable across
  repeated fixed-fixture calls and returns `21` for the audited two-message
  fixture. No Ollama request occurred.
- This is **not** a Qwen-exact result. The installed LiteLLM source maps a
  non-OpenAI model through `_fix_model_name()` to `gpt-3.5-turbo`; its
  OpenAI-tokenizer branch falls back to `cl100k_base`. Its default three-token
  per-message framing is likewise not proof of Ollama/Qwen chat framing.
- An initial diagnostic import without the existing local-cost-map environment
  variable attempted a LiteLLM GitHub model-price-map refresh; the restricted
  environment refused it and LiteLLM used its local backup. Subsequent audit
  calls set `LITELLM_LOCAL_MODEL_COST_MAP=True`. No external request succeeded.
- Package/cache inventory found `tokenizers` and `tiktoken`, but no
  `transformers` or `sentencepiece`; the local Hugging Face cache contains only
  `faster-whisper-tiny` and no Qwen tokenizer assets. An installed generic
  tokenizers library without the Qwen vocabulary/merges cannot prove Qwen
  counts.

### Safe next options

1. Approve a separate dependency change for the official Qwen tokenizer (and
   its required local assets), then repeat the Phase 11 clean-install contract
   and add exact-count tests.
2. Obtain a documented local Ollama tokenization interface and prove its
   result/framing with an opt-in infrastructure run; this is a separate
   authorization because it contacts the service.
3. Keep the current approximation and label it as an estimate until one of the
   preceding evidence paths is approved. No unverified counter is substituted.

## Completion record — 2026-09-21

- The user authorized official Qwen assets on `E:` at revision
  `cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8`. `tokenizer.json` SHA-256 is
  `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539`; config
  SHA-256 is `5b5d4f65d0acd3b2d56a35b56d374a36cbc1c8fa5cf3b3febbbfabf22f359583`.
- The asset stays outside Git/RAG and is accepted only through explicit
  `MINI_AGENT_QWEN_TOKENIZER_DIR` plus both hash checks.
- One real local Ollama chat reported `prompt_eval_count=26`; offline Qwen
  template rendering/tokenization returned the same 26. Previous values were
  9 (`chars / 4`) and 24 (LiteLLM generic).
- Shared runner/router accounting uses exact mode for the measured Qwen text
  chat and Phase 13.1 tool formats: declared schema, assistant tool call, and
  tool response. Unknown message/schema shapes retain explicit legacy fallback.
- Phase 13.1 measured local `prompt_eval_count` values 135, 52, and 76 for
  those tool fixtures. Focused counter/router/manifest tests passed 33/33,
  focused Ruff and `git diff --check` passed.
