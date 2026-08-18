from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Player
from schemas import PlayerSchema
from auth import get_active_room_id

router = APIRouter(prefix="/api/players", tags=["Players"])

@router.get("", response_model=List[PlayerSchema])
def get_players(
    search: Optional[str] = Query(None, description="Search by name or code"),
    position: Optional[str] = Query(None, description="Filter by position (GK, DEF, MID, ATT)"),
    status: Optional[str] = Query(None, description="Filter by status (AVAILABLE, SOLD, UNSOLD)"),
    sort: Optional[str] = Query("code_asc", description="Sort by score_desc, score_asc, price_desc, price_asc, name_asc, code_asc"),
    db: Session = Depends(get_db),
    room_id: int = Depends(get_active_room_id)
):
    query = db.query(Player).filter(Player.room_id == room_id)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter((Player.name.ilike(term)) | (Player.player_code.ilike(term)))

    if position and position.upper() != "ALL":
        query = query.filter(Player.position == position.upper())

    if status and status.upper() != "ALL":
        query = query.filter(Player.status == status.upper())

    if sort == "score_desc":
        query = query.order_by(Player.score.desc())
    elif sort == "score_asc":
        query = query.order_by(Player.score.asc())
    elif sort == "price_desc":
        query = query.order_by(Player.base_price.desc())
    elif sort == "price_asc":
        query = query.order_by(Player.base_price.asc())
    elif sort == "name_asc":
        query = query.order_by(Player.name.asc())
    else:
        query = query.order_by(Player.player_code.asc())

    players = query.all()
    return [PlayerSchema.model_validate(p) for p in players]

@router.get("/{player_id}", response_model=PlayerSchema)
def get_player(player_id: int, db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    player = db.query(Player).filter(Player.id == player_id, Player.room_id == room_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return PlayerSchema.model_validate(player)
