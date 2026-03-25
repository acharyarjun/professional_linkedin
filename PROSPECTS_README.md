# 🚢 Daily LinkedIn Port Prospects

Automatically finds **10 qualified LinkedIn prospects per day** in the port/maritime sector — people who would be interested in buying Prosertek products like BAMS, gangways, quick-release hooks, and fender systems.

## How It Works

```
Every day at 09:00 CET
        ↓
Google Custom Search → LinkedIn profiles (port directors, terminal managers, etc.)
        ↓
Gemini AI → Score each profile 0-10 by purchase likelihood
        ↓
Gemini AI → Write personalized connection message (< 300 chars)
        ↓
Save to CSV + Notion database + GitHub artifact
```

## Setup (One-Time)

### 1. Google Custom Search API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable **Custom Search JSON API**
3. Create an API key → add as `GOOGLE_API_KEY` secret in GitHub
4. Go to [Programmable Search Engine](https://programmablesearchengine.google.com)
5. Create a search engine targeting `linkedin.com`
6. Copy the **Search Engine ID (cx)** → add as `GOOGLE_CX` secret in GitHub

**Free tier:** 100 searches/day — enough for ~10 prospects/day

### 2. Notion Integration (Optional but Recommended)

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create a new integration → copy the **Internal Integration Token**
3. Add as `NOTION_TOKEN` secret in GitHub
4. Create a Notion page for the database, share it with your integration
5. Run setup script:
   ```bash
   NOTION_TOKEN=your_token NOTION_PARENT_PAGE_ID=your_page_id python scripts/setup_notion_db.py
   ```
6. Copy the printed database ID → add as `NOTION_PROSPECTS_DB_ID` secret in GitHub

### 3. GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `GEMINI_API_KEY` | Already set ✅ |
| `GOOGLE_API_KEY` | Google Custom Search API key |
| `GOOGLE_CX` | Custom Search Engine ID |
| `NOTION_TOKEN` | Notion integration token (optional) |
| `NOTION_PROSPECTS_DB_ID` | Notion database ID (optional) |

## Output

### GitHub Artifacts
Each daily run uploads a Markdown report to GitHub Actions artifacts (kept 30 days):
```
data/reports/prospects_2026-03-25.md
```

### CSV Database
All prospects accumulate in:
```
data/prospects.csv
```
Columns: `date, name, username, url, job_title, company, relevance_score, reason, connection_message, status`

### Notion Dashboard
If configured, each prospect appears as a Notion card with:
- Status tracking: **Pending → Request Sent → Connected → Replied**
- LinkedIn URL
- Personalized message ready to copy
- Relevance score and reason

## Ideal Customer Profile (ICP)

The system targets:

**Decision Makers (Score 9-10)**
- Port Director / Port Authority Manager
- Terminal Manager / Marine Terminal Manager  
- Harbour Master / Harbor Master
- LNG Terminal Manager

**Influencers (Score 7-8)**
- Marine Superintendent
- Port Engineer / Naval Architect
- Mooring Master / Berth Master
- Marine Operations Manager

**Indirect (Score 5-6)**
- Maritime Procurement Manager
- Marine Equipment Procurement
- Port Logistics Manager

**Regions:** Middle East, Asia Pacific, Europe, Americas, Africa, North Sea, Persian Gulf

## Daily Usage

1. Check GitHub Actions at 09:00 CET for today's run
2. Download the artifact report OR open Notion dashboard
3. For each prospect (start with highest score):
   - Open their LinkedIn profile
   - Click "Connect"
   - Paste the generated message
   - Mark as "Request Sent" in Notion

**LinkedIn limit:** Max 10-15 connection requests/day for safety. This workflow targets exactly 10.

## Manual Run

Trigger from GitHub Actions → `Daily LinkedIn Prospects` → `Run workflow`
