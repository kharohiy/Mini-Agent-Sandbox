# Security Boundary Matrix — Phases 20–22

| Privileged effect | Untrusted input | Deterministic boundary | Observable assertion |
|---|---|---|---|
| Workspace files | Any agent path/contents | `SandboxStorage.resolve_workspace_path` plus role tool allowlist | Traversal creates no sibling file; Reviewer writes are denied |
| Connected project source | Coder patch text | approved plan scope, unified-diff policy, proposal-only ledger | proposal is stored while source bytes stay unchanged |
| Patch validation | Reviewer `APPROVE` | exact patch SHA user approval plus `ValidationWorker` | missing/rejected/wrong approval invokes no executor |
| Generated execution | validation request | `CapabilityPolicy` and `DockerSandboxExecutor` | host execution denied; temporary copy and container flags inspected |
| Network | generated validation code | Docker `--network none` | command contract always tested; outbound socket tested when Docker runs |
| Tool execution | any role tool call | per-role exposed tools and `authorize_tool_arguments` | unsupported tools never prompt, resolve secrets or dispatch |
| Tool volume/state | Coder tool calls | Phase 19 N/N+1 breaker | N records persist; N+1 is absent; `breaker_blocked` is durable |
| Vault access | tool arguments | `SecretCapability` allowlist after tool authorization | denied tool causes zero Vault lookups; tenant mappings stay isolated |
| Project facts | model proposal | `FactPolicy` and evidence review workflow | security fact is denied and store remains unchanged |
| Documentation completion | Reviewer verdict | artifact hash, required sections, source evidence and structured review | uncited artifact cannot complete despite `APPROVE` |
| Arbitration | Arbitrator recommendation | state machine returns to Coder, validation, then Reviewer | arbitration alone never marks completion |
| Regulation | Regulator JSON | evidence-ID admission in `regulator_policy.py` | no tools, `auto_apply=false`, policy files unchanged |

`tests/security_behavioral_manifest.json` is the executable Phase 20 subset.
The matrix also references focused and integration tests documented in
`TESTS.md`. A passing model response is never listed as a security boundary.
