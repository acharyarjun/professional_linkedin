#!/usr/bin/env python3
"""
LinkedIn OAuth (authorization code) helper for local development.

1. Add to your LinkedIn app "Authorized redirect URLs":
   http://127.0.0.1:8765/oauth/callback
2. Set in .env:
   LINKEDIN_CLIENT_SECRET=...   (Auth tab in Developer Portal)
     Optional: LINKEDIN_CLIENT_ID=your_linkedin_app_client_id3. Run: python scripts/linkedin_oauth_local.py
   Browser opens → sign in → Allow → token is written to .env
"""
from __future__ import annotations

import re
import sys
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:
    pass

import os

PORT = 8765
REDIRECT_PATH = "/oauth/callback"
REDIRECT_URI = f"http://127.0.0.1:{PORT}{REDIRECT_PATH}"

CODE: list[str] = []
OAUTH_ERROR: list[str] = []


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        return

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != REDIRECT_PATH:
            self.send_response(404)
            self.end_headers()
            return
        qs = urllib.parse.parse_qs(parsed.query)
        if "error" in qs:
            OAUTH_ERROR.append(qs.get("error_description", qs["error"])[0])
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed. Check the terminal.")
            return
        if "code" not in qs:
            self.send_response(400)
            self.end_headers()
            return
        CODE.append(qs["code"][0])
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>Success</h1><p>You can close this tab.</p></body></html>"
        )


def _update_env_file(token: str) -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        print(f"No {env_path} found; paste LINKEDIN_ACCESS_TOKEN manually.", file=sys.stderr)
        return
    raw = env_path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if re.match(r"^\s*LINKEDIN_ACCESS_TOKEN\s*=", line):
            out.append(f"LINKEDIN_ACCESS_TOKEN={token}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        if out and out[-1].strip():
            out.append("")
        out.append(f"LINKEDIN_ACCESS_TOKEN={token}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Updated LINKEDIN_ACCESS_TOKEN in {env_path}")


def main() -> None:
    client_id = os.environ.get("LINKEDIN_CLIENT_ID", "78ujj98or1kf6a").strip()
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "").strip()
    if not client_secret:
        print(
            "Missing LINKEDIN_CLIENT_SECRET. Add it to .env (LinkedIn app → Auth → Client secret).",
            file=sys.stderr,
        )
        sys.exit(1)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": "w_member_social",
        "state": "professional_linkedin_oauth",
    }
    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization?"
        + urllib.parse.urlencode(params)
    )

    print("Add this exact redirect URL to your LinkedIn app (Developer Portal → Auth):")
    print(f"  {REDIRECT_URI}")
    print()
    httpd = HTTPServer(("127.0.0.1", PORT), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    print("Opening browser — sign in and click Allow...")
    import webbrowser

    webbrowser.open(auth_url)

    deadline = time.time() + 300
    while not CODE and not OAUTH_ERROR and time.time() < deadline:
        time.sleep(0.25)
    httpd.shutdown()

    if OAUTH_ERROR:
        print(f"OAuth error: {OAUTH_ERROR[0]}", file=sys.stderr)
        sys.exit(1)
    if not CODE:
        print("Timed out waiting for redirect (5 min).", file=sys.stderr)
        sys.exit(1)

    print("Exchanging authorization code for access token...")
    r = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": CODE[0],
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=45,
    )
    if r.status_code != 200:
        print(r.status_code, r.text[:1500], file=sys.stderr)
        sys.exit(1)
    data = r.json()
    token = data.get("access_token")
    if not token:
        print(data, file=sys.stderr)
        sys.exit(1)

    print()
    print("LINKEDIN_ACCESS_TOKEN obtained successfully.")
    _update_env_file(token)
    print("Run: python main.py --test-linkedin")


if __name__ == "__main__":
    main()
