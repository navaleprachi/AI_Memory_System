import logging
from datetime import timezone
from src.compression.summarizer import summarize_messages, save_summary_as_chunk
from src.chunking import count_tokens
logger = logging.getLogger(__name__)

# Compress when this many uncompressed messages accumalte
COMPRESSION_THRESHOLD = 20

async def get_uncompressed_messages(db, conversation_id: str) -> list[dict]:
    # Fetch messages not yet compressed, older first.
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, role, content, created_at, importance_score
            FROM messages
            WHERE conversation_id = $1 AND is_compressed = FALSE
            AND role!= 'system'
            ORDER BY created_at ASC
            """,
            conversation_id,
        )
    return [dict(row) for row in rows]

async def mark_messages_as_compressed(db, message_ids: list[str]) -> None:
    # Set is_compressed = TRUE on a list of messages.
    if not message_ids:
        return
    async with db.acquire() as conn:
        await conn.execute(
            """
            UPDATE messages
            SET is_compressed = TRUE
            WHERE id = ANY($1::uuid[])
            """,
            message_ids,
        )

async def save_summary_record(db, conversation_id: str, content: str, source_ids: list[str], level: int, covers_from, covers_to) -> str:
    # Insert a row into the summaries table, returning the new summary ID(UUID)
    async with db.acquire() as conn:
        summary_id = await conn.fetchval(
            """
            INSERT INTO summaries(conversation_id, level, content, source_ids, token_count, covers_from, covers_to)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """,
            conversation_id,
            level,
            content,
            source_ids,
            count_tokens(content),
            covers_from,
            covers_to,
        )
    return str(summary_id)

async def maybe_compress(db, conversation_id: str) -> bool:
    # Check if there are enough uncompressed messages to trigger compression.
    uncompressed_messages = await get_uncompressed_messages(db, conversation_id)
    if len(uncompressed_messages) < COMPRESSION_THRESHOLD:
        return False  # Not enough messages to compress yet.
    
    # Take the oldest COMPRESSION_THRESHOLD messages for summarization.
    messages_to_compress = uncompressed_messages[:COMPRESSION_THRESHOLD]
    source_ids = [str(msg['id']) for msg in messages_to_compress]
    covers_from = messages_to_compress[0]['created_at']
    covers_to = messages_to_compress[-1]['created_at']
    
    logger.info(f"[Compression] firing for {conversation_id} " f"— {len(messages_to_compress)} messages -> L1 summary")
    
    # Step 1. Generate the summary text via LLM
    summary_text = await summarize_messages(messages_to_compress)
    
    # Step 2. Save the summary as a new chunk in the summaries table
    summary_id = await save_summary_record(
        db,
        conversation_id = conversation_id,
        content = summary_text,
        source_ids = source_ids,
        level=1,
        covers_from=covers_from,
        covers_to=covers_to,
    )
    
    # Step 3. Embed the summary and store as a searchable chunk
    await save_summary_as_chunk(db, conversation_id, summary_text, source_ids[0])
    
    # Step 4. Mark the original messages as compressed
    await mark_messages_as_compressed(db, source_ids)
    logger.info(f"[Compression] done — summary {summary_id[:8]}... " f"covers {len(messages_to_compress)} messages"
    )
    
    return True  # Compression was performed
    