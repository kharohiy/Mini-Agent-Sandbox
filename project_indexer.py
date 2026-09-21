"""Read-only incremental project inventory for Android/Kotlin repositories.

The indexed project is never modified. SQLite and JSON snapshots are stored in
the agent workspace (or an explicitly supplied output directory).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


INDEX_VERSION = 1
ALLOWED_SUFFIXES = {".kt", ".java", ".gradle", ".kts", ".xml", ".md"}
ALLOWED_NAMES = {"settings.gradle", "settings.gradle.kts", "gradle.properties"}
IGNORED_DIRECTORIES = {".git", ".gradle", ".idea", "build", "node_modules", ".mini-agent"}
SYMBOL_PATTERN = re.compile(
    r"^\s*(?:(?:public|private|protected|internal|open|abstract|final|data|sealed|"
    r"enum|annotation|inline|suspend|override|operator|infix|tailrec|external)\s+)*"
    r"(?P<kind>class|interface|object|fun|enum\s+class|record)\s+(?P<name>[A-Za-z_]\w*)",
    re.MULTILINE,
)


@dataclass(frozen=True)
class IndexReport:
    project: str
    database: str
    snapshot: str
    indexed: int
    unchanged: int
    removed: int
    modules: int
    symbols: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _default_output(project: Path) -> Path:
    key = hashlib.sha256(str(project).encode("utf-8")).hexdigest()[:16]
    return Path(__file__).resolve().parent / "data" / "project_snapshots" / key


def _is_indexable(path: Path) -> bool:
    return path.name in ALLOWED_NAMES or path.suffix.lower() in ALLOWED_SUFFIXES


def _iter_files(project: Path):
    for path in project.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        relative = path.relative_to(project)
        if any(part in IGNORED_DIRECTORIES for part in relative.parts[:-1]):
            continue
        if _is_indexable(path):
            yield path


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _extract_modules(project: Path) -> list[str]:
    settings = next((project / name for name in ("settings.gradle.kts", "settings.gradle") if (project / name).is_file()), None)
    if not settings:
        return [":"]
    text = _read_text(settings)
    modules = {":"}
    for match in re.finditer(r"include\s*(?:\(|\s)([^\n)]*)", text):
        for quoted in re.findall(r"[\"'](:[^\"']+)[\"']", match.group(1)):
            modules.add(quoted)
    return sorted(modules)


def _gradle_details(project: Path, modules: list[str]) -> dict:
    details = {"plugins": {}, "modules": {}}
    for build_file in project.rglob("*.gradle*"):
        if not build_file.is_file() or build_file.is_symlink():
            continue
        if any(part in IGNORED_DIRECTORIES for part in build_file.relative_to(project).parts[:-1]):
            continue
        text = _read_text(build_file)
        relative = build_file.relative_to(project)
        for plugin, kotlin_plugin, version in re.findall(r"(?:id\s*\(?\s*[\"']([^\"']+)[\"']\s*\)?|kotlin\s*\(\s*[\"']([^\"']+)[\"']\s*\))\s*version\s*[\"']([^\"']+)", text):
            details["plugins"][plugin or f"kotlin:{kotlin_plugin}"] = version
        module = _module_for(relative, modules)
        if module not in details["modules"]:
            details["modules"][module] = {"build_file": relative.as_posix(), "sdk": {}, "dependencies": [], "source_roots": []}
        record = details["modules"][module]
        for name, value in re.findall(r"\b(compileSdk|minSdk|targetSdk)\s*(?:=\s*)?(\d+)", text):
            record["sdk"][name] = int(value)
        record["dependencies"] = sorted(set(re.findall(r"project\s*\(?\s*[\"'](:[^\"')]+)", text)))
    for module in modules:
        directory = project if module == ":" else project / module.lstrip(":").replace(":", "/")
        record = details["modules"].setdefault(module, {"build_file": None, "sdk": {}, "dependencies": [], "source_roots": []})
        for source_root in ("src/main/java", "src/main/kotlin", "src/test/java", "src/test/kotlin", "src/androidTest/java", "src/androidTest/kotlin"):
            if (directory / source_root).is_dir():
                record["source_roots"].append(source_root)
    return details


def _module_for(relative: Path, modules: list[str]) -> str:
    candidates = sorted((module for module in modules if module != ":"), key=len, reverse=True)
    value = relative.as_posix()
    for module in candidates:
        directory = module.lstrip(":").replace(":", "/")
        if value == directory or value.startswith(f"{directory}/"):
            return module
    return ":"


def _language(path: Path) -> str:
    return {
        ".kt": "kotlin", ".java": "java", ".gradle": "gradle", ".kts": "gradle-kotlin", ".xml": "xml", ".md": "markdown",
    }.get(path.suffix.lower(), "properties")


def _symbols(text: str, language: str):
    if language not in {"kotlin", "java"}:
        return []
    package = re.search(r"^\s*package\s+([\w.]+)", text, re.MULTILINE)
    package_name = package.group(1) if package else ""
    results = []
    for found in SYMBOL_PATTERN.finditer(text):
        line = text.count("\n", 0, found.start()) + 1
        results.append((package_name, found.group("kind"), found.group("name"), line))
    return results


def _imports(text: str, language: str):
    if language not in {"kotlin", "java"}:
        return []
    return re.findall(r"^\s*import\s+(?:static\s+)?([\w.*]+)", text, re.MULTILINE)


def _connect(database: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS files (
          path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, language TEXT NOT NULL,
          module TEXT NOT NULL, is_test INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS symbols (
          file_path TEXT NOT NULL REFERENCES files(path) ON DELETE CASCADE,
          package_name TEXT NOT NULL, kind TEXT NOT NULL, name TEXT NOT NULL, line INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS relations (
          source_path TEXT NOT NULL REFERENCES files(path) ON DELETE CASCADE,
          relation TEXT NOT NULL, target TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS symbols_name_idx ON symbols(name);
        CREATE INDEX IF NOT EXISTS relations_source_idx ON relations(source_path);
        """
    )
    return connection


