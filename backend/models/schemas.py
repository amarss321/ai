from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel

# Check if we're using MongoDB or SQL database
try:
    from .database import Base
    
    # SQL Models
    class Session(Base):
        __tablename__ = "sessions"
        
        id = Column(String, primary_key=True, index=True)
        created_at = Column(DateTime, default=datetime.now)
        is_active = Column(Boolean, default=True)
        
        transcripts = relationship("Transcript", back_populates="session")
        responses = relationship("Response", back_populates="session")
    
    
    class Transcript(Base):
        __tablename__ = "transcripts"
        
        id = Column(String, primary_key=True, index=True)
        session_id = Column(String, ForeignKey("sessions.id"))
        text = Column(Text)
        timestamp = Column(DateTime, default=datetime.now)
        
        session = relationship("Session", back_populates="transcripts")
        responses = relationship("Response", back_populates="transcript")
    
    
    class Response(Base):
        __tablename__ = "responses"
        
        id = Column(String, primary_key=True, index=True)
        session_id = Column(String, ForeignKey("sessions.id"))
        transcript_id = Column(String, ForeignKey("transcripts.id"))
        text = Column(Text)
        timestamp = Column(DateTime, default=datetime.now)
        
        session = relationship("Session", back_populates="responses")
        transcript = relationship("Transcript", back_populates="responses")

except (NameError, ImportError):
    # MongoDB Models (Pydantic models for validation)
    class SessionBase(BaseModel):
        id: str
        created_at: datetime
        is_active: bool = True
    
    
    class Session(SessionBase):
        pass
    
    
    class TranscriptBase(BaseModel):
        session_id: str
        text: str
        timestamp: datetime
    
    
    class Transcript(TranscriptBase):
        id: str
    
    
    class ResponseBase(BaseModel):
        session_id: str
        transcript_id: str
        text: str
        timestamp: datetime
    
    
    class Response(ResponseBase):
        id: str