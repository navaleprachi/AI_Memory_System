import asyncio
from openai import AsyncOpenAI
from typing import List

client = AsyncOpenAI()
EMBEDDING_MODEL = 'text-embedding-3-small'

async def embed_text(text: str) -> List[float]:
	#Convert text to a 1536-dim vector using OpenAI.
	response = await client.embeddings.create(
		model=EMBEDDING_MODEL,
		input=text.replace('\n', ' ')
	)
	return response.data[0].embedding

async def embed_batch(texts: List[str]) -> List[List[float]]:
	#Embed multiple texts in one API call (more efficient).
	if not texts:
		return []
	response = await client.embeddings.create(
		model=EMBEDDING_MODEL,
		input=[t.replace('\n', ' ') for t in texts]
	)
	return [item.embedding for item in response.data]