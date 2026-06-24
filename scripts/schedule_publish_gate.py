#!/usr/bin/env python3
"""GitHub Actions gate: decide if today is a publish day (random twice-weekly schedule).

Writes key=value lines to stdout for GITHUB_OUTPUT (same algorithm as orchestrator).
"""
from __future__ import annotations

import datetime
import os
import random
import sys
from zoneinfo import ZoneInfo


def should_publish_today(
    today: datetime.date,
    *,
    seed: str,
    days_per_week: int,
) -> tuple[bool, str, list[int], int]:
    iso = today.isocalendar()
    week_key = f"{iso.year:04d}-W{iso.week:02d}"
    rng = random.Random(f"{seed}:{week_key}")
    selected_days = sorted(rng.sample(list(range(7)), days_per_week))
    weekday = today.weekday()
    return weekday in selected_days, week_key, selected_days, weekday


def main() -> None:
    seed = os.environ.get("SCHEDULE_SEED", "industrial-ai-content-factory")
    timezone_name = os.environ.get("SCHEDULE_TIMEZONE", "Europe/Madrid")
    try:
        days_per_week = int(os.environ.get("DAYS_PER_WEEK", "2"))
    except ValueError:
        days_per_week = 2
    days_per_week = max(1, min(7, days_per_week))

    try:
        tz = ZoneInfo(timezone_name)
    except Exception:
        tz = datetime.timezone.utc

    today = datetime.datetime.now(tz).date()
    publish, week_key, selected_days, weekday = should_publish_today(
        today, seed=seed, days_per_week=days_per_week
    )

    print(f"should_publish={'true' if publish else 'false'}")
    print("manual_override=false")
    print(f"selection_week={week_key}")
    print(f"selection_weekdays={','.join(str(d) for d in selected_days)}")
    print(f"today_weekday={weekday}")


if __name__ == "__main__":
    main()
    sys.exit(0)
