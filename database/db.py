"""
db.py

Sets up the SQLAlchemy engine and session. Defaults to a local SQLite
file (data/app.db) so the project runs with zero external setup.

To move to PostgreSQL later (e.g. for deployment), you'd only need to
change DATABASE_URL -- nothing else in the codebase references SQLite
directly, since all queries go through the ORM.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/app.db")

# check_same_thread=False is only needed for SQLite (it's not thread-safe
# by default, and FastAPI/Streamlit may hit the DB from different threads).
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Create all tables if they don't already exist. Safe to call every startup."""
    import database.models  # noqa: F401 -- ensures models are registered on Base
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency: yields a session, closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
