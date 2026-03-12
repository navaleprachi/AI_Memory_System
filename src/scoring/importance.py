import json
import logging
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)
client = AsyncOpenAI()

# The scoring prompt
IMPOTANCE_PROMPT = """
    You are a memory importance scorer for an AI assistant.
    Score the importance of the following message for long-term memory retention.
    Scoring rubric:
    0.9-1.0 : Critical facts — name, role, location, explicit goals, decisions
    0.7-0.9 : Important context — preferences, skills, projects, key opinions
    0.4-0.7 : Useful context — questions asked, topics explored, explanations
    0.1-0.4 : Low value — greetings, thanks, filler, acknowledgements
    Respond ONLY with a JSON object. No explanation. No prose.
    Example: {"score": 0.8} 
"""

async def score_importance(content: str, role: str ="user") -> float:
    """
        Score the long-term importance of a message using the LLM.
        Returns a float between 0.0 and 1.0.
        Falls back to 0.5 on any error so the system never breaks.
    """
    
    # System messages are always important - score them high
    if role == "system":
        return 0.8
    
    # Very short messages are almost always low importance (greetings, thanks, etc) - score them low
    if len(content.strip()) < 10:
        return 0.2
    
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": IMPOTANCE_PROMPT},
                {"role": "user", "content": content}
            ],
            max_tokens=20,    # need only {"score": 0.8} - tiny
            temperature=0.0,  # deterministic scoring
        )
        text = response.choices[0].message.content
        data = json.loads(text)
        score = float(data["score"])
        return max(0.0, min(1.0, score))  # Ensure between 0 and 1
    except Exception as e:
        logger.warning(f"importance scoring failed: {e} — using default 0.5")
        return 0.5  # Neutral fallback score on error

async def score_batch(messages: list[dict]) -> list[float]:
    """
        Score a list of messages. Used when back-filling scores
        for existing messages that still have the 0.5 default.
    """
    import asyncio
    
    tasks = [score_importance(m['content'], m.get('role', 'user')) for m in messages]
    
    return await asyncio.gather(*tasks)