"""APScheduler-based cron for the daily content pipeline."""

from __future__ import annotations

import signal
import threading
from typing import TYPE_CHECKING, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from zoneinfo import ZoneInfo

from .config import AppConfig

if TYPE_CHECKING:
    from .orchestrator import IndustrialAIOrchestrator


class PostScheduler:
    """Runs `IndustrialAIOrchestrator.run_daily_pipeline` on a cron schedule."""

    def __init__(self, config: AppConfig, orchestrator: "IndustrialAIOrchestrator") -> None:
        self._config = config
        self._orchestrator = orchestrator
        tz = ZoneInfo(config.timezone)
        self._scheduler = BackgroundScheduler(timezone=tz)
        trigger = CronTrigger(
            hour=config.schedule_hour,
            minute=config.schedule_minute,
            timezone=tz,
        )
        self._scheduler.add_job(
            orchestrator.run_daily_pipeline,
            trigger=trigger,
            id="daily_linkedin_post",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the scheduler loop (blocking) with graceful signal handling."""
        job = self._scheduler.get_job("daily_linkedin_post")
        next_run = job.next_run_time if job else None
        logger.info(
            "Post scheduler started — next run at {} ({})",
            next_run,
            self._config.timezone,
        )
        self._scheduler.start()

        def _handle_signal(signum: int, frame: Optional[object]) -> None:
            logger.info("Received signal {}, shutting down scheduler", signum)
            self._stop_event.set()
            self._scheduler.shutdown(wait=False)

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT, _handle_signal)

        self._stop_event.wait()

    def stop(self) -> None:
        """Stop the scheduler."""
        self._scheduler.shutdown(wait=False)
        self._stop_event.set()

    def run_now(self) -> None:
        """Trigger the pipeline immediately (same thread)."""
        logger.info("Manual run_now() triggered")
        self._orchestrator.run_daily_pipeline()
