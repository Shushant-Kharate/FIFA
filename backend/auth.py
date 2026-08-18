import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from config import load_local_env


load_local_env()


@dataclass(frozen=True)
class CurrentUser:
    username: str
    role: str
    room_id: Optional[int]


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _auth_secret() -> bytes:
    secret = os.getenv("AUTH_SECRET")
    if not secret:
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    return secret.encode("utf-8")


def configured_accounts():
    return {
        os.getenv("ROOM1_ADMIN_USERNAME", "room1_admin"): {
            "password": os.getenv("ROOM1_ADMIN_PASSWORD"), "role": "ROOM_ADMIN", "room_id": 1
        },
        os.getenv("ROOM2_ADMIN_USERNAME", "room2_admin"): {
            "password": os.getenv("ROOM2_ADMIN_PASSWORD"), "role": "ROOM_ADMIN", "room_id": 2
        },
        os.getenv("SUPER_ADMIN_USERNAME", "super_admin"): {
            "password": os.getenv("SUPER_ADMIN_PASSWORD"), "role": "SUPER_ADMIN", "room_id": None
        },
    }


def authenticate(username: str, password: str) -> Optional[CurrentUser]:
    account = configured_accounts().get(username)
    # Keep unknown and unconfigured accounts on the same comparison path so the
    # login response does not provide an easy username timing oracle.
    candidate = account["password"] if account and account["password"] else "invalid-account"
    password_matches = hmac.compare_digest(password.encode(), candidate.encode())
    if not account or not account["password"] or not password_matches:
        return None
    return CurrentUser(username=username, role=account["role"], room_id=account["room_id"])


def create_access_token(user: CurrentUser) -> str:
    payload = {
        "sub": user.username,
        "role": user.role,
        "room_id": user.room_id,
        "exp": int(time.time()) + int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "43200")),
    }
    encoded = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _b64encode(hmac.new(_auth_secret(), encoded.encode(), hashlib.sha256).digest())
    return f"{encoded}.{signature}"


def get_current_user(authorization: Optional[str] = Header(None)) -> CurrentUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        encoded, signature = authorization[7:].split(".", 1)
        expected = _b64encode(hmac.new(_auth_secret(), encoded.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("invalid signature")
        payload = json.loads(_b64decode(encoded))
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("expired token")
        account = configured_accounts().get(payload["sub"])
        if (
            not account
            or account["role"] != payload["role"]
            or account["room_id"] != payload.get("room_id")
        ):
            raise ValueError("account no longer configured")
        return CurrentUser(payload["sub"], payload["role"], payload.get("room_id"))
    except (ValueError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def get_active_room_id(
    user: CurrentUser = Depends(get_current_user),
    x_room_id: Optional[int] = Header(None),
) -> int:
    if user.role == "ROOM_ADMIN":
        return user.room_id
    room_id = x_room_id or 1
    if room_id not in (1, 2):
        raise HTTPException(status_code=400, detail="Room must be 1 or 2")
    return room_id


def require_super_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Super-admin access required")
    return user
