import os
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from openai import OpenAI
from src.models import ChatRequest, CreateConversationRequest, ChatResponse, ConversationResponse, MessageResponse
from src.database.queries import save_message, get_messages, create_conversation, get_conversations, save_chunks, update_importance_score
from src.retrieval import search_chunks, score_and_rank, build_memory_context
from src.retrieval.injector import build_prompt_with_memory
from src.scoring import score_importance
from src.compression import maybe_compress
from src.models import MemoryChunkDebug, CompressionStats, ChatDebugResponse

router = APIRouter()
llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SYSTEM_PROMPT = "You are a helpful assistant. Remember everything the user tells you."
# Background: Score task for importance scoring to save it in DB without blocking the API response
async def score_and_store(db, message_id: str, content: str, role: str)-> None:
    score = await score_importance(content, role)
    await update_importance_score(db, message_id, score)

# 1. Create a new conversation
@router.post('/conversations')
async def new_conversation(req: CreateConversationRequest, request: Request):
    db = request.app.state.db
    async with db.acquire() as conn:
        conv_id = await create_conversation(conn, req.title)
    return {"conversation_id": conv_id, 'status': 'created'}

#2. Send message + retrieve relevant memory context and get AI(LLM) response
@router.post('/chat/{conversation_id}')
async def chat(conversation_id: str, req: ChatRequest, request: Request, background: BackgroundTasks):
    db = request.app.state.db
    # Step 1: Retrieve conversation history and save the new user message to DB
    async with db.acquire() as conn:
        # 1. Get full conversation history from DB
        history = await get_messages(conn, conversation_id)
        
        if not history:
            # 2. First message - add system prompt and reload history
            await save_message(conn, conversation_id, 'system', SYSTEM_PROMPT)
            history = await get_messages(conn, conversation_id)
        
        # 3. Save the incoming user message to DB
        user_msg_id = await save_message(conn, conversation_id, 'user', req.message)
        
    #Step 2: Chunk and embed the user message for better retrieval later.
    await save_chunks(db, user_msg_id, conversation_id, req.message)
    background.add_task(score_and_store, db, user_msg_id, req.message, 'user')  # Score importance in background without blocking response
    background.add_task(maybe_compress, db, conversation_id)  # Trigger compression in background if needed, without blocking response
        
    # Step 3: Embed query, search ALL conversations for relevant chunks
    raw_chunks = await search_chunks(db, req.message, conv_id=None, top_k=20)  # Search across all conversations for cross-session memory
    
    # Step 4: Score and rank the retrieved chunks using relevance + recency + importance
    top_chunks = score_and_rank(raw_chunks, top_k=5)  # Keep top 5 for context injection
    
    # Step 5: Format into a memory context block (token-budgeted)
    memory_text, n_chunks, n_tokens = build_memory_context(top_chunks)
    
    print(f"[Memory] injected {n_chunks} chunks ({n_tokens} tokens)") #Log what was injected to inspect during experiments
    if top_chunks:
        print(f"[Memory] top score: {top_chunks[0]['final_score']:.4f}, content: {top_chunks[0]['content'][:60]}")
    
    # Step 6: Get recent history (last 6 messages)
    async with db.acquire() as conn:
        all_history = await get_messages(conn, conversation_id)   # Keep only last 6 non-system messages to avoid flooding the prompt
   
    # Step 7: Assemble the full prompt with memory injected
    recent = [m for m in all_history if m["role"] != "system"][-6:]
    recent_fmt = [{"role": m["role"], "content": m["content"]} for m in recent]   
    llm_messages = build_prompt_with_memory(
        system_prompt=SYSTEM_PROMPT, 
        user_message=req.message, 
        memory_text=memory_text, 
        recent_history=recent_fmt
    )
    
    # Step 8: Call the LLM
    response = llm.chat.completions.create(
         model="gpt-4o-mini",
        messages=llm_messages
    )
    reply = response.choices[0].message.content
    tokens = response.usage.total_tokens
        
    # Step 9: Save the assistant's reply to DB
    async with db.acquire() as conn:
        reply_msg_id = await save_message(conn, conversation_id, 'assistant', reply)
        updated = await get_messages(conn, conversation_id)
       
    # Step 10: Chunk and embed the assistant's reply too so it's searchable later. 
    await save_chunks(db, reply_msg_id, conversation_id, reply)
    background.add_task(score_and_store, db, reply_msg_id, reply, 'assistant')  # Score importance in background without blocking response
        
    return ChatResponse(
        reply=reply, 
        tokens_used=tokens, 
        conversation_id=conversation_id, 
        message_count=len(updated)
    )

