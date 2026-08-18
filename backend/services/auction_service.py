from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models import Player, Team, Transaction
from services.scoring import get_team_state
from schemas import TeamStateSchema, PlayerSchema

def sell_player(player_id: int, team_id: int, price: float, db: Session, room_id: int) -> TeamStateSchema:
    player = db.query(Player).filter(Player.id == player_id, Player.room_id == room_id).with_for_update().first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player ID {player_id} not found")

    if player.status == "SOLD":
        raise HTTPException(
            status_code=400,
            detail=f"Player {player.name} is already SOLD to Team {player.team_id}"
        )

    team = db.query(Team).filter(Team.id == team_id, Team.room_id == room_id).with_for_update().first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team ID {team_id} not found")

    team_state = get_team_state(team_id, db, room_id)
    if round(price, 2) > team_state.remaining_budget:
        raise HTTPException(
            status_code=400,
            detail=f"Team {team.team_number} has only {team_state.remaining_budget:.2f} M remaining. Cannot afford {price:.2f} M."
        )

    # Update player
    player.status = "SOLD"
    player.team_id = team_id
    player.sold_price = round(price, 2)

    # Log transaction
    txn = Transaction(
        room_id=room_id,
        event_type="SOLD",
        player_id=player_id,
        team_id=team_id,
        amount=round(price, 2)
    )
    db.add(txn)
    db.commit()

    return get_team_state(team_id, db, room_id)

def mark_unsold(player_id: int, db: Session, room_id: int) -> PlayerSchema:
    player = db.query(Player).filter(Player.id == player_id, Player.room_id == room_id).with_for_update().first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player ID {player_id} not found")

    if player.status != "AVAILABLE":
        raise HTTPException(status_code=400, detail="Only an AVAILABLE player can be marked UNSOLD")

    prev_team_id = player.team_id
    player.status = "UNSOLD"
    player.team_id = None
    player.sold_price = None
    player.is_captain = False

    txn = Transaction(
        room_id=room_id,
        event_type="UNSOLD",
        player_id=player_id,
        team_id=prev_team_id,
        amount=None
    )
    db.add(txn)
    db.commit()
    db.refresh(player)

    return PlayerSchema.model_validate(player)

def undo_last_sale(player_id: int, db: Session, room_id: int) -> PlayerSchema:
    player = db.query(Player).filter(Player.id == player_id, Player.room_id == room_id).with_for_update().first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player ID {player_id} not found")

    last_txn = db.query(Transaction).filter(
        Transaction.player_id == player_id
    ).filter(
        Transaction.room_id == room_id
    ).order_by(Transaction.timestamp.desc(), Transaction.id.desc()).first()

    if not last_txn:
        raise HTTPException(status_code=400, detail=f"No transaction history found for player ID {player_id}")

    if player.status != "SOLD" or last_txn.event_type != "SOLD":
        raise HTTPException(status_code=400, detail="Only the player's latest sale can be undone")

    prev_team_id = player.team_id
    player.status = "AVAILABLE"
    player.team_id = None
    player.sold_price = None
    player.is_captain = False

    undo_txn = Transaction(
        room_id=room_id,
        event_type="UNDO",
        player_id=player_id,
        team_id=prev_team_id,
        amount=None
    )
    db.add(undo_txn)
    db.commit()
    db.refresh(player)

    return PlayerSchema.model_validate(player)

def return_to_pool(player_id: int, db: Session, room_id: int) -> PlayerSchema:
    player = db.query(Player).filter(Player.id == player_id, Player.room_id == room_id).with_for_update().first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player ID {player_id} not found")

    if player.status != "UNSOLD":
        raise HTTPException(status_code=400, detail=f"Player is not in UNSOLD status")

    player.status = "AVAILABLE"
    player.team_id = None
    player.sold_price = None
    player.is_captain = False

    txn = Transaction(
        room_id=room_id,
        event_type="RETURN_TO_POOL",
        player_id=player_id,
        team_id=None,
        amount=None
    )
    db.add(txn)
    db.commit()
    db.refresh(player)

    return PlayerSchema.model_validate(player)

def set_captain(team_id: int, player_id: int, db: Session, room_id: int) -> TeamStateSchema:
    player = db.query(Player).filter(Player.id == player_id, Player.room_id == room_id).with_for_update().first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player ID {player_id} not found")

    if player.team_id != team_id or player.status != "SOLD":
        raise HTTPException(status_code=400, detail="Player is not owned by this team")

    # Serialize captain changes for one team so concurrent administrators can
    # never commit two captains for the same squad.
    team = db.query(Team).filter(
        Team.id == team_id, Team.room_id == room_id
    ).with_for_update().first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team ID {team_id} not found")

    team_state = get_team_state(team_id, db, room_id)
    if player_id not in team_state.best_8_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Captain must be a member of the team's Best 8 players. {player.name} is currently on the bench or team is unqualified."
        )

    # Reset captain for all team players
    db.query(Player).filter(Player.team_id == team_id, Player.room_id == room_id).update({"is_captain": False})

    player.is_captain = True

    txn = Transaction(
        room_id=room_id,
        event_type="CAPTAIN_SET",
        player_id=player_id,
        team_id=team_id,
        amount=None
    )
    db.add(txn)
    db.commit()

    return get_team_state(team_id, db, room_id)
