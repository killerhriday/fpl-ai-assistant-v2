from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import uuid

class PlayerSchema(BaseModel):
    id: int
    name: str
    position_id: int
    club: str
    price: float
    ep_next: float
    ep_next_4: Optional[float] = None
    is_new: bool = False
    photo_url: str

class TransferCard(BaseModel):
    out_player_id: int
    in_player_id: int
    out_player_name: str
    in_player_name: str
    position_id: int
    club_in: str
    club_out: str
    current_price: float
    new_price: float
    ep_next_in: float
    ep_next_out: float
    projected_gain_1gw: float
    hit_cost: int
    confidence: float
    reasons: List[str]
    warnings: List[str]
    score_breakdown: Dict[str, float]

class PrivacyStatus(BaseModel):
    input_persisted: bool = False
    temporary_files_deleted: bool = True
    deletion_status: str = "deleted"

class ProcessResponse(BaseModel):
    schema_version: int = 1
    request_id: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    data_timestamp: Optional[str] = None
    strategy: str = "next_gameweek"
    input_metadata: Dict[str, Any]
    ocr_summary: Dict[str, Any] = {}
    original_team: Dict[str, List[PlayerSchema]] = {}
    suggested_team: Dict[str, List[PlayerSchema]] = {}
    transfers: List[TransferCard] = []
    fixtures: List[Any] = []
    analytics: Dict[str, Any] = {}
    warnings: List[str] = []
    methodology: Dict[str, Any] = {}
    performance: Dict[str, float] = {}
    privacy: PrivacyStatus = PrivacyStatus()
    stage: str = "Screenshot received"
    message: str = "Your screenshot was received securely."
    error: Optional[str] = None
