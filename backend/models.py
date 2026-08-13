from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

class PlayerSchema(BaseModel):
    id: int
    name: str
    team: int
    club: str
    position: str
    position_id: int
    price: float
    ep_next: float
    is_new: bool = False
    photo_url: str

class TransferCard(BaseModel):
    out_player_id: int
    out_player_name: str
    in_player_id: int
    in_player_name: str
    current_price: float
    new_price: float
    projected_gain_1gw: float
    hit_cost: int
    reasons: List[str]

class BudgetStatus(BaseModel):
    squad_value: float
    in_the_bank: float
    total_budget: float

class InjuryAlert(BaseModel):
    player_name: str
    team_name: str
    status: str
    color: str
    chance_of_playing: int
    news: str
    return_date: str
    photo_url: str

class DataFreshness(BaseModel):
    age_seconds: int
    is_stale: bool
    source: str

class PrivacyStatus(BaseModel):
    input_persisted: bool = False
    temporary_files_deleted: bool = True
    deletion_status: str = "deleted"

class ProcessResponse(BaseModel):
    request_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    stage: str
    message: str
    input_metadata: Dict[str, Any]
    strategy: Optional[str] = None
    
    # Processed Results
    original_team: Optional[Dict[str, List[PlayerSchema]]] = None
    suggested_team: Optional[Dict[str, List[PlayerSchema]]] = None
    transfers: Optional[List[TransferCard]] = None
    fixtures: Optional[List[Dict[str, Any]]] = None
    ocr_summary: Optional[Dict[str, Any]] = None
    formation: Optional[str] = None
    gameweek_fixtures: Optional[List[Dict[str, Any]]] = None
    
    # New Dashboard Metrics
    budget: Optional[BudgetStatus] = None
    global_injuries: Optional[List[InjuryAlert]] = None
    data_freshness: Optional[DataFreshness] = None
    ai_summary: Optional[str] = None
    news: Optional[List[Dict[str, str]]] = None
    
    performance: Dict[str, float] = {}
    privacy: PrivacyStatus = PrivacyStatus()
    error: Optional[str] = None
