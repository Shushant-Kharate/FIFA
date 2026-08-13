import io
import pandas as pd
from typing import List, Tuple
from sqlalchemy.orm import Session
from models import Player, Team, Setting
from schemas import ImportResultSchema

def process_excel_import(file_bytes: bytes, filename: str, db: Session) -> ImportResultSchema:
    errors: List[str] = []

    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            xl = pd.ExcelFile(io.BytesIO(file_bytes))
            # Read first sheet
            df = pd.read_excel(xl, sheet_name=xl.sheet_names[0])
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
        elif c_clean in ["p1", "diving", "tackling", "passing", "finishing", "param1", "p1_rating"]:
            col_map[col] = "p1"
        elif c_clean in ["p2", "handling", "interceptions", "dribbling", "pace", "param2", "p2_rating"]:
            col_map[col] = "p2"
        elif c_clean in ["p3", "kicking", "aerial", "stamina", "shooting", "param3", "p3_rating"]:
            col_map[col] = "p3"
        elif c_clean in ["base_price", "baseprice", "base_price_cr", "price"]:
            col_map[col] = "base_price"

    df = df.rename(columns=col_map)

    # Positional column fallback for P1, P2, P3 if headers were not explicitly matched
    if "player_code" not in df.columns and len(cols_orig) > 0:
        df = df.rename(columns={cols_orig[0]: "player_code"})
    if "name" not in df.columns and len(cols_orig) > 1:
        df = df.rename(columns={cols_orig[1]: "name"})
    if "position" not in df.columns and len(cols_orig) > 2:
        df = df.rename(columns={cols_orig[2]: "position"})
    if "p1" not in df.columns and len(cols_orig) > 3:
        df = df.rename(columns={cols_orig[3]: "p1"})
    if "p2" not in df.columns and len(cols_orig) > 4:
        df = df.rename(columns={cols_orig[4]: "p2"})
    if "p3" not in df.columns and len(cols_orig) > 5:
        df = df.rename(columns={cols_orig[5]: "p3"})

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

        if len(errors) == 0:
            score = p1 + p2 + p3
            valid_rows.append({
                "player_code": code,
                "name": name,
                "position": pos,
                "p1": p1,
                "p2": p2,
                "p3": p3,
                "score": score,
                "base_price": round(base_price, 2)
            })

    if errors:
        return ImportResultSchema(
            success=False,
            message=f"Found {len(errors)} error(s) during Excel validation. No records inserted.",
            player_count=0, gk_count=0, def_count=0, mid_count=0, att_count=0,
            errors=errors
        )

    # Database updates
    db.query(Player).delete()

    gk_c, def_c, mid_c, att_c = 0, 0, 0, 0
    for r in valid_rows:
        player = Player(
            player_code=r["player_code"],
            name=r["name"],
            position=r["position"],
            p1=r["p1"],
            p2=r["p2"],
            p3=r["p3"],
            score=r["score"],
            base_price=r["base_price"],
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

    # Ensure Teams 1..25 exist
    existing_teams = {t.team_number for t in db.query(Team).all()}
    for t_num in range(1, 26):
        if t_num not in existing_teams:
            db.add(Team(team_number=t_num, starting_budget=70.0))

    # Ensure default settings
    default_settings = {
        "starting_budget": "70",
        "required_gk": "1",
        "required_def": "3",
        "required_mid": "2",
        "required_att": "2",
        "auction_status": "ACTIVE"
    }
    for k, v in default_settings.items():
        if not db.query(Setting).filter(Setting.key == k).first():
            db.add(Setting(key=k, value=v))

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
    import os
    real_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "FIFA AUCTION 2026.xlsx")
    if os.path.exists(real_path):
        with open(real_path, "rb") as f:
            return f.read()
    import random
    first_names = ["Kylian", "Lionel", "Cristiano", "Erling", "Kevin", "Jude", "Mohamed", "Harry", "Vinicius", "Rodri"]
    last_names = ["Mbappe", "Messi", "Ronaldo", "Haaland", "De Bruyne", "Bellingham", "Salah", "Kane", "Junior", "Hernandez"]
    positions = ["GK"] * 32 + ["DEF"] * 64 + ["MID"] * 56 + ["ATT"] * 40
    data = []
    for idx, pos in enumerate(positions, start=1):
        data.append({
            "SR. NO.": idx,
            "NAME": f"{random.choice(first_names)} {random.choice(last_names)}",
            "POSITION": pos,
            "DIVING": 80,
            "HANDLING": 82,
            "KICKING": 84,
            "TOTAL": 246
        })
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="GK")
    return output.getvalue()
