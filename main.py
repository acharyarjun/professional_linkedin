#!/usr/bin/env python3
"""Industrial AI Content Factory - Main Entry Point"""
import argparse
import sys

from dotenv import load_dotenv
from pydantic import ValidationError

# `.env` should win over a stale GEMINI_API_KEY in the OS/user environment (python-dotenv default does not override).
load_dotenv(override=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Industrial AI Content Factory")
    parser.add_argument("--run-now", action="store_true", help="Run pipeline immediately")
    parser.add_argument("--day", type=int, help="Calendar day index (1..N per post_calendar.csv)")
    parser.add_argument("--schedule", action="store_true", help="Start scheduler daemon")
    parser.add_argument("--dry-run", action="store_true", help="Test without posting")
    parser.add_argument(
        "--test-linkedin",
        action="store_true",
        help="Verify LinkedIn OAuth (GET /v2/me) using LINKEDIN_ACCESS_TOKEN (no Gemini key needed)",
    )
    args = parser.parse_args()

    if args.test_linkedin:
        from src.config import LinkedInCredentials
        from src.linkedin_publisher import LinkedInPublisher

        try:
            result = LinkedInPublisher(LinkedInCredentials()).test_connection()
        except ValidationError:
            print(
                "Missing LinkedIn settings. Copy .env.example to .env and set "
                "LINKEDIN_ACCESS_TOKEN (OAuth).",
                file=sys.stderr,
            )
            sys.exit(1)
        except Exception as exc:
            print(f"LinkedIn API error: {exc}", file=sys.stderr)
            sys.exit(1)
        print("LinkedIn connection test succeeded.")
        print(f"  Profile: {result['name']}")
        print(f"  URL:     {result['profile_url']}")
        print(f"  Recent posts fetched: {result['recent_posts_fetched']}")
        return

    from src.config import AppConfig
    from src.orchestrator import IndustrialAIOrchestrator
    from src.scheduler import PostScheduler

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
        print(
            "Use --run-now, --day N, --schedule, or --test-linkedin. "
            "Use --dry-run to skip publishing."
        )


if __name__ == "__main__":
    main()
