"""LinkedIn publishing via linkedin-api session and Voyager normShares endpoint."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from linkedin_api import Linkedin
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import AppConfig

NORM_SHARES_PATH = "/contentcreation/normShares"


class LinkedInPublisher:
    """Posts text updates to the authenticated member profile."""

    def __init__(self, config: AppConfig) -> None:
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

    def _public_identifier(self, api: Linkedin) -> str:
        me = api.get_user_profile(use_cache=True)
        mini = me.get("miniProfile") or me.get("included", [{}])[0] if me.get("included") else {}
        if isinstance(mini, dict):
            pid = mini.get("publicIdentifier")
            if pid:
                return str(pid)
        included = me.get("included") or []
        for block in included:
            if not isinstance(block, dict):
                continue
            if "publicIdentifier" in block:
                return str(block["publicIdentifier"])
        raise RuntimeError("Could not resolve LinkedIn public identifier from /me payload")

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
