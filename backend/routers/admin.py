import json
from typing import Dict, List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from models import Setting, Player, Team, Transaction
from schemas import ImportResultSchema, SettingSchema
from services.excel_import import process_excel_import, generate_sample_excel

router = APIRouter(tags=["Admin & Settings"])

@router.post("/api/admin/import", response_model=ImportResultSchema)
async def import_excel_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls") or file.filename.endswith(".csv")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an Excel (.xlsx, .xls) or CSV (.csv) file.")

    contents = await file.read()
    return process_excel_import(contents, file.filename, db)

@router.get("/api/admin/sample-template")
def download_sample_template():
    excel_bytes = generate_sample_excel()
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=fifa_players_sample.xlsx"}
    )

import io

@router.get("/api/admin/backup")
def export_backup_json(db: Session = Depends(get_db)):
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
            "status": p.status,
            "team_id": p.team_id,
            "sold_price": p.sold_price,
            "is_captain": p.is_captain
        }
        for p in db.query(Player).all()
    ]
    teams = [
        {
            "id": t.id,
            "team_number": t.team_number,
            "starting_budget": t.starting_budget
        }
        for t in db.query(Team).all()
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
        for tx in db.query(Transaction).all()
    ]
    settings = {s.key: s.value for s in db.query(Setting).all()}

    backup_data = {
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

@router.get("/api/settings", response_model=Dict[str, str])
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(Setting).all()
    return {s.key: s.value for s in settings}

@router.put("/api/settings", response_model=Dict[str, str])
def update_settings(new_settings: Dict[str, str], db: Session = Depends(get_db)):
    for key, value in new_settings.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            db.add(Setting(key=key, value=str(value)))
    
    # If starting_budget updated, update all teams
    if "starting_budget" in new_settings:
        try:
            b_val = float(new_settings["starting_budget"])
            db.query(Team).update({"starting_budget": b_val})
        except ValueError:
            pass

    db.commit()
    return get_settings(db)
