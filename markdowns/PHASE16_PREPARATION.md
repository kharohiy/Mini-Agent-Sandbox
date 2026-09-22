# Phase 16 Preparation — tenant-scoped persistent Vault

## Status

Completed locally on 2026-09-22; awaiting review, commit and push.

## Historical issue and current-state reconciliation

Analysis item 16 correctly requires that no process-global vault or key can
serve multiple tenants. Its historical description is no longer an exact
description of the checked-out code: `get_user_vault(user_id, base_dir)`
currently validates the user ID, rejects a symlink tenant directory, and
creates separate files at:

```text
data/<user_id>/.vault
data/<user_id>/.vault_key
```

The current `DataGuardrail` keeps mappings per `user_id`, and the existing
temporary-directory tests prove that Alice's persisted token cannot be read by
Bob. This is evidence of partial/core remediation, not a reason to close Phase
16 without checking all persistence and compatibility paths.

The approved target naming is:

```text
data/<user_id>/vault.enc
data/<user_id>/vault.key
```

No KMS, remote secret store, package, model, or cloud service is required for
this phase.

## Objective

Make the tenant boundary explicit and testable at the public vault factory and
at every Runner/Guardrail persistence call site. If canonical filenames replace
the existing hidden filenames, preserve existing per-user vault data through a
safe, deterministic, documented compatibility path; never silently orphan or
overwrite a vault.

## Planned implementation

1. Audit every `VaultRegistry` construction, `get_user_vault()` call,
   `save_mapping()`, and `get_secret()` call. Record whether any route can use
   a current-working-directory or unscoped vault.
2. Define a canonical per-user layout using `vault.enc` and `vault.key`, with
   a validated `data/<user_id>` root and no fallback to a process-global path.
3. Decide compatibility before editing code:
   - If legacy hidden files are retained, document them as the canonical
     compatibility layout and close only the audit gap.
   - If names change, support only a bounded same-user migration when both
     legacy files are present and canonical files are absent. Migration must
     verify that the legacy pair decrypts before writing canonical files and
     must never delete the legacy pair in the same phase.
4. Preserve token opacity and existing `resolve_secrets()` authorization.
   A token issued for one tenant must neither resolve nor persist in another
   tenant's vault, including after a new process/factory instance.
5. Make vault writes durable and fail closed on malformed ciphertext, invalid
   key material, unsafe tenant IDs, symlink traversal, or conflicting legacy
   and canonical files. Do not print decrypted values in exceptions or logs.
6. Add temporary-directory tests under `tests/sandbox/policy/` or
   `tests/sandbox/storage/`; update `TESTS.md` only with observed outcomes.

## Acceptance

- Two tenants using the same token text have independent encrypted mappings;
  neither vault can decrypt the other.
- A fresh `get_user_vault()` instance can recover only its own mapping.
- Invalid IDs and symlink escape attempts fail before reading or creating a
  vault outside the supplied `data` root.
- The canonical-layout decision is covered by tests: safe legacy compatibility
  or safe, non-destructive migration, never silent data loss.
- Existing guardrail and runner tests remain compatible; focused Vault tests,
  Ruff for changed files, and then the deterministic suite pass.

## Hard boundaries and prohibitions

- During development and tests, do not inspect, print, decrypt, manually
  migrate, rename, delete, or commit live `data/` vaults. Use temporary test
  directories only. The production factory's bounded compatibility copy is
  defined below; it is not authorization for a bulk operational migration.
- Do not add a KMS, cloud secret service, new dependency, model call, or
  background secret migration.
- Do not weaken guardrail masking, reveal tokens to tools, change
  `resolve_secrets()` authority, alter task state, RAG, GTA, Docker, Gradle,
  providers, roles, approval, validation, or project facts.
- Do not treat in-memory `DataGuardrail` mapping isolation as proof that
  persistent-file isolation is complete; test both boundaries.

## Expected blockers and decisions

1. **Legacy files contain real user secrets.** Do not manually batch-migrate
   them. The factory may make its bounded validated copy only for that tenant
   when it is used; a proactive/bulk migration still requires a separately
   approved, backup-first operational plan.
2. **Canonical and legacy pairs both exist but differ.** Fail closed and report
   a conflict; never choose, merge, or overwrite either file automatically.
3. **Atomic replacement is unavailable on a target platform.** Keep the
   existing safe path and document the operational blocker rather than risking
   vault corruption.
4. **An unscoped direct `VaultRegistry` call exists outside the audited
   factory.** Refuse Phase 16 closure until it is removed or explicitly made
   tenant-scoped with regression coverage.

## Completion condition

Phase 16 is complete only when the checked source has one explicit,
tenant-scoped persistence contract with tested compatibility behaviour. A
historical analysis statement alone, or tests of only in-memory mappings, is
not sufficient.

## Completion record — 2026-09-22

Audit found no production call site constructing `VaultRegistry` directly:
Runner secret resolution and Guardrail persistence use `get_user_vault()`.
The canonical layout is now `data/<user_id>/vault.enc` and `vault.key`.
Existing complete `.vault` / `.vault_key` pairs are validated by decryption and
copied only into an absent canonical pair; legacy files remain untouched.
Canonical mappings may extend a preserved legacy mapping with the same key.
Incomplete pairs, non-regular files, invalid key/material, unsafe IDs,
symlinks, and divergent pairs fail closed. Vault writes are atomic per file;
existing vaults are never silently re-keyed.

Focused Vault/guardrail tests passed 17/17 with one expected platform skip:
this Windows process lacks permission to create a real symlink fixture. A
separate deterministic mock test passed and covers the Vault symlink-refusal
branch without any Windows privilege.
The full deterministic suite passed 197 tests with 20 expected skips; focused
Ruff and `git diff --check` passed. No live vault, model, RAG, GTA, Docker,
Gradle or dependency state changed.
