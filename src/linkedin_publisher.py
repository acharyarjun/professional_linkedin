"""LinkedIn publishing via official LinkedIn API v2 with OAuth access token (ugcPosts)."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Protocol

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

LINKEDIN_UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
LINKEDIN_ME_URL = "https://api.linkedin.com/v2/me"


class LinkedInAuth(Protocol):
    """Subset of config used by this publisher."""

    linkedin_access_token: str
    dry_run: bool


class LinkedInPublisher:
    """Posts text updates using LinkedIn UGC Posts API v2 and a Bearer token."""

    def __init__(self, config: LinkedInAuth) -> None:
        self._config = config
        self._person_urn: Optional[str] = None

    def _auth_headers(self, *, restli: bool = True) -> Dict[str, str]:
        h: Dict[str, str] = {
            "Authorization": f"Bearer {self._config.linkedin_access_token}",
        }
        if restli:
            h["X-Restli-Protocol-Version"] = "2.0.0"
        return h

    def _json_post_headers(self) -> Dict[str, str]:
        return {**self._auth_headers(restli=True), "Content-Type": "application/json"}

    def _get_person_urn(self) -> str:
        """Resolve `urn:li:person:{id}` for ugcPosts (OpenID userinfo `sub` first, else /v2/me)."""
        if self._person_urn:
            return self._person_urn

        headers = {"Authorization": f"Bearer {self._config.linkedin_access_token}"}
        resp = requests.get(LINKEDIN_USERINFO_URL, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            sub = data.get("sub")
            if sub:
                self._person_urn = f"urn:li:person:{sub}"
                logger.debug("LinkedIn person URN from userinfo: {}", self._person_urn)
                return self._person_urn

        resp = requests.get(LINKEDIN_ME_URL, headers=self._auth_headers(restli=True), timeout=30)
        resp.raise_for_status()
        data = resp.json()
        person_id = data.get("id")
        if not person_id:
            raise RuntimeError(f"Could not read person id from /v2/me: {data}")
        self._person_urn = f"urn:li:person:{person_id}"
        return self._person_urn

    def publish_post(self, text: str) -> Dict[str, Any]:
        """Publish `text` to the member profile; respects dry-run mode."""
        if self._config.dry_run:
            logger.info("[DRY RUN] Would publish LinkedIn post via /v2/ugcPosts:\n{}", text)
            return {
                "dry_run": True,
                "post_id": "dry-run",
                "url": "https://www.linkedin.com/feed/",
                "text_length": len(text),
            }

        token = (self._config.linkedin_access_token or "").strip()
        if not token:
            raise RuntimeError(
                "LINKEDIN_ACCESS_TOKEN is missing or empty. "
                "Set it in .env or GitHub Actions secrets."
            )

        author = self._get_person_urn()
        payload: Dict[str, Any] = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        @retry(
            stop=stop_after_attempt(4),
            wait=wait_exponential(multiplier=1, min=4, max=120),
            reraise=True,
        )
        def _post() -> Dict[str, Any]:
            res = requests.post(
                LINKEDIN_UGC_POSTS_URL,
                headers=self._json_post_headers(),
                data=json.dumps(payload),
                timeout=60,
            )
            if res.status_code not in (200, 201):
                raise RuntimeError(
                    f"LinkedIn post failed: HTTP {res.status_code} — {res.text[:1200]}"
                )
            try:
                data = res.json()
            except json.JSONDecodeError:
                data = {}
            urn = data.get("id", "") or res.headers.get("x-restli-id", "") or ""
            url = "https://www.linkedin.com/feed/"
            if "urn:li:activity:" in urn:
                aid = urn.split("urn:li:activity:", 1)[-1].strip()
                url = f"https://www.linkedin.com/feed/update/urn:li:activity:{aid}"
            elif "urn:li:share:" in urn:
                url = f"https://www.linkedin.com/feed/update/{urn}"
            logger.success("Published LinkedIn post id={}", urn or "unknown")
            return {"post_id": urn or "unknown", "url": url, "raw": data}

        return _post()

    def get_recent_posts(self, count: int = 5) -> List[Dict[str, Any]]:
        """Member feed listing requires extra APIs/scopes; not implemented."""
        logger.debug("get_recent_posts: skipped; count={}", count)
        return []

    def test_connection(self, fetch_posts: int = 3) -> Dict[str, Any]:
        """
        Verify OAuth token (OpenID userinfo, else /v2/me). Does not publish.

        Use this to verify `LINKEDIN_ACCESS_TOKEN` before running the pipeline.
        """
        _ = fetch_posts
        token = (self._config.linkedin_access_token or "").strip()
        if not token:
            raise RuntimeError("LINKEDIN_ACCESS_TOKEN is missing or empty.")

        headers = {"Authorization": f"Bearer {self._config.linkedin_access_token}"}
        resp_ui = requests.get(LINKEDIN_USERINFO_URL, headers=headers, timeout=30)
        if resp_ui.status_code == 200:
            data = resp_ui.json()
            sub = str(data.get("sub", "") or "")
            name = (data.get("name") or "").strip()
            if not name:
                name = (
                    f"{data.get('given_name') or ''} {data.get('family_name') or ''}".strip()
                )
            if not name:
                name = "(name not in userinfo)"
            profile_url = "https://www.linkedin.com/feed/"
            logger.success("LinkedIn OAuth OK — {}", name)
            return {
                "ok": True,
                "public_id": sub,
                "name": name,
                "profile_url": profile_url,
                "recent_posts_fetched": 0,
                "recent_posts": [],
            }

        resp = requests.get(LINKEDIN_ME_URL, headers=self._auth_headers(restli=True), timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(
                f"LinkedIn token rejected: userinfo HTTP {resp_ui.status_code}, "
                f"/v2/me HTTP {resp.status_code}. Refresh LINKEDIN_ACCESS_TOKEN "
                f"(tokens expire ~60 days). userinfo: {resp_ui.text[:200]} | me: {resp.text[:200]}"
            )
        data = resp.json()
        person_id = str(data.get("id", "") or "")
        first = str(data.get("localizedFirstName", "") or "")
        last = str(data.get("localizedLastName", "") or "")
        vanity = data.get("vanityName")
        slug = vanity if isinstance(vanity, str) and vanity.strip() else person_id
        name = f"{first} {last}".strip() or "(name not in /v2/me)"
        profile_url = (
            f"https://www.linkedin.com/in/{slug}/" if slug else "https://www.linkedin.com/feed/"
        )
        logger.success("LinkedIn OAuth OK — {} ({})", name, profile_url)
        return {
            "ok": True,
            "public_id": str(slug),
            "name": name,
            "profile_url": profile_url,
            "recent_posts_fetched": 0,
            "recent_posts": [],
        }
