from ai.config import settings


def test_settings_load():
    assert settings.app_env == "development"
