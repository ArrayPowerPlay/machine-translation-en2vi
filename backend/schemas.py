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


class ContributionRequest(BaseModel):
    suggestion: str
