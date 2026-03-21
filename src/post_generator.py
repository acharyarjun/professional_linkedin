"""Gemini-powered LinkedIn post generation from the editorial calendar."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import google.generativeai as genai
import pandas as pd
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import AppConfig

GEMINI_MODEL = "gemini-2.0-flash"


@dataclass(frozen=True)
class CalendarTopic:
    """One row from the 100-day post calendar."""

    day: int
    theme: str
    hook: str
    technical_angle: str
    hashtags: str


class PostGenerator:
    """Generates PhD-level LinkedIn posts using Gemini 1.5 Pro."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        genai.configure(api_key=config.gemini_api_key)
        self._model = genai.GenerativeModel(GEMINI_MODEL)
        self._calendar: List[CalendarTopic] = self._load_calendar(config.post_calendar_path)

    @property
    def calendar(self) -> List[CalendarTopic]:
        return list(self._calendar)

    def _load_calendar(self, path: str) -> List[CalendarTopic]:
        csv_path = Path(path)
        if not csv_path.is_file():
            raise FileNotFoundError(f"Post calendar not found: {csv_path}")
        df = pd.read_csv(csv_path)
        required = {"day", "theme", "hook", "technical_angle", "hashtags"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Calendar CSV missing columns: {sorted(missing)}")
        topics: List[CalendarTopic] = []
        for _, row in df.iterrows():
            topics.append(
                CalendarTopic(
                    day=int(row["day"]),
                    theme=str(row["theme"]).strip(),
                    hook=str(row["hook"]).strip(),
                    technical_angle=str(row["technical_angle"]).strip(),
                    hashtags=str(row["hashtags"]).strip(),
                )
            )
        topics.sort(key=lambda t: t.day)
        return topics

    def get_topic_for_day(self, day_number: int) -> CalendarTopic:
        """Return the calendar row for `day_number` in 1..100 (wraps if needed)."""
        if not self._calendar:
            raise ValueError("Calendar is empty")
        n = ((int(day_number) - 1) % len(self._calendar)) + 1
        for t in self._calendar:
            if t.day == n:
                return t
        raise ValueError(f"No topic for calendar day {n}")

    def _build_system_instructions(self) -> str:
        return (
            "You are Arjun Acharya, Port Automation & AI Engineer based in Bilbao, Spain, "
            "working at Prosertek. You write first-person LinkedIn thought leadership for peers "
            "in maritime and industrial automation.\n\n"
            "Expertise you may draw on authentically: vessel berthing systems, mooring automation, "
            "gangway safety, bollard inspection AI, BAS monitoring, Cavotec and Trelleborg marine "
            "solutions, Siemens / Omron / Allen-Bradley PLCs, TIA Portal, Sysmac Studio, "
            "CX Programmer, Docklight scripting, RS485/RS422/RS232 fieldbus, VFDs, soft starters, "
            "contactors, motor control centers, CAD and electrical diagram automation, Python and "
            "Azure applied to industrial AI, Coursera AI/ML coursework, and the informes.prosertek.com "
            "web platform.\n\n"
            "Tone: rigorous, reflective, practitioner-scholar — comparable to a strong PhD "
            "industrial engineer explaining field experience. No hype, no emojis, no bullet lists "
            "unless essential. Avoid naming yourself in third person.\n\n"
            "Hard constraints:\n"
            "- Length: 1200–1800 characters inclusive (count carefully).\n"
            "- Open with a concise personal or site hook tied to the given hook line.\n"
            "- Deliver technical depth aligned with the technical_angle.\n"
            "- Weave in at least one concrete signal from the market insights block when it is non-empty "
            "(paraphrase; do not paste URLs).\n"
            "- Close with a clear call to action (discussion, reflection, or follow).\n"
            "- End with exactly five relevant hashtags on one line, space-separated, each starting with #. "
            "Prefer a mix from the suggested hashtags plus topical ones.\n"
            "- Do not fabricate proprietary data; stay plausible for a Prosertek field engineer.\n"
        )

    def _build_user_prompt(
        self,
        topic: CalendarTopic,
        market_insights: str,
    ) -> str:
        suggested_tags = topic.hashtags
        return (
            f"Calendar day: {topic.day}\n"
            f"Theme: {topic.theme}\n"
            f"Hook to honour: {topic.hook}\n"
            f"Technical angle: {topic.technical_angle}\n"
            f"Suggested hashtags (adapt as needed): {suggested_tags}\n\n"
            "--- Market & news context (may be partial) ---\n"
            f"{market_insights.strip() or '(no external items today — rely on field expertise)'}\n"
            "---\n\n"
            "Write the LinkedIn post now. Output only the post text, no title line or preamble."
        )

    @retry(
        reraise=True,
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    def _generate_raw(self, prompt: str) -> str:
        full_prompt = f"{self._build_system_instructions()}\n\n{prompt}"
        response = self._model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.65,
                max_output_tokens=4096,
            ),
        )
        text = (getattr(response, "text", None) or "").strip()
        if not text and response.candidates:
            parts = response.candidates[0].content.parts
            text = "".join(getattr(p, "text", "") for p in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned empty post text")
        return text

    def _count_hashtags(self, text: str) -> int:
        return len(re.findall(r"#[\w\u0080-\uFFFF]+", text))

    def _trim_to_length(self, text: str, min_chars: int, max_chars: int) -> str:
        if min_chars <= len(text) <= max_chars:
            return text
        if len(text) > max_chars:
            return text[: max_chars - 1].rstrip() + "…"
        return text

    def generate_post(self, topic: CalendarTopic, market_insights: str = "") -> str:
        """Generate a single post for `topic`, optionally enriched with `market_insights` text."""
        user_prompt = self._build_user_prompt(topic, market_insights)
        raw = self._generate_raw(user_prompt)
        cleaned = raw.strip()
        if len(cleaned) < 1200:
            expand_prompt = (
                user_prompt
                + "\n\nThe previous draft was too short. Rewrite to 1200–1800 characters "
                "with deeper technical reasoning and a stronger closing CTA. Output only the post."
            )
            cleaned = self._generate_raw(expand_prompt).strip()
        if self._count_hashtags(cleaned) < 5:
            expand_prompt = (
                user_prompt
                + "\n\nEnsure exactly five hashtags at the end, one line, space-separated. "
                "Output only the full post."
            )
            cleaned = self._generate_raw(expand_prompt).strip()
        if len(cleaned) > 1800:
            cleaned = self._trim_to_length(cleaned, 1200, 1800)
        if len(cleaned) < 1200:
            logger.warning("Post still below 1200 chars after expansion; accepting best effort")
        return cleaned
