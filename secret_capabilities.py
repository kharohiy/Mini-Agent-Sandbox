"""Default-deny secret resolution for explicitly trusted tool parameters."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from vault_registry import VaultRegistry, get_user_vault


TOKEN_PATTERN = re.compile(r"__VAULT_SECRET_[A-Z0-9_]+__")


@dataclass(frozen=True)
class SecretCapability:
    """Permission to resolve Vault tokens for one exact tool parameter."""

    tool_name: str
    parameter_name: str


PRODUCTION_SECRET_CAPABILITIES: frozenset[SecretCapability] = frozenset()


def resolve_capability_arguments(
    tool_name: str,
    arguments: Mapping[str, object],
    user_id: str,
    *,
    capabilities: frozenset[SecretCapability] = PRODUCTION_SECRET_CAPABILITIES,
    vault_factory: Callable[[str], VaultRegistry] | None = None,
) -> dict[str, object]:
    """Resolve tokens only for exact, capability-bearing string parameters.

    No capability means no Vault lookup. Nested values, lists, paths, file
    content, and arbitrary strings are intentionally left unchanged.
    """
    resolved = dict(arguments)
    allowed_parameters = {
        capability.parameter_name
        for capability in capabilities
        if capability.tool_name == tool_name
    }
    if not allowed_parameters:
        return resolved

    vault: VaultRegistry | None = None
    for parameter_name in allowed_parameters:
        value = resolved.get(parameter_name)
        if not isinstance(value, str) or "__VAULT_SECRET_" not in value:
            continue
        if vault is None:
            vault = (vault_factory or get_user_vault)(user_id)
        resolved[parameter_name] = TOKEN_PATTERN.sub(
            lambda match: vault.get_secret(match.group(0)) or match.group(0),
            value,
        )
    return resolved
