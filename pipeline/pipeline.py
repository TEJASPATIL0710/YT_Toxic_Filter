"""
pipeline.py

The glue layer: takes any CommentFetcher (VOD or live), runs each
comment through a ToxicityClassifier, and persists both the comment
and its classification to the database.

This is deliberately fetcher-agnostic and classifier-agnostic -- it
depends only on the two abstract interfaces, not on any concrete
implementation. That's what lets VOD and live chat share this exact
same code path.
"""

from sqlalchemy.orm import Session

from classifier.base import ToxicityClassifier
from database.models import ClassificationRecord, CommentRecord
from fetcher.base import CommentFetcher


def process_batch(
    fetcher: CommentFetcher, classifier: ToxicityClassifier, db: Session
) -> list[dict]:
    """
    Pulls one batch from the fetcher, classifies each comment, stores
    both the comment and its classification, and returns a list of
    plain dicts describing what was processed (handy for the API/UI
    layer to display immediately without a second DB query).
    """
    results = []

    for comment in fetcher.fetch_batch():
        # Skip if we've already stored this exact comment (e.g. re-polling
        # live chat can occasionally overlap at page boundaries).
        existing = (
            db.query(CommentRecord)
            .filter(CommentRecord.comment_id == comment.comment_id)
            .first()
        )
        if existing:
            continue

        record = CommentRecord(
            comment_id=comment.comment_id,
            video_id=comment.video_id,
            author=comment.author,
            text=comment.text,
            published_at=comment.published_at,
            source=comment.source,
        )
        db.add(record)
        db.flush()  # assigns record.id without committing yet

        classification = classifier.classify(comment.text)
        db.add(
            ClassificationRecord(
                comment_pk=record.id,
                classifier_name=classification.classifier_name,
                toxicity_score=classification.toxicity_score,
                is_toxic=int(classification.is_toxic),
            )
        )

        results.append(
            {
                "comment_id": comment.comment_id,
                "author": comment.author,
                "text": comment.text,
                "source": comment.source,
                "toxicity_score": classification.toxicity_score,
                "is_toxic": classification.is_toxic,
                "classifier": classification.classifier_name,
            }
        )

    db.commit()
    return results
