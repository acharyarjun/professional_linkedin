"""
Daily Prospect Runner
----------------------
Entry point for the GitHub Actions daily_prospects workflow.
Runs the full pipeline and outputs results.
"""

import sys
import os
import json
import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.prospect_finder import find_daily_prospects, format_daily_report
from src.notion_reporter import push_prospects_to_notion


def main():
    print("=" * 60)
    print(f"🚢 Daily Port Prospect Finder — {datetime.date.today()}")
    print("=" * 60)
    
    # Run the prospect finder
    prospects = find_daily_prospects(target=10)
    
    if not prospects:
        print("[ERROR] No prospects found today. Check API keys and quotas.")
        sys.exit(1)
    
    # Generate and print report
    report = format_daily_report(prospects)
    print("\n" + report)
    
    # Save report to file
    report_dir = Path("data/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"prospects_{datetime.date.today().isoformat()}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n✅ Report saved: {report_path}")
    
    # Push to Notion if configured
    notion_db_id = os.getenv("NOTION_PROSPECTS_DB_ID", "")
    notion_token = os.getenv("NOTION_TOKEN", "")
    if notion_token and notion_db_id:
        pushed = push_prospects_to_notion(prospects)
        print(f"✅ Pushed {pushed} prospects to Notion")
    else:
        print("ℹ️  Notion not configured — skipping push (set NOTION_TOKEN + NOTION_PROSPECTS_DB_ID)")
    
    # Output JSON for GitHub Actions step output
    output_file = os.getenv("GITHUB_OUTPUT", "")
    if output_file:
        with open(output_file, "a") as f:
            f.write(f"prospect_count={len(prospects)}\n")
            f.write(f"report_path={report_path}\n")
    
    print(f"\n🎯 Done! Found {len(prospects)} prospects today.")
    return prospects


if __name__ == "__main__":
    main()
