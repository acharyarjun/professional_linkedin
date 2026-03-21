"""End-to-end pipeline test: calendar → research (mocked) → RAG → generation (mocked) → LinkedIn dry-run."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config import AppConfig
from src.market_researcher import MarketResearcher, ResearchItem
from src.orchestrator import IndustrialAIOrchestrator
from src.post_generator import CalendarTopic, PostGenerator


def _fake_post_text() -> str:
    # Within generator bounds; five hashtags
    body = "x" * 1250 + " #a #b #c #d #e"
    assert 1200 <= len(body) <= 1800, len(body)
    return body


@pytest.fixture()
def pipeline_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AppConfig:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-used")
    monkeypatch.setenv("LINKEDIN_EMAIL", "test@example.com")
    monkeypatch.setenv("LINKEDIN_PASSWORD", "test-password")
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    root = Path(__file__).resolve().parent.parent
    monkeypatch.setenv("POST_CALENDAR_PATH", str(root / "data" / "post_calendar.csv"))
    return AppConfig()


def test_full_pipeline_dry_run_day1(
    monkeypatch: pytest.MonkeyPatch,
    pipeline_config: AppConfig,
) -> None:
    """Runs the same stages as `main.py --run-now --dry-run --day 1` without Gemini or HTTP."""
    pipeline_config.dry_run = True

    monkeypatch.setattr(
        MarketResearcher,
        "get_daily_insights",
        lambda self: [
            ResearchItem(
                title="Test headline",
                url="https://example.com/a",
                summary="Synthetic summary for pipeline test.",
                date="2099-01-01",
                source="test",
            )
        ],
    )

    def _fake_generate(self: PostGenerator, topic: CalendarTopic, market_insights: str = "") -> str:
        assert topic.day >= 1
        return _fake_post_text()

    monkeypatch.setattr(PostGenerator, "generate_post", _fake_generate)

    orch = IndustrialAIOrchestrator(pipeline_config)
    orch.run_once(1)


def test_full_pipeline_dry_run_today_slot(
    monkeypatch: pytest.MonkeyPatch,
    pipeline_config: AppConfig,
) -> None:
    pipeline_config.dry_run = True
    monkeypatch.setattr(MarketResearcher, "get_daily_insights", lambda self: [])

    def _fake_generate(self: PostGenerator, topic: CalendarTopic, market_insights: str = "") -> str:
        return _fake_post_text()

    monkeypatch.setattr(PostGenerator, "generate_post", _fake_generate)

    orch = IndustrialAIOrchestrator(pipeline_config)
    orch.run_daily_pipeline()
