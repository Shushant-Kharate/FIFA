import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from models import AuditLog


def add_audit_log(
    db: Session,
    room_id: int,
    action: str,
    actor_username: str,
    description: str,
    *,
    player_id: Optional[int] = None,
    team_id: Optional[int] = None,
    amount: Optional[float] = None,
    details: Optional[dict[str, Any]] = None,
) -> AuditLog:
    entry = AuditLog(
        room_id=room_id,
        action=action,
        actor_username=actor_username,
        description=description,
        player_id=player_id,
        team_id=team_id,
        amount=amount,
        details_json=json.dumps(details, sort_keys=True) if details else None,
    )
    db.add(entry)
    return entry
