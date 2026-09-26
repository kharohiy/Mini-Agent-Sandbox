# Phase 17 Preparation — tool-scoped secret capabilities

## Status

Completed and reviewed locally on 2026-09-27.

## Observed boundary

Analysis item 17 is a P0 disclosure boundary, distinct from Phase 16
persistence isolation. `runner.py` currently applies `resolve_secrets()` to
each top-level string tool argument before checking whether the tool is allowed
for the role and task mode. A tenant-scoped Vault does not make that generic
plaintext release safe.

The current agent-visible tools are `create_file`, `read_file`,
`list_directory`, `read_project_facts`, and, in bound project-patch mode,
`propose_patch`. None has a demonstrated need for plaintext secret material.
Tokens in their arguments must remain opaque.

## Objective

Replace generic argument deobfuscation with a static default-deny capability
boundary. A Vault token may be resolved only after tool authorization and only
for one explicitly named parameter of an explicitly trusted tool.

```text
incoming tool call
  -> authorize tool for role and task mode
  -> match exact (tool name, parameter name) capability
  -> resolve only that one string parameter for the current tenant
  -> dispatch the authorized tool
```

## Planned work

1. Audit all `resolve_secrets()` call sites, tool dispatch paths, tool schemas,
   and fields persisted in tool history/state. Confirm that the Runner's
   generic top-level string loop is the only production disclosure path.
2. Add a small deterministic capability helper or module using immutable exact
   `(tool_name, parameter_name)` matching. It is not model-configurable and
   does not recursively scan strings, dictionaries, lists, paths, file
   content, or diffs.
3. Reorder tool dispatch so the tool/role/task-mode check occurs before any
   Vault lookup. Unknown, forbidden, documentation-restricted, and
   reviewer-disallowed tools must not open a Vault.
4. Start with an empty production capability set. Do not grant current file,
   directory, fact, or patch parameters plaintext access merely for legacy
   compatibility.
5. Ensure plaintext values, token mappings, and token values are not printed
   or persisted in state, telemetry, tool results, exceptions, or test output.
6. Add focused deterministic tests using temporary vaults or mocks; update
   `TESTS.md` only with observed outcomes.

## Acceptance

- Tokens in every current string-bearing tool argument remain unchanged and do
  not trigger a Vault lookup.
- Unknown and disallowed tools are rejected before any Vault lookup.
- An isolated synthetic capability fixture proves resolution only for its exact
  trusted tool/parameter and only for the same tenant.
- Nested objects, lists, file contents, paths, and diffs are never recursively
  resolved.
- Existing Vault isolation, guardrail masking, task-mode, project-patch, and
  Runner contracts remain compatible. Focused tests and Ruff for changed files
  pass before a deterministic suite is considered.

## Prohibitions

- Do not inspect, decrypt, print, migrate, rename, delete, or commit live
  `data/` vaults. Use temporary roots and synthetic secrets only.
- Do not add or activate web, email, HTTP, MCP, shell, Docker, Gradle, or any
  other external tool; none may become a secret capability in this phase.
- Do not add a KMS, cloud service, dependency, model call, network operation,
  or background secret synchronization.
- Do not alter Phase 16 Vault paths or compatibility, RAG, GTA, Docker, Gradle,
  roles, providers, prompts, task state, approval, validation, or facts.
- Do not use Ollama, `evals_pipeline.py`, Docker, Gradle, or a broad runtime
  loop as acceptance.

## Decisions and blockers

1. If a future caller actually requires plaintext, stop and require a separate
   decision naming the trusted tool, exact parameter, local handling contract,
   and tests. It is not implicitly covered here.
2. A test that expects deobfuscation in file content or a patch describes
   unsafe legacy behavior; update it to expect opaque token preservation, not
   a broader registry.
3. If plaintext must be recorded for a workflow, block that design. Only
   opaque tokens or bounded non-secret metadata may be persisted.

## Completion condition

Phase 17 is complete only when production tool dispatch is default-deny for
secret revelation, all current agent-visible tools preserve opaque tokens, and
focused deterministic tests prove both denial and one exact capability-only
positive path. Documentation alone is not completion.

## Completion record — 2026-09-27

`secret_capabilities.py` defines an immutable default-deny production registry,
which is intentionally empty. `runner.py` now authorizes the requested tool
before calling the capability resolver; current file, directory, fact, and
patch arguments retain opaque tokens. The former generic resolver and its
token logging were removed.

Focused capability tests passed 5/5. They cover no Vault lookup for current
tools, refusal before resolver invocation for an unknown tool and a Reviewer
file write, same-tenant resolution only through an explicit synthetic
capability, and non-recursive nested values. The deterministic suite passed
202 tests with 20 expected
skips. Ruff passed for the new module and tests; `runner.py` retains 10
pre-existing Ruff findings outside this phase. An initial unit-test import
attempted LiteLLM's remote cost-map refresh; the sandbox refused it and no
external request succeeded. Subsequent verification set
`LITELLM_LOCAL_MODEL_COST_MAP=True`. No live vault, model, RAG, GTA, Docker,
or Gradle operation occurred.
