import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key: raise ValueError('OPENAI_API_KEY not found in .env')
print(f'Key loaded: {openai_api_key[:8]}...{openai_api_key[-4:]} ✓')

openai_model = os.getenv("OPENAI_MODEL")
if not openai_model: raise ValueError('OPENAI_MODEL not found in .env')
print(f'Model loaded: {openai_model} ✓')

client = OpenAI()

response = client.chat.completions.create(
    model=openai_model,
    messages=[
        {
            "role": "user",
            "content": "Say: API connected"
        }
    ],
    max_tokens=10
)

print(response.choices[0].message.content)
print(f" - Total tokens: {response.usage.total_tokens}")
print("Setup complete")