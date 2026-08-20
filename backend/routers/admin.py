import json
import io
import math
from typing import Dict, List
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from database import get_db
from models import AuditLog, Setting, Player, Team, Transaction
from schemas import AuditLogSchema, ImportResultSchema, SettingSchema, ScaleDatasetRequest, ScaleDatasetResponseSchema, RemovedPlayerSchema
from services.excel_import import process_excel_import, generate_sample_excel
from services.excel_export import generate_audit_excel, generate_results_excel, generate_removed_players_excel

from services.audit_service import add_audit_log
from auth import CurrentUser, get_active_room_id, get_current_user, require_super_admin

router = APIRouter(tags=["Admin & Settings"])
MAX_IMPORT_BYTES = 4 * 1024 * 1024
POSITION_SETTING_KEYS = {
    "required_gk",
    "required_def",
    "required_mid",
    "required_att",
}
ALLOWED_SETTING_KEYS = POSITION_SETTING_KEYS | {"starting_budget", "auction_status", "participating_teams"}
BASE_POS_COUNTS = {
    "GK": 17,
    "DEF": 59,
    "MID": 38,
    "ATT": 38,
}

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
    result = process_excel_import(contents, filename, db, room_id)
    if result.success:
        add_audit_log(
            db, room_id, "DATASET_IMPORTED", _admin.username,
            f"Imported {result.player_count} players from {filename}",
            details={"filename": filename, "player_count": result.player_count},
        )
        db.commit()
    return result

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


@router.get("/api/admin/audit-log", response_model=List[AuditLogSchema])
def get_audit_log(
    limit: int = 200,
    db: Session = Depends(get_db),
    room_id: int = Depends(get_active_room_id),
):
    safe_limit = max(1, min(limit, 1000))
    return db.query(AuditLog).filter(
        AuditLog.room_id == room_id
    ).order_by(AuditLog.timestamp.desc(), AuditLog.id.desc()).limit(safe_limit).all()


@router.get("/api/admin/export-results")
def export_results_excel(
    db: Session = Depends(get_db),
    room_id: int = Depends(get_active_room_id),
    user: CurrentUser = Depends(get_current_user),
):
    add_audit_log(
        db, room_id, "RESULTS_EXPORTED", user.username,
        f"Downloaded ranked auction results for Room {room_id}",
    )
    db.commit()
    content = generate_results_excel(db, room_id)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=fifa_room_{room_id}_ranked_results.xlsx"},
    )


@router.get("/api/admin/export-audit-log")
def export_audit_log_excel(
    db: Session = Depends(get_db),
    room_id: int = Depends(get_active_room_id),
    user: CurrentUser = Depends(get_current_user),
):
    add_audit_log(
        db, room_id, "AUDIT_LOG_EXPORTED", user.username,
        f"Downloaded the full audit log for Room {room_id}",
    )
    db.commit()
    content = generate_audit_excel(db, room_id)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=fifa_room_{room_id}_audit_log.xlsx"},
    )

@router.post("/api/admin/reset")
def reset_room_auction(db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id), user: CurrentUser = Depends(get_current_user)):
    player_count = db.query(Player).filter(Player.room_id == room_id).update(
        {
            "status": "AVAILABLE",
            "team_id": None,
            "sold_price": None,
            "is_captain": False,
        },
        synchronize_session=False,
    )
    transaction_count = db.query(Transaction).filter(Transaction.room_id == room_id).count()
    add_audit_log(
        db, room_id, "ROOM_RESET", user.username,
        f"Reset Room {room_id} auction; {player_count} players returned to the pool",
        details={"players_reset": player_count, "transactions_preserved": transaction_count},
    )
    db.commit()
    return {
        "success": True,
        "room_id": room_id,
        "players_reset": player_count,
        "transactions_preserved": transaction_count,
    }


