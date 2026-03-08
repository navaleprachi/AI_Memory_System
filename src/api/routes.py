import os
from fastapi import APIRouter, Request, HTTPException
from openai import OpenAI
from src.models import ChatRequest, CreateConversationRequest, ChatResponse, ConversationResponse, MessageResponse
from src.database.queries import save_message, get_messages, create_conversation, get_conversations, save_chunks

router = APIRouter()
llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 1. Create a new conversation
@router.post('/conversations')
async def new_conversation(req: CreateConversationRequest, request: Request):
    db = request.app.state.db
    async with db.acquire() as conn:
        conv_id = await create_conversation(conn, req.title)
    return {"conversation_id": conv_id, 'status': 'created'}

#2. Send message  and get AI(LLM) response
@router.post('/chat/{conversation_id}')
async def chat(conversation_id: str, req: ChatRequest, request: Request):
    db = request.app.state.db
    async with db.acquire() as conn:
        # 1. Get full conversation history from DB
        history = await get_messages(conn, conversation_id)
        
        if not history:
            # 2. First message - add system prompt and reload history
            await save_message(conn, conversation_id, 'system', 'You are a helpful assistant. Remember everything the user tells you.')
            history = await get_messages(conn, conversation_id)
        
        # 3. Save the incoming user message to DB
        user_msg_id = await save_message(conn, conversation_id, 'user', req.message)
        
    # Chunk and embed the user message for better retrieval later.
    await save_chunks(db, user_msg_id, conversation_id, req.message)
        
    # 4. Build messages list to send to the LLM
    llm_messages = [{'role': m['role'], 'content': m['content']} for m in history]
    llm_messages.append({'role': 'user', 'content': req.message})
        
    # 5. Call the LLM
    response = llm.chat.completions.create(
         model="gpt-4o-mini",
        messages=llm_messages
    )
    reply = response.choices[0].message.content
    tokens = response.usage.total_tokens
        
    # 6. Save the assistant's reply to DB
    async with db.acquire() as conn:
        reply_msg_id = await save_message(conn, conversation_id, 'assistant', reply)
        updated = await get_messages(conn, conversation_id)
       
    # Chunk and embed the assistant's reply too so it's searchable later. 
    await save_chunks(db, reply_msg_id, conversation_id, reply)
        
    return ChatResponse(reply=reply, tokens_used=tokens, conversation_id=conversation_id, message_count=len(updated))

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