def index_project(project_path: str | Path, output_path: str | Path | None = None) -> IndexReport:
    project = Path(project_path).resolve()
    if not project.is_dir() or project.is_symlink():
        raise ValueError("project must be an existing non-symlink directory")
    output = Path(output_path).resolve() if output_path else _default_output(project)
    output.mkdir(parents=True, exist_ok=True)
    database = output / "project_snapshot.sqlite"
    snapshot = output / "snapshot.json"
    modules = _extract_modules(project)
    gradle = _gradle_details(project, modules)
    existing_paths: set[str]
    indexed = unchanged = 0
    with _connect(database) as connection:
        existing = dict(connection.execute("SELECT path, sha256 FROM files"))
        current_paths = set()
        for path in _iter_files(project):
            relative = path.relative_to(project).as_posix()
            current_paths.add(relative)
            digest = _sha256(path)
            if existing.get(relative) == digest:
                unchanged += 1
                continue
            indexed += 1
            text = _read_text(path)
            language = _language(path)
            module = _module_for(Path(relative), modules)
            is_test = int("/src/test/" in f"/{relative}" or "/src/androidTest/" in f"/{relative}")
            connection.execute("DELETE FROM files WHERE path = ?", (relative,))
            connection.execute(
                "INSERT INTO files(path, sha256, language, module, is_test) VALUES (?, ?, ?, ?, ?)",
                (relative, digest, language, module, is_test),
            )
            connection.executemany(
                "INSERT INTO symbols(file_path, package_name, kind, name, line) VALUES (?, ?, ?, ?, ?)",
                [(relative, *symbol) for symbol in _symbols(text, language)],
            )
            connection.executemany(
                "INSERT INTO relations(source_path, relation, target) VALUES (?, 'imports', ?)",
                [(relative, item) for item in _imports(text, language)],
            )
        removed = len(set(existing) - current_paths)
        for missing in set(existing) - current_paths:
            connection.execute("DELETE FROM files WHERE path = ?", (missing,))
        metadata = {
            "index_version": str(INDEX_VERSION), "project": str(project),
            "indexed_at": datetime.now(timezone.utc).isoformat(), "modules": json.dumps(modules),
            "gradle": json.dumps(gradle, sort_keys=True),
        }
        connection.executemany("INSERT OR REPLACE INTO metadata(key, value) VALUES (?, ?)", metadata.items())
        file_count = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        symbol_count = connection.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
    connection.close()
    snapshot.write_text(json.dumps({"project": str(project), "modules": modules, "gradle": gradle,
        "files": file_count, "symbols": symbol_count, "index_version": INDEX_VERSION}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return IndexReport(str(project), str(database), str(snapshot), indexed, unchanged, removed, len(modules), symbol_count)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a read-only Android project snapshot")
    parser.add_argument("project")
    parser.add_argument("--output", help="Directory for SQLite/JSON snapshot; default is agent data directory")
    arguments = parser.parse_args()
    print(json.dumps(asdict(index_project(arguments.project, arguments.output)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
