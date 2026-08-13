from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import TeamStateSchema
from services.scoring import get_all_teams_leaderboard

router = APIRouter(prefix="/api/results", tags=["Results"])

@router.get("", response_model=List[TeamStateSchema])
def get_leaderboard(db: Session = Depends(get_db)):
    return get_all_teams_leaderboard(db)
