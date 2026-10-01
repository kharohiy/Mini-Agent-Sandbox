# Phase 18 Preparation — close the unsupported critical-tool HITL path

## Status

Completed locally on 2026-10-01.

## Source and current-state reconciliation

Analysis item 18 says that `send_email`, `access_calendar`, and `web_search`
have a runtime confirmation branch but are absent from `AGENT_TOOLS`, making
that HITL path effectively dead. Current source confirms both facts: the
special branch remains in `runner.py`, while none of those names is exposed to
the model. Tool authorization runs before the branch, so these names are
rejected before the `input("Allow execution? (y/n): ")` prompt. The `y` path
only returns a mocked message; it performs no external action.

There is a separate, real human-approval boundary for project patches. A
positive Reviewer decision moves a patch to `awaiting_user_approval`; the
project API and `WorkLedger.approve_patch()` require explicit approval bound
to the patch SHA-256 before validation. Phase 18 must preserve this flow and
must not describe it as approval for arbitrary external tools.

## Objective

Close the mismatch between the advertised general critical-tool HITL and the
actual default-deny tool surface. Keep external tools unavailable. Remove the
unreachable mocked confirmation/execution branch and document the narrower,
implemented human-approval contract accurately.

## Planned work

1. Reconfirm the tool registry, role/task-mode authorization order, dispatch
   branch, and existing patch-approval API/ledger contract before editing.
2. Remove the `send_email` / `access_calendar` / `web_search` special-case
   confirmation branch and its simulated success path. Do not add a registry
   entry or external integration.
3. Add focused deterministic regression coverage showing that each
   unsupported tool is rejected before prompting, dispatch, network activity,
   or stateful side effects. Use mocks/temporary fixtures only.
4. Correct the inaccurate general-HITL claims in `README.md` and the
   corresponding security scenario in `TESTS.md`; describe exact-hash human
   approval only for reviewed project patches.
5. Record only observed test and lint outcomes in the phase status documents.

## Acceptance

- None of the three external tool names is exposed through `AGENT_TOOLS` or
  can reach a confirmation/simulated-execution branch.
- A direct/forged call for each name fails closed before input or dispatch;
  tests prove the absence of side effects.
- Existing hash-bound project-patch approval and validation gates remain
  unchanged and retain focused regression coverage.
- Documentation no longer claims that arbitrary critical tools have a
  working console HITL path.
- Focused tests and Ruff for changed files pass before considering the phase
  complete.

## Blockers and decisions

1. **Analysis wording is broader than current implementation.** HITL is not
   wholly absent: exact-hash approval exists for reviewed project patches.
   The defect is the dead mock-tool branch and inaccurate general-tool claim.
2. **No interactive approval surface for arbitrary tools exists.** If a real
   email, calendar, or web tool is later required, stop and design it as a
   separate scope with authentication, authorization, consent, data handling,
   audit, revocation, and tests. A `y/n` prompt plus mocked success is not a
   production integration.
3. **Existing tests or documentation may encode the old claim.** Update only
   assertions and statements directly contradicted by the observed dispatch;
   preserve the existing patch-approval contract.
4. **Approval API deployment/authentication requirements are not established
   by this phase.** Do not infer that the endpoint is an authenticated UI or
   broaden this work into API authentication design.

## Prohibitions

- Do not add or activate email, calendar, web-search, MCP, HTTP, shell, or
  other external tools; do not make network calls.
- Do not weaken or bypass tool authorization, project policy, patch review,
  exact-SHA user approval, or trusted validation gates.
- Do not change `roles.json`, providers, prompts, secret capabilities, Vault
  paths/data, task state, RAG, GTA, facts, Docker, or Gradle.
- Do not run models, Ollama, `evals_pipeline.py`, Docker, Gradle, or a broad
  runtime loop for acceptance.
- Do not claim general HITL is implemented after removing the dead branch;
  describe only the verified project-patch approval flow.

## Completion condition

Phase 18 is complete only when unsupported external-tool calls are proven to
fail before prompting or side effects, the dead mock branch is removed, the
existing project-patch human approval remains intact, and documentation states
the actual boundary. This plan alone is not phase completion.

## Completion record — 2026-10-01

Removed the unreachable mocked confirmation branch from `runner.py`. Added a
regression test covering all three unsupported tool names; authorization
rejects them, leaves arguments unchanged, and does not invoke the capability
resolver or prompt. Updated `README.md` and `TESTS.md` to describe default-deny
external tools and exact-SHA approval for project patches.

The focused capability suite passed 6/6. The existing API test for Reviewer
approval followed by explicit exact-SHA user approval passed 1/1. Ruff passed
for the modified test module. `ruff check runner.py` reports 10 existing
findings elsewhere in that file; none are in the edited dispatch block. No
model, network, RAG, Vault, Docker, or Gradle operation occurred. The full
deterministic suite was not run.
