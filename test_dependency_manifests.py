import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def manifest_entries(name: str, seen: set[str] | None = None) -> set[str]:
    seen = seen or set()
    if name in seen:
        raise ValueError(f"requirements include cycle: {name}")
    seen.add(name)
    entries: set[str] = set()
    for raw in (ROOT / name).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("-r "):
            entries.update(manifest_entries(line.removeprefix("-r ").strip(), seen))
        else:
            entries.add(line.split("==", 1)[0])
    return entries


class DependencyManifestTests(unittest.TestCase):
    def test_runtime_covers_direct_application_imports(self):
        runtime = manifest_entries("requirements-runtime.txt")
        self.assertEqual(
            runtime,
            {"litellm", "fastapi", "pydantic", "uvicorn", "chromadb", "cryptography", "flashrank"},
        )

    def test_ingestion_inherits_runtime_and_adds_only_pdf_dependencies(self):
        runtime = manifest_entries("requirements-runtime.txt")
        ingestion = manifest_entries("requirements-ingest.txt")
        self.assertTrue(runtime.issubset(ingestion))
        self.assertEqual(ingestion - runtime, {"pymupdf4llm", "langchain-text-splitters"})

    def test_default_entry_point_preserves_runtime_and_existing_dev_tools(self):
        default = manifest_entries("requirements.txt")
        self.assertTrue(manifest_entries("requirements-runtime.txt").issubset(default))
        self.assertTrue({"ruff", "semgrep"}.issubset(default))


if __name__ == "__main__":
    unittest.main()
