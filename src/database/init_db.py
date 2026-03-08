import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

SCHEMA = '''
CREATE TABLE IF NOT EXISTS conversations (
	id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	title TEXT,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	last_active TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	message_count INT NOT NULL DEFAULT 0,
	status TEXT NOT NULL DEFAULT 'active'
);
CREATE TABLE IF NOT EXISTS messages (
	id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	conversation_id UUID NOT NULL REFERENCES conversations(id),
	role TEXT NOT NULL,
	content TEXT NOT NULL,
	token_count INT,
	importance_score FLOAT DEFAULT 0.5,
	is_compressed BOOLEAN DEFAULT FALSE,
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, created_at);
CREATE EXTENSION IF NOT EXISTS vector; 
CREATE TABLE IF NOT EXISTS chunks ( 
	id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
 	message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE, 
	conversation_id UUID NOT NULL REFERENCES conversations(id), 
	content TEXT NOT NULL, 
	chunk_index INT NOT NULL, 
	token_count INT, 
	embedding VECTOR(1536), 
	created_at TIMESTAMPTZ NOT NULL DEFAULT NOW() 
);
CREATE INDEX IF NOT EXISTS idx_chunks_message ON chunks(message_id);
CREATE INDEX IF NOT EXISTS idx_chunks_conversation ON chunks(conversation_id);
'''

async def init_db():
	conn = await asyncpg.connect(os.environ['DATABASE_URL'])
	await conn.execute(SCHEMA)
	await conn.close()
	print('✓ Database schema initialized')

if __name__ == '__main__':
	asyncio.run(init_db())