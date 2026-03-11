import os
from fastapi import APIRouter, Request, HTTPException
from openai import OpenAI
from src.models import ChatRequest, CreateConversationRequest, ChatResponse, ConversationResponse, MessageResponse
from src.database.queries import save_message, get_messages, create_conversation, get_conversations, save_chunks
from src.retrieval import search_chunks, score_and_rank, build_memory_context
from src.retrieval.injector import build_prompt_with_memory

router = APIRouter()
llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

SYSTEM_PROMPT = "You are a helpful assistant. Remember everything the user tells you."

# 1. Create a new conversation
@router.post('/conversations')
async def new_conversation(req: CreateConversationRequest, request: Request):
    db = request.app.state.db
    async with db.acquire() as conn:
        conv_id = await create_conversation(conn, req.title)
    return {"conversation_id": conv_id, 'status': 'created'}

#2. Send message + retrieve relevant memory context and get AI(LLM) response
@router.post('/chat/{conversation_id}')
async def chat(conversation_id: str, req: ChatRequest, request: Request):
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
    all_history = await get_messages(db, conversation_id)   
    # Keep only last 6 non-system messages to avoid flooding the prompt
    recent = [m for m in all_history if m["role"] != "system"][-6:]
    recent_fmt = [{"role": m["role"], "content": m["content"]} for m in recent]   
    
    # Step 7: Assemble the full prompt with memory injected
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