import json
import io
import math
from typing import Dict, List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from models import Setting, Player, Team, Transaction
from schemas import ImportResultSchema, SettingSchema
from services.excel_import import process_excel_import, generate_sample_excel
from auth import CurrentUser, get_active_room_id, get_current_user, require_super_admin

router = APIRouter(tags=["Admin & Settings"])
MAX_IMPORT_BYTES = 4 * 1024 * 1024
POSITION_SETTING_KEYS = {
    "required_gk",
    "required_def",
    "required_mid",
    "required_att",
}
ALLOWED_SETTING_KEYS = POSITION_SETTING_KEYS | {"starting_budget", "auction_status"}

@router.post("/api/admin/import", response_model=ImportResultSchema)
async def import_excel_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    room_id: int = Depends(get_active_room_id),
    _admin: CurrentUser = Depends(require_super_admin),
):
    filename = file.filename or ""
    if not filename.lower().endswith((".xlsx", ".xls", ".csv")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel (.xlsx, .xls) or CSV (.csv) file.")

    contents = await file.read(MAX_IMPORT_BYTES + 1)
    if len(contents) > MAX_IMPORT_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Import file exceeds the 4 MB application limit for Vercel requests.",
        )
    return process_excel_import(contents, filename, db, room_id)

@router.get("/api/admin/sample-template")
def download_sample_template(_user: CurrentUser = Depends(get_current_user)):
    excel_bytes = generate_sample_excel()
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=fifa_players_sample.xlsx"}
    )

import io

@router.get("/api/admin/backup")
def export_backup_json(db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    players = [
        {
            "id": p.id,
            "player_code": p.player_code,
            "name": p.name,
            "position": p.position,
            "p1": p.p1,
            "p2": p.p2,
            "p3": p.p3,
            "score": p.score,
            "base_price": p.base_price,
            "nationality": p.nationality,
            "club": p.club,
            "status": p.status,
            "team_id": p.team_id,
            "sold_price": p.sold_price,
            "is_captain": p.is_captain
        }
        for p in db.query(Player).filter(Player.room_id == room_id).all()
    ]
    teams = [
        {
            "id": t.id,
            "team_number": t.team_number,
            "starting_budget": t.starting_budget
        }
        for t in db.query(Team).filter(Team.room_id == room_id).all()
    ]
    txns = [
        {
            "id": tx.id,
            "event_type": tx.event_type,
            "player_id": tx.player_id,
            "team_id": tx.team_id,
            "amount": tx.amount,
            "timestamp": tx.timestamp.isoformat() if tx.timestamp else None
        }
        for tx in db.query(Transaction).filter(Transaction.room_id == room_id).all()
    ]
    settings = {
        s.key: s.value for s in db.query(Setting).filter(Setting.room_id == room_id).all()
    }

    backup_data = {
        "room_id": room_id,
        "players": players,
        "teams": teams,
        "transactions": txns,
        "settings": settings
    }

    content = json.dumps(backup_data, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=fifa_auction_backup.json"}
    )

@router.post("/api/admin/reset")
def reset_room_auction(db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    player_count = db.query(Player).filter(Player.room_id == room_id).update(
        {
            "status": "AVAILABLE",
            "team_id": None,
            "sold_price": None,
            "is_captain": False,
        },
        synchronize_session=False,
    )
    transaction_count = db.query(Transaction).filter(Transaction.room_id == room_id).delete(
        synchronize_session=False
    )
    db.commit()
    return {
        "success": True,
        "room_id": room_id,
        "players_reset": player_count,
        "transactions_removed": transaction_count,
    }

@router.get("/api/settings", response_model=Dict[str, str])
def get_settings(db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    settings = db.query(Setting).filter(Setting.room_id == room_id).all()
    return {s.key: s.value for s in settings}

@router.put("/api/settings", response_model=Dict[str, str])
def update_settings(new_settings: Dict[str, str], db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    unknown_keys = sorted(set(new_settings) - ALLOWED_SETTING_KEYS)
    if unknown_keys:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown setting(s): {', '.join(unknown_keys)}",
        )

    normalized_settings = {key: str(value) for key, value in new_settings.items()}
    if "starting_budget" in new_settings:
        try:
            budget = float(new_settings["starting_budget"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="starting_budget must be a number")
        if not math.isfinite(budget) or budget <= 0:
            raise HTTPException(
                status_code=422,
                detail="starting_budget must be a finite number greater than zero",
            )

        highest_spend = db.query(
            func.coalesce(func.sum(Player.sold_price), 0.0)
        ).filter(
            Player.room_id == room_id,
            Player.status == "SOLD",
        ).group_by(Player.team_id).order_by(
            func.sum(Player.sold_price).desc()
        ).first()
        minimum_budget = round(float(highest_spend[0]), 2) if highest_spend else 0.0
        if round(budget, 2) < minimum_budget:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"starting_budget cannot be lower than the highest amount already "
                    f"spent by a team ({minimum_budget:.2f} M)"
                ),
            )
        normalized_settings["starting_budget"] = format(budget, "g")

    for key in POSITION_SETTING_KEYS.intersection(new_settings):
        try:
            requirement = int(new_settings[key])
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail=f"{key} must be a whole number")
        if requirement < 0 or requirement > 20:
            raise HTTPException(status_code=422, detail=f"{key} must be between 0 and 20")
        normalized_settings[key] = str(requirement)

    for key, value in normalized_settings.items():
        setting = db.query(Setting).filter(Setting.room_id == room_id, Setting.key == key).first()
        if setting:
            setting.value = value
        else:
            db.add(Setting(room_id=room_id, key=key, value=value))
    
    # If starting_budget updated, update all teams
    if "starting_budget" in new_settings:
        db.query(Team).filter(Team.room_id == room_id).update({"starting_budget": budget})

    db.commit()
    settings = db.query(Setting).filter(Setting.room_id == room_id).all()
    return {s.key: s.value for s in settings}
