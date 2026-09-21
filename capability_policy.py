import json
from pathlib import Path


class CapabilityDenied(PermissionError):
    pass


class CapabilityPolicy:
    def __init__(self, manifest_path="capabilities.json"):
        with open(Path(manifest_path), "r", encoding="utf-8") as manifest_file:
            self.manifest = json.load(manifest_file)
        self._capabilities = {
            capability
            for permissions in self.manifest.get("modes", {}).values()
            for capability in permissions
        }

    def is_allowed(self, mode: str, capability: str) -> bool:
        # Never permit an undeclared capability, even if a future manifest's
        # default is changed accidentally.
        if capability not in self._capabilities:
            return False
        return self.manifest.get("modes", {}).get(mode, {}).get(
            capability, self.manifest.get("default", "deny")
        ) == "allow"

    def require(self, mode: str, capability: str) -> None:
        if not self.is_allowed(mode, capability):
            raise CapabilityDenied(
                f"Security Error: capability '{capability}' is denied in mode '{mode}'."
            )
