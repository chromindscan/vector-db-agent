from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Create database directory if it doesn't exist
os.makedirs("app/database/data", exist_ok=True)

SQLALCHEMY_DATABASE_URL = "sqlite:///./app/database/data/vector_db.sqlite"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Database models
class EmbeddingRecord(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship with conversation responses
    conversations = relationship("ConversationRecord", back_populates="embedding")


class ConversationRecord(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    embedding_id = Column(Integer, ForeignKey("embeddings.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # For market data if available
    coin_symbol = Column(String(10), nullable=True)
    coin_price = Column(Float, nullable=True)
    
    # Relationship with embedding record
    embedding = relationship("EmbeddingRecord", back_populates="conversations")


class RelatedAnswer(Base):
    __tablename__ = "related_answers"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    answer = Column(Text, nullable=False)
    distance = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 