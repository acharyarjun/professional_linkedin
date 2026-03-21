"""LinkedIn publishing via official UGC Posts API (OAuth access token)."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import AppConfig

LINKEDIN_UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_ME_URL = "https://api.linkedin.com/v2/me"


class LinkedInPublisher:
    """Posts text updates to the authenticated member profile via OAuth."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._access_token: Optional[str] = os.environ.get("LINKEDIN_ACCESS_TOKEN")
        self._person_urn: Optional[str] = None

    def _get_person_urn(self) -> str:
        if self._person_urn:
            return self._person_urn
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        resp = requests.get(LINKEDIN_ME_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        person_id = data.get("id")
        if not person_id:
            raise RuntimeError(f"Could not get LinkedIn person ID: {data}")
        self._person_urn = f"urn:li:person:{person_id}"
        return self._person_urn

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

        if not self._access_token:
            raise RuntimeError(
                "LINKEDIN_ACCESS_TOKEN environment variable not set. "
                "Generate one at https://www.linkedin.com/developers/"
            )

        author = self._get_person_urn()

        payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=60),
            reraise=True,
        )
        def _post() -> Dict[str, Any]:
            headers = {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }
            res = requests.post(
                LINKEDIN_UGC_POSTS_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=30,
            )
            if res.status_code not in (200, 201):
                raise RuntimeError(
                    f"LinkedIn post failed: HTTP {res.status_code} — {res.text[:800]}"
                )
            try:
                data = res.json()
            except json.JSONDecodeError:
                data = {}
            urn = data.get("id", "")
            if "activity:" in urn:
                aid = urn.split("activity:", 1)[-1].strip()
                url = f"https://www.linkedin.com/feed/update/urn:li:activity:{aid}"
            else:
                url = "https://www.linkedin.com/feed/"
            logger.success("Published LinkedIn post urn={}", urn or "unknown")
            return {"post_id": urn or "unknown", "url": url, "raw": data}

        return _post()

    def get_recent_posts(self, count: int = 5) -> List[Dict[str, Any]]:
        """Return recent profile posts (placeholder)."""
        return []
