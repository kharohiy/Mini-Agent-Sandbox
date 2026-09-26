# Phase 17 Continuation Prompt — tool-scoped secret capabilities

Read `PHASE17_PREPARATION.md`, `CODEX_HANDOVER.md`, `TESTS.md`, and analysis
item 17 in `mini_agent_sandbox_analysis.md` before implementation.

Start with the call-site and dispatch-order audit. The issue is not tenant
persistence: Phase 16 already scopes persisted Vaults by user. The issue is
that the Runner resolves every top-level string tool argument before tool
authorization. Do not preserve that generic behavior as compatibility.

Implement only the static default-deny, exact tool-and-parameter capability
boundary in the preparation file. Authorize a tool first; resolve a token only
for an explicitly registered trusted parameter. The production registry begins
empty: file, directory, fact, and patch arguments keep opaque token text.

Use synthetic temporary vaults or mocks. Prove that forbidden and unknown
tools do not open a Vault, current tools never receive plaintext, and an
explicit synthetic capability cannot cross tenant boundaries. Do not log a
plaintext secret or token.

Do not inspect live `data/`, add tools or dependencies, call a model, run
Ollama/Docker/Gradle, alter RAG/GTA, modify Vault paths, or change roles,
providers, prompts, task state, approval, validation, or facts.

## Status

Completed and reviewed locally on 2026-09-27. Retain the
empty production capability registry unless a separately approved trusted tool
and exact parameter require plaintext. Do not restore generic deobfuscation.
