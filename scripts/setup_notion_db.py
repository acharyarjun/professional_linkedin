"""
One-time Notion Database Setup
--------------------------------
Run this ONCE to create the prospects tracking database in Notion.
Prints the database ID — add it as NOTION_PROSPECTS_DB_ID secret in GitHub.

Usage:
    NOTION_TOKEN=your_token NOTION_PARENT_PAGE_ID=your_page_id python scripts/setup_notion_db.py
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.notion_reporter import ensure_database_exists

token = os.getenv("NOTION_TOKEN", "")
parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID", "")

if not token or not parent_page_id:
    print("ERROR: Set NOTION_TOKEN and NOTION_PARENT_PAGE_ID environment variables")
    print("  NOTION_TOKEN: Your Notion integration token (from notion.so/my-integrations)")
    print("  NOTION_PARENT_PAGE_ID: ID of a Notion page where the database will be created")
    print("    (Get it from the page URL: notion.so/Your-Page-<ID>)")
    sys.exit(1)

db_id = ensure_database_exists(parent_page_id)
if db_id:
    print(f"\n✅ SUCCESS!")
    print(f"Database ID: {db_id}")
    print(f"\nAdd this as a GitHub secret:")
    print(f"  Name:  NOTION_PROSPECTS_DB_ID")
    print(f"  Value: {db_id}")
else:
    print("❌ Failed to create database. Check your NOTION_TOKEN and page permissions.")
    sys.exit(1)
