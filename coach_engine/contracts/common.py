from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping


CONTRACT_VALIDATOR_VERSION = "0.1.0"


class ArtifactContractError(ValueError):
    """
    Bir artifact yapısal veya semantik contract'ı ihlal ettiğinde oluşur.
    """

    def __init__(
        self,
        artifact: str,
        path: str,
        message: str,
    ) -> None:
        self.artifact = artifact
        self.path = path
        self.message = message
        super().__init__(
            f"{artifact} contract violation at {path}: {message}"
        )


def fail(
    artifact: str,
    path: str,
    message: str,
) -> None:
    raise ArtifactContractError(artifact, path, message)


def require_mapping(
    value: Any,
    *,
    artifact: str,
    path: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        fail(artifact, path, "object/dict olmalı.")
    return value


def require_list(
    value: Any,
    *,
    artifact: str,
    path: str,
) -> list[Any]:
    if not isinstance(value, list):
        fail(artifact, path, "list olmalı.")
    return value


def require_key(
    mapping: Mapping[str, Any],
    key: str,
    *,
    artifact: str,
    path: str,
) -> Any:
    if key not in mapping:
        fail(artifact, f"{path}.{key}", "zorunlu alan eksik.")
    return mapping[key]


def require_string(
    value: Any,
    *,
    artifact: str,
    path: str,
    allow_empty: bool = False,
) -> str:
    if not isinstance(value, str):
        fail(artifact, path, "string olmalı.")

    if not allow_empty and not value.strip():
        fail(artifact, path, "boş string olamaz.")

    return value


def require_bool(
    value: Any,
    *,
    artifact: str,
    path: str,
) -> bool:
    if not isinstance(value, bool):
        fail(artifact, path, "boolean olmalı.")
    return value


def require_int(
    value: Any,
    *,
    artifact: str,
    path: str,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        fail(artifact, path, "integer olmalı.")

    if minimum is not None and value < minimum:
        fail(
            artifact,
            path,
            f"{minimum} değerinden küçük olamaz.",
        )

    if maximum is not None and value > maximum:
        fail(
            artifact,
            path,
            f"{maximum} değerinden büyük olamaz.",
        )

    return value


def require_number(
    value: Any,
    *,
    artifact: str,
    path: str,
    minimum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        fail(artifact, path, "numeric olmalı.")

    numeric = float(value)

    if minimum is not None and numeric < minimum:
        fail(
            artifact,
            path,
            f"{minimum} değerinden küçük olamaz.",
        )

    return numeric


def require_literal(
    value: Any,
    allowed: set[str],
    *,
    artifact: str,
    path: str,
) -> str:
    normalized = require_string(
        value,
        artifact=artifact,
        path=path,
    )

    if normalized not in allowed:
        fail(
            artifact,
            path,
            "geçersiz değer. İzin verilenler: "
            + ", ".join(sorted(allowed)),
        )

    return normalized


def require_iso_date(
    value: Any,
    *,
    artifact: str,
    path: str,
) -> date:
    normalized = require_string(
        value,
        artifact=artifact,
        path=path,
    )

    try:
        return date.fromisoformat(normalized)
    except ValueError:
        fail(artifact, path, "YYYY-MM-DD ISO tarihi olmalı.")


def require_iso_datetime(
    value: Any,
    *,
    artifact: str,
    path: str,
) -> datetime:
    normalized = require_string(
        value,
        artifact=artifact,
        path=path,
    )

    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        fail(artifact, path, "geçerli ISO datetime olmalı.")


def validate_optional_metadata_strings(
    artifact_data: Mapping[str, Any],
    fields: tuple[str, ...],
    *,
    artifact: str,
    path: str = "$",
) -> None:
    for field in fields:
        value = artifact_data.get(field)

        if value is None:
            continue

        require_string(
            value,
            artifact=artifact,
            path=f"{path}.{field}",
        )


def validate_duration(
    value: Any,
    *,
    artifact: str,
    path: str,
) -> Mapping[str, Any]:
    duration = require_mapping(
        value,
        artifact=artifact,
        path=path,
    )

    target = require_int(
        require_key(
            duration,
            "target_min",
            artifact=artifact,
            path=path,
        ),
        artifact=artifact,
        path=f"{path}.target_min",
        minimum=1,
    )
    minimum = require_int(
        require_key(
            duration,
            "min",
            artifact=artifact,
            path=path,
        ),
        artifact=artifact,
        path=f"{path}.min",
        minimum=1,
    )
    maximum = require_int(
        require_key(
            duration,
            "max",
            artifact=artifact,
            path=path,
        ),
        artifact=artifact,
        path=f"{path}.max",
        minimum=1,
    )

    if not minimum <= target <= maximum:
        fail(
            artifact,
            path,
            "min <= target_min <= max ilişkisi sağlanmalı.",
        )

    if "binding_max" in duration:
        require_bool(
            duration["binding_max"],
            artifact=artifact,
            path=f"{path}.binding_max",
        )

    return duration


def validate_string_list(
    value: Any,
    *,
    artifact: str,
    path: str,
) -> list[str]:
    values = require_list(
        value,
        artifact=artifact,
        path=path,
    )

    for index, item in enumerate(values):
        require_string(
            item,
            artifact=artifact,
            path=f"{path}[{index}]",
        )

    return values
