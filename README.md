# Industrial AI Content Factory

Autonomous daily LinkedIn content pipeline for **Arjun Acharya** — Port Automation & AI Engineer at **Prosertek** (Bilbao, Spain). The system researches maritime and industrial automation news, avoids near-duplicate posts via vector memory, generates PhD-level long-form posts with **Gemini 1.5 Pro**, and publishes through the unofficial **linkedin-api** client (email/password session) unless **dry-run** mode is enabled.

## Architecture

```
┌─────────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ post_calendar.csv   │────▶│ Orchestrator     │────▶│ PostGenerator   │
│ (100-day themes)    │     │ (daily pipeline) │     │ (Gemini 1.5 Pro)│
└─────────────────────┘     └────────┬─────────┘     └────────▲────────┘
                                     │                        │
┌─────────────────────┐              │              ┌──────────┴────────┐
│ MarketResearcher    │──────────────┼──────────────▶│ Prompt w/ news   │
│ (RSS + site scrape) │              │              └──────────────────┘
└─────────────────────┘              │
                                     ▼
                            ┌─────────────────┐
                            │ RAGEngine       │
                            │ (ChromaDB)      │
                            │ dedupe + recall │
                            └────────┬────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ LinkedInPublisher│
                            │ (normShares)    │
                            └─────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │ PostScheduler    │
                            │ (APScheduler)    │
                            └─────────────────┘
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in API keys and credentials.

## Configuration

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Google AI Studio key for Gemini |
| `LINKEDIN_EMAIL` / `LINKEDIN_PASSWORD` | LinkedIn login for `linkedin-api` |
| `CHROMA_PERSIST_DIR` | Persistent ChromaDB directory |
| `POST_CALENDAR_PATH` | CSV calendar (`data/post_calendar.csv`) |
| `SCHEDULE_HOUR` / `SCHEDULE_MINUTE` | Local cron time |
| `TIMEZONE` | IANA zone (default `Europe/Madrid`) |
| `DRY_RUN` | `true` to skip publishing |

## Usage

```bash
# One-off run for “today’s” slot (1–100 cycle from day-of-year)
python main.py --run-now

# Specific calendar day (1–100)
python main.py --day 42

# Daemon scheduler (cron at configured local time)
python main.py --schedule

# No LinkedIn post — log only
python main.py --run-now --dry-run
```

## Repository layout

```
professional_linkedin/
├── main.py
├── requirements.txt
├── .env.example
├── data/
│   └── post_calendar.csv
├── src/
│   ├── config.py
│   ├── post_generator.py
│   ├── market_researcher.py
│   ├── rag_engine.py
│   ├── linkedin_publisher.py
│   ├── scheduler.py
│   └── orchestrator.py
└── tests/
    └── test_post_generator.py
```

## Tech stack

- **Python 3.10+**
- **Gemini AI** (`google-generativeai`) for long-form posts
- **ChromaDB** for embeddings, post history, and market insight recall
- **APScheduler** with cron triggers and timezone support
- **linkedin-api** (unofficial) plus Voyager `contentcreation/normShares` for publishing
- **BeautifulSoup** + **requests** for lightweight research scraping and Google News RSS
- **Azure** themes appear in prompts and calendar topics (cloud IoT patterns)

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
