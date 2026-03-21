#!/usr/bin/env python3
"""Industrial AI Content Factory - Main Entry Point"""
import argparse

from dotenv import load_dotenv

load_dotenv()

from src.config import AppConfig
from src.orchestrator import IndustrialAIOrchestrator
from src.scheduler import PostScheduler


def main() -> None:
    parser = argparse.ArgumentParser(description="Industrial AI Content Factory")
    parser.add_argument("--run-now", action="store_true", help="Run pipeline immediately")
    parser.add_argument("--day", type=int, help="Specific day number to generate (1-100)")
    parser.add_argument("--schedule", action="store_true", help="Start scheduler daemon")
    parser.add_argument("--dry-run", action="store_true", help="Test without posting")
    args = parser.parse_args()

    config = AppConfig()
    if args.dry_run:
        config.dry_run = True

    orchestrator = IndustrialAIOrchestrator(config)

    if args.run_now or args.day:
        day = args.day or None
        orchestrator.run_once(day)
    elif args.schedule:
        scheduler = PostScheduler(config, orchestrator)
        scheduler.start()
    else:
        print("Use --run-now, --day N, or --schedule. Use --dry-run to test.")


if __name__ == "__main__":
    main()
