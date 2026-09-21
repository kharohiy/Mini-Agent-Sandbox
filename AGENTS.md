# Repository Guidelines

## Project Structure & Module Organization

Mini Agent Sandbox is a security-focused multi-agent Python system. Orchestration is in `runner.py`; `roles.json` defines roles and `model_router.py` selects completion routing. FastAPI endpoints are in `api.py`. Keep policy and guardrail work in dedicated modules such as `capability_policy.py` and `data_guardrail.py`.

Project/RAG state is handled by `project_registry.py`, `project_rag_ingestion.py`, `project_retrieval.py`, and `rag_service.py`. Trusted validation belongs in `validation_worker.py` and `sandbox_executor.py`; the API must not control Docker. Rules are in `rules/`; fixtures are in `tests/fixtures/`. Runtime state and vector stores under `data/` are not source code.

## Required Project Documentation

The canonical session documentation is in `markdowns/`. Before any
non-trivial change, read it in this order:

1. `markdowns/CODEX_HANDOVER.md` — current status, handover, and boundaries.
2. `markdowns/README.md` — architecture and runtime.
3. `markdowns/NEXT_STEPS_PLAN.md` — active priority.
4. `markdowns/PROJECT_EVOLUTION_ROADMAP.md` — approved milestones.
5. `markdowns/TESTS.md` — security-test scenarios.
6. The active phase files in `markdowns/` (currently
   `PHASE9_PREPARATION.md` and `PHASE9_CONTINUATION_PROMPT.md`).
7. `markdowns/mini_agent_sandbox_analysis.md` when architectural context is
   needed.

The root-level Markdown copies are legacy copies. Do not update, move, or use
them as authoritative status unless the user explicitly asks. Follow the
newest explicit status and preserve all saved task, run, ledger, and retrieval
evidence.

## Working Contract for Agent Sessions

- Start the active phase from its continuation prompt; do not invent a new
  phase, change its objective, or resume a superseded workflow.
- Do not consume budget on broad test loops, synthetic test generation, or
  repeated local-LLM retries. Run a command, test, or model request only when
  it is the smallest direct action required by the active phase's acceptance
  condition or an observed defect.
- Do not turn an uncertain model answer into a new implementation theory.
  Inspect the documented scope and existing evidence first; if retrieved
  evidence is insufficient, report that fact instead of widening the task.
- The connected sample project is read-only unless the active phase explicitly
  authorizes a controlled proposal workflow. Never browse its dependency tree,
  edit it, build it, run Gradle, or run Docker merely to explore or validate a
  hypothesis.
- Do not modify `runner.py`, `roles.json`, provider policy, task state, or
  codegen/reviewer orchestration while working on a read-only RAG/Q&A phase.
- Keep updates factual and concise. Record only observed results; do not claim
  a test, model answer, approval, validation, or phase closure that did not
  occur.

## Build, Test, and Development Commands

- `python -m pip install -r requirements.txt` installs default dependencies.
- `python -m unittest discover -s tests -t . -v` runs the deterministic test suite.
- `python -m unittest tests.sandbox.core.test_documentation_mode -v` runs a focused regression module; substitute the relevant fully-qualified test module as needed.
- `python -m ruff check .` runs static checks.
- `python evals_pipeline.py` runs the security evaluation pipeline.
- `uvicorn api:app --host 127.0.0.1 --port 8000` starts the loopback API.
- `docker compose --profile build-executor build` builds the isolated executor image.

Ollama/Chroma integration is opt-in. Set `MINI_AGENT_RUN_OFFLINE_INTEGRATION=1` before `python -m unittest tests.integration.local_ollama.test_offline_integration -v`; standard tests must not contact a model service. Set `MINI_AGENT_OFFLINE=1` to require local Ollama routing at runtime.

## Coding Style & Naming Conventions

Use four-space indentation and Python imports. Use `snake_case` for files, functions, variables, and helpers; `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants. Run Ruff before submitting. Do not weaken capability checks, path isolation, approval gates, output redaction, or Docker-validation boundaries.

## Testing Guidelines

Tests use `unittest`, with modules under `tests/<area>/test_<area>.py` and methods named `test_<behavior>`. `tests/sandbox/` covers the Sandbox itself, `tests/project_rag/` covers generic registered-project/RAG contracts, and `tests/integration/` contains explicitly bounded Docker or local-Ollama checks. `tests/fixtures/` contains only synthetic inputs; never place a connected project's source there. Add a focused regression test for every behavioral or security change. Prefer mocks and temporary directories; Docker tests may skip when Docker is unavailable.

## Commit & Pull Request Guidelines

The available history uses concise imperative summaries, for example `Initial commit: prepare project and translate to English`. Keep commits focused. PRs should describe behavior and security impact, reference issues when available, list commands run and results, and include API examples or screenshots for visible changes.

## Security & Configuration

Never commit vault files, credentials, model caches, generated state, or user data. Do not silently reset saved tasks or modify connected source projects during validation.
