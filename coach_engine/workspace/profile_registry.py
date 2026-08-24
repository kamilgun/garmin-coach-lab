import json
from dataclasses import dataclass
from pathlib import Path

from .profile_workspace import normalize_profile_id


DEFAULT_PROFILE_REGISTRY_PATH = Path("profiles.local.json")


@dataclass(frozen=True)
class ProfileDefinition:
    profile_id: str
    display_name: str
    enabled: bool = True


def load_profile_registry(
    path: Path | str = DEFAULT_PROFILE_REGISTRY_PATH,
) -> list[ProfileDefinition]:
    registry_path = Path(path)

    if not registry_path.exists():
        raise FileNotFoundError(
            f"Profile registry not found: {registry_path}"
        )

    with registry_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if payload.get("schema_version") != "1.0":
        raise ValueError(
            "Unsupported profile registry schema_version"
        )

    raw_profiles = payload.get("profiles")

    if not isinstance(raw_profiles, list) or not raw_profiles:
        raise ValueError(
            "Profile registry must contain at least one profile"
        )

    profiles = []
    seen_ids = set()

    for item in raw_profiles:
        if not isinstance(item, dict):
            raise ValueError("Each profile must be an object")

        profile_id = normalize_profile_id(
            str(item.get("id", ""))
        )

        display_name = str(
            item.get("display_name", "")
        ).strip()

        if not display_name:
            raise ValueError(
                f"display_name is required for profile '{profile_id}'"
            )

        if profile_id in seen_ids:
            raise ValueError(
                f"Duplicate profile id: {profile_id}"
            )

        seen_ids.add(profile_id)

        profiles.append(
            ProfileDefinition(
                profile_id=profile_id,
                display_name=display_name,
                enabled=bool(item.get("enabled", True)),
            )
        )

    return profiles


def get_enabled_profiles(
    path: Path | str = DEFAULT_PROFILE_REGISTRY_PATH,
) -> list[ProfileDefinition]:
    return [
        profile
        for profile in load_profile_registry(path)
        if profile.enabled
    ]