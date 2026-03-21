# Industrial AI Content Factory

Autonomous daily LinkedIn content pipeline for **Arjun Acharya** — Port Automation & AI Engineer at **Prosertek** (Bilbao, Spain). The system researches maritime and industrial automation news, avoids near-duplicate posts via vector memory, generates PhD-level long-form posts with **Gemini 1.5 Pro**, and publishes via the **official LinkedIn REST API v2** (`/v2/ugcPosts`) using an **OAuth 2.0 access token** (`w_member_social`), unless **dry-run** mode is enabled.

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
                            │ (OAuth /v2)     │
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

The **`.env` file is gitignored** and will not be committed or pushed; only **`.env.example`** (placeholders) belongs in the repository. If you ever ran `git add .env` by mistake, run `git rm --cached .env` and keep secrets only locally.

## Configuration

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Google AI Studio key for Gemini |
| `LINKEDIN_ACCESS_TOKEN` | OAuth 2.0 access token with `w_member_social` (UGC Posts) |
| `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` | Only needed to **refresh** the token locally (see script below) |
| `LINKEDIN_EMAIL` / `LINKEDIN_PASSWORD` | Optional legacy placeholders (not used for publishing) |
| `CHROMA_PERSIST_DIR` | Persistent ChromaDB directory |
| `POST_CALENDAR_PATH` | CSV calendar (`data/post_calendar.csv`) |
| `SCHEDULE_HOUR` / `SCHEDULE_MINUTE` | Local cron time |
| `TIMEZONE` | IANA zone (default `Europe/Madrid`) |
| `DRY_RUN` | `true` to skip publishing |

## Test LinkedIn (no Gemini key)

With `LINKEDIN_ACCESS_TOKEN` set in `.env`, verify the token against `GET https://api.linkedin.com/v2/me`:

```bash
python main.py --test-linkedin
```

This does **not** publish anything. If the token is expired or missing scopes, refresh the OAuth token in the [LinkedIn Developer Portal](https://www.linkedin.com/developers/).

### Refresh `LINKEDIN_ACCESS_TOKEN` locally (browser + terminal)

1. In the LinkedIn app **Auth** tab, add this **Authorized redirect URL** (exactly):  
   `http://127.0.0.1:8765/oauth/callback`
2. Put **`LINKEDIN_CLIENT_SECRET`** (and optionally `LINKEDIN_CLIENT_ID`) in `.env`.
3. Run:

```bash
python scripts/linkedin_oauth_local.py
```

Sign in when the browser opens, click **Allow**, and the script will exchange the code and **update `LINKEDIN_ACCESS_TOKEN` in `.env`**.

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
├── scripts/
│   └── linkedin_oauth_local.py
└── tests/
    ├── test_post_generator.py
    └── test_full_pipeline.py
```

## Tech stack

- **Python 3.10+**
- **Gemini AI** (`google-generativeai`) for long-form posts
- **ChromaDB** for embeddings, post history, and market insight recall
- **APScheduler** with cron triggers and timezone support
- **LinkedIn REST API v2** (`ugcPosts`, OAuth2 bearer token) via **requests**
- **BeautifulSoup** + **requests** for lightweight research scraping and Google News RSS
- **Azure** themes appear in prompts and calendar topics (cloud IoT patterns)

## Tests

**Unit + generator tests:**

```bash
python -m pytest tests/ -v
```

**Full pipeline (orchestrator) without real Gemini or LinkedIn:**

```bash
python -m pytest tests/test_full_pipeline.py -v
```

These tests mock `PostGenerator.generate_post` and stub market research so Chroma + dry-run publish run end-to-end.

**Live smoke test** (real Gemini + HTTP research + Chroma; LinkedIn skipped if `--dry-run`):

```bash
# Requires a valid GEMINI_API_KEY and LinkedIn credentials in .env
python main.py --run-now --dry-run --day 1
```

If you see `API_KEY_INVALID`, create a new key in [Google AI Studio](https://aistudio.google.com/) and set `GEMINI_API_KEY` in `.env`.

## License

MIT
