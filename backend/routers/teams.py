from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import TeamStateSchema, SetCaptainRequest
from services.scoring import get_all_team_states, get_team_state
from services.auction_service import set_captain
from auth import get_active_room_id

router = APIRouter(prefix="/api/teams", tags=["Teams"])

@router.get("", response_model=List[TeamStateSchema])
def get_all_teams(db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    return get_all_team_states(db, room_id)

@router.get("/{team_id}", response_model=TeamStateSchema)
def get_single_team(team_id: int, db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    try:
        return get_team_state(team_id, db, room_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{team_id}/captain", response_model=TeamStateSchema)
def update_team_captain(team_id: int, body: SetCaptainRequest, db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    return set_captain(team_id=team_id, player_id=body.player_id, db=db, room_id=room_id)
