import json
import tempfile
from pathlib import Path

from coach_engine.artifact_io import (
    load_json_file,
)


def run_tests():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # 1. Missing artifact is not an error.
        missing = root / "missing.json"

        data, error = load_json_file(
            missing,
            default={"fallback": True},
        )

        assert data == {"fallback": True}
        assert error is None

        # 2. Valid JSON loads normally.
        valid = root / "valid.json"

        valid.write_text(
            json.dumps(
                {
                    "status": "ready",
                    "session_count": 2,
                }
            ),
            encoding="utf-8",
        )

        data, error = load_json_file(
            valid,
            default=None,
        )

        assert error is None
        assert data["status"] == "ready"
        assert data["session_count"] == 2

        # 3. Malformed JSON falls back safely.
        broken = root / "broken.json"

        broken.write_text(
            '{"status": "ready", broken',
            encoding="utf-8",
        )

        data, error = load_json_file(
            broken,
            default=None,
        )

        assert data is None
        assert error is not None
        assert error["filename"] == "broken.json"
        assert error["error_type"] == "JSONDecodeError"

        # 4. Broken artifact respects supplied default.
        data, error = load_json_file(
            broken,
            default={"fallback": True},
        )

        assert data == {"fallback": True}
        assert error is not None

        # 5. A directory cannot masquerade as JSON.
        directory = root / "directory.json"
        directory.mkdir()

        data, error = load_json_file(
            directory,
            default=None,
        )

        assert data is None
        assert error is not None
        assert error["error_type"] in {
            "IsADirectoryError",
            "OSError",
        }

    print("All artifact IO tests passed.")


if __name__ == "__main__":
    run_tests()
