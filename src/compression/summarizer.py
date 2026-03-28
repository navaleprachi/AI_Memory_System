import json
import logging
from openai import AsyncOpenAI
from src.chunking import chunk_text, count_tokens
from src.embeddings import embed_batch
logger = logging.getLogger(__name__)
client = AsyncOpenAI()

SUMMARY_PROMPT = """
    You are a memory compression engine for an AI assistant.
    Compress the following conversation messages into concise bullet points.
    Rules:
    - Preserve: names, roles, locations, decisions, preferences, technical facts, goals
    - Drop: greetings, filler, thanks, repetition, questions already answered
    - Format: bullet points starting with -
    - Length: maximum 200 words
    - Tone: factual, third-person ("User stated...", "User prefers...")
    Output ONLY the bullet points. No introduction, no conclusion.
"""

HIGHER_SUMMARY_PROMPT = """
    You are a memory compression engine for an AI assistant.
    You will receive several bullet-point summaries from different parts of a conversation.
    Merge them into a single, condensed summary.
    Rules:
    - Merge duplicate or overlapping facts into one bullet point
    - Preserve all unique facts: names, roles, decisions, preferences, goals, technical details
    - Drop anything superseded by a later fact (e.g. old preference overridden by new one)
    - Format: bullet points starting with -
    - Length: maximum 200 words
    - Tone: factual, third-person ("User stated...", "User prefers...")
    Output ONLY the bullet points. No introduction, no conclusion.
"""

async def summarize_messages(messages: list[dict]) -> str:
    """
        Compress a list of message dicts into a bullet-point summary.
        Each dict must have 'role' and 'content' keys.
        Returns the summary string.
    """
    # Step 1: Format messages as a readable string for the LLM
    transcript_lines = []
    for msg in messages:
        role = msg['role'].upper()  # USER, SYSTEM, ASSISTANT
        content = msg['content'][:500] # cap very long messages to avoid hitting token limits in prompt
        transcript_lines.append(f"{role}: {content}")
        
    transcript = "\n".join(transcript_lines)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": transcript}
        ],
        max_tokens=400,  # ~200 words bullet points only - short
        temperature=0.1, # deterministic summary
    )  
    
    return response.choices[0].message.content.strip()

async def summarize_summaries(summaries: list[dict]) -> str:
    """
    Compress a list of L1 summary dicts into a single higher-level bullet-point summary.
    Each dict must have a 'content' key.
    Returns the merged summary string.
    """
    combined = "\n\n---\n\n".join(s["content"] for s in summaries)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": HIGHER_SUMMARY_PROMPT},
            {"role": "user",   "content": combined}
        ],
        max_tokens=400,
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()

async def save_summary_as_chunk(db, conversation_id: str, summary_text: str, source_message_id: str) -> str:
    """
        Embed the summary text and store it in the chunks table
        with source_type = 'summary' so it appears in vector search.
        Returns the chunk UUID.
    """
    
    # Summaries are short enough to be a single chunk
    vectors = await embed_batch([summary_text])
    vector = vectors[0]
    vector_text = '[' + ','.join(str(v) for v in vector) + ']'
    
    async with db.acquire() as conn:
        chunk_id = await conn.fetchval("""
            INSERT INTO chunks(message_id, conversation_id, content, chunk_index, token_count, embedding, source_type)
            VALUES ($1, $2, $3, 0, $4, $5, 'summary')
            RETURNING id
            """,
            source_message_id,
            conversation_id,
            summary_text,
            count_tokens(summary_text),
            vector_text,
            )
    return str(chunk_id)