# 3. Get Conversation history
@router.get('/conversations/{conversation_id}')
async def get_conversation(conversation_id: str, request: Request):
    db = request.app.state.db
    async with db.acquire() as conn:
        messages = await get_messages(conn, conversation_id)
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {'conversation_id': conversation_id, 'messages': messages}

# 4. List all conversations
@router.get('/conversations')
async def list_conversations(request: Request):
    db = request.app.state.db
    async with db.acquire() as conn:
        convs = await get_conversations(conn)
    return {'conversations': convs}

# 5. Debug endpoint to inspect retrieved memory chunks and their scores for a given message (for experimentation)
@router.post('/chat-with-debug/{conversation_id}')
async def chat_with_debug(conversation_id: str, req: ChatRequest, request: Request, background: BackgroundTasks):
    db = request.app.state.db

    # Step 1: Get the conversation and its messages
    async with db.acquire() as conn:
        history = await get_messages(conn, conversation_id)
        if not history:
            # First message - add system prompt and reload history
            await save_message(conn, conversation_id, 'system', SYSTEM_PROMPT)
        # Save the incoming user message to DB    
        user_msg_id = await save_message(conn, conversation_id, 'user', req.message)   

    #Step 2: Chunk and embed the user message for better retrieval later.
    await save_chunks(db, user_msg_id, conversation_id, req.message)
    background.add_task(score_and_store, db, user_msg_id, req.message, 'user')  # Score importance in background without blocking response
    background.add_task(maybe_compress, db, conversation_id)  # Trigger compression in background if needed, without blocking response
        
    # Step 4: Embed query and search ALL conversations for relevant chunks
    raw_chunks = await search_chunks(db, req.message, conv_id=None, top_k=20)  # Search across all conversations for cross-session memory
    
    # Step 5: Score and rank the retrieved chunks using relevance + recency + importance
    top_chunks = score_and_rank(raw_chunks, top_k=8)  # Keep top 8 for context injection
    memory_text, n_chunks, n_tokens = build_memory_context(top_chunks)
    
    # Step 6: Get recent history (last 6 messages)
    async with db.acquire() as conn:
        all_history = await get_messages(conn, conversation_id)   # Keep only last 6 non-system messages to avoid flooding the prompt
   
    # Step 7: Assemble the full prompt with memory injected
    recent = [m for m in all_history if m["role"] != "system"][-6:]
    recent_fmt = [{"role": m["role"], "content": m["content"]} for m in recent]   
    llm_messages = build_prompt_with_memory(
        system_prompt=SYSTEM_PROMPT, 
        user_message=req.message,
        memory_text=memory_text,
        recent_history=recent_fmt
    )
    
    # Step 8: Call the LLM
    response = llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=llm_messages
    )
    
    reply = response.choices[0].message.content
    tokens = response.usage.total_tokens
        
    # Step 9: Save the assistant's reply to DB
    async with db.acquire() as conn:
        reply_msg_id = await save_message(conn, conversation_id, 'assistant', reply)
        updated = await get_messages(conn, conversation_id)
       
    # Step 10: Chunk and embed the assistant's reply too so it's searchable later. 
    await save_chunks(db, reply_msg_id, conversation_id, reply)
    background.add_task(score_and_store, db, reply_msg_id, reply, 'assistant')  # Score importance in background without blocking response
    
    async with db.acquire() as conn:
        total = await conn.fetchval('SELECT COUNT(*) FROM messages WHERE conversation_id = $1 AND role != $2', conversation_id, 'system')
        compressed = await conn.fetchval('SELECT COUNT(*) FROM messages WHERE conversation_id = $1 AND is_compressed = TRUE', conversation_id)
        tokens_summaries = await conn.fetchval('SELECT COALESCE(SUM(token_count), 0) FROM summaries WHERE conversation_id = $1', conversation_id)
        
    ratio = round(compressed / total, 2) if total > 0 else 0.0
        
    return ChatDebugResponse(
        reply=reply,
        conversation_id=conversation_id,
        tokens_used=tokens,
        message_count=len(updated),
        memories_injected = [
            MemoryChunkDebug(
                content          = c["content"][:200],
                similarity       = round(c["similarity"],                4),
                recency_score    = round(c["recency_score"],             4),
                importance_score = round(c.get("importance_score", 0.5), 4),
                final_score      = round(c["final_score"],               4),
                source_type      = c.get("source_type", "message"),
            )
            for c in top_chunks
        ],
        compression_stats = CompressionStats(
            total_messages      = total,
            compressed_messages = compressed,
            tokens_summaries    = tokens_summaries,
            compression_ratio   = ratio,
        ),
    )
