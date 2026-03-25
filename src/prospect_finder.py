"""
Port Product Prospect Finder
-----------------------------
Uses Google Custom Search + Gemini to identify 10 LinkedIn profiles
daily of people who would buy port products (BAMS, gangways, mooring hooks, etc.)
"""

import os
import json
import re
import csv
import time
import datetime
import hashlib
import requests
import google.generativeai as genai
from pathlib import Path


# ── Configuration ──────────────────────────────────────────────────────────────

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")      # Google Custom Search API key
GOOGLE_CX     = os.getenv("GOOGLE_CX", "")             # Custom Search Engine ID
PROSPECTS_FILE = os.getenv("PROSPECTS_FILE", "data/prospects.csv")
SEEN_FILE      = os.getenv("SEEN_FILE", "data/seen_prospects.json")


# ── Ideal Customer Profile ─────────────────────────────────────────────────────

ICP = {
    "job_titles": [
        "Port Director", "Harbour Master", "Port Operations Manager",
        "Terminal Manager", "Marine Superintendent", "Port Captain",
        "Mooring Master", "Marine Operations Manager", "Port Engineer",
        "Naval Architect", "Port Authority Manager", "Berth Master",
        "Marine Terminal Manager", "LNG Terminal Manager", "Oil Terminal Manager",
        "Offshore Operations Manager", "Port Infrastructure Manager",
        "Marine Safety Manager", "Vessel Traffic Services Manager",
        "Pilot Station Manager", "Port Logistics Manager",
        "Port Development Manager", "Maritime Project Manager",
        "Procurement Manager Maritime", "Marine Equipment Procurement",
    ],
    "industries": [
        "Maritime", "Port Operations", "Oil and Gas", "Shipping",
        "LNG Terminal", "Offshore", "Marine Engineering", "Port Authority",
        "Naval", "Logistics and Supply Chain",
    ],
    "keywords": [
        "berthing", "mooring", "gangway", "port safety", "vessel management",
        "marine operations", "port automation", "BAMS", "quick release hook",
        "fender system", "bollard", "marine navigation", "pilotage",
        "port equipment", "terminal operations",
    ],
    "regions": [
        "Middle East", "Asia Pacific", "Europe", "Americas",
        "Africa", "Southeast Asia", "North Sea", "Persian Gulf",
    ],
}

PRODUCTS = [
    "Berthing Aided Monitoring Systems (BAMS)",
    "Quick Release Mooring Hooks",
    "Gangways and Access Bridges",
    "Fender Systems",
    "Mooring Bollards",
    "Vessel Traffic Management Systems",
    "Port Safety and Monitoring Equipment",
    "Marine Navigation Aids",
    "Port Automation Solutions",
    "LNG Terminal Safety Equipment",
]

# ── Search Query Generator ─────────────────────────────────────────────────────

SEARCH_ROTATION = [
    # Day-based rotation — vary daily to avoid duplicate prospects
    'site:linkedin.com/in "Port Director" "port operations" OR "maritime"',
    'site:linkedin.com/in "Terminal Manager" "LNG" OR "mooring" OR "berthing"',
    'site:linkedin.com/in "Harbour Master" OR "Harbor Master" "port" "operations"',
    'site:linkedin.com/in "Marine Superintendent" "vessel" "port"',
    'site:linkedin.com/in "Mooring Master" OR "Berth Master" "maritime"',
    'site:linkedin.com/in "Port Engineer" "automation" OR "equipment" OR "systems"',
    'site:linkedin.com/in "Port Operations Manager" "safety" OR "monitoring"',
    'site:linkedin.com/in "Naval Architect" "port" OR "offshore" OR "terminal"',
    'site:linkedin.com/in "Marine Terminal Manager" "LNG" OR "oil" OR "gas"',
    'site:linkedin.com/in "Port Authority" "director" OR "manager" "operations"',
    'site:linkedin.com/in "Marine Operations" "procurement" OR "equipment"',
    'site:linkedin.com/in "Port Captain" OR "Marine Captain" "operations" "port"',
    'site:linkedin.com/in "Offshore Operations Manager" "terminal" OR "marine"',
    'site:linkedin.com/in "Port Development" "infrastructure" OR "equipment"',
]


def get_daily_query() -> str:
    """Rotate search queries daily to ensure variety."""
    day_index = datetime.date.today().toordinal() % len(SEARCH_ROTATION)
    return SEARCH_ROTATION[day_index]


