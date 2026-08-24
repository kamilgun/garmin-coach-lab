from pathlib import Path
from tempfile import TemporaryDirectory

from coach_engine.workspace import (
    get_profile_workspace,
    normalize_profile_id,
)


def test_normalize_profile_id():
    assert normalize_profile_id("kamil") == "kamil"
    assert normalize_profile_id(" Burcu ") == "burcu"
    assert normalize_profile_id("user_123") == "user_123"
    assert normalize_profile_id("usr-abc123") == "usr-abc123"


def test_invalid_profile_id():
    invalid_values = [
        "",
        "   ",
        "../kamil",
        "kamil/gun",
        "kamil gün",
        "/tmp/test",
    ]

    for value in invalid_values:
        try:
            normalize_profile_id(value)
        except ValueError:
            pass
        else:
            raise AssertionError(
                f"Expected ValueError for profile_id={value!r}"
            )


def test_profile_isolation():
    with TemporaryDirectory() as repo_tmp, TemporaryDirectory() as private_tmp:
        repo_root = Path(repo_tmp).resolve()
        private_root = Path(private_tmp).resolve()

        kamil = get_profile_workspace(
            "kamil",
            repo_root=repo_root,
            private_root=private_root,
        )

        burcu = get_profile_workspace(
            "burcu",
            repo_root=repo_root,
            private_root=private_root,
        )

        assert kamil.data_dir != burcu.data_dir
        assert kamil.weekly_plan_path != burcu.weekly_plan_path
        assert kamil.garmin_tokenstore != burcu.garmin_tokenstore


def test_expected_paths():
    with TemporaryDirectory() as repo_tmp, TemporaryDirectory() as private_tmp:
        repo_root = Path(repo_tmp).resolve()
        private_root = Path(private_tmp).resolve()

        workspace = get_profile_workspace(
            "kamil",
            repo_root=repo_root,
            private_root=private_root,
        )

        assert workspace.profile_dir == repo_root / "profiles" / "kamil"
        assert (
            workspace.weekly_plan_path
            == repo_root
            / "profiles"
            / "kamil"
            / "data"
            / "weekly_plan.json"
        )

        assert (
            workspace.garmin_tokenstore
            == private_root
            / "profiles"
            / "kamil"
            / "garmin"
        )


def test_directory_creation():
    with TemporaryDirectory() as repo_tmp, TemporaryDirectory() as private_tmp:
        workspace = get_profile_workspace(
            "kamil",
            repo_root=repo_tmp,
            private_root=private_tmp,
        )

        workspace.ensure_directories()

        assert workspace.profile_dir.exists()
        assert workspace.data_dir.exists()
        assert workspace.garmin_tokenstore.exists()


if __name__ == "__main__":
    test_normalize_profile_id()
    test_invalid_profile_id()
    test_profile_isolation()
    test_expected_paths()
    test_directory_creation()

    print("All profile workspace tests passed.")