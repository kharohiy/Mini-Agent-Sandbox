# Phase 16 Continuation Prompt — tenant-scoped persistent Vault

Read `PHASE16_PREPARATION.md`, `CODEX_HANDOVER.md`, `TESTS.md`, and analysis
item 16 in `mini_agent_sandbox_analysis.md` before implementation.

Start with the required call-site audit. The historical global-vault statement
must be reconciled with the existing per-user `.vault` / `.vault_key` factory
before changing names or persistence behaviour. Do not assume the required
`vault.enc` / `vault.key` naming is a harmless rename: a rename can orphan real
encrypted data when only one half of a key/vault pair moves.

Implement only the explicit, local tenant-vault contract from the preparation
file after the compatibility decision and focused temporary-directory tests
exist. Every vault operation must validate `user_id`, remain within its `data`
root, and fail closed for symlinks, malformed files and filename conflicts.
Preserve token opacity and current secret-resolution authority.

Never touch live `data/` vaults, print or log plaintext values, add a KMS or
dependency, use a model, alter RAG/GTA/Docker/Gradle, or modify roles, provider
policy, approval, validation, task state, or facts. Do not run a broad runtime
loop as Vault acceptance; deterministic temporary-fixture tests are required.

## Status

Completed locally on 2026-09-22. Retain the canonical/legacy compatibility
contract: do not delete legacy pairs, auto-resolve divergent pairs, or bypass
the tenant factory without a separately approved migration or design change.
