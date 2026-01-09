from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str
    password: str = Field(..., min_length=6, description="Password must has at least 6 characters")
    confirm_password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "en" 
    target_lang: str = "vi" 
    

class HistoryResponse(BaseModel):
    id: int
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    created_at: datetime
    is_saved: bool = False
    rating: Optional[int] = None
    suggestion: Optional[str] = None

    class Config:
        from_attributes = True


class SavedTranslationCreate(BaseModel):
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str


class SavedTranslationResponse(SavedTranslationCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class ContributionCreate(BaseModel):
    original_text: str
    suggested_translation: str
    source_lang: str
    target_lang: str


class RatingCreate(BaseModel):
    original_text: str
    translated_text: str
    rating: int = Field(..., ge=1, le=5)
