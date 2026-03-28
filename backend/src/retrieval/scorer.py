import math
from datetime import datetime, timezone
from typing import List, Dict, Any

# Tunable weights for scoring components - must sum to 1.0
WEIGHT_RELEVANCE = 0.5
WEIGHT_RECENCY = 0.3
WEIGHT_IMPORTANCE = 0.2

# Recency half-line in days
# Score halves every 7 days, so recent chunks get higher scores.
HALF_LIFE_DAYS = 7

def recency_score(created_at) -> float:
    # Exponential decay based on age of the chunk. Newer chunks score higher.
    # Returns 1.0 for brand-new, approaches 0.0 as it gets very old.
    
    # Parse string to datetime if needed
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    
    now = datetime.now(timezone.utc)
    # Make sure created_at is timezone-aware for accurate comparison
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    
    days_old = (now - created_at).total_seconds() / (3600 * 24)
    return math.exp(-0.693 * days_old / HALF_LIFE_DAYS)

def final_score(relevance: float, recency: float, importance: float) -> float:
    # Weighted sum of the three components. Higher is better.
    return (WEIGHT_RELEVANCE * relevance) + (WEIGHT_RECENCY * recency) + (WEIGHT_IMPORTANCE * importance)

def score_and_rank(chunks: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    # Score each chunk and return the top_k ranked by final score.
    scored = []
    for chunk in chunks:
        relevance = chunk["similarity"]  # Already between 0 and 1 from the vector search
        recency = recency_score(chunk["created_at"])
        
        # importance_score not in DB yet — Phase 5 adds it
        # Use 0.5 as neutral default for now
        imp = chunk.get("importance_score", 0.5)
        fscore = final_score(relevance, recency, imp)
        scored.append({
            "id": chunk["id"],
            "content": chunk["content"],
            "message_id": chunk["message_id"],
            "conversation_id": chunk["conversation_id"],
            "token_count": chunk["token_count"],
            "created_at": chunk["created_at"],
            "source_type": chunk.get("source_type", "message"),
            "similarity": relevance * 100,  # convert to percentage for easier interpretation
            "recency_score": recency,
            "importance_score": imp,
            "final_score": fscore,
        })
        
    # Sort by final score descending and return top_k
    scored.sort(key=lambda x: x["final_score"], reverse=True)
    return scored[:top_k]