"""Register a project and create its isolated snapshot without modifying source."""
from __future__ import annotations

import argparse
import json

from project_indexer import index_project
from project_registry import ProjectRegistry


def register_and_index(
    source_path: str,
    display_name: str | None = None,
    *,
    description: str = "",
    repository_url: str | None = None,
    configured_ref: str = "",
    resolved_revision: str = "",
) -> dict:
    registry = ProjectRegistry()
    project = registry.register(
        source_path,
        display_name,
        description=description,
        source_kind="git" if repository_url else "local",
        source_uri=repository_url,
        configured_ref=configured_ref,
        resolved_revision=resolved_revision,
    )
    report = index_project(project["source_path"], registry.state_dir(project["id"]) / "snapshot")
    return {"project": project, "index": report.__dict__}


def main() -> None:
    parser = argparse.ArgumentParser(description="Register and index a project without changing its source")
    parser.add_argument("source_path")
    parser.add_argument("--name")
    parser.add_argument("--description", default="")
    parser.add_argument("--repository-url")
    parser.add_argument("--ref", dest="configured_ref", default="")
    parser.add_argument("--resolved-revision", default="")
    arguments = parser.parse_args()
    print(json.dumps(register_and_index(
        arguments.source_path,
        arguments.name,
        description=arguments.description,
        repository_url=arguments.repository_url,
        configured_ref=arguments.configured_ref,
        resolved_revision=arguments.resolved_revision,
    ), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
