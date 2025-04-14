from sqlalchemy.orm import Session
from app.database.db import EmbeddingRecord, ConversationRecord, RelatedAnswer
from typing import List, Dict, Any, Optional


async def store_embedding(db: Session, text: str) -> EmbeddingRecord:
    """Store the text used for embedding in the database"""
    db_embedding = EmbeddingRecord(text=text)
    db.add(db_embedding)
    db.commit()
    db.refresh(db_embedding)
    return db_embedding


async def store_conversation(
    db: Session,
    embedding_id: int,
    question: str,
    answer: str,
    related_answers: List[Dict[str, Any]],
    market_data: Optional[Dict[str, Any]] = None,
) -> ConversationRecord:
    """Store the conversation response in the database"""
    
    # Create conversation record
    db_conversation = ConversationRecord(
        embedding_id=embedding_id,
        question=question,
        answer=answer,
        coin_symbol=market_data.get("symbol") if market_data else None,
        coin_price=market_data.get("current_price") if market_data else None,
    )
    
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    
    # Store related answers
    if related_answers:
        for item in related_answers:
            db_related = RelatedAnswer(
                conversation_id=db_conversation.id,
                answer=item["answer"],
                distance=item["distance"]
            )
            db.add(db_related)
        
        db.commit()
    
    return db_conversation


async def get_embedding_by_text(db: Session, text: str) -> Optional[EmbeddingRecord]:
    """Get embedding record by text"""
    return db.query(EmbeddingRecord).filter(EmbeddingRecord.text == text).first()


async def get_recent_conversations(
    db: Session, limit: int = 10
) -> List[ConversationRecord]:
    """Get recent conversations"""
    return db.query(ConversationRecord).order_by(
        ConversationRecord.created_at.desc()
    ).limit(limit).all() 