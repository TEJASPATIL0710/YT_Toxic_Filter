# YouTube Toxic Comment Filter — Full Project Overview & Setup

A full-stack moderation tool that fetches YouTube comments (regular
videos AND live stream chat), scores them for toxicity, stores results
in a database, and shows everything in a browsable dashboard.

## 1. Architecture (Current Architecture)

```
┌────────────────┐     ┌────────────────┐
│ VodFetcher      │     │ LiveChatFetcher │
└───────┬────────┘     └───────┬────────┘
        │   (both implement CommentFetcher)
        ▼
┌──────────────────────────────────────┐
│ Pipeline (pipeline/pipeline.py)        │
│  - dedupes comments already stored     │
│  - runs classifier                     │
│  - writes CommentRecord +              │
│    ClassificationRecord to DB          │
└───────────────┬───────────────────────┘
                ▼
     ┌─────────────────────┐
     │ SQLite DB (data/app.db) │
     │  via SQLAlchemy models  │
     └───────────┬─────────┘
                 ▼
     ┌────────────────────┐        ┌───────────────────────┐
     │ FastAPI backend      │◄──────│ Streamlit dashboard      │
     │ (backend/main.py)    │  HTTP │ (dashboard/app.py)       │
     └────────────────────┘        └───────────────────────┘
```

- **Classifier**: `KeywordClassifier` is the default — a fully offline,
  zero-API-key baseline, so the whole app runs immediately without any
  paid service. `PerspectiveClassifier` is included and ready to swap
  in once you get a (free) Perspective API key — see
  `classifier/perspective_classifier.py`.
- **Database**: SQLite by default (`data/app.db`), created
  automatically on first run. Swappable to PostgreSQL later by just
  changing the `DATABASE_URL` environment variable — no code changes
  needed, since everything goes through the SQLAlchemy ORM.

## 2. Project structure

```
yt-toxic-filter/
├── fetcher/
│   ├── base.py               # Shared CommentFetcher interface + Comment model
│   ├── vod_fetcher.py        # Regular video comments
│   └── livechat_fetcher.py   # Live stream chat (polling)
├── classifier/
│   ├── base.py                    # Shared ToxicityClassifier interface
│   ├── keyword_classifier.py      # Offline baseline (default, no API key)
│   └── perspective_classifier.py  # Optional Google Perspective API wrapper
├── pipeline/
│   └── pipeline.py           # fetch -> dedupe -> classify -> store
├── database/
│   ├── db.py                 # Engine/session setup (SQLite by default)
│   └── models.py             # CommentRecord, ClassificationRecord
├── backend/
│   └── main.py                # FastAPI app: /fetch/vod, /fetch/live, /comments
├── dashboard/
│   └── app.py                 # Streamlit UI, calls the backend over HTTP
├── data/                      # SQLite DB file lives here (gitignored)
├── tests/                     # 8 passing unit tests, no network/API key needed
├── requirements.txt
├── .gitignore
└── README.md
```

## 3. Setup

1. Unzip the project, open a terminal inside `yt-toxic-filter/`.
2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```
3. Install everything (backend, frontend, db, fetcher — all deps in one file):
   ```
   pip install -r requirements.txt
   ```
4. Get a YouTube Data API key (console.cloud.google.com → enable
   "YouTube Data API v3" → Credentials → Create API key), then set it:
   ```
   export YT_API_KEY="your-key-here"
   ```
5. Confirm everything's wired up:
   ```
   pytest tests/ -v
   ```
   Expect `8 passed`.

## 4. Running the full app (two terminals)

**Terminal 1 — backend:**
```
uvicorn backend.main:app --reload
```
This creates `data/app.db` automatically on first run and serves the
API at `http://localhost:8000` (interactive docs at
`http://localhost:8000/docs`).

**Terminal 2 — frontend:**
```
streamlit run dashboard/app.py
```
Opens a browser tab. Paste a YouTube video ID into the "Fetch VOD
comments" tab (or a live video's ID into the "Fetch live chat" tab)
and click fetch — it calls the backend, classifies each comment with
the keyword baseline, stores results in SQLite, and shows them in a
table. The "Browse stored comments" tab lets you review everything
that's been fetched so far, filtered by video or by toxic-only.

## 5. Swapping in a stronger classifier

Once you have a Perspective API key (free, from
developers.perspectiveapi.com), set `PERSPECTIVE_API_KEY` and change
one line in `backend/main.py`:
```python
# from:
_classifier = KeywordClassifier()
# to:
from classifier.perspective_classifier import PerspectiveClassifier
_classifier = PerspectiveClassifier()
```
No other code changes needed — the pipeline, database, and dashboard
all work against the shared `ToxicityClassifier` interface.

## 6. What's next (not yet built)

- A fine-tuned custom transformer classifier (Jigsaw dataset),
  benchmarked against the keyword/Perspective baselines.
- Actual moderation actions (auto-hide/ban) via `setModerationStatus`
  (VOD) and `liveChatBans` (live) — right now the app flags/stores,
  it doesn't take action on YouTube itself.
- A background scheduler for continuous live-chat polling (currently
  each dashboard click fetches one batch; a long-running poll loop
  would be needed for true real-time moderation during a stream).
