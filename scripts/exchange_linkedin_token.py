#!/usr/bin/env python3
"""Exchange a LinkedIn OAuth authorization code for token details (CI/local helper)."""
from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import datetime, timedelta, timezone

import requests

DEFAULT_REDIRECT_URI = "http://127.0.0.1:8765/oauth/callback"


def _decode_id_token_payload(id_token: str) -> dict[str, object]:
    try:
        parts = id_token.split(".")
        if len(parts) != 3:
            return {}
        pad = "=" * (-len(parts[1]) % 4)
        raw = base64.urlsafe_b64decode(parts[1] + pad)
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return {}


def exchange_code(
    *,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str = DEFAULT_REDIRECT_URI,
) -> dict[str, object]:
    r = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=45,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Token exchange HTTP {r.status_code}: {r.text[:1200]}")
    data = r.json()
    if not data.get("access_token"):
        raise RuntimeError(f"No access_token in response: {data}")
    return data


def format_token_report(data: dict[str, object]) -> str:
    token = str(data.get("access_token", ""))
    expires_in = data.get("expires_in")
    scopes = data.get("scope", "")
    id_token = data.get("id_token")
    member_sub = ""
    if isinstance(id_token, str):
        member_sub = str(_decode_id_token_payload(id_token).get("sub", "") or "")

    expires_at = ""
    if expires_in is not None:
        try:
            when = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
            expires_at = when.strftime("%Y-%m-%dT%H:%M:%SZ")
        except (TypeError, ValueError):
            pass

    lines = [
        "=== LinkedIn OAuth token exchange ===",
        f"access_token: {token}",
        f"expires_in: {expires_in}",
        f"scope: {scopes or '(not returned)'}",
        f"LINKEDIN_MEMBER_SUB: {member_sub or '(missing — ensure openid scope)'}",
    ]
    if expires_at:
        lines.append(f"LINKEDIN_TOKEN_EXPIRES_AT: {expires_at}")
    lines.extend(
        [
            "",
            "Update GitHub secrets:",
            "  python scripts/push_linkedin_secrets.py",
            "",
            "LinkedIn tokens expire in ~60 days — set a calendar reminder.",
        ]
    )
    return "\n".join(lines)


def write_json_report(data: dict[str, object], path: str) -> None:
    id_token = data.get("id_token")
    member_sub = ""
    if isinstance(id_token, str):
        member_sub = str(_decode_id_token_payload(id_token).get("sub", "") or "")
    out = dict(data)
    out["member_sub"] = member_sub
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh)


def main() -> None:
    parser = argparse.ArgumentParser(description="Exchange LinkedIn OAuth code for token")
    parser.add_argument("--code", required=True, help="Authorization code from redirect URL")
    parser.add_argument("--client-id", required=True)
    parser.add_argument("--client-secret", required=True)
    parser.add_argument("--redirect-uri", default=DEFAULT_REDIRECT_URI)
    parser.add_argument(
        "--json-out",
        help="Write full token response JSON (plus member_sub) to this path",
    )
    args = parser.parse_args()

    data = exchange_code(
        code=args.code.strip(),
        client_id=args.client_id.strip(),
        client_secret=args.client_secret.strip(),
        redirect_uri=args.redirect_uri.strip(),
    )
    if args.json_out:
        write_json_report(data, args.json_out)
    print(format_token_report(data))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
