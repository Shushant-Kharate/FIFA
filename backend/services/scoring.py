from typing import Dict, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Team, Player, Setting
from schemas import TeamStateSchema, PlayerInTeamSchema

DEFAULT_REQUIREMENTS = {
    "GK": 1,
    "DEF": 3,
    "MID": 2,
    "ATT": 2
}

def get_required_positions(db: Session) -> Dict[str, int]:
    requirements = dict(DEFAULT_REQUIREMENTS)
    settings = db.query(Setting).all()
    setting_dict = {s.key: s.value for s in settings}

    if "required_gk" in setting_dict:
        requirements["GK"] = int(setting_dict["required_gk"])
    if "required_def" in setting_dict:
        requirements["DEF"] = int(setting_dict["required_def"])
    if "required_mid" in setting_dict:
        requirements["MID"] = int(setting_dict["required_mid"])
    if "required_att" in setting_dict:
        requirements["ATT"] = int(setting_dict["required_att"])

    return requirements

def get_team_state(team_id: int, db: Session) -> TeamStateSchema:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise ValueError(f"Team with id {team_id} not found")

    players = db.query(Player).filter(Player.team_id == team_id, Player.status == "SOLD").all()
    spent = round(sum((p.sold_price or 0.0) for p in players), 2)
    remaining_budget = round(team.starting_budget - spent, 2)

    required = get_required_positions(db)

    by_pos: Dict[str, List[Player]] = {"GK": [], "DEF": [], "MID": [], "ATT": []}
    for p in players:
        pos = p.position.upper()
        if pos in by_pos:
            by_pos[pos].append(p)
        else:
            by_pos.setdefault(pos, []).append(p)

    for pos in by_pos:
        by_pos[pos].sort(key=lambda p: (p.score, p.id), reverse=True)

    counts = {pos: len(by_pos.get(pos, [])) for pos in ["GK", "DEF", "MID", "ATT"]}

    missing: Dict[str, int] = {}
    for pos, req in required.items():
        owned = counts.get(pos, 0)
        if owned < req:
            missing[pos] = req - owned

    qualified = len(missing) == 0

    # Always compute starter slots (up to required count per position)
    candidate_best_8 = (
        by_pos["GK"][:required.get("GK", 1)] +
        by_pos["DEF"][:required.get("DEF", 3)] +
        by_pos["MID"][:required.get("MID", 2)] +
        by_pos["ATT"][:required.get("ATT", 2)]
    )
    best_8_ids = {p.id for p in candidate_best_8}

    base_score = 0
    captain_id = None
    captain_name = None
    captain_score = 0
    final_score = 0

    captain = next((p for p in players if p.is_captain), None)
    if captain:
        captain_id = captain.id
        captain_name = captain.name

    if qualified:
        base_score = sum(p.score for p in candidate_best_8)
        if captain and captain.id in best_8_ids:
            captain_score = captain.score
            final_score = base_score + captain_score
        else:
            final_score = base_score

    # Formation at risk calculation
    formation_at_risk = False
    if len(missing) > 0:
        needed_min_cost = 0.0
        for pos, count_needed in missing.items():
            # Query lowest base price for available player in this position
            min_base = db.query(func.min(Player.base_price)).filter(
                Player.status == "AVAILABLE",
                Player.position == pos
            ).scalar()

            if min_base is None:
                # No available players for required position
                formation_at_risk = True
                break
            else:
                needed_min_cost += (min_base * count_needed)

        if not formation_at_risk and remaining_budget < round(needed_min_cost, 2):
            formation_at_risk = True

    # Construct player schemas with best 8 flag
    player_schemas = []
    for p in players:
        p_dict = PlayerInTeamSchema.model_validate(p)
        p_dict.is_best_8 = p.id in best_8_ids
        player_schemas.append(p_dict)

    return TeamStateSchema(
        team_id=team.id,
        team_number=team.team_number,
        starting_budget=team.starting_budget,
        spent=spent,
        remaining_budget=remaining_budget,
        qualified=qualified,
        missing=missing,
        counts=counts,
        base_score=base_score,
        captain_id=captain_id,
        captain_name=captain_name,
        captain_score=captain_score,
        final_score=final_score,
        formation_at_risk=formation_at_risk,
        players=player_schemas,
        best_8_ids=list(best_8_ids)
    )

def get_all_teams_leaderboard(db: Session) -> List[TeamStateSchema]:
    teams = db.query(Team).order_by(Team.team_number).all()
    states = [get_team_state(t.id, db) for t in teams]

    # Sort leaderboard by:
    # 1. qualified DESC
    # 2. final_score DESC
    # 3. base_score DESC
    # 4. spent ASC
    # 5. team_number ASC
    states.sort(
        key=lambda s: (
            1 if s.qualified else 0,
            s.final_score,
            s.base_score,
            -s.spent,
            -s.team_number
        ),
        reverse=True
    )
    return states
