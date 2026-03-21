"""LinkedIn publishing via official LinkedIn API v2 with OAuth access token."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Protocol

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class LinkedInAuth(Protocol):
    """Subset of config used by this publisher."""

    linkedin_access_token: str
    dry_run: bool


class LinkedInPublisher:
    """Posts text updates to LinkedIn using the official API v2."""

    def __init__(self, config: LinkedInAuth) -> None:
        self._config = config
        self._person_id: Optional[str] = None

    def _get_person_id(self) -> str:
        """Get LinkedIn person URN using userinfo endpoint."""
        if self._person_id:
            return self._person_id

        headers = {"Authorization": f"Bearer {self._config.linkedin_access_token}"}
        resp = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers, timeout=30)
        
        if resp.status_code != 200:
            raise RuntimeError(f"Failed to fetch LinkedIn userinfo: {resp.status_code} {resp.text[:300]}")
        
        data = resp.json()
        sub = data.get("sub")
        if not sub:
            raise RuntimeError("LinkedIn userinfo did not return 'sub' field")
        
        self._person_id = f"urn:li:person:{sub}"
        logger.debug("LinkedIn person_id: {}", self._person_id)
        return self._person_id

    def publish_post(self, text: str) -> Dict[str, Any]:
        """Publish text to LinkedIn; respects dry-run mode."""
        if self._config.dry_run:
            logger.info("[DRY RUN] Would publish LinkedIn post:\n{}", text)
            return {
                "dry_run": True,
                "post_id": "dry-run",
                "url": "https://www.linkedin.com/feed/",
                "text_length": len(text),
            }

        person_id = self._get_person_id()

        payload = {
            "author": person_id,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        headers = {
            "Authorization": f"Bearer {self._config.linkedin_access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=60),
            reraise=True,
        )
        def _post() -> Dict[str, Any]:
            resp = requests.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if resp.status_code not in (200, 201):
                raise RuntimeError(f"LinkedIn post failed: HTTP {resp.status_code} — {resp.text[:500]}")

            data = resp.json()
            post_id = data.get("id", "unknown")
            url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id != "unknown" else "https://www.linkedin.com/feed/"

            logger.success("Published LinkedIn post id={}", post_id)
            return {"post_id": post_id, "url": url, "raw": data}

        return _post()

    def test_connection(self) -> Dict[str, Any]:
        """Test the access token and get profile info."""
        headers = {"Authorization": f"Bearer {self._config.linkedin_access_token}"}
        resp = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers, timeout=30)

        if resp.status_code != 200:
            return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}

        data = resp.json()
        logger.success("LinkedIn connection OK — sub={}", data.get("sub"))
        return {"ok": True, "data": data}
