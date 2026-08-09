from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "app.db"

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
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

    create_all() only creates missing tables, so pre-existing SQLite files
    need their new columns added by hand.
    """
    inspector = inspect(engine)
    if "recipes" not in inspector.get_table_names():
        return
    existing_cols = {c["name"] for c in inspector.get_columns("recipes")}
    with engine.begin() as conn:
        if "times_cooked" not in existing_cols:
            conn.execute(text("ALTER TABLE recipes ADD COLUMN times_cooked INTEGER DEFAULT 0"))
        if "last_cooked_at" not in existing_cols:
            conn.execute(text("ALTER TABLE recipes ADD COLUMN last_cooked_at DATETIME"))
