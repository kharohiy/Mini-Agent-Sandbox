"""Read-only local Analyst → Reviewer Q&A over a registered project RAG corpus."""

from __future__ import annotations

import argparse
import json
import sys

from ollama_runtime import unload_ollama_models
from project_qa_service import ProjectQaError, ProjectQaService


def ask_project(project_id: str, question: str, *, include_technical_reference: bool = False) -> dict[str, object]:
    from runner import safe_llm_completion

    return ProjectQaService(completion=safe_llm_completion).ask(
        project_id,
        question,
        include_technical_reference=include_technical_reference,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_id")
    parser.add_argument(
        "question",
        nargs="*",
    )
    parser.add_argument(
        "--technical-reference",
        action="store_true",
        help="add shared library excerpts as explanation-only context after project evidence",
    )
    args = parser.parse_args()
    question = " ".join(args.question) or "Does the project define a Scaffold?"
    try:
        result = ask_project(
            args.project_id,
            question,
            include_technical_reference=args.technical_reference,
        )
    except ProjectQaError as error:
        print(f"Project Q&A failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except Exception:
        print("Project Q&A failed due to an internal error; no answer was produced.", file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        unload_ollama_models(announce=False)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
