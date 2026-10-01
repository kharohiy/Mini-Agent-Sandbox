"""Small Ollama lifecycle operations shared by CLI entry points."""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path


ROLES_FILE = Path(__file__).with_name("roles.json")


def _configured_ollama_models() -> list[str]:
    try:
        configuration = json.loads(ROLES_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        configuration = {}
    if not isinstance(configuration, dict):
        configuration = {}
    models = set()
    for section in (configuration.get("agents", {}), configuration.get("project_qa", {})):
        if not isinstance(section, dict):
            continue
        for role in section.values():
            if not isinstance(role, dict):
                continue
            candidates = [role.get("model")]
            routing = role.get("routing", {})
            if isinstance(routing, dict):
                fallbacks = routing.get("fallback_models", [])
                if isinstance(fallbacks, (list, tuple)):
                    candidates.extend(fallbacks)
            for candidate in candidates:
                if isinstance(candidate, str) and candidate.startswith("ollama/"):
                    model = candidate.removeprefix("ollama/").strip()
                    if model:
                        models.add(model)
    models.add("nomic-embed-text:latest")
    return sorted(models)


def unload_ollama_models(*, announce: bool = True) -> None:
    if announce:
        print("\n[System] Clearing VRAM from local Ollama models...")
    for model in _configured_ollama_models():
        try:
            payload = json.dumps({"model": model, "keep_alive": 0}).encode("utf-8")
            request = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(request, timeout=5)
            if announce:
                print(f"[System] Model {model} successfully unloaded from memory.")
        except Exception:
            pass
