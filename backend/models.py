from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    player_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)  # GK, DEF, MID, ATT
    p1 = Column(Integer, default=0)
    p2 = Column(Integer, default=0)
    p3 = Column(Integer, default=0)
    score = Column(Integer, default=0)
    base_price = Column(Float, default=1.0)
    status = Column(String, default="AVAILABLE")  # AVAILABLE, SOLD, UNSOLD
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    sold_price = Column(Float, nullable=True)
    is_captain = Column(Boolean, default=False)

    team = relationship("Team", back_populates="players")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    team_number = Column(Integer, unique=True, nullable=False)
    starting_budget = Column(Float, default=70.0)

    players = relationship("Player", back_populates="team")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)  # SOLD, UNSOLD, UNDO, CAPTAIN_SET, CAPTAIN_CHANGED, RETURN_TO_POOL
    player_id = Column(Integer, nullable=True)
    team_id = Column(Integer, nullable=True)
    amount = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
