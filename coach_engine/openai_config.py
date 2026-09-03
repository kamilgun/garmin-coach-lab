from __future__ import annotations

from typing import Optional


PLACEHOLDER_VALUES = {
    "your_openai_api_key_here",
    "your_openai_key_here",
    "replace_me",
    "replace-with-your-key",
    "changeme",
    "change_me",
}


def validate_openai_api_key(
    value: Optional[str],
) -> tuple[bool, str | None]:
    """
    OPENAI_API_KEY için yalnızca local config doğrulaması yapar.

    Gerçek API erişimini test etmez ve key değerini hiçbir zaman
    hata mesajına yazmaz.
    """
    if value is None:
        return (
            False,
            "OPENAI_API_KEY tanımlı değil.",
        )

    normalized = value.strip()

    if not normalized:
        return (
            False,
            "OPENAI_API_KEY boş.",
        )

    lowered = normalized.lower()

    if (
        lowered in PLACEHOLDER_VALUES
        or lowered.startswith("your_openai")
        or "placeholder" in lowered
    ):
        return (
            False,
            "OPENAI_API_KEY placeholder değer içeriyor. "
            "Geçerli bir API key tanımla.",
        )

    return True, None


def require_openai_api_key(
    value: Optional[str],
) -> str:
    valid, error = validate_openai_api_key(
        value
    )

    if not valid:
        raise RuntimeError(
            error
            or "OPENAI_API_KEY geçerli değil."
        )

    assert value is not None
    return value.strip()
