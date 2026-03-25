"""
Notion Reporter
---------------
Pushes today's prospect list into a Notion database for easy tracking.
Each prospect becomes a Notion page with status tracking (Pending → Requested → Connected).
"""

import os
import json
import datetime
import requests
from pathlib import Path


NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_DB_ID  = os.getenv("NOTION_PROSPECTS_DB_ID", "")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def create_prospect_page(prospect: dict) -> dict | None:
    """Create a Notion page for a single prospect."""
    if not NOTION_TOKEN or not NOTION_DB_ID:
        print("[Notion] Skipping — NOTION_TOKEN or NOTION_PROSPECTS_DB_ID not set")
        return None
    
    date_str = datetime.date.today().isoformat()
    
    payload = {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": {
            "Name": {
                "title": [{"text": {"content": prospect.get("name", "Unknown")}}]
            },
            "Job Title": {
                "rich_text": [{"text": {"content": prospect.get("job_title", "")}}]
            },
            "Company": {
                "rich_text": [{"text": {"content": prospect.get("company", "")}}]
            },
            "LinkedIn URL": {
                "url": prospect.get("url", "")
            },
            "Relevance Score": {
                "number": prospect.get("relevance_score", 0)
            },
            "Status": {
                "select": {"name": "Pending"}
            },
            "Date Added": {
                "date": {"start": date_str}
            },
            "Message": {
                "rich_text": [{"text": {"content": prospect.get("connection_message", "")}}]
            },
            "Reason": {
                "rich_text": [{"text": {"content": prospect.get("reason", "")}}]
            },
        }
    }
    
    try:
        r = requests.post(
            "https://api.notion.com/v1/pages",
            headers=HEADERS,
            json=payload,
            timeout=15
        )
        r.raise_for_status()
        result = r.json()
        print(f"[Notion] Created page for {prospect.get('name')} → {result.get('url', '')}")
        return result
    except Exception as e:
        print(f"[Notion] Error creating page for {prospect.get('name')}: {e}")
        return None


def push_prospects_to_notion(prospects: list[dict]) -> int:
    """Push all prospects to Notion. Returns count of successful creates."""
    if not NOTION_TOKEN or not NOTION_DB_ID:
        print("[Notion] Skipping push — credentials not set")
        return 0
    
    success = 0
    for p in prospects:
        result = create_prospect_page(p)
        if result:
            success += 1
    
    print(f"[Notion] Pushed {success}/{len(prospects)} prospects")
    return success


def ensure_database_exists(parent_page_id: str) -> str:
    """Create the Notion database if it doesn't exist. Returns the database ID."""
    if not NOTION_TOKEN:
        return ""
    
    payload = {
        "parent": {"page_id": parent_page_id},
        "title": [{"text": {"content": "🚢 LinkedIn Port Prospects"}}],
        "properties": {
            "Name": {"title": {}},
            "Job Title": {"rich_text": {}},
            "Company": {"rich_text": {}},
            "LinkedIn URL": {"url": {}},
            "Relevance Score": {"number": {"format": "number"}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Pending", "color": "gray"},
                        {"name": "Request Sent", "color": "yellow"},
                        {"name": "Connected", "color": "green"},
                        {"name": "Replied", "color": "blue"},
                        {"name": "Not Interested", "color": "red"},
                    ]
                }
            },
            "Date Added": {"date": {}},
            "Message": {"rich_text": {}},
            "Reason": {"rich_text": {}},
        }
    }
    
    try:
        r = requests.post(
            "https://api.notion.com/v1/databases",
            headers=HEADERS,
            json=payload,
            timeout=15
        )
        r.raise_for_status()
        db_id = r.json().get("id", "")
        print(f"[Notion] Created database: {db_id}")
        return db_id
    except Exception as e:
        print(f"[Notion] Error creating database: {e}")
        return ""
