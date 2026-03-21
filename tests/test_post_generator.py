"""Tests for PostGenerator."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.config import AppConfig
from src.post_generator import CalendarTopic, PostGenerator


@pytest.fixture()
def config() -> AppConfig:
    return AppConfig()


@pytest.fixture()
def sample_topic() -> CalendarTopic:
    return CalendarTopic(
        day=1,
        theme="Test theme",
        hook="A hook from the field",
        technical_angle="PLC interlocks and BAS signals",
        hashtags="#Automation #Ports #Test #PLC #Safety",
    )


def test_calendar_topic_loads_from_csv(config: AppConfig) -> None:
    gen = PostGenerator(config)
    assert len(gen.calendar) >= 1
    first = gen.calendar[0]
    assert first.day == 1
    assert first.theme


def test_generate_post_returns_string(config: AppConfig, sample_topic: CalendarTopic) -> None:
    fake_response = MagicMock()
    fake_response.text = "x" * 1250 + " #" + " #t2 #t3 #t4 #t5"
    fake_model = MagicMock()
    fake_model.generate_content.return_value = fake_response

    with patch("src.post_generator.genai.GenerativeModel", return_value=fake_model):
        gen = PostGenerator(config)
        out = gen.generate_post(sample_topic, market_insights="News: test item")
        assert isinstance(out, str)
        assert len(out) > 0
        fake_model.generate_content.assert_called()


def test_post_length_within_bounds(config: AppConfig, sample_topic: CalendarTopic) -> None:
    body = "y" * 1300
    fake_response = MagicMock()
    fake_response.text = body + " #a #b #c #d #e"
    fake_model = MagicMock()
    fake_model.generate_content.return_value = fake_response

    with patch("src.post_generator.genai.GenerativeModel", return_value=fake_model):
        gen = PostGenerator(config)
        out = gen.generate_post(sample_topic)
        assert 1200 <= len(out) <= 1800


def test_post_contains_hashtags(config: AppConfig, sample_topic: CalendarTopic) -> None:
    text = "Intro " * 200
    fake_response = MagicMock()
    fake_response.text = text[:1300] + " #one #two #three #four #five"
    fake_model = MagicMock()
    fake_model.generate_content.return_value = fake_response

    with patch("src.post_generator.genai.GenerativeModel", return_value=fake_model):
        gen = PostGenerator(config)
        out = gen.generate_post(sample_topic)
        assert out.count("#") >= 5


def test_retry_on_api_failure(config: AppConfig, sample_topic: CalendarTopic) -> None:
    fake_model = MagicMock()
    fail = MagicMock()
    fail.text = ""
    fail.candidates = []
    ok = MagicMock()
    ok.text = "z" * 1250 + " #h1 #h2 #h3 #h4 #h5"
    fake_model.generate_content.side_effect = [RuntimeError("timeout"), ok]

    with patch("src.post_generator.genai.GenerativeModel", return_value=fake_model):
        gen = PostGenerator(config)
        out = gen.generate_post(sample_topic)
        assert "z" in out
        assert fake_model.generate_content.call_count >= 2
