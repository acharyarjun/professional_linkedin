"""Orchestrates market research, RAG, generation, and LinkedIn publishing."""

from __future__ import annotations

import json
import random
from datetime import date, datetime
from pathlib import Path
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

    def _today_in_timezone(self) -> date:
        tz = ZoneInfo(self._config.timezone)
        return datetime.now(tz).date()

    def _calendar_day_from_today(self) -> int:
        today = self._today_in_timezone()
        return calendar_slot_for_date(
            today,
            sequence_start=self._config.calendar_sequence_start,
        )

    def _calendar_days(self) -> list[int]:
        days = sorted({topic.day for topic in self._generator.calendar})
        if not days:
            raise ValueError("Calendar is empty")
        return days

    def _cursor_file_path(self) -> Path:
        return Path(self._config.publish_cursor_path)

    def _default_cursor_state(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "next_topic_index": 1,
            "topics_posted_lifetime": 0,
            "last_published_date": "",
        }

    def _is_pristine_cursor(self, state: dict[str, object]) -> bool:
        return (
            int(state["next_topic_index"]) == 1
            and int(state["topics_posted_lifetime"]) == 0
            and not state.get("last_published_date")
        )

    def _maybe_seed_cursor_from_calendar(self, state: dict[str, object]) -> dict[str, object]:
        if not self._config.use_publish_cursor:
            return state
        if not self._is_pristine_cursor(state):
            return state
        seq_start = self._config.calendar_sequence_start
        if seq_start is None:
            return state

        today = self._today_in_timezone()
        n_topics = len(self._calendar_days())
        expected = calendar_slot_for_date(
            today,
            sequence_start=seq_start,
            cycle_length=n_topics,
        )
        if expected <= 1:
            return state

        seeded = {
            "schema_version": 1,
            "next_topic_index": expected,
            "topics_posted_lifetime": int(state["topics_posted_lifetime"]),
            "last_published_date": state["last_published_date"],
        }
        self._save_cursor_state(seeded)
        logger.info(
            "Seeded publish cursor from CALENDAR_SEQUENCE_START: next_topic_index={} (was 1)",
            expected,
        )
        return seeded

    def _parse_cursor_raw(self, raw: dict[str, object]) -> dict[str, object]:
        n_topics = len(self._calendar_days())
        next_idx = raw.get("next_topic_index", 1)
        try:
            next_idx = int(next_idx)
        except (TypeError, ValueError):
            next_idx = 1
        if next_idx < 1 or next_idx > n_topics:
            next_idx = 1

        posted_total = raw.get("topics_posted_lifetime", 0)
        try:
            posted_total = int(posted_total)
        except (TypeError, ValueError):
            posted_total = 0
        if posted_total < 0:
            posted_total = 0

        last_date = raw.get("last_published_date", "")
        if not isinstance(last_date, str):
            last_date = ""

        return {
            "schema_version": 1,
            "next_topic_index": next_idx,
            "topics_posted_lifetime": posted_total,
            "last_published_date": last_date,
        }

    def _load_cursor_state(self) -> dict[str, object]:
        path = self._cursor_file_path()
        state = self._default_cursor_state()
        if not path.exists():
            self._save_cursor_state(state)
            return self._maybe_seed_cursor_from_calendar(state)

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Cursor file unreadable; resetting cursor: {}", exc)
            self._save_cursor_state(state)
            return self._maybe_seed_cursor_from_calendar(state)

        if not isinstance(raw, dict):
            logger.warning("Cursor file has invalid schema; resetting cursor")
            self._save_cursor_state(state)
            return self._maybe_seed_cursor_from_calendar(state)

        state = self._parse_cursor_raw(raw)
        return self._maybe_seed_cursor_from_calendar(state)

    def set_cursor(self, next_index: int) -> None:
        """Set the next topic index without auto-seeding from the calendar."""
        n_topics = len(self._calendar_days())
        if next_index < 1 or next_index > n_topics:
            raise ValueError(f"next_index must be 1..{n_topics}, got {next_index}")

        path = self._cursor_file_path()
        state = self._default_cursor_state()
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    state = self._parse_cursor_raw(raw)
            except (json.JSONDecodeError, OSError):
                pass

        state["next_topic_index"] = next_index
        self._save_cursor_state(state)
        logger.info("Publish cursor set: next_topic_index={}", next_index)

    def _save_cursor_state(self, state: dict[str, object]) -> None:
        path = self._cursor_file_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        tmp_path.replace(path)

    def _cursor_day_for_today(self, today: date) -> int:
        if not self._config.use_publish_cursor:
            return calendar_slot_for_date(
                today,
                sequence_start=self._config.calendar_sequence_start,
            )

        state = self._load_cursor_state()
        index = int(state["next_topic_index"])
        days = self._calendar_days()
        day = days[index - 1]
        logger.info(
            "Cursor policy: next_topic_index={} calendar_day={} posted_lifetime={}",
            index,
            day,
            state["topics_posted_lifetime"],
        )
        return day

    def _advance_cursor_after_publish(self, today: date) -> None:
        if not self._config.use_publish_cursor:
            return

        state = self._load_cursor_state()
        days = self._calendar_days()
        n_topics = len(days)
        current_index = int(state["next_topic_index"])
        next_index = (current_index % n_topics) + 1
        posted_total = int(state["topics_posted_lifetime"]) + 1
        updated = {
            "schema_version": 1,
            "next_topic_index": next_index,
            "topics_posted_lifetime": posted_total,
            "last_published_date": today.isoformat(),
        }
        self._save_cursor_state(updated)
        logger.info(
            "Cursor advanced: previous_index={} next_index={} last_published_date={}",
            current_index,
            next_index,
            today,
        )

    def _should_publish_today(self, today: date) -> bool:
        if not self._config.random_publish_twice_weekly:
            return True

        iso = today.isocalendar()
        week_key = f"{iso.year:04d}-W{iso.week:02d}"
        seed = f"{self._config.random_publish_seed}:{week_key}"
        rng = random.Random(seed)
        selected_days = sorted(
            rng.sample(list(range(7)), self._config.random_publish_days_per_week)
        )
        weekday = today.weekday()
        should_publish = weekday in selected_days
        logger.info(
            "Random weekly publish policy: week={} selected_weekdays={} today_weekday={} publish_today={}",
            week_key,
            selected_days,
            weekday,
            should_publish,
        )
        return should_publish

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
        today = self._today_in_timezone()
        if not self._should_publish_today(today):
            logger.info("Skipping publish for {} due to random twice-weekly schedule", today)
            return
        day = self._cursor_day_for_today(today)
        if self._run_pipeline_for_day(day):
            self._advance_cursor_after_publish(today)

    def run_once(self, day_number: Optional[int] = None) -> bool:
        """Run the pipeline for a specific calendar day or today's slot if None.

        Returns True on success or intentional skip; False when the pipeline fails.
        """
        if day_number is not None:
            day = int(day_number)
            return self._run_pipeline_for_day(day)

        today = self._today_in_timezone()
        if not self._should_publish_today(today):
            logger.info("Skipping publish for {} due to random twice-weekly schedule", today)
            return True

        day = self._cursor_day_for_today(today)
        if self._run_pipeline_for_day(day):
            self._advance_cursor_after_publish(today)
            return True
        return False

    def _run_pipeline_for_day(self, day: int) -> bool:
        logger.info("Starting pipeline for calendar day {}", day)
        try:
            topic = self._generator.get_topic_for_day(day)
        except Exception as exc:
            logger.exception("Failed to load topic: {}", exc)
            return False

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
            logger.exception("Duplicate check failed (stopping pipeline): {}", exc)
            return False

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
            return False

        try:
            result = self._publisher.publish_post(post_text)
        except Exception as exc:
            logger.exception("Publishing failed: {}", exc)
            return False

        try:
            self._rag.add_post(post_text, topic=topic.theme)
        except Exception as exc:
            logger.warning("Could not index published post in Chroma: {}", exc)

        logger.success(
            "Pipeline complete — day={} theme={!r} chars={} result={}",
            day,
            topic.theme,
            len(post_text),
            result,
        )
        return True
