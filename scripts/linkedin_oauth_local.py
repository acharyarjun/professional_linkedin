#!/usr/bin/env python3
"""
LinkedIn OAuth (authorization code) helper for local development.

1. In Developer Portal, add products: "Sign In with LinkedIn using OpenID Connect"
   and "Share on LinkedIn" (for posting). Add an **Authorized redirect URL** that matches
   this script exactly (default below, or set LINKEDIN_REDIRECT_URI in .env).
2. Set in .env:
   LINKEDIN_CLIENT_ID=...       (Auth tab)
   LINKEDIN_CLIENT_SECRET=...   (Auth tab)
   Optional: LINKEDIN_REDIRECT_URI=http://127.0.0.1:8765/oauth/callback
3. Run: python scripts/linkedin_oauth_local.py
   Browser opens → sign in → Allow → token is written to .env
"""
from __future__ import annotations

import base64
import json
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

DEFAULT_REDIRECT_URI = "http://127.0.0.1:8765/oauth/callback"
# userinfo needs openid/profile; posting needs w_member_social (all space-separated for OAuth).
OAUTH_SCOPES = "openid profile email w_member_social"

CODE: list[str] = []
OAUTH_ERROR: list[str] = []


def _listener_from_redirect_uri(redirect_uri: str) -> tuple[str, int, str]:
    """
    Parse http://host:port/path for the local HTTP listener.
    Only http:// and loopback hosts are supported.
    """
    u = urllib.parse.urlparse(redirect_uri.strip())
    if u.scheme != "http":
        print(
            "LINKEDIN_REDIRECT_URI must use http:// (this script listens on plain HTTP). "
            "Example: http://127.0.0.1:8765/oauth/callback",
            file=sys.stderr,
        )
        sys.exit(1)
    host = (u.hostname or "127.0.0.1").lower()
    if host not in ("127.0.0.1", "localhost"):
        print("LINKEDIN_REDIRECT_URI host must be 127.0.0.1 or localhost.", file=sys.stderr)
        sys.exit(1)
    port = u.port if u.port is not None else 80
    path = u.path or "/"
    return host, port, path


def _make_handler(expected_path: str) -> type[BaseHTTPRequestHandler]:
    exp = expected_path.rstrip("/") or "/"

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args: object) -> None:
            return

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            got = parsed.path.rstrip("/") or "/"
            if got != exp:
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

    return _Handler


def _decode_id_token_payload(id_token: str) -> dict[str, object]:
    """Read JWT payload (no signature verification; local dev only)."""
    try:
        parts = id_token.split(".")
        if len(parts) != 3:
            return {}
        pad = "=" * (-len(parts[1]) % 4)
        raw = base64.urlsafe_b64decode(parts[1] + pad)
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError):
        return {}


def _update_env_keys(updates: dict[str, str]) -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        print(f"No {env_path} found; paste credentials manually.", file=sys.stderr)
        return
    lines = env_path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    keys_done: set[str] = set()
    for line in lines:
        matched = False
        for k, v in updates.items():
            if re.match(rf"^\s*{re.escape(k)}\s*=", line):
                out.append(f"{k}={v}")
                keys_done.add(k)
                matched = True
                break
        if not matched:
            out.append(line)
    for k, v in updates.items():
        if k not in keys_done:
            if out and out[-1].strip():
                out.append("")
            out.append(f"{k}={v}")
    env_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    for k in updates:
        print(f"Updated {k} in {env_path}")


def main() -> None:
    client_id = os.environ.get("LINKEDIN_CLIENT_ID", "").strip()
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "").strip()
    if not client_id:
        print(
            "Missing LINKEDIN_CLIENT_ID. Add it to .env (LinkedIn app → Auth → Client ID).",
            file=sys.stderr,
        )
        sys.exit(1)
    if not client_secret:
        print(
            "Missing LINKEDIN_CLIENT_SECRET. Add it to .env (LinkedIn app → Auth → Client secret).",
            file=sys.stderr,
        )
        sys.exit(1)

    redirect_uri = os.environ.get("LINKEDIN_REDIRECT_URI", "").strip() or DEFAULT_REDIRECT_URI
    bind_host, bind_port, callback_path = _listener_from_redirect_uri(redirect_uri)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": OAUTH_SCOPES,
        "state": "professional_linkedin_oauth",
    }
    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization?"
        + urllib.parse.urlencode(params)
    )

    print("Add this exact redirect URL to your LinkedIn app (Developer Portal → Auth):")
    print(f"  {redirect_uri}")
    print()
    handler = _make_handler(callback_path)
    httpd = HTTPServer((bind_host, bind_port), handler)
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
            "redirect_uri": redirect_uri,
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

    exp = data.get("expires_in")
    scopes = data.get("scope", "")
    print()
    print("Token response: expires_in=", exp, " scope=", scopes or "(not returned)", sep="")

    id_token = data.get("id_token")
    id_payload = _decode_id_token_payload(id_token) if isinstance(id_token, str) else {}
    member_sub = str(id_payload.get("sub", "") or "").strip()

    updates: dict[str, str] = {"LINKEDIN_ACCESS_TOKEN": token}
    if member_sub:
        updates["LINKEDIN_MEMBER_SUB"] = member_sub
        print("OpenID id_token present; member sub will be saved for profile API fallback.")

    print("Verifying token against GET /v2/userinfo...")
    verify = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={
            "Authorization": f"Bearer {token}",
            "LinkedIn-Version": "202411",
        },
        timeout=30,
    )
    if verify.status_code != 200:
        print(
            f"userinfo failed HTTP {verify.status_code}: {verify.text[:800]}",
            file=sys.stderr,
        )
        if member_sub:
            print(
                "Continuing: LINKEDIN_MEMBER_SUB from id_token can still be used for "
                "urn:li:person and --test-linkedin.",
                file=sys.stderr,
            )
            _update_env_keys(updates)
            print("Run: python main.py --test-linkedin")
            return
        print(
            "Fix: enable 'Sign In with LinkedIn using OpenID Connect' (Products), "
            "check redirect URL, and retry.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("LINKEDIN_ACCESS_TOKEN obtained and verified.")
    _update_env_keys(updates)
    print("Run: python main.py --test-linkedin")


if __name__ == "__main__":
    main()