def load_seen() -> set:
    p = Path(SEEN_FILE)
    if p.exists():
        with open(p) as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set):
    Path(SEEN_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def profile_hash(url: str) -> str:
    return hashlib.md5(url.lower().encode()).hexdigest()


# ── Google Custom Search ───────────────────────────────────────────────────────

def google_search_linkedin(query: str, num: int = 10, start: int = 1) -> list[dict]:
    """Search Google for LinkedIn profiles matching query."""
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return []
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query,
        "num": min(num, 10),
        "start": start,
        "siteSearch": "linkedin.com",
        "siteSearchFilter": "i",
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        results = []
        for item in data.get("items", []):
            link = item.get("link", "")
            if "/in/" in link:
                results.append({
                    "url": link,
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                })
        return results
    except Exception as e:
        print(f"[GoogleSearch] Error: {e}")
        return []


def scrape_profile_snippet(result: dict) -> dict:
    """Extract name, title, company from the Google snippet."""
    title = result.get("title", "")
    snippet = result.get("snippet", "")
    url = result.get("url", "")
    
    # Extract LinkedIn username from URL
    match = re.search(r"linkedin\.com/in/([^/?\s]+)", url)
    username = match.group(1) if match else ""
    
    # Parse name and title from Google title (format: "Name - Title - Company | LinkedIn")
    parts = re.split(r" - | \| ", title)
    name = parts[0].strip() if parts else username
    job_title = parts[1].strip() if len(parts) > 1 else ""
    company = parts[2].strip() if len(parts) > 2 else ""
    company = re.sub(r"\s*\|\s*LinkedIn.*", "", company).strip()
    
    return {
        "name": name,
        "username": username,
        "url": url,
        "job_title": job_title,
        "company": company,
        "snippet": snippet[:300],
    }


# ── Gemini Qualifier ───────────────────────────────────────────────────────────

def qualify_prospects_with_gemini(candidates: list[dict]) -> list[dict]:
    """Use Gemini to score and rank candidates by relevance to port products."""
    if not GEMINI_API_KEY or not candidates:
        return candidates
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    products_str = "\n".join(f"- {p}" for p in PRODUCTS)
    candidates_json = json.dumps(candidates, indent=2)
    
    prompt = f"""You are a B2B sales analyst for a maritime port equipment company (Prosertek).

Our products:
{products_str}

Below are LinkedIn profiles found via search. For each profile, assign a relevance score (0-10) 
based on how likely this person would be interested in or influence the purchase of our port products.

Scoring criteria:
- 9-10: Decision-maker at port authority, terminal, offshore/LNG — directly buys equipment
- 7-8: Marine engineer, operations manager, port captain — major influencer
- 5-6: Procurement, logistics, maritime consultant — moderate influence
- 3-4: Shipping company, freight forwarder — indirect interest
- 0-2: Irrelevant (HR, marketing, etc.)

Candidates:
{candidates_json}

Return ONLY a JSON array with the same objects, each having an added "relevance_score" (int 0-10) 
and "reason" (one sentence why). Sort by score descending. Return ONLY JSON, no markdown.
"""
    
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        # Strip markdown code blocks if present
        raw = re.sub(r"^```json\s*|^```\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
        scored = json.loads(raw)
        return scored
    except Exception as e:
        print(f"[Gemini] Qualification error: {e}")
        # Assign default score
        for c in candidates:
            c["relevance_score"] = 5
            c["reason"] = "Could not qualify — default score"
        return candidates


# ── Message Generator ─────────────────────────────────────────────────────────

def generate_connection_message(prospect: dict) -> str:
    """Generate a personalized, human-sounding connection request note (max 300 chars)."""
    if not GEMINI_API_KEY:
        return (
            f"Hi {prospect.get('name','').split()[0]}, I noticed your work in port operations. "
            "I share content on BAMS, gangways & mooring systems. Would love to connect!"
        )
    
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    prompt = f"""Write a LinkedIn connection request note for the following port professional.
The note must:
- Be personalized (mention their role or company)
- Reference our products naturally (BAMS, gangways, mooring hooks, port safety)
- Sound human, not salesy — curious and collegial tone
- Be UNDER 300 characters (LinkedIn limit)
- Be in English
- NOT start with "Hi" (vary the opener)

Prospect:
Name: {prospect.get('name', '')}
Title: {prospect.get('job_title', '')}
Company: {prospect.get('company', '')}
Context: {prospect.get('snippet', '')}

Return ONLY the message text, nothing else.
"""
    
    try:
        response = model.generate_content(prompt)
        msg = response.text.strip().strip('"').strip("'")
        # Ensure under 300 chars
        if len(msg) > 290:
            msg = msg[:287] + "..."
        return msg
    except Exception as e:
        print(f"[Gemini] Message gen error: {e}")
        name = prospect.get('name', '').split()[0] or 'there'
        return f"I follow port operations closely and publish on BAMS, gangways & mooring systems. Would love to connect, {name}!"


# ── CSV Logger ────────────────────────────────────────────────────────────────

PROSPECT_CSV_HEADERS = [
    "date", "name", "username", "url", "job_title", "company",
    "relevance_score", "reason", "connection_message", "status"
]


def save_prospects_to_csv(prospects: list[dict], file_path: str = PROSPECTS_FILE):
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    file_exists = Path(file_path).exists()
    
    with open(file_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PROSPECT_CSV_HEADERS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        for p in prospects:
            p["date"] = datetime.date.today().isoformat()
            p["status"] = "pending"
            writer.writerow({k: p.get(k, "") for k in PROSPECT_CSV_HEADERS})
    
    print(f"[CSV] Saved {len(prospects)} prospects to {file_path}")


# ── Main Orchestrator ─────────────────────────────────────────────────────────

def find_daily_prospects(target: int = 10) -> list[dict]:
    """Full pipeline: search → deduplicate → qualify → generate messages → save."""
    seen = load_seen()
    query = get_daily_query()
    print(f"[Prospect] Today's search query: {query}")
    
    raw_results = []
    
    # Fetch up to 3 pages to get enough candidates
    for page in range(1, 4):
        start = (page - 1) * 10 + 1
        results = google_search_linkedin(query, num=10, start=start)
        print(f"[Search] Page {page}: {len(results)} results")
        raw_results.extend(results)
        if len(raw_results) >= 30:
            break
        time.sleep(1)
    
    # Fallback: try alternate queries if not enough results
    if len(raw_results) < target:
        alt_query = SEARCH_ROTATION[(datetime.date.today().toordinal() + 1) % len(SEARCH_ROTATION)]
        extra = google_search_linkedin(alt_query, num=10)
        raw_results.extend(extra)
    
    # Parse snippets
    candidates = [scrape_profile_snippet(r) for r in raw_results]
    
    # Deduplicate against already-seen
    fresh = []
    for c in candidates:
        h = profile_hash(c["url"])
        if h not in seen and c["url"] not in [f["url"] for f in fresh]:
            fresh.append(c)
            seen.add(h)
    
    print(f"[Dedup] {len(fresh)} fresh candidates after dedup")
    
    # Qualify with Gemini
    qualified = qualify_prospects_with_gemini(fresh[:30])  # Send max 30 to Gemini
    
    # Sort by score and take top N
    qualified.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    top = qualified[:target]
    
    # Generate personalized messages
    for p in top:
        p["connection_message"] = generate_connection_message(p)
        time.sleep(0.5)  # Rate limit Gemini calls
    
    # Save to CSV and update seen
    save_prospects_to_csv(top)
    save_seen(seen)
    
    return top


def format_daily_report(prospects: list[dict]) -> str:
    """Format a human-readable daily report of today's prospects."""
    today = datetime.date.today().strftime("%B %d, %Y")
    lines = [f"# LinkedIn Prospects — {today}", f"Found {len(prospects)} qualified prospects\n"]
    
    for i, p in enumerate(prospects, 1):
        lines.append(f"## {i}. {p.get('name', 'Unknown')}")
        lines.append(f"**Role:** {p.get('job_title', 'N/A')}")
        lines.append(f"**Company:** {p.get('company', 'N/A')}")
        lines.append(f"**Profile:** {p.get('url', '')}")
        lines.append(f"**Relevance:** {p.get('relevance_score', 0)}/10 — {p.get('reason', '')}")
        lines.append(f"**Message to send:**")
        lines.append(f"> {p.get('connection_message', '')}")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == "__main__":
    prospects = find_daily_prospects(10)
    report = format_daily_report(prospects)
    print(report)
    
    # Save report
    report_path = f"data/reports/prospects_{datetime.date.today().isoformat()}.md"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\n[Report] Saved to {report_path}")
