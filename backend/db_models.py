from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class TranslationHistory(Base):
    __tablename__ = "translation_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    source_lang = Column(String(10))
    target_lang = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Gộp từ SavedTranslation
    is_saved = Column(Boolean, default=False)
    
    # Gộp từ TranslationRating (5=like, 1=dislike, None=chưa rate)
    rating = Column(Integer, nullable=True)
    
    # Gộp từ TranslationContribution (lưu suggestion mới nhất của user)
    suggestion = Column(Text, nullable=True)


