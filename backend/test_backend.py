import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models
from services.excel_import import generate_sample_excel, process_excel_import
from services.scoring import get_team_state, get_all_teams_leaderboard, calculate_chemistry_bonuses
from services.auction_service import sell_player, mark_unsold, undo_last_sale, return_to_pool, set_captain
from fastapi import HTTPException
from auth import authenticate, create_access_token, get_active_room_id, get_current_user

# In-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    db.add_all([models.Room(id=1, name="Room 1"), models.Room(id=2, name="Room 2")])
    db.commit()
    
    # Import sample template
    sample_bytes = generate_sample_excel()
    res = process_excel_import(sample_bytes, "fifa_sample.xlsx", db, room_id=1)
    res2 = process_excel_import(sample_bytes, "fifa_sample.xlsx", db, room_id=2)
    assert res.success == True
    assert res.player_count == 152
    assert res2.player_count == 152

    yield db
    db.close()

def test_excel_import_and_seeding(db_session):
    player_count = db_session.query(models.Player).count()
    team_count = db_session.query(models.Team).count()
    assert player_count == 304
    assert team_count == 40
    player = db_session.query(models.Player).first()
    assert player.nationality
    assert player.club

def test_nationality_and_multi_club_bonuses():
    players = [
        models.Player(nationality="X", club="Club A, Club B"),
        models.Player(nationality="X", club="Club C"),
        models.Player(nationality="Y", club="Club B"),
        models.Player(nationality="Y", club="Club B"),
    ]

    nationality, club, nationality_groups, club_groups = calculate_chemistry_bonuses(players)

    assert nationality == 40
    assert nationality_groups == {"X": 20, "Y": 20}
    assert club == 15
    assert club_groups == {"CLUB B": 15}

def test_auction_sell_and_budget(db_session):
    # Get available GK
    gk = db_session.query(models.Player).filter(models.Player.room_id == 1, models.Player.position == "GK", models.Player.status == "AVAILABLE").first()
    assert gk is not None

    # Sell player to Team 1 for 10.0 M
    state = sell_player(player_id=gk.id, team_id=1, price=10.0, db=db_session, room_id=1)
    assert state.spent == 10.0
    assert state.remaining_budget == 690.0
    assert len(state.players) == 1
    assert state.qualified == False  # Needs 3 DEF, 2 MID, 2 ATT
    assert state.base_score == gk.score
    assert state.final_score == gk.score


def test_incomplete_leaderboard_uses_current_positional_score(db_session):
    players = db_session.query(models.Player).filter(
        models.Player.room_id == 1,
        models.Player.position == "GK",
        models.Player.status == "AVAILABLE",
    ).order_by(models.Player.score.desc()).limit(2).all()
    assert len(players) == 2 and players[0].score >= players[1].score

    sell_player(players[1].id, 1, 1.0, db_session, room_id=1)
    sell_player(players[0].id, 2, 1.0, db_session, room_id=1)

    leaderboard = get_all_teams_leaderboard(db_session, room_id=1)
    assert leaderboard[0].team_number == 2
    assert leaderboard[0].qualified is False
    assert leaderboard[0].final_score == players[0].score

def test_sell_exceeding_budget(db_session):
    gk = db_session.query(models.Player).filter(models.Player.room_id == 1, models.Player.position == "GK", models.Player.status == "AVAILABLE").first()
    with pytest.raises(HTTPException) as exc:
        sell_player(player_id=gk.id, team_id=1, price=800.0, db=db_session, room_id=1)
    assert "remaining" in exc.value.detail

def test_full_team_qualification_and_captain(db_session):
    # Sell required players to Team 1
    gks = db_session.query(models.Player).filter(models.Player.room_id == 1, models.Player.position == "GK", models.Player.status == "AVAILABLE").limit(1).all()
    defs = db_session.query(models.Player).filter(models.Player.room_id == 1, models.Player.position == "DEF", models.Player.status == "AVAILABLE").limit(3).all()
    mids = db_session.query(models.Player).filter(models.Player.room_id == 1, models.Player.position == "MID", models.Player.status == "AVAILABLE").limit(2).all()
    atts = db_session.query(models.Player).filter(models.Player.room_id == 1, models.Player.position == "ATT", models.Player.status == "AVAILABLE").limit(2).all()

    squad = gks + defs + mids + atts
    assert len(squad) == 8

    for p in squad:
        sell_player(player_id=p.id, team_id=1, price=2.0, db=db_session, room_id=1)

    state = get_team_state(1, db_session, room_id=1)
    assert state.qualified == True
    assert len(state.best_8_ids) == 8
    assert state.base_score > 0
    assert state.spent == 16.0

    # Set captain to one of the best 8
    cap_player = squad[0]
    updated_state = set_captain(team_id=1, player_id=cap_player.id, db=db_session, room_id=1)
    assert updated_state.captain_id == cap_player.id
    assert updated_state.final_score == (
        updated_state.base_score
        + cap_player.score
        + updated_state.nationality_bonus
        + updated_state.club_bonus
    )

