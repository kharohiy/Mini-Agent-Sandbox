"""Register a project and create its isolated snapshot without modifying source."""
from __future__ import annotations

import argparse
import json

from project_indexer import index_project
from project_registry import ProjectRegistry


def register_and_index(source_path: str, display_name: str | None = None) -> dict:
    registry = ProjectRegistry()
    project = registry.register(source_path, display_name)
    report = index_project(project["source_path"], registry.state_dir(project["id"]) / "snapshot")
    return {"project": project, "index": report.__dict__}


def main() -> None:
    parser = argparse.ArgumentParser(description="Register and index a project without changing its source")
    parser.add_argument("source_path")
    parser.add_argument("--name")
    arguments = parser.parse_args()
    print(json.dumps(register_and_index(arguments.source_path, arguments.name), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
