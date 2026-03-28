import os
from dotenv import load_dotenv
from openai import OpenAI
import tiktoken

load_dotenv()

client = OpenAI()

enc = tiktoken.encoding_for_model('gpt-4o-mini')
MODEL_LIMIT = 128_000

# ---- Token Utility Functions ----
def count_tokens(messages: list) -> int:
    total = 0
    for msg in messages:
        total += 4  # Base tokens for message structure
        total += len(enc.encode(msg['content']))
        total += 2  # Tokens for end of message
    return total

def print_token_bar(used: int, limit: int) -> None:
    pct = used / limit
    bar_length = 30
    filled_length = int(bar_length * pct)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    color = '\033[92m' 
    if pct > 0.5: color = '\033[93m' 
    if pct > 0.8: color = '\033[91m'
    reset = '\033[0m'
    print(f'{color}[{bar}] {used:,} / {limit:,} tokens ({pct:.1%}){reset}')

# --- Command Handling ---
def handle_command(command: str, messages: list):
    if command == "/q":
        print("Good Bye.")
        exit(0)
    elif command == "/reset":
        system = messages[0]
        messages = [system]
        print("\nMemory Cleared. Fresh Start.")
        return True, messages
    elif command == "/history":
        print("\n Conversation history:")
        for i, msg in enumerate(messages):
            role = msg['role'].capitalize()
            preview = msg['content'][:100].replace('\n', ' ')
            print(f" {i}: [{role} ] {preview}...")
            print(f' Total: {count_tokens([msg]):,} tokens \n')
            return True, messages
    elif command == "/token":
        print("\nToken breakdown:")
        for msg in messages:
            t = 4 + len(enc.encode(msg['content'])) + 2
            print(f' [{msg["role"]:9}] {t:4} tokens | {msg["content"][:50]}')
        print(f' TOTAL: {count_tokens(messages):,} tokens\n')
        return True, messages
    else:
        print("Unknown command.")
        return False, messages


# --- Main Chat loop ---
def chat_with_gpt():
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant. Remember everything the user tells you."
        }
    ]

    print("\n AI Memory Chatbot ready.. \n")
    print(" Commands: Type /q to exit /reset /history /token\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("Good Bye.")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            skip, messages = handle_command(user_input, messages)
            if skip:
                continue

        messages.append({
            "role": "user",
            "content": user_input
        })

        try:
            response = client.chat.completions.create(
                model='gpt-4o-mini',
                messages=messages,
                temperature=0.7,
            )
        except Exception as e:
            print(f"API error occurred: {e}")
            messages.pop()  # Remove last user message on error
            continue

        reply = response.choices[0].message.content
        messages.append({
            "role": "assistant",
            "content": reply
        })

        print(f"AI: {reply}")
        print_token_bar(count_tokens(messages), MODEL_LIMIT)

if __name__ == "__main__":
    chat_with_gpt()