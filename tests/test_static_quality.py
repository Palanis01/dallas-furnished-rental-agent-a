from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE_FILES = [p for p in (ROOT / "app").rglob("*.py")]
WORKFLOW_FILES = list((ROOT / ".github").rglob("*.yml"))
TEXT_FILES = SOURCE_FILES + WORKFLOW_FILES


def all_source_text():
    return "\n".join(p.read_text(errors="ignore") for p in TEXT_FILES)


def test_no_entra_dependency_or_configuration():
    text = all_source_text()
    forbidden = ["DefaultAzureCredential", "AZURE_TENANT_ID", "AZURE_CLIENT_ID", "azure/login@v2"]
    assert not any(item in text for item in forbidden)


def test_no_legacy_fastapi_startup_pattern():
    text = (ROOT / "app" / "main.py").read_text()
    assert "@app.on_event" not in text
    assert "lifespan=" in text


def test_no_legacy_openai_preview_web_search():
    text = all_source_text()
    assert "web_search_preview" not in text