def test_undo_transaction(db_session):
    player = db_session.query(models.Player).filter(models.Player.room_id == 1, models.Player.status == "AVAILABLE").first()
    sell_player(player_id=player.id, team_id=2, price=5.0, db=db_session, room_id=1)
    
    state_before = get_team_state(2, db_session, room_id=1)
    assert state_before.spent == 5.0

    # Undo
    undo_last_sale(player_id=player.id, db=db_session, room_id=1)
    state_after = get_team_state(2, db_session, room_id=1)
    assert state_after.spent == 0.0

    reloaded_player = db_session.query(models.Player).filter(models.Player.id == player.id).first()
    assert reloaded_player.status == "AVAILABLE"
    assert reloaded_player.team_id == None

def test_room_auction_isolation(db_session):
    room1_player = db_session.query(models.Player).filter(
        models.Player.room_id == 1, models.Player.player_code == "P001"
    ).first()
    room2_player = db_session.query(models.Player).filter(
        models.Player.room_id == 2, models.Player.player_code == "P001"
    ).first()
    room1_team = db_session.query(models.Team).filter(
        models.Team.room_id == 1, models.Team.team_number == 1
    ).first()

    sell_player(room1_player.id, room1_team.id, 10.0, db_session, room_id=1)
    db_session.refresh(room2_player)

    assert room1_player.status == "SOLD"
    assert room2_player.status == "AVAILABLE"
    assert db_session.query(models.Transaction).filter(models.Transaction.room_id == 2).count() == 0

def test_room_admin_cannot_override_room(monkeypatch):
    monkeypatch.setenv("AUTH_SECRET", "test-secret-that-is-long-enough")
    monkeypatch.setenv("ROOM1_ADMIN_PASSWORD", "room-one-password")
    user = authenticate("room1_admin", "room-one-password")
    token = create_access_token(user)
    authenticated = get_current_user(f"Bearer {token}")

    assert authenticated.room_id == 1
    assert get_active_room_id(authenticated, x_room_id=2) == 1


def test_formation_at_risk_when_too_few_distinct_players_remain():
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = testing_session()
    db.add(models.Room(id=1, name="Room 1"))
    db.flush()
    team = models.Team(room_id=1, team_number=1, starting_budget=700.0)
    db.add(team)
    db.flush()

    # One cheap player per position is not enough to satisfy 1/3/2/2.
    for index, position in enumerate(("GK", "DEF", "MID", "ATT"), start=1):
        db.add(models.Player(
            room_id=1,
            player_code=f"P{index:03d}",
            name=f"Available {position}",
            position=position,
            base_price=1.0,
            status="AVAILABLE",
        ))
    db.commit()

    state = get_team_state(team.id, db, room_id=1)
    assert state.formation_at_risk is True
    db.close()


def test_dataset_scaling_for_10_teams(db_session):
    from routers.admin import scale_dataset_for_teams
    from schemas import ScaleDatasetRequest
    from models import Room

    mock_user = type("MockUser", (), {"username": "admin"})()

    # Scale room 1 to 10 teams
    res = scale_dataset_for_teams(ScaleDatasetRequest(participating_teams=10), db=db_session, room_id=1, user=mock_user)

    assert res.success is True
    assert res.participating_teams == 10
    assert res.gk_count == 9      # round(17 * 10 / 20) = 9
    assert res.def_count == 30    # round(59 * 10 / 20) = 30
    assert res.mid_count == 19    # round(38 * 10 / 20) = 19
    assert res.att_count == 19    # round(38 * 10 / 20) = 19
    assert res.removed_players_count == 75
    assert len(res.removed_players) == 75

    from routers.admin import get_removed_players
    removed = get_removed_players(db=db_session, room_id=1)
    assert len(removed) == 75
    assert removed[0]["player_code"] is not None

    # Verify team count trimmed to 10
    team_count = db_session.query(models.Team).filter(models.Team.room_id == 1).count()
    assert team_count == 10

    # Verify room 2 remains untouched (152 players, 20 teams)
    room2_player_count = db_session.query(models.Player).filter(models.Player.room_id == 2).count()
    room2_team_count = db_session.query(models.Team).filter(models.Team.room_id == 2).count()
    assert room2_player_count == 152
    assert room2_team_count == 20

    restored = scale_dataset_for_teams(
        ScaleDatasetRequest(participating_teams=15),
        db=db_session,
        room_id=1,
        user=mock_user,
    )
    assert restored.restored_players_count == 38
    assert restored.player_count == 115
    assert db_session.query(models.Player).filter(
        models.Player.room_id == 1,
        models.Player.status == "SCALED_OUT",
    ).count() == 37

    expanded = scale_dataset_for_teams(
        ScaleDatasetRequest(participating_teams=35),
        db=db_session,
        room_id=1,
        user=mock_user,
    )
    assert expanded.player_count == 152
    assert expanded.restored_players_count == 37
    assert db_session.query(models.Team).filter(models.Team.room_id == 1).count() == 35



def test_dataset_scaling_blocked_when_player_sold(db_session):
    from routers.admin import scale_dataset_for_teams
    from schemas import ScaleDatasetRequest

    mock_user = type("MockUser", (), {"username": "admin"})()

    # Sell one player in room 1
    gk = db_session.query(models.Player).filter(models.Player.room_id == 1, models.Player.position == "GK").first()
    sell_player(gk.id, 1, 5.0, db_session, room_id=1)

    with pytest.raises(HTTPException) as exc_info:
        scale_dataset_for_teams(ScaleDatasetRequest(participating_teams=10), db=db_session, room_id=1, user=mock_user)

    assert exc_info.value.status_code == 400
    assert "Cannot scale dataset after auction has started" in exc_info.value.detail

