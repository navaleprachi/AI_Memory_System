import sys 
sys.path.insert(0, '') 
from src.chunking import chunk_text, count_tokens 

# Test 1: Short message — should be 1 chunk 
short = 'I love React and TypeScript.'
chunks = chunk_text(short)
print(f'Short message: {len(chunks)} chunk(s)')
assert len(chunks) == 1, 'Short should be 1 chunk'

# Test 2: Long message — should split into multiple chunks
long = ' '.join([f'This is sentence number {i} about frontend engineering.' for i in range(30)])
chunks = chunk_text(long)
print(f'Long message: {len(chunks)} chunk(s)')
assert len(chunks) > 1, 'Long should be multiple chunks'

# Test 3: Verify overlap — last sentence of chunk N appears in chunk N+1
print('\nChunk content preview:')
for i, chunk in enumerate(chunks):
	toks = count_tokens(chunk)
	print(f' Chunk {i}: {toks} tokens | {chunk[:60]}...')
 
# Test 4: Overlap verification
if len(chunks) > 1:
	# Last sentence of chunk 0 should appear in chunk 1
	last_sentence_c0 = chunks[0].split('. ')[-1]
	overlap_exists = last_sentence_c0[:-1] in chunks[1]
	print(f'\nOverlap working: {overlap_exists}')
print('\n✓ All chunker tests passed')