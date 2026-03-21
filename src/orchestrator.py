"""Orchestrates market research, RAG, generation, and LinkedIn publishing."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from loguru import logger
from zoneinfo import ZoneInfo

from .config import AppConfig
from .linkedin_publisher import LinkedInPublisher
from .market_researcher import MarketResearcher, ResearchItem
from .post_generator import PostGenerator
from .rag_engine import RAGEngine


def calendar_slot_for_date(
    today: date,
    *,
    sequence_start: Optional[date] = None,
    cycle_length: int = 100,
) -> int:
    """Return calendar row ``1..cycle_length`` for ``today``.

    If ``sequence_start`` is set, day 1 is that calendar date and each midnight step
    advances the row (wrapping after ``cycle_length``). If unset, uses day-of-year
    mapped to ``1..cycle_length`` — this does **not** depend on how many times the
    workflow ran.
    """
    if cycle_length < 1:
        raise ValueError("cycle_length must be >= 1")
    if sequence_start is not None:
        delta = (today - sequence_start).days
        if delta < 0:
            return 1
        return (delta % cycle_length) + 1
    doy = int(today.timetuple().tm_yday)
    return (doy - 1) % cycle_length + 1


class IndustrialAIOrchestrator:
    """End-to-end daily pipeline for Industrial AI Content Factory."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._generator = PostGenerator(config)
        self._researcher = MarketResearcher()
        self._rag = RAGEngine(config)
        self._publisher = LinkedInPublisher(config)

    def _calendar_day_from_today(self) -> int:
        tz = ZoneInfo(self._config.timezone)
        today = datetime.now(tz).date()
        return calendar_slot_for_date(
            today,
            sequence_start=self._config.calendar_sequence_start,
        )

    def _format_insights_for_prompt(self, items: list[ResearchItem]) -> str:
        lines: list[str] = []
        for it in items[:12]:
            line = f"- [{it.source}] {it.title} ({it.date})"
            if it.summary:
                line += f" — {it.summary[:240]}"
            lines.append(line)
        return "\n".join(lines)

    def run_daily_pipeline(self) -> None:
        """Execute the full daily workflow using today's calendar slot (wraps to CSV length)."""
        day = self._calendar_day_from_today()
        self._run_pipeline_for_day(day)

    def run_once(self, day_number: Optional[int] = None) -> None:
        """Run the pipeline for a specific calendar day or today's slot if None."""
        day = int(day_number) if day_number is not None else self._calendar_day_from_today()
        self._run_pipeline_for_day(day)

    def _run_pipeline_for_day(self, day: int) -> None:
        logger.info("Starting pipeline for calendar day {}", day)
        try:
            topic = self._generator.get_topic_for_day(day)
        except Exception as exc:
            logger.exception("Failed to load topic: {}", exc)
            return

        try:
            insights = self._researcher.get_daily_insights()
        except Exception as exc:
            logger.warning("Market research degraded: {}", exc)
            insights = []

        for item in insights:
            try:
                self._rag.add_market_insight(item)
            except Exception as exc:
                logger.warning("Could not index market item: {}", exc)

        rag_insights = self._rag.get_relevant_insights(topic.theme, n=3)
        insights_text = self._format_insights_for_prompt(insights)
        if rag_insights:
            extra = "\n".join(
                f"- (RAG) {row.get('text', '')[:400]}" for row in rag_insights
            )
            insights_text = f"{insights_text}\n\nRetrieved context:\n{extra}"

        duplicate = False
        try:
            duplicate = self._rag.topic_already_posted(topic.theme)
        except Exception as exc:
            logger.warning("Duplicate check failed (continuing): {}", exc)

        if duplicate:
            logger.warning(
                "Similar topic found in post history — requesting a distinct angle from the model"
            )
            insights_text += (
                "\n\nConstraint: Prior coverage exists for this theme. Differentiate with a new "
                "angle, site anecdote, or instrumentation detail; avoid repeating prior phrasing."
            )

        try:
            post_text = self._generator.generate_post(topic, market_insights=insights_text)
        except Exception as exc:
            logger.exception("Post generation failed: {}", exc)
            return

        try:
            self._rag.add_post(post_text, topic=topic.theme)
        except Exception as exc:
            logger.warning("Could not index generated post in Chroma: {}", exc)

        try:
            result = self._publisher.publish_post(post_text)
        except Exception as exc:
            logger.exception("Publishing failed: {}", exc)
            return

        logger.success(
            "Pipeline complete — day={} theme={!r} chars={} result={}",
            day,
            topic.theme,
            len(post_text),
            result,
        )
