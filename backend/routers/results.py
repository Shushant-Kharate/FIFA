from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import TeamStateSchema
from services.scoring import get_all_teams_leaderboard
from auth import get_active_room_id

router = APIRouter(prefix="/api/results", tags=["Results"])

@router.get("", response_model=List[TeamStateSchema])
def get_leaderboard(db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    return get_all_teams_leaderboard(db, room_id)
