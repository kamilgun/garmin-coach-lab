from dataclasses import dataclass
from pathlib import Path
import re


DEFAULT_PRIVATE_ROOT = Path.home() / ".garmin-coach-lab"


def normalize_profile_id(profile_id: str) -> str:
    """
    Convert a profile/user identifier into a safe local workspace key.

    This is intentionally independent from display names so that
    future authenticated user IDs can be used without changing
    the rest of the application.
    """
    value = profile_id.strip().lower()

    if not value:
        raise ValueError("profile_id cannot be empty")

    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value):
        raise ValueError(
            "profile_id may contain only lowercase letters, "
            "numbers, '-' and '_'"
        )

    return value


@dataclass(frozen=True)
class ProfileWorkspace:
    profile_id: str
    repo_root: Path
    private_root: Path

    @property
    def profile_dir(self) -> Path:
        return self.repo_root / "profiles" / self.profile_id

    @property
    def data_dir(self) -> Path:
        return self.profile_dir / "data"

    @property
    def athlete_profile_path(self) -> Path:
        return self.profile_dir / "athlete_profile.json"

    @property
    def manual_context_path(self) -> Path:
        return self.data_dir / "manual_context.json"

    @property
    def activity_summary_path(self) -> Path:
        return self.data_dir / "activity_summary.json"

    @property
    def performance_summary_path(self) -> Path:
        return self.data_dir / "performance_summary.json"

    @property
    def coach_context_path(self) -> Path:
        return self.data_dir / "coach_context.json"

    @property
    def session_candidates_path(self) -> Path:
        return self.data_dir / "session_candidates.json"

    @property
    def session_selection_path(self) -> Path:
        return self.data_dir / "session_selection.json"

    @property
    def weekly_plan_path(self) -> Path:
        return self.data_dir / "weekly_plan.json"

    @property
    def weekly_review_path(self) -> Path:
        return self.data_dir / "weekly_review.md"

    @property
    def llm_coach_prompt_path(self) -> Path:
        return self.data_dir / "llm_coach_prompt.md"

    @property
    def coach_message_path(self) -> Path:
        return self.data_dir / "coach_message.md"

    @property
    def feedback_log_path(self) -> Path:
        return self.data_dir / "feedback_log.jsonl"

    @property
    def garmin_tokenstore(self) -> Path:
        return (
            self.private_root
            / "profiles"
            / self.profile_id
            / "garmin"
        )

    def ensure_directories(self) -> None:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.garmin_tokenstore.mkdir(parents=True, exist_ok=True)


def get_profile_workspace(
    profile_id: str,
    *,
    repo_root: Path | str = ".",
    private_root: Path | str | None = None,
) -> ProfileWorkspace:
    normalized_id = normalize_profile_id(profile_id)

    resolved_repo_root = Path(repo_root).resolve()

    resolved_private_root = (
        Path(private_root).expanduser().resolve()
        if private_root is not None
        else DEFAULT_PRIVATE_ROOT
    )

    return ProfileWorkspace(
        profile_id=normalized_id,
        repo_root=resolved_repo_root,
        private_root=resolved_private_root,
    )