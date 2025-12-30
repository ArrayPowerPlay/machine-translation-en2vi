from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
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


class SavedTranslation(Base):
    __tablename__ = "saved_translations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    source_lang = Column(String(10))
    target_lang = Column(String(10))
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TranslationContribution(Base):
    __tablename__ = "contributions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_text = Column(Text, nullable=False)
    suggested_translation = Column(Text, nullable=False)
    source_lang = Column(String(10))
    target_lang = Column(String(10))



class TranslationRating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=False) # 1-5

