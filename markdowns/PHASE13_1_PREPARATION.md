# Phase 13.1 Preparation — Qwen tool-message token accounting

## Status

Completed on 2026-09-21.

## Objective

Extend Phase 13's exact Qwen/Ollama count only to tool-bearing message shapes
that match real local Ollama `prompt_eval_count`: tool schemas, assistant tool
calls, and tool responses. Unsupported shapes remain legacy fallback.

## Plan and boundaries

1. Use fixed, minimal local fixtures and measure each shape once with Ollama.
2. Implement only renderings that match the observed count exactly.
3. Route tools into the shared runner/router counter and add regression tests.
4. Do not touch RAG, facts, knowledge, GTA, models, Docker, Gradle, or source
   projects. Do not download further assets.

## Exit condition

Each enabled tool shape has an observed Ollama count, an equal offline Qwen
count, and a focused test. Any mismatch remains explicit fallback.

## Completion record

- `qwen2.5:14b` / Ollama 0.21.0 accepted fixed fixtures with
  `prompt_eval_count`: tool schema 135, assistant tool call 52, and tool
  response 76. The Phase 13 text-chat fixture remains 26.
- The renderer mirrors the installed Modelfile's tool output. It intentionally
  supports only the measured basic function-schema shape; unknown extensions
  fall back to the explicitly labelled legacy estimate.
- Ollama's tool-schema metric is one token below direct `tokenizers` asset
  output for the same debug-rendered prompt. The narrowly scoped correction is
  measured and tested only for a declared tool schema, never text or tool history.
- Runner and router both pass their declared tools into the shared counter; the
  runner reuses the exact same `turn_tools` list for counting and completion.
- No RAG, GTA project, Chroma collection, facts, model weights, Docker,
  Gradle, or source project changed. The hash-verified tokenizer stays on `E:`
  outside Git and RAG.
- Verification: focused counter/router/manifest suite 33/33, focused Ruff,
  full deterministic suite 178/178 (15 expected skips), and `git diff --check`
  passed.
