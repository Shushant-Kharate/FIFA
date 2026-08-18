from typing import Dict, List, Tuple
from collections import Counter
import re
from sqlalchemy.orm import Session
from models import Team, Player, Setting
from schemas import TeamStateSchema, PlayerInTeamSchema

DEFAULT_REQUIREMENTS = {
    "GK": 1,
    "DEF": 3,
    "MID": 2,
    "ATT": 2
}

def _normalize_label(value: str) -> str:
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", value.strip().upper()).split())

def _normalize_club(value: str) -> str:
    # Treat punctuation differences and optional "FC" consistently.
    tokens = [token for token in _normalize_label(value).split() if token != "FC"]
    return " ".join(tokens)

def calculate_chemistry_bonuses(players: List[Player]) -> Tuple[int, int, Dict[str, int], Dict[str, int]]:
    """Calculate stackable nationality and club bonuses for the Best 8."""
    nationality_counts = Counter(
        _normalize_label(p.nationality)
        for p in players
        if p.nationality and p.nationality.strip()
    )

    club_counts = Counter()
    for player in players:
        # A player can contribute once to every comma-separated club listed.
        clubs = {
            _normalize_club(club)
            for club in (player.club or "").split(",")
            if club.strip()
        }
        club_counts.update(clubs)

    nationality_breakdown = {
        nationality: count * 10
        for nationality, count in nationality_counts.items()
        if count >= 2
    }
    club_breakdown = {
        club: count * 5
        for club, count in club_counts.items()
        if count >= 2
    }

    return (
        sum(nationality_breakdown.values()),
        sum(club_breakdown.values()),
        nationality_breakdown,
        club_breakdown,
    )

def get_required_positions(db: Session, room_id: int) -> Dict[str, int]:
    requirements = dict(DEFAULT_REQUIREMENTS)
    settings = db.query(Setting).filter(Setting.room_id == room_id).all()
    setting_dict = {s.key: s.value for s in settings}

    for setting_key, position in (
        ("required_gk", "GK"),
        ("required_def", "DEF"),
        ("required_mid", "MID"),
        ("required_att", "ATT"),
    ):
        try:
            value = int(setting_dict.get(setting_key, requirements[position]))
            if 0 <= value <= 20:
                requirements[position] = value
        except (TypeError, ValueError):
            # Invalid legacy rows must not take down team and leaderboard APIs.
            continue

    return requirements

def get_team_state(team_id: int, db: Session, room_id: int = None) -> TeamStateSchema:
    query = db.query(Team).filter(Team.id == team_id)
    if room_id is not None:
        query = query.filter(Team.room_id == room_id)
    team = query.first()
    if not team:
        raise ValueError(f"Team with id {team_id} not found")

    room_id = team.room_id
    players = db.query(Player).filter(
        Player.room_id == room_id, Player.team_id == team_id, Player.status == "SOLD"
    ).all()
    spent = round(sum((p.sold_price or 0.0) for p in players), 2)
    remaining_budget = round(team.starting_budget - spent, 2)

    required = get_required_positions(db, room_id)

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

    # The current score always reflects the strongest owned players in each
    # positional quota. Qualification still requires the full 1/3/2/2 lineup.
    base_score = sum(p.score for p in candidate_best_8)
    captain_id = None
    captain_name = None
    captain_score = 0
    nationality_bonus = 0
    club_bonus = 0
    nationality_bonus_breakdown: Dict[str, int] = {}
    club_bonus_breakdown: Dict[str, int] = {}
    final_score = base_score

    captain = next((p for p in players if p.is_captain), None)
    if captain:
        captain_id = captain.id
        captain_name = captain.name

    if qualified:
        (
            nationality_bonus,
            club_bonus,
            nationality_bonus_breakdown,
            club_bonus_breakdown,
        ) = calculate_chemistry_bonuses(candidate_best_8)
        if captain and captain.id in best_8_ids:
            captain_score = captain.score
        final_score = base_score + captain_score + nationality_bonus + club_bonus

    # Formation at risk calculation
    formation_at_risk = False
    if len(missing) > 0:
        needed_min_cost = 0.0
        for pos, count_needed in missing.items():
            # A formation is possible only when enough distinct players remain.
            available_prices = db.query(Player.base_price).filter(
                Player.status == "AVAILABLE",
                Player.room_id == room_id,
                Player.position == pos
            ).order_by(Player.base_price.asc()).limit(count_needed).all()

            if len(available_prices) < count_needed:
                formation_at_risk = True
                break
            needed_min_cost += sum(price for (price,) in available_prices)

        if not formation_at_risk and remaining_budget < round(needed_min_cost, 2):
            formation_at_risk = True

    # Construct player schemas with best 8 flag
    player_schemas = []
    for p in players:
        p_dict = PlayerInTeamSchema.model_validate(p)
        p_dict.is_best_8 = p.id in best_8_ids
        player_schemas.append(p_dict)

    return TeamStateSchema(
        room_id=room_id,
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
        nationality_bonus=nationality_bonus,
        club_bonus=club_bonus,
        nationality_bonus_breakdown=nationality_bonus_breakdown,
        club_bonus_breakdown=club_bonus_breakdown,
        final_score=final_score,
        formation_at_risk=formation_at_risk,
        players=player_schemas,
        best_8_ids=list(best_8_ids)
    )

def get_all_teams_leaderboard(db: Session, room_id: int) -> List[TeamStateSchema]:
    teams = db.query(Team).filter(Team.room_id == room_id).order_by(Team.team_number).all()
    states = [get_team_state(t.id, db, room_id) for t in teams]

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
