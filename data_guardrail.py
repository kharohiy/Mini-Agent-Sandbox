import hashlib
import json
import os
import re
from datetime import datetime, timezone

from prompt_injection import PromptInjectionBoundary
from secret_scanner import DetectorRule, SecretScanner


def log_guardrail_telemetry(user_id, rule_name, layer, matched_text_length):
    if not user_id:
        return
    telemetry_file = os.path.join("data", user_id, "telemetry.json")
    os.makedirs(os.path.dirname(telemetry_file), exist_ok=True)
    try:
        if os.path.exists(telemetry_file):
            with open(telemetry_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        else:
            data = []
    except Exception:
        data = []
    data.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "guardrail_triggered",
        "rule": rule_name,
        "layer": layer,
        "matched_length": matched_text_length,
    })
    with open(telemetry_file, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


class DataGuardrail:
    """Compatibility facade for local secret/PII masking and limited markup handling."""

    def __init__(self, config_path="guardrail_config.json"):
        self.__vault_registries = {}
        self.scanner = SecretScanner(self._load_external_rules(config_path))
        self.prompt_boundary = PromptInjectionBoundary()

    @staticmethod
    def _load_external_rules(config_path):
        if not os.path.exists(config_path):
            return []
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                configured = json.load(file)
            return [
                DetectorRule(rule["name"], "external-regex", re.compile(rule["regex"]), "medium")
                for rule in configured
                if isinstance(rule, dict) and isinstance(rule.get("name"), str)
                and isinstance(rule.get("regex"), str)
            ]
        except Exception as error:
            print(f"[Guardrail] Failed to load external config: {type(error).__name__}")
            return []

    def context_check(self, text: str, match, rule) -> tuple[bool, str]:
        """Legacy compatibility helper; structured scanning owns new context checks."""
        context_words = rule.get("context_words", [])
        if not context_words:
            return True, "Regex"
        window = text[max(0, match.start() - 50):min(len(text), match.end() + 50)].lower()
        return (True, "Legacy context") if any(word in window for word in context_words) else (False, "")

    def _generate_vault_token(self, rule_name: str, real_value: str, user_id: str) -> str:
        value_hash = hashlib.sha256(real_value.encode("utf-8")).hexdigest()[:8].upper()
        token = f"__VAULT_SECRET_{rule_name}_{value_hash}__"
        self.__vault_registries.setdefault(user_id, {})[token] = real_value
        return token

    def run(self, text: str, user_id: str = "system") -> str:
        """Sanitize legacy markup, then redact structured secret/PII findings once."""
        if not text:
            return ""
        sanitized = self.prompt_boundary.sanitize_untrusted_markup(text)
        for finding in reversed(self.scanner.scan(sanitized)):
            real_value = sanitized[finding.start:finding.end]
            token = self._generate_vault_token(finding.kind, real_value, user_id)
            log_guardrail_telemetry(user_id, finding.kind, finding.detector, finding.length)
            sanitized = sanitized[:finding.start] + token + sanitized[finding.end:]
        return sanitized.strip()

    def extract_vault_mapping(self, user_id: str) -> dict:
        return self.__vault_registries.get(user_id, {}).copy()


guardrail = DataGuardrail()
