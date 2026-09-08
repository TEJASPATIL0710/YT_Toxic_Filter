"""
models.py

Defines the two tables this project needs:

1. CommentRecord  -- one row per comment/chat message we've fetched
2. ClassificationRecord -- one row per toxicity score computed for a
   comment (kept separate from CommentRecord so you can re-run a
   different classifier later and keep both sets of scores side by
   side for comparison, e.g. baseline vs. custom model in Sprint 3)
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database.db import Base


class CommentRecord(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_id = Column(String, unique=True, index=True, nullable=False)
    video_id = Column(String, index=True, nullable=False)
    author = Column(String, nullable=False)
    text = Column(String, nullable=False)
    published_at = Column(String, nullable=True)
    source = Column(String, nullable=False)  # "vod" or "live"
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    classifications = relationship(
        "ClassificationRecord", back_populates="comment", cascade="all, delete-orphan"
    )


class ClassificationRecord(Base):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    comment_pk = Column(Integer, ForeignKey("comments.id"), nullable=False)
    classifier_name = Column(String, nullable=False)  # e.g. "keyword_baseline", "perspective"
    toxicity_score = Column(Float, nullable=False)  # 0.0 - 1.0
    is_toxic = Column(Integer, nullable=False)  # 0 or 1, based on threshold at classify-time
    classified_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    comment = relationship("CommentRecord", back_populates="classifications")
