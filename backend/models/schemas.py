"""
backend/models/schemas.py

Pydantic request/response models for the FastAPI layer (Phase 4).
These define the API's public contract — what shape of data callers
send and receive — separate from the internal service-layer logic in
backend/services/.
"""
from pydantic import BaseModel
from typing import Optional, Literal


class SuggestionItem(BaseModel):
    type: Literal["missing_skill", "missing_section"]
    priority: Literal["high", "medium", "low"]
    message: str
    skill: Optional[str] = None
    jd_frequency: Optional[int] = None
    reason: Optional[str] = None


class MatchResponse(BaseModel):
    score: float
    matched_skills: list[str]
    missing_skills: list[str]
    suggestions: list[SuggestionItem]