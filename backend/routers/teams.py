from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Team
from schemas import TeamStateSchema, SetCaptainRequest
from services.scoring import get_team_state
from services.auction_service import set_captain

router = APIRouter(prefix="/api/teams", tags=["Teams"])

@router.get("", response_model=List[TeamStateSchema])
def get_all_teams(db: Session = Depends(get_db)):
    teams = db.query(Team).order_by(Team.team_number.asc()).all()
    return [get_team_state(t.id, db) for t in teams]

@router.get("/{team_id}", response_model=TeamStateSchema)
def get_single_team(team_id: int, db: Session = Depends(get_db)):
    try:
        return get_team_state(team_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{team_id}/captain", response_model=TeamStateSchema)
def update_team_captain(team_id: int, body: SetCaptainRequest, db: Session = Depends(get_db)):
    return set_captain(team_id=team_id, player_id=body.player_id, db=db)
