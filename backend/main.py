import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import engine, Base, SessionLocal, get_db
import models
from config import validate_production_environment
from routers import players, teams, auction, results, admin, auth
from services.excel_import import process_excel_import

logger = logging.getLogger(__name__)
DATASET_PATH = Path(__file__).resolve().with_name("FIFA AUCTION 2026.xlsx")
FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
BOOTSTRAP_LOCK_ID = 2026081801


def initialize_database() -> None:
    """Create and seed the schema once, safely across concurrent cold starts."""
    validate_production_environment()
    connection = engine.connect()
    is_postgres = engine.dialect.name == "postgresql"
    lock_acquired = False
    db = None
    try:
        if is_postgres:
            tables_ready = connection.execute(
                text(
                    "SELECT to_regclass('public.rooms') IS NOT NULL "
                    "AND to_regclass('public.teams') IS NOT NULL "
                    "AND to_regclass('public.players') IS NOT NULL"
                )
            ).scalar()
            if tables_ready:
                room_count, team_count, room1_players, room2_players = connection.execute(
                    text(
                        "SELECT "
                        "(SELECT COUNT(*) FROM rooms), "
                        "(SELECT COUNT(*) FROM teams), "
                        "(SELECT COUNT(*) FROM players WHERE room_id = 1), "
                        "(SELECT COUNT(*) FROM players WHERE room_id = 2)"
                    )
                ).one()
                if (
                    room_count >= 2
                    and team_count >= 40
                    and room1_players > 0
                    and room2_players > 0
                ):
                    return

            connection.execute(
                text("SELECT pg_advisory_lock(:lock_id)"), {"lock_id": BOOTSTRAP_LOCK_ID}
            )
            lock_acquired = True

        Base.metadata.create_all(bind=connection)
        db = SessionLocal(bind=connection)
        for room_id in (1, 2):
            if not db.query(models.Room).filter(models.Room.id == room_id).first():
                db.add(models.Room(id=room_id, name=f"Room {room_id}"))
        db.commit()

        if not DATASET_PATH.is_file():
            raise RuntimeError(f"Required bundled dataset is missing: {DATASET_PATH.name}")
        dataset_bytes = DATASET_PATH.read_bytes()

        for room_id in (1, 2):
            player_count = db.query(models.Player).filter(models.Player.room_id == room_id).count()
            if player_count == 0:
                result = process_excel_import(
                    dataset_bytes, DATASET_PATH.name, db, room_id
                )
                if not result.success:
                    raise RuntimeError(
                        f"Room {room_id} dataset seed failed: {result.message}; "
                        + "; ".join(result.errors[:5])
                    )
                logger.info("Seeded Room %s with %s players", room_id, result.player_count)
        # The session is deliberately bound to this bootstrap connection so the
        # schema and both room seeds become one atomic initialization unit.
        connection.commit()
    except Exception:
        if db is not None:
            db.rollback()
        connection.rollback()
        logger.exception("Database initialization failed")
        raise
    finally:
        if db is not None:
            db.close()
        if lock_acquired:
            connection.execute(
                text("SELECT pg_advisory_unlock(:lock_id)"), {"lock_id": BOOTSTRAP_LOCK_ID}
            )
        connection.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    yield

app = FastAPI(
    title="FIFA Auction Management System API",
    description="Backend API for 20-team live FIFA player auction",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in os.getenv(
            "ALLOWED_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173"
        ).split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def prevent_api_caching(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response

app.include_router(players.router)
app.include_router(teams.router)
app.include_router(auction.router)
app.include_router(results.router)
app.include_router(admin.router)
app.include_router(auth.router)

@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "online",
        "database": "online",
        "message": "FIFA Auction API operational",
    }


if FRONTEND_DIST.is_dir():
    @app.get("/{requested_path:path}", include_in_schema=False)
    def serve_frontend(requested_path: str):
        """Serve built Vite assets and fall back to the SPA entry point."""
        dist_root = FRONTEND_DIST.resolve()
        requested_file = (dist_root / requested_path).resolve()
        try:
            requested_file.relative_to(dist_root)
        except ValueError:
            requested_file = dist_root / "index.html"

        if requested_path and requested_file.is_file():
            return FileResponse(
                requested_file,
                headers={
                    "Cache-Control": "public, max-age=31536000, immutable",
                    "CDN-Cache-Control": "public, s-maxage=31536000, immutable",
                },
            )
        return FileResponse(
            dist_root / "index.html",
            headers={
                "Cache-Control": "no-cache",
                "CDN-Cache-Control": "public, s-maxage=60, stale-while-revalidate=86400",
            },
        )
