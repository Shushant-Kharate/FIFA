import os
from pathlib import Path


def load_local_env() -> None:
    """Load ignored local-development secrets without overriding real env vars."""
    env_path = Path(__file__).with_name(".env")
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def validate_production_environment() -> None:
    """Fail explicitly when a Vercel deployment is missing required secrets."""
    if not os.getenv("VERCEL"):
        return

    required = (
        "DATABASE_URL",
        "AUTH_SECRET",
        "ROOM1_ADMIN_PASSWORD",
        "ROOM2_ADMIN_PASSWORD",
        "SUPER_ADMIN_PASSWORD",
    )
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            "Missing required Vercel environment variables: " + ", ".join(missing)
        )

    if len(os.environ["AUTH_SECRET"]) < 32:
        raise RuntimeError("AUTH_SECRET must contain at least 32 characters in production")

    if os.environ["DATABASE_URL"].startswith("sqlite"):
        raise RuntimeError("SQLite is not supported for persistent production data on Vercel")
