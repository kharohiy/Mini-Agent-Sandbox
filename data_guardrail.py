import re
import os
import json
import hashlib
from datetime import datetime, timezone

def log_guardrail_telemetry(user_id, rule_name, layer, matched_text_length):
    if not user_id: return
    telemetry_file = os.path.join("data", user_id, "telemetry.json")
    os.makedirs(os.path.dirname(telemetry_file), exist_ok=True)
    
    try:
        if os.path.exists(telemetry_file):
            with open(telemetry_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
    except Exception:
        data = []
        
    data.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "guardrail_triggered",
        "rule": rule_name,
        "layer": layer,
        "matched_length": matched_text_length
    })
    
    with open(telemetry_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class DataGuardrail:
    def __init__(self, config_path="guardrail_config.json"):
        # Private In-Memory Vault Registry (Name mangling prevents accidental outer access)
        self.__vault_registry = {}
        
        # Layer 1: Pattern Recognition Rules
        self.rules = [
            {
                "name": "API_KEY",
                "regex": re.compile(r'\bsk-[a-zA-Z0-9]{32,64}\b'),
                "context_words": ["bearer", "api", "key", "token", "secret", "authorization"]
            },
            {
                "name": "EMAIL",
                "regex": re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'),
                "context_words": []
            },
            {
                "name": "IPV4",
                "regex": re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'),
                "context_words": []
            },
            {
                "name": "AWS_KEY",
                "regex": re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
                "context_words": []
            },
            {
                "name": "AWS_SECRET",
                "regex": re.compile(r'\b[0-9a-zA-Z/+]{40}\b'),
                "context_words": ["aws", "secret", "key", "access", "credentials"]
            }
        ]
        
        # Load external config if exists to make it configurable
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    external_rules = json.load(f)
                    for er in external_rules:
                        er["regex"] = re.compile(er["regex"])
                        self.rules.append(er)
            except Exception as e:
                print(f"[Guardrail] ⚠️ Failed to load external config: {e}")

        # Basic tags sanitizer
        self.system_tags_regex = re.compile(r"<(image|script|system)[^>]*>.*?</\1>", flags=re.IGNORECASE | re.DOTALL)

    def context_check(self, text: str, match, rule) -> tuple[bool, str]:
        """Layer 2: Contextual Heuristics Validation"""
        context_words = rule.get("context_words", [])
        if not context_words:
            return True, "Layer 1 (Regex)"  

        window_size = 50
        start = max(0, match.start() - window_size)
        end = min(len(text), match.end() + window_size)
        window_text = text[start:end].lower()

        for word in context_words:
            if word in window_text:
                return True, f"Layer 2 (Context: {word})"
                
        return False, ""

    def _generate_vault_token(self, rule_name: str, real_value: str) -> str:
        """Generates a strict unique token and registers it in the private Vault."""
        # Deterministic short hash avoids duplicates and keeps tokens concise
        val_hash = hashlib.sha256(real_value.encode('utf-8')).hexdigest()[:8].upper()
        token = f"__VAULT_SECRET_{rule_name}_{val_hash}__"
        
        # Store in private registry
        self.__vault_registry[token] = real_value
        return token

    def run(self, text: str, user_id: str = "system") -> str:
        """Executes the 3-Layer pipeline with Tokenization (Two-Way Obfuscation)."""
        if not text:
            return ""

        # Pre-filter malicious tags
        text = self.system_tags_regex.sub("", text)

        def make_replacer(rule):
            def replacer(match):
                is_valid, layer_info = self.context_check(text, match, rule)
                if is_valid:
                    real_value = match.group(0)
                    token = self._generate_vault_token(rule["name"], real_value)
                    
                    log_guardrail_telemetry(user_id, rule["name"], layer_info, len(real_value))
                    print(f"[Guardrail] 🛡️ Tokenized {rule['name']} via {layer_info}. Token: {token}")
                    return token
                return match.group(0)
            return replacer

        for rule in self.rules:
            text = rule["regex"].sub(make_replacer(rule), text)

        return text.strip()
        
    def extract_vault_mapping(self) -> dict:
        """
        Controlled Proxy for the Interceptor.
        Returns a hard copy of the registry to prevent memory reference leaks.
        """
        return self.__vault_registry.copy()

# Global singleton instance for easy import
guardrail = DataGuardrail()
