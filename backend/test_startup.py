import os
import sqlite3
import subprocess
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent


def test_clean_database_startup_seeds_both_rooms(tmp_path):
    database_path = tmp_path / "fresh-start.db"
    env = os.environ.copy()
    env.pop("VERCEL", None)
    env["DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
    env["AUTH_SECRET"] = "startup-test-secret-with-at-least-32-characters"
    env["ROOM1_ADMIN_PASSWORD"] = "test-room-1"
    env["ROOM2_ADMIN_PASSWORD"] = "test-room-2"
    env["SUPER_ADMIN_PASSWORD"] = "test-super"

    result = subprocess.run(
        [sys.executable, "-c", "from main import initialize_database; initialize_database()"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    with sqlite3.connect(database_path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM teams").fetchone()[0] == 40
        assert connection.execute("SELECT COUNT(*) FROM players").fetchone()[0] == 304


def test_vercel_refuses_ephemeral_database_configuration():
    env = os.environ.copy()
    env["VERCEL"] = "1"
    # Empty blocks a developer's ignored backend/.env from filling the value.
    env["DATABASE_URL"] = ""
    result = subprocess.run(
        [sys.executable, "-c", "import database"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0
    assert "DATABASE_URL is required on Vercel" in result.stderr
