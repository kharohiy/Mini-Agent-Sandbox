import os
import json
from cryptography.fernet import Fernet

class VaultRegistry:
    _instance = None
    
    def __new__(cls, vault_path=".vault", key_path=".vault_key"):
        if cls._instance is None:
            cls._instance = super(VaultRegistry, cls).__new__(cls)
            cls._instance.vault_path = vault_path
            cls._instance.key_path = key_path
            cls._instance._init_encryption()
        return cls._instance

    def _init_encryption(self):
        """Initializes the Master Key for encryption/decryption."""
        if not os.path.exists(self.key_path):
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
        if not os.path.exists(self.vault_path):
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

# Singleton instantiation
vault = VaultRegistry()
