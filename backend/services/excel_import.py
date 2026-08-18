import io
import zipfile
from pathlib import Path
import pandas as pd
from typing import List, Tuple
from sqlalchemy.orm import Session
from models import Player, Team, Setting, Transaction
from schemas import ImportResultSchema

TEAM_COUNT = 20
MAX_EXCEL_UNCOMPRESSED_BYTES = 32 * 1024 * 1024


def _validate_xlsx_archive(file_bytes: bytes) -> None:
    """Reject compressed workbooks that could expand excessively in memory."""
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as archive:
            if len(archive.infolist()) > 1000:
                raise ValueError("Excel workbook contains too many internal files")
            expanded_size = sum(item.file_size for item in archive.infolist())
            if expanded_size > MAX_EXCEL_UNCOMPRESSED_BYTES:
                raise ValueError("Excel workbook expands beyond the 32 MB safety limit")
    except zipfile.BadZipFile as exc:
        raise ValueError("Invalid .xlsx workbook") from exc

def process_excel_import(file_bytes: bytes, filename: str, db: Session, room_id: int) -> ImportResultSchema:
    errors: List[str] = []
    filename_lower = filename.lower()

    try:
        if filename_lower.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            if filename_lower.endswith(".xlsx"):
                _validate_xlsx_archive(file_bytes)
            xl = pd.ExcelFile(io.BytesIO(file_bytes))
            sheets = []
            for sheet_name in xl.sheet_names:
                sheet_df = pd.read_excel(xl, sheet_name=sheet_name)
                sheet_df = sheet_df.dropna(how="all")
                if not sheet_df.empty:
                    if len(sheet_df.columns) >= 6:
                        canonical = [
                            "player_code", "name", "position", "p1", "p2", "p3",
                            "total", "base_price", "national", "club"
                        ]
                        sheet_df = sheet_df.iloc[:, :len(canonical)]
                        sheet_df.columns = canonical[:len(sheet_df.columns)]
                        sheet_df = sheet_df.dropna(
                            subset=["name", "position", "p1", "p2", "p3"],
                            how="all"
                        )
                    sheets.append(sheet_df)

            if not sheets:
                raise ValueError("Workbook does not contain any player rows")

            # Multi-sheet auction workbooks restart their serial number on each
            # position sheet. Generate one global sequence so player codes stay
            # unique after the sheets are combined.
            df = pd.concat(sheets, ignore_index=True)
            if len(sheets) > 1:
                df.iloc[:, 0] = range(1, len(df) + 1)
    except Exception as e:
        return ImportResultSchema(
            success=False,
            message=f"Failed to read file: {str(e)}",
            player_count=0, gk_count=0, def_count=0, mid_count=0, att_count=0,
            errors=[f"File reading error: {str(e)}"]
        )

    # Clean column headers
    cols_orig = list(df.columns)
    col_map = {}

    for idx, col in enumerate(cols_orig):
        c_clean = str(col).strip().lower().replace(" ", "_").replace(".", "")
        if c_clean in ["sr_no", "srno", "code", "player_code", "playercode", "sr", "no"]:
            col_map[col] = "player_code"
        elif c_clean in ["name", "player_name", "playername"]:
            col_map[col] = "name"
        elif c_clean in ["position", "pos"]:
            col_map[col] = "position"
        elif c_clean in ["p1", "param1", "p1_rating"]:
            col_map[col] = "p1"
        elif c_clean in ["p2", "param2", "p2_rating"]:
            col_map[col] = "p2"
        elif c_clean in ["p3", "param3", "p3_rating"]:
            col_map[col] = "p3"
        elif c_clean in ["base_price", "baseprice", "base_price_cr", "price"]:
            col_map[col] = "base_price"
        elif c_clean in ["national", "nationality", "country"]:
            col_map[col] = "nationality"
        elif c_clean in ["club", "clubs", "team"]:
            col_map[col] = "club"

    df = df.rename(columns=col_map)

    # Positional column fallback for P1, P2, P3. Position-specific sheets use
    # different rating names (e.g. Handling/Diving/Kicking or
    # Pace/Defense/Physical), but the three rating columns are always D:F.
    if "player_code" not in df.columns and len(cols_orig) > 0:
        df = df.rename(columns={cols_orig[0]: "player_code"})
    if "name" not in df.columns and len(cols_orig) > 1:
        df = df.rename(columns={cols_orig[1]: "name"})
    if "position" not in df.columns and len(cols_orig) > 2:
        df = df.rename(columns={cols_orig[2]: "position"})
    rating_columns = list(df.columns[3:6])
    if not all(col in df.columns for col in ["p1", "p2", "p3"]) and len(rating_columns) == 3:
        df = df.rename(columns={
            rating_columns[0]: "p1",
            rating_columns[1]: "p2",
            rating_columns[2]: "p3"
        })

    required_cols = ["player_code", "name", "position", "p1", "p2", "p3"]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        return ImportResultSchema(
            success=False,
            message="Missing required columns in Excel file",
            player_count=0, gk_count=0, def_count=0, mid_count=0, att_count=0,
            errors=[f"Missing columns: {', '.join(missing_cols)}. Expected columns: player_code, name, position, p1, p2, p3"]
        )

    seen_codes = set()
    valid_rows = []

    for idx, row in df.iterrows():
        errors_before_row = len(errors)
        row_num = idx + 2  # 1-indexed header + row offset
        code_raw = str(row["player_code"]).strip() if pd.notna(row["player_code"]) else ""
        
        # Format code as P001 if numeric
        if code_raw.isdigit():
            code = f"P{int(code_raw):03d}"
        elif not code_raw.startswith("P") and code_raw != "":
            code = f"P{code_raw}"
        else:
            code = code_raw

        name = str(row["name"]).strip() if pd.notna(row["name"]) else ""
        pos_raw = str(row["position"]).strip().upper() if pd.notna(row["position"]) else ""
        
        # Position mapping: MF -> MID
        if pos_raw in ["MF", "MIDFIELD", "MIDFIELDER"]:
            pos = "MID"
        else:
            pos = pos_raw

        if not code:
            errors.append(f"Row {row_num}: player_code cannot be empty")
        elif code in seen_codes:
            errors.append(f"Row {row_num}: Duplicate player_code '{code}'")
        else:
            seen_codes.add(code)

        if not name:
            errors.append(f"Row {row_num}: name cannot be empty")

        if pos not in ["GK", "DEF", "MID", "ATT"]:
            errors.append(f"Row {row_num}: Invalid position '{pos_raw}'. Must be GK, DEF, MID/MF, or ATT")

        p1, p2, p3 = 0, 0, 0
        try:
            p1 = int(row["p1"])
            if not (0 <= p1 <= 100):
                errors.append(f"Row {row_num}: P1 rating must be between 0 and 100 (got {p1})")
        except (ValueError, TypeError):
            errors.append(f"Row {row_num}: P1 rating must be an integer (got {row['p1']})")

        try:
            p2 = int(row["p2"])
            if not (0 <= p2 <= 100):
                errors.append(f"Row {row_num}: P2 rating must be between 0 and 100 (got {p2})")
        except (ValueError, TypeError):
            errors.append(f"Row {row_num}: P2 rating must be an integer (got {row['p2']})")

        try:
            p3 = int(row["p3"])
            if not (0 <= p3 <= 100):
                errors.append(f"Row {row_num}: P3 rating must be between 0 and 100 (got {p3})")
        except (ValueError, TypeError):
            errors.append(f"Row {row_num}: P3 rating must be an integer (got {row['p3']})")

        base_price = 1.0
        if "base_price" in df.columns and pd.notna(row["base_price"]):
            try:
                base_price = float(row["base_price"])
                if base_price < 0:
                    errors.append(f"Row {row_num}: base_price must be >= 0")
            except (ValueError, TypeError):
                base_price = 1.0

        nationality = None
        if "nationality" in df.columns and pd.notna(row["nationality"]):
            nationality = str(row["nationality"]).strip().upper() or None

        club = None
        if "club" in df.columns and pd.notna(row["club"]):
            club = str(row["club"]).strip() or None

        if len(errors) == errors_before_row:
            score = p1 + p2 + p3
            valid_rows.append({
                "player_code": code,
                "name": name,
                "position": pos,
                "p1": p1,
                "p2": p2,
                "p3": p3,
                "score": score,
                "base_price": round(base_price, 2),
                "nationality": nationality,
                "club": club
            })

    if errors:
        return ImportResultSchema(
            success=False,
            message=f"Found {len(errors)} error(s) during Excel validation. No records inserted.",
            player_count=0, gk_count=0, def_count=0, mid_count=0, att_count=0,
            errors=errors
        )

    if not valid_rows:
        return ImportResultSchema(
            success=False,
            message="The dataset contains no valid player rows. No records inserted.",
            player_count=0, gk_count=0, def_count=0, mid_count=0, att_count=0,
            errors=["At least one valid player row is required"]
        )

    # Database updates are committed together; validation failures above never
    # modify the current room's dataset or auction activity.
    db.query(Transaction).filter(Transaction.room_id == room_id).delete(synchronize_session=False)
    db.query(Player).filter(Player.room_id == room_id).delete(synchronize_session=False)

    gk_c, def_c, mid_c, att_c = 0, 0, 0, 0
    for r in valid_rows:
        player = Player(
            room_id=room_id,
            player_code=r["player_code"],
            name=r["name"],
            position=r["position"],
            p1=r["p1"],
            p2=r["p2"],
            p3=r["p3"],
            score=r["score"],
            base_price=r["base_price"],
            nationality=r["nationality"],
            club=r["club"],
            status="AVAILABLE",
            team_id=None,
            sold_price=None,
            is_captain=False
        )
        db.add(player)
        pos = r["position"]
        if pos == "GK": gk_c += 1
        elif pos == "DEF": def_c += 1
        elif pos == "MID": mid_c += 1
        elif pos == "ATT": att_c += 1

    # Keep the configured set of auction teams exactly in sync.
    surplus_team_ids = [
        t.id for t in db.query(Team).filter(
            Team.room_id == room_id, Team.team_number > TEAM_COUNT
        ).all()
    ]
    if surplus_team_ids:
        db.query(Transaction).filter(Transaction.team_id.in_(surplus_team_ids)).delete(
            synchronize_session=False
        )
        db.query(Team).filter(Team.id.in_(surplus_team_ids)).delete(
            synchronize_session=False
        )

    existing_teams = {
        t.team_number for t in db.query(Team).filter(Team.room_id == room_id).all()
    }
    for t_num in range(1, TEAM_COUNT + 1):
        if t_num not in existing_teams:
            db.add(Team(room_id=room_id, team_number=t_num, starting_budget=700.0))

    # Ensure default settings
    default_settings = {
        "starting_budget": "700",
        "required_gk": "1",
        "required_def": "3",
        "required_mid": "2",
        "required_att": "2",
        "auction_status": "ACTIVE"
    }
    for k, v in default_settings.items():
        if not db.query(Setting).filter(Setting.room_id == room_id, Setting.key == k).first():
            db.add(Setting(room_id=room_id, key=k, value=v))

    db.commit()

    return ImportResultSchema(
        success=True,
        message=f"Successfully imported {len(valid_rows)} real players from Excel into database!",
        player_count=len(valid_rows),
        gk_count=gk_c,
        def_count=def_c,
        mid_count=mid_c,
        att_count=att_c,
        errors=[]
    )

def generate_sample_excel() -> bytes:
    """Generates sample template if needed."""
    # Use real file if present, else template
    real_path = Path(__file__).resolve().parents[1] / "FIFA AUCTION 2026.xlsx"
    if real_path.is_file():
        return real_path.read_bytes()

    # A deterministic structural template is useful for recovery without ever
    # pretending randomly generated players are the production dataset.
    df = pd.DataFrame([{
        "SR. NO.": 1,
        "NAME": "Example Player",
        "POSITION": "GK",
        "P1": 80,
        "P2": 82,
        "P3": 84,
        "BASE PRICE": 1,
        "NATIONALITY": "Example Country",
        "CLUB": "Example Club",
    }])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Players")
    return output.getvalue()
