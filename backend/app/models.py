from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    source_lang = Column(String(5), nullable=False)
    target_lang = Column(String(5), nullable=False)
    style_profile_id = Column(Integer, ForeignKey("style_profiles.id"), nullable=True)
    status = Column(String, default="uploaded")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    segments = relationship("Segment", back_populates="project", cascade="all, delete-orphan")
    style_profile = relationship("StyleProfile")

class Segment(Base):
    __tablename__ = "segments"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    position = Column(Integer, nullable=False)
    segment_type = Column(String, default="body")
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=True)
    back_translated_text = Column(Text, nullable=True)
    
    match_type = Column(String, nullable=True)
    match_score = Column(Float, default=0.0)
    
    status = Column(String, default="pending")
    confidence_score = Column(Float, nullable=True)
    
    project = relationship("Project", back_populates="segments")

class TranslationMemoryEntry(Base):
    __tablename__ = "translation_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    source_lang = Column(String(5), nullable=False)
    target_lang = Column(String(5), nullable=False)
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GlossaryTerm(Base):
    __tablename__ = "glossary"
    
    id = Column(Integer, primary_key=True, index=True)
    source_term = Column(String, nullable=False, index=True)
    target_term = Column(String, nullable=False)
    source_lang = Column(String(5), nullable=False)
    target_lang = Column(String(5), nullable=False)
    context_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StyleProfile(Base):
    __tablename__ = "style_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    tone = Column(String, default="Formal")
    custom_rules = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    action = Column(String, nullable=False)
    previous_translation = Column(Text, nullable=True)
    final_translation = Column(Text, nullable=False)
    user_name = Column(String, default="Linguist")
    timestamp = Column(DateTime, default=datetime.utcnow)
