import tiktoken, sys 
from openai import OpenAI 
from dotenv import load_dotenv 
load_dotenv() 
client = OpenAI() 
enc = tiktoken.encoding_for_model('gpt-4o-mini') 
FAKE_LIMIT = 300 # tweak this to stress-test different levels 

def count_tokens(messages):
	total = 2
	for m in messages:
		total += 4 + len(enc.encode(m['content']))
	return total

def print_window_state(messages, limit):
	print('\n── Window State ───────────────────────')
	running = 2
	for i, m in enumerate(messages):
		t = 4 + len(enc.encode(m['content']))
		running += t
		icon = '✅' if running <= limit else '❌'
		role = m['role'][:3].upper()
		prev = m['content'][:45].replace('\n', ' ')
		print(f' {icon} {i:2}. [{role}] ({t:3}t) {prev}')
	print(f'── {count_tokens(messages)} / {limit} tokens\n')

def truncate_oldest(messages, limit):
	system = [m for m in messages if m['role'] == 'system']
	rest = [m for m in messages if m['role'] != 'system']
	dropped = 0
	while count_tokens(system + rest) > limit and len(rest) > 1:
		lost = rest.pop(0)
		dropped += 1
		print(f' ⚠️ Dropped [{lost["role"]}]: {lost["content"][:50]}...')
	if dropped:
		print()
	return system + rest

def run(use_truncation: bool):
	mode = 'TRUNCATION' if use_truncation else 'NO TRUNCATION'
	messages = [{'role': 'system', 'content': 'You are helpful. Remember everything the user tells you.'} ]
	print(f'\n{mode} MODE | Limit: {FAKE_LIMIT} tokens\n')
	while True:
		try:
			user_input = input('You: ').strip()
		except (KeyboardInterrupt, EOFError):
			break
		if not user_input:
			continue
		messages.append({'role': 'user', 'content': user_input})
		if use_truncation:
			messages = truncate_oldest(messages, FAKE_LIMIT)
		print_window_state(messages, FAKE_LIMIT)
		response = client.chat.completions.create(
			model='gpt-4o-mini',
			messages=messages,
			temperature=0.7
		)
		reply = response.choices[0].message.content
		messages.append({'role': 'assistant', 'content': reply})
		print(f'AI: {reply}\n')

if __name__ == '__main__':
	# python3 context_test.py → no truncation
	# python3 context_test.py truncate → with truncation
	use_trunc = len(sys.argv) > 1 and sys.argv[1] == 'truncate'
	run(use_trunc)