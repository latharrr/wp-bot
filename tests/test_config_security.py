from app.core.config import Settings


def test_detects_all_placeholder_secrets():
    settings = Settings(_env_file=None)
    insecure = settings.insecure_defaults_still_in_use()
    assert set(insecure) == {
        "API_KEY",
        "JWT_SECRET",
        "WHATSAPP_INTERNAL_TOKEN",
        "WHATSAPP_BRIDGE_CONTROL_TOKEN",
    }


def test_no_warnings_once_all_secrets_are_real():
    settings = Settings(
        _env_file=None,
        api_key="a-real-random-value",
        jwt_secret="another-real-random-value",
        whatsapp_internal_token="yet-another-real-value",
        whatsapp_bridge_control_token="and-another-real-value",
    )
    assert settings.insecure_defaults_still_in_use() == []


def test_flags_only_the_secrets_left_at_default():
    settings = Settings(
        _env_file=None,
        api_key="a-real-random-value",
        jwt_secret="another-real-random-value",
        whatsapp_internal_token="yet-another-real-value",
        # whatsapp_bridge_control_token left at its default
    )
    assert settings.insecure_defaults_still_in_use() == ["WHATSAPP_BRIDGE_CONTROL_TOKEN"]


def test_cors_wildcard_passthrough():
    settings = Settings(_env_file=None, cors_allowed_origins="*")
    assert settings.cors_allowed_origin_list == ["*"]


def test_cors_parses_comma_separated_origins():
    settings = Settings(_env_file=None, cors_allowed_origins="https://a.example.com, https://b.example.com")
    assert settings.cors_allowed_origin_list == ["https://a.example.com", "https://b.example.com"]
