import os
from dataclasses import dataclass
from pathlib import Path

from .profile_workspace import ProfileWorkspace


ENV_PROFILE_ID = "GARMIN_COACH_PROFILE_ID"
ENV_DATA_DIR = "GARMIN_COACH_DATA_DIR"
ENV_ATHLETE_PROFILE_PATH = "GARMIN_COACH_ATHLETE_PROFILE_PATH"
ENV_GARMIN_TOKENSTORE = "GARMIN_COACH_TOKENSTORE"


@dataclass(frozen=True)
class RuntimeWorkspace:
    """
    Runtime paths used by pipeline scripts.

    With no environment overrides this preserves the legacy local layout:

        data/
        athlete_profile.json
        ~/.garminconnect

    Profile-aware execution injects isolated paths through environment
    variables. This keeps pipeline scripts independent from how identity
    is resolved.
    """

    profile_id: str | None
    data_dir: Path
    athlete_profile_path: Path
    garmin_tokenstore: Path

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


def get_runtime_workspace() -> RuntimeWorkspace:
    """
    Resolve runtime paths.

    Environment variables are used by profile-aware pipeline execution.
    Without them the existing single-profile layout remains intact.
    """

    profile_id = os.getenv(ENV_PROFILE_ID) or None

    data_dir = Path(
        os.getenv(
            ENV_DATA_DIR,
            "data",
        )
    ).expanduser()

    athlete_profile_path = Path(
        os.getenv(
            ENV_ATHLETE_PROFILE_PATH,
            "athlete_profile.json",
        )
    ).expanduser()

    garmin_tokenstore = Path(
        os.getenv(
            ENV_GARMIN_TOKENSTORE,
            str(Path.home() / ".garminconnect"),
        )
    ).expanduser()

    return RuntimeWorkspace(
        profile_id=profile_id,
        data_dir=data_dir,
        athlete_profile_path=athlete_profile_path,
        garmin_tokenstore=garmin_tokenstore,
    )


def build_profile_runtime_env(
    workspace: ProfileWorkspace,
) -> dict[str, str]:
    """
    Build environment overrides for a profile-aware pipeline process.
    """

    return {
        ENV_PROFILE_ID: workspace.profile_id,
        ENV_DATA_DIR: str(workspace.data_dir),
        ENV_ATHLETE_PROFILE_PATH: str(
            workspace.athlete_profile_path
        ),
        ENV_GARMIN_TOKENSTORE: str(
            workspace.garmin_tokenstore
        ),
    }