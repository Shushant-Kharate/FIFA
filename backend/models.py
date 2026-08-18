from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    teams = relationship("Team", back_populates="room")
    players = relationship("Player", back_populates="room")


class Player(Base):
    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("room_id", "player_code", name="uq_room_player_code"),)

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    player_code = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    p1 = Column(Integer, default=0)
    p2 = Column(Integer, default=0)
    p3 = Column(Integer, default=0)
    score = Column(Integer, default=0)
    base_price = Column(Float, default=1.0)
    nationality = Column(String, nullable=True)
    club = Column(String, nullable=True)
    status = Column(String, default="AVAILABLE")
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    sold_price = Column(Float, nullable=True)
    is_captain = Column(Boolean, default=False)

    room = relationship("Room", back_populates="players")
    team = relationship("Team", back_populates="players")


class Team(Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("room_id", "team_number", name="uq_room_team_number"),)

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    team_number = Column(Integer, nullable=False)
    starting_budget = Column(Float, default=700.0)
    room = relationship("Room", back_populates="teams")
    players = relationship("Player", back_populates="team")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    player_id = Column(Integer, nullable=True)
    team_id = Column(Integer, nullable=True)
    amount = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"

    room_id = Column(Integer, ForeignKey("rooms.id"), primary_key=True)
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)
