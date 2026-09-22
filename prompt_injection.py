"""Compatibility-only boundary for untrusted markup, separate from secret masking."""

from __future__ import annotations

import re


class PromptInjectionBoundary:
    """Removes legacy paired tags without claiming general injection defence."""

    _legacy_untrusted_markup = re.compile(
        r"<(image|script|system)[^>]*>.*?</\1>", flags=re.IGNORECASE | re.DOTALL
    )

    def sanitize_untrusted_markup(self, text: str) -> str:
        return self._legacy_untrusted_markup.sub("", text)
