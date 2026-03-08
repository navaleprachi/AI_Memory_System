import re 
import tiktoken 
from typing import List 

enc = tiktoken.encoding_for_model('gpt-4o-mini')

def count_tokens(text: str) -> int:
	return len(enc.encode(text))

def split_sentences(text: str) -> List[str]:
	# Split text at sentence boundaries.
	# Split on . ! ? followed by space or end of string
	sentences = re.split(r'(?<=[.!?])(?:\s+|$)', text.strip())
	return [s.strip() for s in sentences if s.strip()]

def chunk_text(
	text: str, max_tokens: int = 200, min_tokens: int = 1
) -> List[str]:
	# Split text into overlapping chunks at sentence boundaries.
	# Short text — return as single chunk
	if count_tokens(text) <= max_tokens:
		return [text.strip()] if count_tokens(text) >= min_tokens else []
	
	sentences = split_sentences(text)
	chunks: List[str] = []
	current: List[str] = []
	current_tokens = 0
	
	for sentence in sentences:
		s_tokens = count_tokens(sentence)
		# Chunk is full — save it and start new with overlap
		if current_tokens + s_tokens > max_tokens and current:
			chunk = ' '.join(current)
			if count_tokens(chunk) >= min_tokens:
				chunks.append(chunk)
			# Overlap: keep last sentence for next chunk
			current = [current[-1]]  # sliding window
			current_tokens = count_tokens(current[0])
		
		current.append(sentence)
		current_tokens += s_tokens
	
	# Don't forget the last chunk
	if current:
		chunk = ' '.join(current)
		if count_tokens(chunk) >= min_tokens:
			chunks.append(chunk)
	
	return chunks