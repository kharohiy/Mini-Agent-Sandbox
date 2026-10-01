# Phase 18 Continuation Prompt — close the unsupported critical-tool HITL path

Phase 18 completed locally on 2026-10-01. Use this file as its historical
scope record; do not resume implementation unless the user opens a new scope.

Before implementation, read `PHASE18_PREPARATION.md`, `CODEX_HANDOVER.md`,
`README.md`, `NEXT_STEPS_PLAN.md`, `PROJECT_EVOLUTION_ROADMAP.md`, `TESTS.md`,
and analysis item 18 in `mini_agent_sandbox_analysis.md`.

The current source has a `runner.py` confirmation branch for
`send_email`, `access_calendar`, and `web_search`, but these tools are absent
from `AGENT_TOOLS`. Authorization precedes that branch, so the branch is
unreachable; its success response is mocked and performs no external action.
The real human-approval boundary in this area is the explicit patch approval
bound to the reviewed diff SHA-256 before validation. Preserve that boundary.

Implement only the bounded removal, focused regression tests, and factual
documentation corrections described in the preparation file. Do not add
external tools or general-purpose HITL. Use synthetic temporary fixtures and
mocks. Do not run a model, network request, Ollama, Docker, Gradle, or broad
runtime loop.

Record phase completion only after the acceptance checks actually pass. If a
test reveals a real requirement for an external tool or interactive approval
surface, stop and report the evidence; that requires a separately approved
design.
