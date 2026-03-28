import os
import tiktoken
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

enc = tiktoken.encoding_for_model('gpt-4o-mini')
def count_tokens_before_call(messages):
    tokens = 0
    for message in messages:
        tokens += 4 +len(enc.encode(message['content']))
    return tokens

messages = [
    {
        "role": "system",
        "content": "Explain everything like the user is 10 years old."
    },
    {
        "role": "user",
        "content": "What is an LLM?"
    }
]

response = client.chat.completions.create(
    model='gpt-4o-mini',
    messages=[
        messages[0],
        messages[1]
    ],
    temperature=0.5,
    max_tokens=10,
)
pre_count = count_tokens_before_call(messages)
print(f"Tokens in prompt before API call: {pre_count}")
print(f"API actual: {response.usage.prompt_tokens} tokens")

print('\n **** RESPONSE CONTENT ****')
print(response.choices[0].message.content)

print('\n **** RESPONSE METADATA ****')
print(f" - Model: {response.model}")
print(f" - ID: {response.id}")
print(f" - Finish Reason: {response.choices[0].finish_reason}")
print(f" - Role: {response.choices[0].message.role}")

print('\n **** TOKEN USAGE ****')
print(f" - Prompt Tokens: {response.usage.prompt_tokens}")
print(f" - Completion Tokens: {response.usage.completion_tokens}")
print(f" - Total Tokens: {response.usage.total_tokens}")

print('\n **** FULL RAW OBJECT ****')
print(response.model_dump_json(indent=2))