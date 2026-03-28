import httpx, asyncio
BASE = "http://localhost:8000"

async def main():
    async with httpx.AsyncClient() as client:
        print("Testing Persistent Chatbot API...")
        print('Commands: /quit to exit, /new to start a new conversation, /history to view conversation history')
        
        # 1. Create a new or resume conversation 
        r = await client.get(f"{BASE}/conversations")
        convs = r.json()['conversations']
        if convs:
            conv_id = convs[0]['id']
            print(f"Resuming conversation: {convs[0]['title'] or conv_id[:8]}... \n")
        else:
            r = await client.post(f"{BASE}/conversations", json={"title": "Session 1"})
            conv_id = r.json()['conversation_id']
            print(f"New Conversation Started: \n")
       
        while True:
            try:
                user_input = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                break
            
            if not user_input:
                continue
            
            if user_input == "/quit":
                print("Good Bye...")
                break
            
            if user_input == "/history":
                r = await client.get(f"{BASE}/conversations/{conv_id}")
                messages = r.json()['messages']
                print(f"\nHistory: ({len(messages)} messages)")
                for m in messages:
                    print(f' [{m["role"]}] {m["content"][:70]}')
                print("\n")
                continue
            
            if user_input == "/new":
                r = await client.post(f"{BASE}/conversations", json={"title": f"New Session {len(convs)+1}"})
                conv_id = r.json()['conversation_id']
                print(f"\nNew Conversation Started: \n")
                continue
            
            r = await client.post(f"{BASE}/chat/{conv_id}", json={"message": user_input}, timeout=30.0)
            data = r.json()
            print(f"AI: {data['reply']}\n")
            print(f' [{data["tokens_used"]} tokens | {data["message_count"]} messages saved]\n')
        
if __name__ == "__main__":
    asyncio.run(main())