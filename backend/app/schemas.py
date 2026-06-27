from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# --- Project Schemas ---
class ProjectCreate(BaseModel):
    name: str = Field(..., example="User Manual V2")
    source_lang: str = Field(..., max_length=5, example="en")
    target_lang: str = Field(..., max_length=5, example="es")
    style_profile_id: Optional[int] = None

class ProjectResponse(BaseModel):
    id: int
    name: str
    source_lang: str
    target_lang: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

# --- Segment Schemas ---
class SegmentResponse(BaseModel):
    id: int
    project_id: int
    position: int
    segment_type: str
    source_text: str
    translated_text: Optional[str] = None
    back_translated_text: Optional[str] = None
    match_type: Optional[str] = None
    match_score: float
    confidence_score: Optional[float] = None
    status: str

    class Config:
        orm_mode = True
        from_attributes = True

# --- Glossary Schemas ---
class GlossaryTermCreate(BaseModel):
    source_term: str
    target_term: str
    source_lang: str
    target_lang: str
    context_note: Optional[str] = None

class GlossaryTermResponse(GlossaryTermCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

# --- Review/Approval Schemas ---
class SegmentApproveRequest(BaseModel):
    approved_translation: str
    reviewer_name: Optional[str] = "Linguist"

# --- Style Profile Schemas ---
class StyleProfileCreate(BaseModel):
    name: str
    tone: str = "Formal"
    custom_rules: Optional[List[str]] = None

class StyleProfileResponse(StyleProfileCreate):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
