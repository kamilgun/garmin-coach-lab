from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json_file(
    path: Path,
    default: Any = None,
) -> tuple[Any, dict[str, str] | None]:
    """
    Local JSON artifact'i güvenli şekilde okur.

    Returns:
        (data, None)
        veya
        (default, error_info)

    Eksik dosya hata değildir; default döner.
    Bozuk/okunamayan dosya kontrollü hata bilgisi üretir.
    """
    if not path.exists():
        return default, None

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file), None

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
    ) as exc:
        return (
            default,
            {
                "path": str(path),
                "filename": path.name,
                "error_type": type(exc).__name__,
                "message": str(exc),
            },
        )
