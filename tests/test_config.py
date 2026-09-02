from app.config import Settings


def test_default_settings_do_not_require_entra():
    settings = Settings()
    assert not hasattr(settings, "azure_openai_use_entra_id")
    assert settings.openai_base_url == "https://api.openai.com/v1"


def test_database_url_is_configurable():
    settings = Settings(database_url="postgresql+psycopg://user:pass@host/db")
    assert settings.database_url.startswith("postgresql+psycopg://")
