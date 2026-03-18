from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MemoryChunkDebug(BaseModel):
    content: str
    similarity: float
    recency_score: float
    importance_score: float
    final_score: float
    source_type: str           # "message" or "summary"
    
class CompressionStats(BaseModel):
    total_messages: int
    compressed_messages: int
    tokens_summaries: int
    compression_ratio: float
    
class ChatDebugResponse(BaseModel):
    reply: str
    conversation_id: str
    tokens_used: int
    message_count: int
    memories_injected: List[MemoryChunkDebug]
    compression_stats: CompressionStats

# Request model (what the client sends to the server(AI))
class ChatRequest(BaseModel):
    message: str
    
class CreateConversationRequest(BaseModel):
    title: Optional[str] = None
    
# Response model (what the server (AI) sends back to the client)
class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    token_count: Optional[int]
    created_at: datetime
    
class ConversationResponse(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: datetime
    last_active: datetime
    messages_count: int
    status: str
    
class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    tokens_used: int
    message_count: int