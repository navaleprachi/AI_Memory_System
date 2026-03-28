import math
from datetime import datetime, timezone
from typing import List, Dict, Any
from src.embeddings import embed_text

TOP_K_CANDIDATES = 20

async def search_chunks(db, query: str, conv_id: str = None, top_k: int = TOP_K_CANDIDATES) -> List[Dict[str, Any]]:
    # Embed the query text and find the most semantically similar chunks
    query_vector = await embed_text(query)
    query_vector_text = '[' + ','.join(str(v) for v in query_vector) + ']'
    
    async with db.acquire() as conn:
        if conv_id:
            rows = await conn.fetch('''
                SELECT
                c.id,
                c.content,
                c.message_id,
                c.conversation_id,
                c.chunk_index,
                c.token_count,
                c.created_at,
                c.source_type,
                1 - (c.embedding <=> $1::vector) AS similarity,
                COALESCE(m.importance_score, 0.5) AS importance_score
                FROM chunks c
                LEFT JOIN messages m ON m.id = c.message_id
                WHERE c.embedding IS NOT NULL
                AND c.conversation_id = $2
                ORDER BY c.embedding <=> $1::vector
                LIMIT $3
                ''',
                query_vector_text, conv_id, top_k
            )
        else:
            # Search across all conversations (cross-session memory)
            rows = await conn.fetch('''
                SELECT
                c.id,
                c.content,
                c.message_id,
                c.conversation_id,
                c.chunk_index,
                c.token_count,
                c.created_at,
                c.source_type,
                1 - (c.embedding <=> $1::vector) AS similarity,
                COALESCE(m.importance_score, 0.5) AS importance_score
                FROM chunks c
                LEFT JOIN messages m ON m.id = c.message_id
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> $1::vector
                LIMIT $2
                ''',
                query_vector_text, top_k
            )
    return [
        {
            'id': str(r['id']),
            'content': r['content'],
            'message_id': str(r['message_id']),
            'conversation_id': str(r['conversation_id']),
            'chunk_index': r['chunk_index'],
            'token_count': r['token_count'],
            'created_at': r['created_at'].isoformat(),
            'similarity': r['similarity'],
            'importance_score': r['importance_score'],
        }
        for r in rows
    ]
