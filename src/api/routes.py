import os
from fastapi import APIRouter, Request, HTTPException
from openai import OpenAI
from src.models import ChatRequest, CreateConversationRequest, ChatResponse, ConversationResponse, MessageResponse
from src.database.queries import save_message, get_messages, create_conversation, get_conversations

router = APIRouter()
llm = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 1. Create a new conversation
@router.post('/conversations')
async def new_conversation(req: CreateConversationRequest, request: Request):
    db = request.app.state.db
    async with db.acquire() as conn:
        conv_id = await create_conversation(conn, req.title)
    return {"conversation_id": conv_id, 'status': 'created'}

#2. Send message to a conversation and get AI response
@router.post('/chat/{conversation_id}')
async def chat(conversation_id: str, req: ChatRequest, request: Request):
    db = request.app.state.db
    async with db.acquire() as conn:
        # 1. Get full conversation history
        history = await get_messages(conn, conversation_id)
        
        if not history:
            # First message - add system prompt
            await save_message(conn, conversation_id, 'system', 'You are a helpful assistant. Remember everything the user tells you.')
            history = await get_messages(conn, conversation_id)
        
        # 2. Save user message
        await save_message(conn, conversation_id, 'user', req.message)
        
        # 3. Build messages list for LLM
        llm_messages = [{'role': m['role'], 'content': m['content']} for m in history]
        llm_messages.append({'role': 'user', 'content': req.message})
        
        # 4. Call LLM
        response = llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=llm_messages
        )
        reply = response.choices[0].message.content
        tokens = response.usage.total_tokens
        
        # 5. Save AI response
        await save_message(conn, conversation_id, 'assistant', reply)
        
        # 6. Get updated message count
        update = await get_messages(conn, conversation_id)
        
        return ChatResponse(reply=reply, tokens_used=tokens, conversation_id=conversation_id, message_count=len(update))

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