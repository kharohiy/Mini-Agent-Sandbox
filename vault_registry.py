import os
import json
import re
from pathlib import Path
from cryptography.fernet import Fernet

class VaultRegistry:
    def __init__(self, vault_path, key_path):
        self.vault_path = Path(vault_path)
        self.key_path = Path(key_path)
        self._init_encryption()

    def _init_encryption(self):
        """Initializes the Master Key for encryption/decryption."""
        if not self.key_path.exists():
            self.cipher_key = Fernet.generate_key()
            with open(self.key_path, "wb") as f:
                f.write(self.cipher_key)
            # Strict permissions on the key file (read-only for owner)
            try:
                os.chmod(self.key_path, 0o400)
            except Exception:
                pass # Windows fallback
        else:
            with open(self.key_path, "rb") as f:
                self.cipher_key = f.read()
                
        self.cipher = Fernet(self.cipher_key)

    def _load_encrypted_vault(self) -> dict:
        """Loads and decrypts the vault mapping."""
        if not self.vault_path.exists():
            return {}
            
        try:
            with open(self.vault_path, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode("utf-8"))
        except Exception as e:
            print(f"[Vault] ⚠️ Failed to load/decrypt vault: {e}")
            return {}

    def save_mapping(self, new_mapping: dict):
        """Merges new tokens with existing and saves the encrypted vault."""
        if not new_mapping:
            return
            
        current_vault = self._load_encrypted_vault()
        
        # Merge new mappings
        updated = False
        for token, real_val in new_mapping.items():
            if current_vault.get(token) != real_val:
                current_vault[token] = real_val
                updated = True
                
        if updated:
            json_data = json.dumps(current_vault).encode("utf-8")
            encrypted_data = self.cipher.encrypt(json_data)
            with open(self.vault_path, "wb") as f:
                f.write(encrypted_data)

    def get_secret(self, token: str) -> str:
        """Retrieves a real secret by its token."""
        current_vault = self._load_encrypted_vault()
        return current_vault.get(token)

def get_user_vault(user_id: str, base_dir="data") -> VaultRegistry:
    """Return a vault isolated to one validated tenant workspace."""
    if not isinstance(user_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", user_id):
        raise ValueError("Invalid user_id: use 1-64 letters, digits, underscores, or hyphens.")

    base_path = Path(base_dir).resolve()
    user_dir = base_path / user_id
    if user_dir.is_symlink():
        raise ValueError("Security Error: user vault directory cannot be a symlink.")
    user_dir.mkdir(parents=True, exist_ok=True)
    resolved_user_dir = user_dir.resolve()
    try:
        resolved_user_dir.relative_to(base_path)
    except ValueError as exc:
        raise ValueError("Security Error: user vault escapes the data directory.") from exc

    return VaultRegistry(resolved_user_dir / ".vault", resolved_user_dir / ".vault_key")
