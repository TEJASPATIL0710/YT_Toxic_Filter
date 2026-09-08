from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from classifier.keyword_classifier import KeywordClassifier
from database.db import Base
from database.models import ClassificationRecord, CommentRecord  # noqa: F401
from fetcher.base import Comment, CommentFetcher
from pipeline.pipeline import process_batch


class FakeFetcher(CommentFetcher):
    """A stand-in fetcher for tests -- returns a fixed list, no network calls."""

    def __init__(self, comments):
        self._comments = comments

    def fetch_batch(self):
        yield from self._comments

    def has_more(self):
        return False

    def poll_delay_seconds(self):
        return None


def _make_test_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_process_batch_stores_comments_and_classifications():
    db = _make_test_session()
    fetcher = FakeFetcher(
        [
            Comment("c1", "v1", "Alice", "You are an idiot", "2026-01-01", "vod"),
            Comment("c2", "v1", "Bob", "Nice video!", "2026-01-01", "vod"),
        ]
    )

    results = process_batch(fetcher, KeywordClassifier(), db)

    assert len(results) == 2
    assert db.query(CommentRecord).count() == 2
    assert db.query(ClassificationRecord).count() == 2

    toxic_result = next(r for r in results if r["comment_id"] == "c1")
    assert toxic_result["is_toxic"] is True


def test_process_batch_skips_duplicate_comments():
    db = _make_test_session()
    comment = Comment("dup1", "v1", "Alice", "Hello", "2026-01-01", "vod")

    process_batch(FakeFetcher([comment]), KeywordClassifier(), db)
    results_second_run = process_batch(FakeFetcher([comment]), KeywordClassifier(), db)

    assert results_second_run == []  # already stored, so nothing new
    assert db.query(CommentRecord).count() == 1
