# Phase 15 Preparation — Secret/PII detection and prompt-injection separation

## Objective

Replace the current single-pass regex/context heuristic with a deterministic,
structured secret/PII detection boundary while keeping the existing
`DataGuardrail.run(text, user_id)` compatibility contract. Prompt-injection
handling becomes a separately named boundary; it is not a secret detector and
must not be represented as complete injection prevention.

## Observed baseline

`data_guardrail.py` currently has five rules (`API_KEY`, `EMAIL`, `IPV4`,
`AWS_KEY`, `AWS_SECRET`), a 50-character substring check for two rules, and a
regex deleting paired `image`, `script`, and `system` tags. It mutates text
while iterating rules, so later matching sees earlier token substitutions.
There is no structured finding/result type or dedicated deterministic
DataGuardrail test module. `evals_pipeline.py` exercises the live local-model
path and is not an acceptance test for this phase.

## Design

```text
input
  ├─ SecretScanner (secrets and PII only)
  │    provider-specific rules + credential assignments + entropy candidates
  │    → structured findings: kind, detector, confidence, span, length
  │    → non-overlapping token substitutions
  └─ PromptInjectionBoundary (untrusted markup only)
       → separately labelled compatibility sanitisation
```

`SecretScanner` is standard-library-only in this phase. It will use a stable
rule registry, Shannon entropy, assignment/identifier context and explicit
allowlists. A generic high-entropy value is masked only when it is in an
assignment/credential context; entropy alone is never proof. Findings and
telemetry must never retain secret values. Existing API keys, AWS keys, email
and IPv4 masking remain compatible.

The initial provider set is deliberately bounded and testable: existing OpenAI-
style and AWS identifiers plus GitHub, GitLab, Slack, Stripe and private-key
headers. A broad provider catalogue is not copied ad hoc. The next optional
integration decision is a pinned, separately reviewed structured scanner such
as `detect-secrets`; no package is added, downloaded, installed or executed
in this phase. This follows the documented distinction between regex plugins,
entropy and keyword/context detection in [detect-secrets](https://github.com/Yelp/detect-secrets)
and the rule/entropy model of [Gitleaks](https://github.com/gitleaks/gitleaks).

## Scope

1. Add deterministic structured secret/PII findings and non-overlapping
   redaction in a dedicated module; retain the public `DataGuardrail` facade.
2. Move the current tag-only sanitisation behind a prompt-injection-specific
   component, with compatibility tests proving it has no vault side effects.
3. Add focused tests under `tests/sandbox/policy/` for existing coverage,
   provider-specific values, high-entropy credential assignments, benign
   high-entropy text, overlapping findings, tenant-scoped tokens and prompt
   boundary separation.
4. Update `TESTS.md`, handover, roadmap and analysis with observed results.

## Explicit non-goals and prohibitions

- Do not claim that markup removal or any classifier fully prevents prompt
  injection. Do not use an LLM to classify untrusted prompts.
- Do not alter `resolve_secrets()` or add generic secret revelation to tools;
  that is the separate analysis item 17.
- Do not weaken or remove existing masking, change vault paths, log secret
  values, make network calls, add/install dependencies, scan the repository,
  re-index RAG, or touch GTA, Docker, Gradle, models, roles or policies.
- Do not run `evals_pipeline.py` or a live Ollama call as a substitute for
  deterministic security acceptance.

## Acceptance

- Existing public masking API remains compatible and all discovered secret
  values are tokenised once without leaking a value in a finding or telemetry.
- The focused guardrail suite covers positive and negative entropy/context
  paths, provider detectors and boundary separation.
- `python -m unittest tests.sandbox.policy.test_data_guardrail -v` and
  `python -m ruff check data_guardrail.py secret_scanner.py prompt_injection.py tests/sandbox/policy`
  pass. A full deterministic suite follows only after focused acceptance.

## Completion record — 2026-09-22

`secret_scanner.py` now emits plaintext-free structured findings and applies
provider-first, non-overlapping selection. It covers the pre-existing OpenAI-
style/AWS/PII cases, GitHub, GitLab, Slack, Stripe, private-key blocks,
credential assignments and context-gated high entropy. `prompt_injection.py`
owns the legacy paired-tag compatibility behaviour; it has no vault side
effect and makes no claim of general injection prevention.

The focused guardrail and vault suite passed 10/10. The full deterministic
suite passed 188 tests with 19 expected skips; targeted Ruff and diff checks
passed. No dependency was installed, and no local model, Docker, RAG, GTA,
Gradle or live vault data was used. External scanner integration remains a
separate explicit dependency decision, not a blocker for this bounded phase.

## Post-phase real integration evidence — 2026-09-22

The existing opt-in `tests.integration.local_ollama.test_offline_integration`
passed 1/1 against installed Ollama/Chroma: real `nomic-embed-text` embeddings,
ephemeral Chroma retrieval and a real local completion. Its temporary fixture
was cleaned by the test.

One actual `runner.py` offline loop then ran from a separate `E:` copy with a
synthetic GitHub-shaped token. The token was absent from saved `state.json` and
existed only in that copy's vault. The local model nevertheless remained
`in_progress` after three turns and ten tool executions, producing unnecessary
workspace files and returning to Analyst. The process was stopped and the
entire `E:` copy, including state, vault and artifacts, was deleted. Therefore
the deterministic Phase 15 contract is verified, but full agent-loop completion
is **not** accepted; local-loop nondeterminism remains a blocker.

## Correct GTA baseline validation — 2026-09-22

The generic Python runner task above was not a valid regression baseline for an
Android/Kotlin-oriented system and must not be used to assess Phases 12–15.
The correct read-only GTA Analyst→Reviewer baselines were then run against the
saved `gta-cheats--cc0fe5de` corpus. `tools:targetApi="31"` from
`app/src/main/AndroidManifest.xml` passed in both answers.

The `MainActivity` `MAIN`/`LAUNCHER` baseline did not pass. Read-only Chroma
audit proved both facts exist, but in two adjacent manifest chunks; retrieval
provided the model only the `LAUNCHER` tail. Analyst and Reviewer correctly
refused to infer the activity name from insufficient supplied evidence. This
is an observed Phase 9 evidence-assembly/retrieval blocker, not a Phase 15
secret-classification result. No source, RAG corpus or retrieval logic changed.

## Phase 9 evidence-assembly correction — 2026-09-22

The blocker was corrected without re-indexing. For an already selected literal
project-code source, retrieval now assembles its bounded stored chunks in
source order. Fusion retains that assembled evidence when semantic retrieval
also returns a tail chunk from the same source. It does not change source
selection, read the connected Android tree, or mix project and global RAG.

Focused retrieval tests passed 6/6. The exact saved GTA `MainActivity`
`MAIN`/`LAUNCHER` Analyst→Reviewer question then passed: both answers named
`.MainActivity` and cited `app/src/main/AndroidManifest.xml`. The full
deterministic suite passed 190 tests with 19 expected skips. Repository-wide
Ruff still reports 52 pre-existing findings outside this change; the changed
retrieval module and its tests pass Ruff.
