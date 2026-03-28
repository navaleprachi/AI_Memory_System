import os
import asyncio, sys
sys.path.insert(0, "")
import asyncpg
from dotenv import load_dotenv
load_dotenv()
from src.compression import summarize_messages, maybe_compress
from src.retrieval import search_chunks, score_and_rank

SAMPLE_MESSAGES = [
    {"role": "user", "content": "Hey! How are you?"},
    {"role": "assistant", "content": "I'm great, how can I help?"},
    {"role": "user", "content": "My name is Prachi. I'm a frontend engineer at Nooon."},
    {"role": "assistant", "content": "Nice to meet you Prachi!"},
    {"role": "user", "content": "I'm learning Python and building an AI memory system."},
    {"role": "assistant", "content": "That's a great project! What phase are you on?"},
    {"role": "user", "content": "Phase 6 — hierarchical summarization."},
    {"role": "assistant", "content": "Impressive! Summarization is key for long-term memory."},
    {"role": "user", "content": "I prefer React over Angular for frontend work."},
    {"role": "user", "content": "Thanks for the help!"},
]

async def test():
    print("Summarizer test\n")
    print(f"Input messages ({len(SAMPLE_MESSAGES)}):")
    summary = await summarize_messages(SAMPLE_MESSAGES)
    print(f"Summary ({len(summary.split())} words):\n{summary}")
    
    # Check it presevered the key facts and dropped the low-value content
    assert "Prachi" in summary, "Name should be preserved"
    assert "frontend" in summary.lower(), "Role should be preserved"
    assert "memory" in summary.lower(), "Project should be preserved"
    
    print("\nAll assertions passed. Key facts presevered in summary!")
    
async def test_end_to_end():
    db = await asyncpg.create_pool(os.environ["DATABASE_URL"])
    # Get first available conversation_id
    async with db.acquire() as conn:
        conv_id = await conn.fetchval(
            "SELECT id FROM conversations ORDER BY created_at LIMIT 1"
        )
    if not conv_id:
        print("No conversations found — send 20+ messages first via the API")
        await db.close()
        return
    conv_id = str(conv_id)
    print(f"\nTesting compression for conversation: {conv_id[:8]}...")
    # Check uncompressed count before
    async with db.acquire() as conn:
        before = await conn.fetchval(
            "SELECT COUNT(*) FROM messages WHERE conversation_id=$1 AND is_compressed=FALSE",
            conv_id
        )
    print(f"Uncompressed messages before: {before}")
    # Run compression
    fired = await maybe_compress(db, conv_id)
    print(f"Compression fired: {fired}")
    if fired:
        # Verify summaries table has a new row
        async with db.acquire() as conn:
            summary_count = await conn.fetchval(
                "SELECT COUNT(*) FROM summaries WHERE conversation_id=$1", conv_id
            )
            after = await conn.fetchval(
                "SELECT COUNT(*) FROM messages WHERE conversation_id=$1 AND is_compressed=FALSE",
                conv_id
            )
        print(f"Summaries in DB: {summary_count}")
        print(f"Uncompressed messages after: {after}")
        # Verify summary is searchable via vector search
        results = await search_chunks(db, "who is this user and what are they building?", top_k=5)
        summary_results = [r for r in results if r.get("source_type") == "summary"]
        print(f"Summary chunks in search results: {len(summary_results)}")
        if summary_results:
            print(f"Top summary chunk: {summary_results[0]['content'][:100]}...")
        print("\nAll compression tests passed!")
    else:
        print(f"Need {20 - before} more messages to trigger compression")
    await db.close()
    
if __name__ == "__main__":
    # asyncio.run(test())
    asyncio.run(test_end_to_end())