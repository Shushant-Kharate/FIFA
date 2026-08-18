import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import load_local_env


load_local_env()


DEFAULT_SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auction_v2.db")
configured_database_url = os.getenv("DATABASE_URL")
if os.getenv("VERCEL") and not configured_database_url:
    raise RuntimeError(
        "DATABASE_URL is required on Vercel. Configure the pooled Neon PostgreSQL "
        "connection string; serverless SQLite storage is not persistent."
    )

DATABASE_URL = configured_database_url or f"sqlite:///{DEFAULT_SQLITE_PATH}"

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine_options = {"connect_args": connect_args, "pool_pre_ping": True}
if DATABASE_URL.startswith("postgresql"):
    # Keep each warm serverless instance's pool deliberately small. Neon pooling
    # multiplexes these client connections onto a controlled database pool.
    engine_options.update(pool_size=2, max_overflow=0, pool_recycle=300)

engine = create_engine(DATABASE_URL, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
