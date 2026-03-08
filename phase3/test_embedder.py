import asyncio
import sys

sys.path.insert(0, '')
from dotenv import load_dotenv
load_dotenv()

from src.embeddings import embed_text, embed_batch

async def test():
	# Test 1: single embedding
	v = await embed_text('I love building with React and TypeScript')
	print(f'Vector dimensions: {len(v)}')
	assert len(v) == 1536, 'Should be 1536-dim'
	print(f'First 5 values: {[round(x, 4) for x in v[:5]]}')
	
	# Test 2: similar texts should have high cosine similarity
	v1 = await embed_text('I love React and frontend development')
	v2 = await embed_text('React is my favorite JavaScript library')
	v3 = await embed_text('I enjoy baking chocolate cake on weekends')
	
	def cosine_sim(a, b):
		dot = sum(x*y for x, y in zip(a, b))
		mag_a = sum(x**2 for x in a)**0.5
		mag_b = sum(x**2 for x in b)**0.5
		return dot / (mag_a * mag_b)
	
	sim_related = cosine_sim(v1, v2)
	sim_unrelated = cosine_sim(v1, v3)
	print(f'\nReact vs React: {sim_related:.4f} (should be HIGH)')
	print(f'React vs Baking: {sim_unrelated:.4f} (should be LOW)')
	assert sim_related > sim_unrelated, 'Related texts should score higher!'
	
	# Test 3: batch embedding
	vectors = await embed_batch(['chunk one', 'chunk two', 'chunk three'])
	print(f'\nBatch: {len(vectors)} vectors returned')
	assert len(vectors) == 3
	print('\n✓ All embedding tests passed')

asyncio.run(test())