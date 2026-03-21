"""LinkedIn publishing via linkedin-api session and Voyager normShares endpoint."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Protocol

from linkedin_api import Linkedin
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

NORM_SHARES_PATH = "/contentcreation/normShares"


class LinkedInAuth(Protocol):
    """Subset of config used by this publisher."""

    linkedin_email: str
    linkedin_password: str
    dry_run: bool


class LinkedInPublisher:
    """Posts text updates to the authenticated member profile."""

    def __init__(self, config: LinkedInAuth) -> None:
        self._config = config
        self._api: Optional[Linkedin] = None

    def _ensure_client(self) -> Linkedin:
        if self._api is None:

            @retry(
                stop=stop_after_attempt(4),
                wait=wait_exponential(multiplier=1, min=3, max=90),
                reraise=True,
            )
            def _connect() -> Linkedin:
                return Linkedin(
                    self._config.linkedin_email,
                    self._config.linkedin_password,
                    refresh_cookies=False,
                )

            self._api = _connect()
        return self._api

    def _me_identity(self, api: Linkedin) -> Dict[str, str]:
        """Parse `/me` payload for public profile id and display name."""
        me = api.get_user_profile(use_cache=True)
        if not isinstance(me, dict):
            raise RuntimeError("Unexpected /me response type")

        mini = me.get("miniProfile")
        if isinstance(mini, dict):
            pid = mini.get("publicIdentifier")
            if pid:
                return {
                    "public_id": str(pid),
                    "first_name": str(mini.get("firstName", "") or ""),
                    "last_name": str(mini.get("lastName", "") or ""),
                }

        for block in me.get("included") or []:
            if not isinstance(block, dict):
                continue
            if "publicIdentifier" in block:
                return {
                    "public_id": str(block["publicIdentifier"]),
                    "first_name": str(block.get("firstName", "") or ""),
                    "last_name": str(block.get("lastName", "") or ""),
                }

        raise RuntimeError(
            "Could not resolve LinkedIn public identifier from /me payload "
            "(try logging in again or check LinkedIn cookie/session)."
        )

    def _public_identifier(self, api: Linkedin) -> str:
        return self._me_identity(api)["public_id"]

    def _extract_post_urn(self, data: Dict[str, Any]) -> str:
        if not isinstance(data, dict):
            return ""
        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        for src in (data, inner, data.get("value", {})):
            if isinstance(src, dict):
                urn = src.get("urn") or src.get("entityUrn")
                if urn:
                    return str(urn)
        return ""

    def _urn_to_activity_url(self, urn: str) -> str:
        if "activity:" in urn:
            aid = urn.split("activity:", 1)[-1].strip()
            aid = aid.split(",", 1)[0].strip()
            return f"https://www.linkedin.com/feed/update/urn:li:activity:{aid}"
        if "ugcPost:" in urn:
            return f"https://www.linkedin.com/feed/update/{urn}"
        return "https://www.linkedin.com/feed/"

    def publish_post(self, text: str) -> Dict[str, Any]:
        """Publish `text` to the member profile; respects dry-run mode."""
        if self._config.dry_run:
            logger.info("[DRY RUN] Would publish LinkedIn post:\n{}", text)
            return {
                "dry_run": True,
                "post_id": "dry-run",
                "url": "https://www.linkedin.com/feed/",
                "text_length": len(text),
            }

        api = self._ensure_client()
        payload = {
            "visibleToConnectionsOnly": False,
            "externalAudienceProviderUnion": {"externalAudienceProvider": "LINKEDIN"},
            "commentaryV2": {"text": text, "attributes": []},
            "origin": "FEED",
            "allowedCommentersScope": "ALL",
            "postState": "PUBLISHED",
        }

        @retry(
            stop=stop_after_attempt(4),
            wait=wait_exponential(multiplier=1, min=4, max=120),
            reraise=True,
        )
        def _post() -> Dict[str, Any]:
            res = api._post(
                NORM_SHARES_PATH,
                data=json.dumps(payload),
                headers={
                    "Content-Type": "application/json",
                    "accept": "application/vnd.linkedin.normalized+json+2.1",
                },
            )
            if res.status_code not in (200, 201):
                raise RuntimeError(
                    f"LinkedIn post failed: HTTP {res.status_code} — {res.text[:800]}"
                )
            try:
                data = res.json()
            except json.JSONDecodeError:
                data = {}
            urn = self._extract_post_urn(data)
            if not urn:
                urn = res.headers.get("x-restli-id", "") or ""
            url = self._urn_to_activity_url(urn) if urn else "https://www.linkedin.com/feed/"
            logger.success("Published LinkedIn post urn={}", urn or "unknown")
            return {"post_id": urn or "unknown", "url": url, "raw": data}

        return _post()

    def get_recent_posts(self, count: int = 5) -> List[Dict[str, Any]]:
        """Return recent profile posts as lightweight dicts."""
        api = self._ensure_client()
        pid = self._public_identifier(api)
        elements = api.get_profile_posts(public_id=pid, post_count=max(1, min(count, 100)))
        simplified: List[Dict[str, Any]] = []
        for el in elements[:count]:
            if not isinstance(el, dict):
                continue
            simplified.append(
                {
                    "entityUrn": el.get("entityUrn"),
                    "type": el.get("$type"),
                }
            )
        return simplified

    def test_connection(self, fetch_posts: int = 3) -> Dict[str, Any]:
        """
        Authenticate and read profile + recent posts (no publishing).

        Use this to verify `LINKEDIN_EMAIL` / `LINKEDIN_PASSWORD` before running the pipeline.
        """
        api = self._ensure_client()
        ident = self._me_identity(api)
        public_id = ident["public_id"]
        name = (ident["first_name"] + " " + ident["last_name"]).strip() or "(name not in payload)"
        profile_url = f"https://www.linkedin.com/in/{public_id}/"
        recent: List[Dict[str, Any]] = []
        try:
            recent = self.get_recent_posts(count=max(1, min(fetch_posts, 10)))
        except Exception as exc:
            logger.warning("Connected, but could not fetch recent posts: {}", exc)

        result: Dict[str, Any] = {
            "ok": True,
            "public_id": public_id,
            "name": name,
            "profile_url": profile_url,
            "recent_posts_fetched": len(recent),
            "recent_posts": recent,
        }
        logger.success(
            "LinkedIn connection OK — {} ({})",
            name,
            profile_url,
        )
        return result
