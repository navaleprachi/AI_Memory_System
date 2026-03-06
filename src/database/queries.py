import asyncpg, tiktoken

enc = tiktoken.encoding_for_model("gpt-4o-mini")

def count_tokens(text: str) -> int:
    return len(enc.encode(text))

# Cnnversation queries
async def create_conversation(db: asyncpg.Connection, title: str = None) -> str:
    row = await db.fetchrow('''
        INSERT INTO conversations (title) VALUES ($1) RETURNING id, title, created_at, last_active, message_count, status
    ''', title)
    return str(row['id'])

async def get_conversations(db: asyncpg.Connection) -> list:
    rows = await db.fetch('''
        SELECT id, title, created_at, last_active, message_count, status FROM conversations ORDER BY last_active DESC
    ''')
    return [dict(r) for r in rows]

# Message queries
async def save_message(db: asyncpg.Connection, conv_id: str, role: str, content: str) -> str:
    tokens = count_tokens(content)
    row = await db.fetchrow('''
        INSERT INTO messages (conversation_id, role, content, token_count) VALUES ($1, $2, $3, $4) RETURNING id
    ''', conv_id, role, content, tokens)

    # Update conversation metadata
    await db.execute('''
        UPDATE conversations SET last_active = NOW(), message_count = message_count + 1 WHERE id = $1
    ''', conv_id)

    return str(row['id'])

async def get_messages(db: asyncpg.Connection, conv_id: str) -> list:
    rows = await db.fetch('''
        SELECT id, role, content, token_count, created_at FROM messages WHERE conversation_id = $1 ORDER BY created_at ASC
    ''', conv_id)
    return [dict(r) for r in rows]
