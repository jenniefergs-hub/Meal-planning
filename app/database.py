import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"


def _normalize_database_url(url: str) -> str:
    """Point postgres://... and postgresql://... URLs at the psycopg driver.

    Hosted Postgres providers (Neon, Render, etc.) commonly hand out URLs
    with a bare postgres:// or postgresql:// scheme; SQLAlchemy needs the
    driver spelled out to pick psycopg.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


def _build_engine():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return create_engine(_normalize_database_url(database_url), pool_pre_ping=True)

    DATA_DIR.mkdir(exist_ok=True)
    db_path = DATA_DIR / "app.db"
    return create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_light_migrations():
    """Add columns introduced after a table already existed on disk.

    create_all() only creates missing tables, so a pre-existing database
    needs new columns added by hand.
    """
    inspector = inspect(engine)
    if "recipes" not in inspector.get_table_names():
        return
    existing_cols = {c["name"] for c in inspector.get_columns("recipes")}
    is_postgres = engine.dialect.name == "postgresql"
    timestamp_type = "TIMESTAMP" if is_postgres else "DATETIME"
    binary_type = "BYTEA" if is_postgres else "BLOB"
    with engine.begin() as conn:
        if "times_cooked" not in existing_cols:
            conn.execute(text("ALTER TABLE recipes ADD COLUMN times_cooked INTEGER DEFAULT 0"))
        if "last_cooked_at" not in existing_cols:
            conn.execute(text(f"ALTER TABLE recipes ADD COLUMN last_cooked_at {timestamp_type}"))
        if "image_data" not in existing_cols:
            conn.execute(text(f"ALTER TABLE recipes ADD COLUMN image_data {binary_type}"))
        if "image_content_type" not in existing_cols:
            conn.execute(text("ALTER TABLE recipes ADD COLUMN image_content_type VARCHAR"))
