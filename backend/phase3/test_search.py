import asyncio, asyncpg, os, sys
sys.path.insert(0, '')
from dotenv import load_dotenv
load_dotenv()
from src.embeddings import embed_text

async def semantic_search(query: str, top_k: int = 5):
    # Step 1: embed the query
    print(f'Search for query: "{query}"')
    query_vector = await embed_text(query)
    
    # Step 2: connect to DB and run vector search
    conn = await asyncpg.connect(os.environ['DATABASE_URL'])
    rows = await conn.fetch(''' SELECT content, 1 - (embedding <=> $1::vector) AS similarity FROM chunks WHERE embedding IS NOT NULL ORDER BY embedding <=> $1::vector LIMIT $2 ''', str(query_vector), top_k)
    
    # Step 3: print results
    print(f'\nTop {top_k} results:')
    for i, row in enumerate(rows):
        print(f' {i+1}. (sim: {row["similarity"]:.4f}) {row["content"][:100]}...')
        
    await conn.close()

async def main():
    # Try different queries related to frontend engineering
    await semantic_search('frontend engineering and JavaScript') 
    await semantic_search('database and backend technology') 
    await semantic_search('machine learning and AI')
    
asyncio.run(main())