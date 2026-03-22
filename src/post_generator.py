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

GEMINI_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class CalendarTopic:
    """One row from the post calendar CSV."""

    day: int
    theme: str
    hook: str
    technical_angle: str
    hashtags: str


class PostGenerator:
    """Generates LinkedIn posts in a neutral, expert, systems-thinking voice."""

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
        """Return the calendar row for `day_number` (wraps to loaded calendar length)."""
        if not self._calendar:
            raise ValueError("Calendar is empty")

        n = ((int(day_number) - 1) % len(self._calendar)) + 1

        for t in self._calendar:
            if t.day == n:
                return t

        raise ValueError(f"No topic for calendar day {n}")

    def _build_system_instructions(self) -> str:
        return (
            "You are a Port Automation & AI Engineer with hands-on field experience in maritime "
            "and industrial environments. You write in first person as an independent practitioner "
            "sharing insights with peers in port operations, automation, and engineering.\n\n"

            "Your expertise includes: vessel berthing systems, mooring automation, gangway safety, "
            "bollard inspection AI, berthing aided systems (laser docking, speed/distance measurement), "
            "PLC-based control systems, industrial communication protocols (RS485/RS422/RS232), "
            "motor control systems, electrical design, and applied AI in industrial environments.\n\n"

            "Tone: rigorous, reflective, practitioner-scholar. Write like an experienced engineer "
            "explaining real-world systems. No hype, no marketing language, no emojis.\n\n"

            "CRITICAL BEHAVIORAL RULES:\n"
            "- Remain vendor-neutral and solution-agnostic.\n"
            "- Do NOT promote, endorse, or criticize any company, brand, or product.\n"
            "- Do NOT mention employers or affiliations.\n"
            "- Focus on engineering principles, system behavior, and operational realities.\n"
            "- If referencing technology, describe it generically (e.g., 'PLC-based system').\n"
            "- When referring to BAS, interpret it as Berthing Aided Systems used in port operations.\n"
            "- Emphasize trade-offs, constraints, and failure modes.\n\n"

            "Output format — NotebookLM-style infographic digest:\n"
            "- Line 1: a single punchy hook (no label).\n"
            "- Blank line.\n"
            "- Then 4–6 sections.\n"
            "- Each section starts with an ALL CAPS header (3–6 words).\n"
            "- Each section contains 1–3 short lines (~90 chars max).\n"
            "- Optional micro-bullets using '• ' (max 6 total).\n"
            "- One idea per section.\n"
            "- Blank line between sections.\n"
            "- One short closing CTA line.\n"
            "- Blank line, then exactly five hashtags.\n\n"

            "Hard constraints:\n"
            "- Length: 1200–1800 characters.\n"
            "- Deliver strong technical depth aligned with the technical angle.\n"
            "- Include at least one real-world operational insight when possible.\n"
            "- If market context is provided, integrate it under CONTEXT or FIELD SIGNAL.\n"
            "- Do not fabricate proprietary or unverifiable data.\n"
            "- Final line must contain exactly five hashtags.\n"
        )

    def _build_user_prompt(self, topic: CalendarTopic, market_insights: str) -> str:
        return (
            f"Calendar day: {topic.day}\n"
            f"Theme: {topic.theme}\n"
            f"Hook: {topic.hook}\n"
            f"Technical angle: {topic.technical_angle}\n"
            f"Suggested hashtags: {topic.hashtags}\n\n"
            "--- Market context ---\n"
            f"{market_insights.strip() or '(no external context)'}\n"
            "---\n\n"
            "Write the LinkedIn post in infographic digest format."
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
                temperature=0.6,
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

    def _normalize_linkedin_format(self, text: str) -> str:
        t = text.strip()
        t = re.sub(r"\r\n", "\n", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
        lines = [ln.rstrip() for ln in t.split("\n")]
        return "\n".join(lines).strip()

    def generate_post(self, topic: CalendarTopic, market_insights: str = "") -> str:
        user_prompt = self._build_user_prompt(topic, market_insights)

        raw = self._generate_raw(user_prompt)
        cleaned = raw.strip()

        if len(cleaned) < 1200:
            cleaned = self._generate_raw(
                user_prompt + "\n\nExpand with deeper technical reasoning."
            ).strip()

        if self._count_hashtags(cleaned) < 5:
            cleaned = self._generate_raw(
                user_prompt + "\n\nEnsure exactly five hashtags."
            ).strip()

        if len(cleaned) > 1800:
            cleaned = self._trim_to_length(cleaned, 1200, 1800)

        if len(cleaned) < 1200:
            logger.warning("Post below 1200 chars; accepting best effort")

        return self._normalize_linkedin_format(cleaned)
