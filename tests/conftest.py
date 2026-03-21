import pytest


@pytest.fixture(autouse=True)
def _test_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("LINKEDIN_EMAIL", "test@example.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD", "test-password")
    monkeypatch.setenv("LINKEDIN_ACCESS_TOKEN", "test-oauth-token")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", "./data/chroma_test")
    monkeypatch.setenv("POST_CALENDAR_PATH", "./data/post_calendar.csv")
