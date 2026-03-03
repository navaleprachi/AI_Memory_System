import tiktoken 

enc = tiktoken.encoding_for_model('gpt-4o-mini') 

def visualize_tokens(text, label=''):
    tokens = enc.encode(text)
    decoded = [enc.decode([t]) for t in tokens]
    colors = ['\033[41m','\033[42m','\033[43m','\033[44m','\033[45m']
    reset = '\033[0m'
    bold = '\033[1m'
    title = label or repr(text[:40])
    print(f'\n{bold}── {title}{reset}')
    print(f' Tokens: {len(tokens):,} | Chars: {len(text):,} | Ratio: {len(text)/len(tokens):.1f} chars/token')
    print(' ', end='')
    for i, tok in enumerate(decoded):
        color = colors[i % len(colors)]
        display = tok.replace('\n','↵').replace(' ','·')
        print(f'{color}{display}{reset}', end='')
    print('\n')
    return len(tokens)

if __name__ == '__main__':
    # 1. Plain English
    visualize_tokens(
        'Hello, my name is Prachi and I work as a frontend engineer.', 'Plain English sentence'
    )
    
    # 2. Compound words
    visualize_tokens('unhappiness misunderstanding uncomfortable', 'Compound words')
    
    # 3. TypeScript code
    visualize_tokens(
        'const fetchUser = async (id: string): Promise<User> => {\n return await api.get(id);\n};', 'TypeScript function'
    )
    
    # 4. JSON blob
    visualize_tokens(
        '{"role": "user", "content": "hello", "timestamp": "2024-01-01"}', 'JSON object'
    )
    
    # 5. Numbers and dates
    visualize_tokens('2024-03-15 $1,234.56 +1 (555) 123-4567', 'Numbers & formats')
    
    # 6. Emojis
    visualize_tokens('Hello! Tokens are fascinating!', 'Emojis vs plain')
    
    # 7. Summary bullets (like your compression will produce)
    visualize_tokens(
        '- User: frontend engineer\n- Stack: React, TypeScript\n- Goal: GenAI/LLMs\n- Project: AI memory system',
        'Bullet-point summary'
    )

    same_prose = ('The user is a frontend engineer with 3 years of experience ' 'who works with React and TypeScript. They are currently ' 'building an AI memory compression system as a learning project.')
    same_bullets = ('- Role: frontend engineer, 3yr exp\n' '- Stack: React, TypeScript\n' '- Project: AI memory compression system')
    same_json = '{"role":"frontend_engineer","years":3,"stack":["React","TypeScript"],"project":"AI memory system"}'
    visualize_tokens(same_prose, 'Same info — prose')
    visualize_tokens(same_bullets, 'Same info — bullets')
    visualize_tokens(same_json, 'Same info — JSON')