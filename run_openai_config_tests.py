from coach_engine.openai_config import (
    require_openai_api_key,
    validate_openai_api_key,
)


def run_tests():
    # 1. Missing key.
    valid, error = validate_openai_api_key(
        None
    )
    assert valid is False
    assert "tanımlı değil" in error

    # 2. Empty key.
    valid, error = validate_openai_api_key(
        "   "
    )
    assert valid is False
    assert "boş" in error

    # 3. README/example placeholder.
    valid, error = validate_openai_api_key(
        "your_openai_api_key_here"
    )
    assert valid is False
    assert "placeholder" in error

    # 4. Old placeholder variant.
    valid, error = validate_openai_api_key(
        "your_openai_key_here"
    )
    assert valid is False

    # 5. Generic placeholder.
    valid, error = validate_openai_api_key(
        "replace_me"
    )
    assert valid is False

    # 6. Non-placeholder value passes local validation.
    valid, error = validate_openai_api_key(
        "test-valid-config-value"
    )
    assert valid is True
    assert error is None

    # 7. require helper returns stripped value.
    value = require_openai_api_key(
        "  test-valid-config-value  "
    )
    assert value == "test-valid-config-value"

    # 8. require helper raises safely and does not
    # expose the supplied value.
    secret = "your_openai_api_key_here"

    try:
        require_openai_api_key(secret)
        raise AssertionError(
            "RuntimeError bekleniyordu."
        )
    except RuntimeError as exc:
        message = str(exc)
        assert "placeholder" in message
        assert secret not in message

    print("All OpenAI config tests passed.")


if __name__ == "__main__":
    run_tests()
