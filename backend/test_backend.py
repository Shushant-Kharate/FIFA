import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import models
from services.excel_import import generate_sample_excel, process_excel_import
from services.scoring import get_team_state, get_all_teams_leaderboard
from services.auction_service import sell_player, mark_unsold, undo_last_sale, return_to_pool, set_captain
from fastapi import HTTPException

# In-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Import sample template
    sample_bytes = generate_sample_excel()
    res = process_excel_import(sample_bytes, "fifa_sample.xlsx", db)
    assert res.success == True
    assert res.player_count == 192

    yield db
    db.close()

def test_excel_import_and_seeding(db_session):
    player_count = db_session.query(models.Player).count()
    team_count = db_session.query(models.Team).count()
    assert player_count == 192
    assert team_count == 25

def test_auction_sell_and_budget(db_session):
    # Get available GK
    gk = db_session.query(models.Player).filter(models.Player.position == "GK", models.Player.status == "AVAILABLE").first()
    assert gk is not None

    # Sell player to Team 1 for 10.0 Cr
    state = sell_player(player_id=gk.id, team_id=1, price=10.0, db=db_session)
    assert state.spent == 10.0
    assert state.remaining_budget == 60.0
    assert len(state.players) == 1
    assert state.qualified == False  # Needs 3 DEF, 2 MID, 2 ATT

def test_sell_exceeding_budget(db_session):
    gk = db_session.query(models.Player).filter(models.Player.position == "GK", models.Player.status == "AVAILABLE").first()
    with pytest.raises(HTTPException) as exc:
        sell_player(player_id=gk.id, team_id=1, price=80.0, db=db_session)
    assert "remaining" in exc.value.detail

def test_full_team_qualification_and_captain(db_session):
    # Sell required players to Team 1
    gks = db_session.query(models.Player).filter(models.Player.position == "GK", models.Player.status == "AVAILABLE").limit(1).all()
    defs = db_session.query(models.Player).filter(models.Player.position == "DEF", models.Player.status == "AVAILABLE").limit(3).all()
    mids = db_session.query(models.Player).filter(models.Player.position == "MID", models.Player.status == "AVAILABLE").limit(2).all()
    atts = db_session.query(models.Player).filter(models.Player.position == "ATT", models.Player.status == "AVAILABLE").limit(2).all()

    squad = gks + defs + mids + atts
    assert len(squad) == 8

    for p in squad:
        sell_player(player_id=p.id, team_id=1, price=2.0, db=db_session)

    state = get_team_state(1, db_session)
    assert state.qualified == True
    assert len(state.best_8_ids) == 8
    assert state.base_score > 0
    assert state.spent == 16.0

    # Set captain to one of the best 8
    cap_player = squad[0]
    updated_state = set_captain(team_id=1, player_id=cap_player.id, db=db_session)
    assert updated_state.captain_id == cap_player.id
    assert updated_state.final_score == updated_state.base_score + cap_player.score

def test_undo_transaction(db_session):
    player = db_session.query(models.Player).filter(models.Player.status == "AVAILABLE").first()
    sell_player(player_id=player.id, team_id=2, price=5.0, db=db_session)
    
    state_before = get_team_state(2, db_session)
    assert state_before.spent == 5.0

    # Undo
    undo_last_sale(player_id=player.id, db=db_session)
    state_after = get_team_state(2, db_session)
    assert state_after.spent == 0.0

    reloaded_player = db_session.query(models.Player).filter(models.Player.id == player.id).first()
    assert reloaded_player.status == "AVAILABLE"
    assert reloaded_player.team_id == None
