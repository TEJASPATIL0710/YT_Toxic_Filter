"""
main.py (backend)

Run with:
    uvicorn backend.main:app --reload

Endpoints:
    POST /fetch/vod/{video_id}   -- fetch + classify one batch of VOD comments
    POST /fetch/live/{video_id}  -- fetch + classify one batch of live chat messages
    GET  /comments                -- list stored comments (optionally filtered)
    GET  /comments/toxic          -- list only comments flagged as toxic

The backend never talks to the frontend directly -- the Streamlit
dashboard calls these HTTP endpoints. This separation means you could
swap the dashboard for a React app later without touching this file.
"""

from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
load_dotenv()  # Load .env file for YT_API_KEY and PERSPECTIVE_API_KEY

from classifier.keyword_classifier import KeywordClassifier
from database.db import get_db, init_db
from database.models import ClassificationRecord, CommentRecord
from fetcher.livechat_fetcher import LiveChatFetcher
from fetcher.vod_fetcher import VodFetcher
from pipeline.pipeline import process_batch

app = FastAPI(title="YouTube Toxic Comment Filter API")

# Using the offline keyword classifier as the default so the whole app
# runs with zero API keys beyond YT_API_KEY. Swap this for
# PerspectiveClassifier() once you have a Perspective API key -- see
# classifier/perspective_classifier.py.
_classifier = KeywordClassifier()


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/fetch/vod/{video_id}")
def fetch_vod(video_id: str, db: Session = Depends(get_db)):
    try:
        fetcher = VodFetcher(video_id=video_id)
        results = process_batch(fetcher, _classifier, db)
        return {"video_id": video_id, "fetched": len(results), "results": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/fetch/live/{video_id}")
def fetch_live(video_id: str, db: Session = Depends(get_db)):
    try:
        fetcher = LiveChatFetcher(video_id=video_id)
        results = process_batch(fetcher, _classifier, db)
        return {
            "video_id": video_id,
            "fetched": len(results),
            "results": results,
            "poll_delay_seconds": fetcher.poll_delay_seconds(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/comments")
def list_comments(
    video_id: Optional[str] = None,
    source: Optional[str] = Query(None, regex="^(vod|live)$"),
    db: Session = Depends(get_db),
):
    query = db.query(CommentRecord)
    if video_id:
        query = query.filter(CommentRecord.video_id == video_id)
    if source:
        query = query.filter(CommentRecord.source == source)

    comments = query.order_by(CommentRecord.fetched_at.desc()).limit(200).all()
    return [_serialize_comment(c) for c in comments]


@app.get("/comments/toxic")
def list_toxic_comments(video_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = (
        db.query(CommentRecord)
        .join(ClassificationRecord)
        .filter(ClassificationRecord.is_toxic == 1)
    )
    if video_id:
        query = query.filter(CommentRecord.video_id == video_id)

    comments = query.order_by(CommentRecord.fetched_at.desc()).limit(200).all()
    return [_serialize_comment(c) for c in comments]


def _serialize_comment(c: CommentRecord) -> dict:
    latest = c.classifications[-1] if c.classifications else None
    return {
        "comment_id": c.comment_id,
        "video_id": c.video_id,
        "author": c.author,
        "text": c.text,
        "source": c.source,
        "toxicity_score": latest.toxicity_score if latest else None,
        "is_toxic": bool(latest.is_toxic) if latest else None,
        "classifier": latest.classifier_name if latest else None,
    }
