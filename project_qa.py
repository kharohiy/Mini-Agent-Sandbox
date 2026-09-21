"""Read-only local Analyst → Reviewer Q&A over a registered project RAG corpus."""

from __future__ import annotations

import argparse
import json

from model_router import TaskClass
from project_retrieval import retrieve_global_technical_references, retrieve_project_context
from runner import safe_llm_completion


def ask_project(project_id: str, question: str, *, include_technical_reference: bool = False) -> dict[str, object]:
    hits = retrieve_project_context(
        project_id,
        question,
        top_k=4,
        prefer_exact_sources=True,
    )
    evidence = [hit for hit in hits if hit.get("scope") == "project-code"]
    if not evidence:
        raise ValueError("No project-code RAG evidence was found for this question.")

    context = "\n\n".join(
        f"SOURCE: {hit['source']}\n{hit['text']}" for hit in evidence
    )
    technical_references = (
        retrieve_global_technical_references(project_id, question, top_k=2)
        if include_technical_reference
        else []
    )
    technical_context = "\n\n".join(
        f"SOURCE: {hit['source']}\n{hit['text']}" for hit in technical_references
    )
    reference_block = (
        f"\n\nTECHNICAL REFERENCE (explanation only; never evidence of a project fact):\n{technical_context}"
        if technical_context
        else ""
    )
    analyst = safe_llm_completion(
        "ollama/qwen2.5:14b",
        [
            {
                "role": "system",
                "content": (
                    "You are a read-only project Analyst. Answer only from the supplied RAG evidence. "
                    "Project facts require project evidence and its source path. Optional technical references "
                    "may explain a concept but never establish a project fact. Do not propose code, tools, "
                    "source changes, or tests."
                ),
            },
            {"role": "user", "content": f"QUESTION: {question}\n\nPROJECT EVIDENCE:\n{context}{reference_block}"},
        ],
        user_id="project_qa",
        project_id=project_id,
        task_class=TaskClass.PLANNING,
        max_tokens=200,
        temperature=0,
    )
    analyst_answer = analyst.choices[0].message.content or ""
    reviewer = safe_llm_completion(
        "ollama/qwen2.5:14b",
        [
            {
                "role": "system",
                "content": (
                    "You are a read-only project Reviewer. Correct the Analyst answer using only supplied RAG evidence. "
                    "A technical reference may explain a concept but cannot support a project fact. Return a concise "
                    "factual answer; do not propose code, tools, source changes, or tests."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"QUESTION: {question}\n\nANALYST ANSWER:\n{analyst_answer}"
                    f"\n\nPROJECT EVIDENCE:\n{context}{reference_block}"
                ),
            },
        ],
        user_id="project_qa",
        project_id=project_id,
        task_class=TaskClass.REVIEW,
        max_tokens=200,
        temperature=0,
    )
    return {
        "project_id": project_id,
        "question": question,
        "sources": [hit["source"] for hit in evidence],
        "project_evidence": [
            {
                "project_id": project_id,
                "scope": "project-code",
                "source": hit["source"],
                "sha256": hit.get("sha256", ""),
            }
            for hit in evidence
        ],
        "technical_references": [hit["source"] for hit in technical_references],
        "analyst": analyst_answer,
        "reviewer": reviewer.choices[0].message.content or "",
    }


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
    print(json.dumps(ask_project(
        args.project_id,
        question,
        include_technical_reference=args.technical_reference,
    ), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
