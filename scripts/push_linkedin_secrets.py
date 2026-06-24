#!/usr/bin/env python3
"""Push LinkedIn OAuth credentials from local .env to GitHub repository secrets.

Run after `python scripts/linkedin_oauth_local.py` to sync CI credentials:

    python scripts/push_linkedin_secrets.py
    python scripts/push_linkedin_secrets.py --repo acharyarjun/professional_linkedin
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

import os

REQUIRED_KEYS = ("LINKEDIN_ACCESS_TOKEN", "LINKEDIN_MEMBER_SUB")
OPTIONAL_KEYS = ("LINKEDIN_TOKEN_EXPIRES_AT",)


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*([A-Z0-9_]+)\s*=\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def _expires_at_from_env(env: dict[str, str]) -> str | None:
    if env.get("LINKEDIN_TOKEN_EXPIRES_AT"):
        return env["LINKEDIN_TOKEN_EXPIRES_AT"]
    raw = env.get("LINKEDIN_TOKEN_EXPIRES_IN", "").strip()
    if not raw:
        return None
    try:
        seconds = int(raw)
    except ValueError:
        return None
    when = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    return when.strftime("%Y-%m-%dT%H:%M:%SZ")


def _gh_secret_set(repo: str, key: str, value: str) -> None:
    proc = subprocess.run(
        ["gh", "secret", "set", key, "--repo", repo],
        input=value,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh secret set {key} failed: {proc.stderr.strip() or proc.stdout}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Push LinkedIn secrets from .env to GitHub")
    parser.add_argument(
        "--repo",
        default=os.environ.get("GITHUB_REPOSITORY", "acharyarjun/professional_linkedin"),
        help="owner/repo (default: GITHUB_REPOSITORY or acharyarjun/professional_linkedin)",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=ROOT / ".env",
        help="Path to .env file",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print keys only; do not push")
    args = parser.parse_args()

    file_env = _read_env_file(args.env_file)
    merged = {**file_env}
    for key in REQUIRED_KEYS + OPTIONAL_KEYS + ("LINKEDIN_TOKEN_EXPIRES_IN",):
        if os.environ.get(key):
            merged[key] = os.environ[key]

    missing = [k for k in REQUIRED_KEYS if not (merged.get(k) or "").strip()]
    if missing:
        print(
            f"Missing in {args.env_file}: {', '.join(missing)}. "
            "Run: python scripts/linkedin_oauth_local.py",
            file=sys.stderr,
        )
        sys.exit(1)

    expires_at = _expires_at_from_env(merged)
    to_push: dict[str, str] = {
        "LINKEDIN_ACCESS_TOKEN": merged["LINKEDIN_ACCESS_TOKEN"].strip(),
        "LINKEDIN_MEMBER_SUB": merged["LINKEDIN_MEMBER_SUB"].strip(),
    }
    if expires_at:
        to_push["LINKEDIN_TOKEN_EXPIRES_AT"] = expires_at

    print(f"Repository: {args.repo}")
    for key in to_push:
        print(f"  {key}: ({len(to_push[key])} chars)")
    if expires_at:
        print(f"  Token expires approximately: {expires_at}")
    else:
        print("  Note: LinkedIn access tokens expire in ~60 days; refresh before then.")

    if args.dry_run:
        print("Dry run — secrets not pushed.")
        return

    for key, value in to_push.items():
        _gh_secret_set(args.repo, key, value)
        print(f"Updated GitHub secret: {key}")

    print("Done. Re-run Actions workflow or: python main.py --test-linkedin")


if __name__ == "__main__":
    main()
