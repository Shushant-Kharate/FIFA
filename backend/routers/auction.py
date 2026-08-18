from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Transaction, Player, Team
from schemas import (
    SellPlayerRequest, UnsoldPlayerRequest, UndoRequest, ReturnToPoolRequest,
    TeamStateSchema, PlayerSchema, TransactionSchema
)
from services.auction_service import sell_player, mark_unsold, undo_last_sale, return_to_pool
from auth import get_active_room_id

router = APIRouter(prefix="/api/auction", tags=["Auction"])

@router.post("/sell", response_model=TeamStateSchema)
def auction_sell(req: SellPlayerRequest, db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    return sell_player(player_id=req.player_id, team_id=req.team_id, price=req.price, db=db, room_id=room_id)

@router.post("/unsold", response_model=PlayerSchema)
def auction_unsold(req: UnsoldPlayerRequest, db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    return mark_unsold(player_id=req.player_id, db=db, room_id=room_id)

@router.post("/undo", response_model=PlayerSchema)
def auction_undo(req: UndoRequest, db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    return undo_last_sale(player_id=req.player_id, db=db, room_id=room_id)

@router.post("/return-to-pool", response_model=PlayerSchema)
def auction_return_to_pool(req: ReturnToPoolRequest, db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    return return_to_pool(player_id=req.player_id, db=db, room_id=room_id)

@router.get("/history", response_model=List[TransactionSchema])
def get_auction_history(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    txns = db.query(Transaction).filter(Transaction.room_id == room_id).order_by(Transaction.timestamp.desc()).limit(limit).all()
    return [TransactionSchema.model_validate(t) for t in txns]