@router.post("/api/admin/scale-dataset", response_model=ScaleDatasetResponseSchema)
def scale_dataset_for_teams(
    req: ScaleDatasetRequest,
    db: Session = Depends(get_db),
    room_id: int = Depends(get_active_room_id),
    user: CurrentUser = Depends(get_current_user),
):
    sold_count = db.query(Player).filter(Player.room_id == room_id, Player.status == "SOLD").count()
    if sold_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot scale dataset after auction has started. {sold_count} player(s) are already sold in Room {room_id}. Please reset the room first."
        )

    n_teams = req.participating_teams
    removed_count = 0
    removed_players_list = []

    # For each position, calculate target count using standard half-up rounding
    for pos, base_count in BASE_POS_COUNTS.items():
        target_count = int(math.floor(((base_count * n_teams) / 20.0) + 0.5))

        pos_players = (
            db.query(Player)
            .filter(Player.room_id == room_id, Player.position == pos)
            .order_by(Player.score.asc(), Player.player_code.asc())
            .all()
        )

        current_count = len(pos_players)
        if current_count > target_count:
            to_remove_count = current_count - target_count
            players_to_delete = pos_players[:to_remove_count]
            
            for p in players_to_delete:
                removed_players_list.append({
                    "player_code": p.player_code,
                    "name": p.name,
                    "position": p.position,
                    "score": p.score,
                    "p1": p.p1,
                    "p2": p.p2,
                    "p3": p.p3,
                    "base_price": p.base_price,
                    "nationality": p.nationality,
                    "club": p.club,
                })

            delete_ids = [p.id for p in players_to_delete]

            db.query(Transaction).filter(Transaction.room_id == room_id, Transaction.player_id.in_(delete_ids)).delete(synchronize_session=False)
            db.query(Player).filter(Player.id.in_(delete_ids)).delete(synchronize_session=False)
            removed_count += len(delete_ids)

    # Adjust teams count in room to n_teams
    surplus_teams = db.query(Team).filter(Team.room_id == room_id, Team.team_number > n_teams).all()
    if surplus_teams:
        surplus_team_ids = [t.id for t in surplus_teams]
        db.query(Transaction).filter(Transaction.room_id == room_id, Transaction.team_id.in_(surplus_team_ids)).delete(synchronize_session=False)
        db.query(Team).filter(Team.room_id == room_id, Team.id.in_(surplus_team_ids)).delete(synchronize_session=False)

    existing_team_numbers = {t.team_number for t in db.query(Team).filter(Team.room_id == room_id).all()}
    budget_setting = db.query(Setting).filter(Setting.room_id == room_id, Setting.key == "starting_budget").first()
    starting_budget = float(budget_setting.value) if budget_setting else 700.0

    for t_num in range(1, n_teams + 1):
        if t_num not in existing_team_numbers:
            db.add(Team(room_id=room_id, team_number=t_num, starting_budget=starting_budget))

    setting = db.query(Setting).filter(Setting.room_id == room_id, Setting.key == "participating_teams").first()
    if setting:
        setting.value = str(n_teams)
    else:
        db.add(Setting(room_id=room_id, key="participating_teams", value=str(n_teams)))

    gk_c = db.query(Player).filter(Player.room_id == room_id, Player.position == "GK").count()
    def_c = db.query(Player).filter(Player.room_id == room_id, Player.position == "DEF").count()
    mid_c = db.query(Player).filter(Player.room_id == room_id, Player.position == "MID").count()
    att_c = db.query(Player).filter(Player.room_id == room_id, Player.position == "ATT").count()
    total_players = gk_c + def_c + mid_c + att_c

    add_audit_log(
        db, room_id, "DATASET_SCALED", user.username,
        f"Scaled dataset and team count to {n_teams} teams in Room {room_id}. Removed {removed_count} lowest-rated player(s). Remaining: {total_players} players.",
        details={
            "participating_teams": n_teams,
            "removed_count": removed_count,
            "total_players": total_players,
            "removed_players": removed_players_list,
        }
    )
    db.commit()

    return ScaleDatasetResponseSchema(
        success=True,
        message=f"Successfully scaled room dataset to {n_teams} teams ({total_players} players remaining).",
        participating_teams=n_teams,
        player_count=total_players,
        gk_count=gk_c,
        def_count=def_c,
        mid_count=mid_c,
        att_count=att_c,
        removed_players_count=removed_count,
        removed_players=removed_players_list,
    )


@router.get("/api/admin/removed-players", response_model=List[RemovedPlayerSchema])
def get_removed_players(
    db: Session = Depends(get_db),
    room_id: int = Depends(get_active_room_id),
):
    latest_log = (
        db.query(AuditLog)
        .filter(AuditLog.room_id == room_id, AuditLog.action == "DATASET_SCALED")
        .order_by(AuditLog.timestamp.desc(), AuditLog.id.desc())
        .first()
    )
    if not latest_log or not latest_log.details_json:
        return []
    try:
        data = json.loads(latest_log.details_json)
        return data.get("removed_players", [])
    except Exception:
        return []


@router.get("/api/admin/export-removed-players")
def export_removed_players_excel(
    db: Session = Depends(get_db),
    room_id: int = Depends(get_active_room_id),
    user: CurrentUser = Depends(get_current_user),
):
    add_audit_log(
        db, room_id, "REMOVED_PLAYERS_EXPORTED", user.username,
        f"Downloaded list of pruned/removed players for Room {room_id}",
    )
    db.commit()

    removed_players = get_removed_players(db=db, room_id=room_id)
    excel_bytes = generate_removed_players_excel(removed_players)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=fifa_room_{room_id}_removed_players.xlsx"}
    )



@router.get("/api/settings", response_model=Dict[str, str])

def get_settings(db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id)):
    settings = db.query(Setting).filter(Setting.room_id == room_id).all()
    return {s.key: s.value for s in settings}

@router.put("/api/settings", response_model=Dict[str, str])
def update_settings(new_settings: Dict[str, str], db: Session = Depends(get_db), room_id: int = Depends(get_active_room_id), user: CurrentUser = Depends(get_current_user)):
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

    add_audit_log(
        db, room_id, "SETTINGS_UPDATED", user.username,
        f"Updated Room {room_id} settings: {', '.join(sorted(normalized_settings))}",
        details=normalized_settings,
    )

    db.commit()
    settings = db.query(Setting).filter(Setting.room_id == room_id).all()
    return {s.key: s.value for s in settings}
