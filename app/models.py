from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TextEmbeddingRequest(BaseModel):
    text: str = Field(..., description="Text to embed in the vector database")
    
class TextEmbeddingResponse(BaseModel):
    success: bool
    error: Optional[str] = None


class TextSearchRequest(BaseModel):
    text: str = Field(..., description="Text to search for in the vector database")
    max_results: int = Field(5, description="Maximum number of results to return")


class TextSearchResponse(BaseModel):
    results: List[Dict[str, Any]]


class TextConversationRequest(BaseModel):
    question: str = Field(..., description="Question about cryptocurrency")
    top_k: int = Field(3, description="Number of vector results to include in context")


class RelatedAnswer(BaseModel):
    answer: str
    distance: float


class MarketDataSimple(BaseModel):
    symbol: Optional[str] = None
    current_price: Optional[float] = None


class TextConversationResponse(BaseModel):
    question: str
    answer: str
    related_answers: List[RelatedAnswer]
    market_data: MarketDataSimple