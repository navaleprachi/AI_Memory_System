import logging
from datetime import timezone
from src.compression.summarizer import summarize_messages, summarize_summaries, save_summary_as_chunk
from src.chunking import count_tokens
logger = logging.getLogger(__name__)

# Compress when this many uncompressed messages accumulate
COMPRESSION_THRESHOLD = 20

# Compress when this many unabsorbed L1 summaries accumulate into an L2 summary
L2_COMPRESSION_THRESHOLD = 5

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

async def get_unabsorbed_summaries(db, conversation_id: str, level: int) -> list[dict]:
    # Fetch summaries at the given level that have not yet been absorbed into a higher-level summary.
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, content, covers_from, covers_to, created_at
            FROM summaries
            WHERE conversation_id = $1 AND level = $2 AND parent_id IS NULL
            ORDER BY created_at ASC
            """,
            conversation_id,
            level,
        )
    return [dict(row) for row in rows]

async def mark_summaries_absorbed(db, summary_ids: list[str], parent_id: str) -> None:
    # Set parent_id on L1 summaries to record that they've been rolled up into a higher summary.
    if not summary_ids:
        return
    async with db.acquire() as conn:
        await conn.execute(
            """
            UPDATE summaries
            SET parent_id = $1
            WHERE id = ANY($2::uuid[])
            """,
            parent_id,
            summary_ids,
        )

async def maybe_compress_summaries(db, conversation_id: str) -> bool:
    # If enough L1 summaries have accumulated, compress them into a single L2 summary.
    unabsorbed = await get_unabsorbed_summaries(db, conversation_id, level=1)
    if len(unabsorbed) < L2_COMPRESSION_THRESHOLD:
        return False

    to_compress = unabsorbed[:L2_COMPRESSION_THRESHOLD]
    source_ids  = [str(s["id"]) for s in to_compress]
    covers_from = to_compress[0]["covers_from"]
    covers_to   = to_compress[-1]["covers_to"]

    logger.info(f"[Compression] L2 firing for {conversation_id} — {len(to_compress)} L1 summaries -> L2 summary")

    # Step 1. Merge L1 summaries into a single L2 summary via LLM
    summary_text = await summarize_summaries(to_compress)

    # Step 2. Save L2 summary record
    l2_summary_id = await save_summary_record(
        db,
        conversation_id=conversation_id,
        content=summary_text,
        source_ids=source_ids,
        level=2,
        covers_from=covers_from,
        covers_to=covers_to,
    )

    # Step 3. Embed and store the L2 summary as a searchable chunk
    await save_summary_as_chunk(db, conversation_id, summary_text, source_ids[0])

    # Step 4. Mark the L1 summaries as absorbed into this L2 summary
    await mark_summaries_absorbed(db, source_ids, l2_summary_id)

    logger.info(f"[Compression] L2 done — summary {l2_summary_id[:8]}... covers {len(to_compress)} L1 summaries")
    return True

async def maybe_compress(db, conversation_id: str, force: bool = False) -> bool:
    # Check if there are enough uncompressed messages to trigger compression.
    # force=True bypasses the threshold (used by the manual "Compress Now" button).
    uncompressed_messages = await get_uncompressed_messages(db, conversation_id)
    if not force and len(uncompressed_messages) < COMPRESSION_THRESHOLD:
        return False  # Not enough messages to compress yet.
    if len(uncompressed_messages) == 0:
        return False  # Nothing to compress at all.

    # Take the oldest COMPRESSION_THRESHOLD messages (or all if force=True).
    messages_to_compress = uncompressed_messages if force else uncompressed_messages[:COMPRESSION_THRESHOLD]
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
    logger.info(f"[Compression] L1 done — summary {summary_id[:8]}... covers {len(messages_to_compress)} messages")

    # Step 5. Check if L1 summaries should now be rolled up into an L2 summary
    await maybe_compress_summaries(db, conversation_id)

    return True  # Compression was performed
    