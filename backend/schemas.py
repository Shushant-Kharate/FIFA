from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class PlayerSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_code: str
    name: str
    position: str
    p1: int
    p2: int
    p3: int
    score: int
    base_price: float
    nationality: Optional[str] = None
    club: Optional[str] = None
    status: str
    team_id: Optional[int] = None
    sold_price: Optional[float] = None
    is_captain: bool = False
    is_best_8: Optional[bool] = False

class PlayerInTeamSchema(PlayerSchema):
    is_best_8: bool = False

class TeamStateSchema(BaseModel):
    room_id: int
    team_id: int
    team_number: int
    starting_budget: float
    spent: float
    remaining_budget: float
    qualified: bool
    missing: Dict[str, int]
    counts: Dict[str, int]
    base_score: int
    captain_id: Optional[int] = None
    captain_name: Optional[str] = None
    captain_score: int = 0
    nationality_bonus: int = 0
    club_bonus: int = 0
    nationality_bonus_breakdown: Dict[str, int] = Field(default_factory=dict)
    club_bonus_breakdown: Dict[str, int] = Field(default_factory=dict)
    final_score: int
    formation_at_risk: bool = False
    players: List[PlayerInTeamSchema] = Field(default_factory=list)
    best_8_ids: List[int] = Field(default_factory=list)

class TeamSummarySchema(BaseModel):
    team_id: int
    team_number: int
    starting_budget: float
    spent: float
    remaining_budget: float
    qualified: bool
    missing: Dict[str, int]
    counts: Dict[str, int]
    total_players: int
    base_score: int
    final_score: int
    formation_at_risk: bool = False

class SellPlayerRequest(BaseModel):
    player_id: int
    team_id: int
    price: float = Field(..., gt=0)

class UnsoldPlayerRequest(BaseModel):
    player_id: int

class UndoRequest(BaseModel):
    player_id: int

class ReturnToPoolRequest(BaseModel):
    player_id: int

class SetCaptainRequest(BaseModel):
    player_id: int

class TransactionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_type: str
    player_id: Optional[int]
    team_id: Optional[int]
    amount: Optional[float]
    timestamp: datetime

class SettingSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str

class ImportResultSchema(BaseModel):
    success: bool
    message: str
    player_count: int
    gk_count: int
    def_count: int
    mid_count: int
    att_count: int
    errors: List[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthUserSchema(BaseModel):
    username: str
    role: str
    room_id: Optional[int] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserSchema
