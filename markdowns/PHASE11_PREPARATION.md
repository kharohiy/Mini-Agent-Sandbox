# Phase 11 Preparation — Reproducible dependency manifests

## Status

Completed on 2026-09-20. Phases 9 and 10 are complete.

## Observed baseline

- `requirements.txt` lists only LiteLLM, Ruff, Semgrep, FastAPI, and Uvicorn.
- Runtime imports also require ChromaDB, Cryptography, and optional FlashRank.
- PDF ingestion separately imports `pymupdf4llm` and
  `langchain-text-splitters`; an existing `requirements-ingest.txt` is not a
  complete inherited runtime manifest.
- Dependency declarations must describe current code without downloading,
  upgrading, or changing provider/model behavior.

## Objective

Make a fresh environment's dependency contract inspectable and reproducible by
separating runtime, PDF-ingestion, and development/test dependencies. Preserve
the existing `requirements.txt` entry point as a compatible runtime install
path or document any intentional replacement.

## First bounded increment

1. Audit direct third-party imports and current installed package versions.
2. Classify every direct dependency as runtime, ingestion-only, or development
   tooling.
3. Define a minimal manifest layout such as `requirements-runtime.txt`,
   `requirements-ingest.txt`, and `requirements-dev.txt`.
4. Add deterministic tests that assert required direct imports are declared in
   their intended manifest and optional paths are documented.

## Hard boundaries

- Do not install, upgrade, download, remove, or lock packages during planning.
- Do not change Python source behavior, model routing, Ollama models, Chroma
  data, Android source, Docker, Gradle, vaults, or saved phase evidence.
- Do not add a dependency merely because an LLM suggests it; every entry must
  map to a direct import or an explicitly documented tool contract.
- Do not run broad suites or external-network dependency resolution.

## Exit condition

The manifest layout accounts for every direct third-party import, preserves the
runtime installation entry point, and has focused regression tests. Any actual
fresh-environment installation check requires separate user authorization
because it downloads and changes external package state.

## Completion record — 2026-09-20

- Added `requirements-runtime.txt` for direct application dependencies and
  `requirements-dev.txt` for existing Ruff/Semgrep tooling.
- `requirements-ingest.txt` now inherits the pinned runtime and adds only PDF
  ingestion dependencies.
- `requirements.txt` remains the backward-compatible default entry point and
  inherits runtime plus the pre-existing development tooling.
- Pinned versions match the observed working environment; no package was
  installed, upgraded, removed, downloaded, or resolved from the network.
- `test_dependency_manifests.py` verifies runtime ownership, ingestion
  inheritance, and the compatible default entry point. Ruff passed; 3/3
  focused tests passed.

Phase 11 is complete. A clean-environment installation remains deliberately
unperformed and requires separate user authorization.
