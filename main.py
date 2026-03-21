#!/usr/bin/env python3
"""Industrial AI Content Factory - Main Entry Point"""
import argparse
import sys

from dotenv import load_dotenv
from pydantic import ValidationError

load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="Industrial AI Content Factory")
    parser.add_argument("--run-now", action="store_true", help="Run pipeline immediately")
    parser.add_argument("--day", type=int, help="Specific day number to generate (1-100)")
    parser.add_argument("--schedule", action="store_true", help="Start scheduler daemon")
    parser.add_argument("--dry-run", action="store_true", help="Test without posting")
    parser.add_argument(
        "--test-linkedin",
        action="store_true",
        help="Verify LinkedIn login and fetch profile + recent posts (no Gemini key needed)",
    )
    args = parser.parse_args()

    if args.test_linkedin:
        from linkedin_api.client import ChallengeException, UnauthorizedException

        from src.config import LinkedInCredentials
        from src.linkedin_publisher import LinkedInPublisher

        try:
            result = LinkedInPublisher(LinkedInCredentials()).test_connection()
        except ValidationError:
            print(
                "Missing LinkedIn credentials. Copy .env.example to .env and set "
                "LINKEDIN_EMAIL and LINKEDIN_PASSWORD.",
                file=sys.stderr,
            )
            sys.exit(1)
        except ChallengeException:
            print(
                "LinkedIn returned a security challenge (CAPTCHA, 2FA, or unusual login). "
                "Open linkedin.com in a browser, complete verification, then retry. "
                "If it persists, the unofficial API may be blocked for this account.",
                file=sys.stderr,
            )
            sys.exit(2)
        except UnauthorizedException:
            print(
                "LinkedIn login failed (wrong password or expired session). "
                "Check LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env.",
                file=sys.stderr,
            )
            sys.exit(3)
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
