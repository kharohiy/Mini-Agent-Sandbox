"""Tenant-scoped encrypted vault persistence."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class VaultRegistry:
    """Encrypted mapping backed by one explicit vault/key file pair."""

    def __init__(self, vault_path: str | Path, key_path: str | Path):
        self.vault_path = Path(vault_path)
        self.key_path = Path(key_path)
        self._init_encryption()

    @staticmethod
    def _atomic_write(path: Path, data: bytes) -> None:
        """Replace one file without leaving a partially written destination."""
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
                temporary.write(data)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_name = temporary.name
            os.replace(temporary_name, path)
        finally:
            if temporary_name and os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def _init_encryption(self) -> None:
        vault_exists = self.vault_path.is_file()
        key_exists = self.key_path.is_file()
        if vault_exists and not key_exists:
            raise ValueError("Vault key is missing; refusing to replace an existing vault key.")
        if not key_exists:
            self.cipher_key = Fernet.generate_key()
            self._atomic_write(self.key_path, self.cipher_key)
            try:
                os.chmod(self.key_path, 0o400)
            except OSError:
                pass
        else:
            self.cipher_key = self.key_path.read_bytes()
        try:
            self.cipher = Fernet(self.cipher_key)
        except (TypeError, ValueError) as exc:
            raise ValueError("Vault key material is invalid.") from exc

    def _load_encrypted_vault(self) -> dict[str, str]:
        """Load one vault or fail closed without logging its contents."""
        if not self.vault_path.exists():
            return {}
        try:
            decrypted_data = self.cipher.decrypt(self.vault_path.read_bytes())
            mapping = json.loads(decrypted_data.decode("utf-8"))
        except (InvalidToken, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Vault data is unreadable.") from exc
        if not isinstance(mapping, dict) or not all(
            isinstance(token, str) and isinstance(value, str)
            for token, value in mapping.items()
        ):
            raise ValueError("Vault data has an invalid mapping shape.")
        return mapping

    def save_mapping(self, new_mapping: dict[str, str]) -> None:
        """Merge token mappings and atomically persist only changed data."""
        if not new_mapping:
            return
        if not all(isinstance(token, str) and isinstance(value, str) for token, value in new_mapping.items()):
            raise ValueError("Vault mappings must contain string tokens and values.")
        current_vault = self._load_encrypted_vault()
        updated = current_vault | new_mapping
        if updated != current_vault:
            self._atomic_write(self.vault_path, self.cipher.encrypt(json.dumps(updated).encode("utf-8")))

    def get_secret(self, token: str) -> str | None:
        """Retrieve one real secret by its opaque token."""
        return self._load_encrypted_vault().get(token)


def _pair_state(vault_path: Path, key_path: Path) -> str:
    vault_exists = vault_path.exists()
    key_exists = key_path.exists()
    if (vault_exists and not vault_path.is_file()) or (key_exists and not key_path.is_file()):
        return "invalid"
    if vault_exists != key_exists:
        return "incomplete"
    return "complete" if vault_exists else "absent"


def _reject_symlink(path: Path) -> None:
    if path.is_symlink():
        raise ValueError("Security Error: vault paths cannot be symlinks.")


def _copy_validated_legacy_pair(
    legacy_vault: Path,
    legacy_key: Path,
    canonical_vault: Path,
    canonical_key: Path,
) -> None:
    """Copy a validated same-tenant legacy pair; never delete its source."""
    VaultRegistry(legacy_vault, legacy_key)._load_encrypted_vault()
    VaultRegistry._atomic_write(canonical_key, legacy_key.read_bytes())
    try:
        os.chmod(canonical_key, 0o400)
    except OSError:
        pass
    VaultRegistry._atomic_write(canonical_vault, legacy_vault.read_bytes())


def _legacy_pair_is_compatible(
    legacy_vault: Path,
    legacy_key: Path,
    canonical_vault: Path,
    canonical_key: Path,
) -> bool:
    """Allow a canonical mapping that only extends the preserved legacy pair."""
    if legacy_key.read_bytes() != canonical_key.read_bytes():
        return False
    legacy_mapping = VaultRegistry(legacy_vault, legacy_key)._load_encrypted_vault()
    canonical_mapping = VaultRegistry(canonical_vault, canonical_key)._load_encrypted_vault()
    return all(canonical_mapping.get(token) == value for token, value in legacy_mapping.items())


def get_user_vault(user_id: str, base_dir: str | Path = "data") -> VaultRegistry:
    """Return the only supported tenant-scoped vault factory.

    Legacy hidden filenames are copied only when they form a valid complete
    pair and canonical files are absent. Both pairs are retained; disagreement
    is a fail-closed conflict, never an automatic merge or overwrite.
    """
    if not isinstance(user_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", user_id):
        raise ValueError("Invalid user_id: use 1-64 letters, digits, underscores, or hyphens.")

    base_path = Path(base_dir).resolve()
    user_dir = base_path / user_id
    _reject_symlink(user_dir)
    user_dir.mkdir(parents=True, exist_ok=True)
    resolved_user_dir = user_dir.resolve()
    try:
        resolved_user_dir.relative_to(base_path)
    except ValueError as exc:
        raise ValueError("Security Error: user vault escapes the data directory.") from exc

    canonical_vault = resolved_user_dir / "vault.enc"
    canonical_key = resolved_user_dir / "vault.key"
    legacy_vault = resolved_user_dir / ".vault"
    legacy_key = resolved_user_dir / ".vault_key"
    for path in (canonical_vault, canonical_key, legacy_vault, legacy_key):
        _reject_symlink(path)

    canonical_state = _pair_state(canonical_vault, canonical_key)
    legacy_state = _pair_state(legacy_vault, legacy_key)
    if "invalid" in {canonical_state, legacy_state}:
        raise ValueError("Vault paths must be regular files.")
    if canonical_state == "incomplete" or legacy_state == "incomplete":
        raise ValueError("Vault files are incomplete; refusing to create or replace a pair.")
    if canonical_state == "complete" and legacy_state == "complete":
        if not _legacy_pair_is_compatible(
            legacy_vault, legacy_key, canonical_vault, canonical_key,
        ):
            raise ValueError("Canonical and legacy vault pairs conflict.")
    elif canonical_state == "absent" and legacy_state == "complete":
        _copy_validated_legacy_pair(legacy_vault, legacy_key, canonical_vault, canonical_key)

    return VaultRegistry(canonical_vault, canonical_key)
