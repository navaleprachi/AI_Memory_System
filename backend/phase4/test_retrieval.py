import asyncio, asyncpg, os, sys
sys.path.insert(0, "")

from dotenv import load_dotenv
load_dotenv()

from src.retrieval import search_chunks, score_and_rank, build_memory_context

async def test_full_pipeline():
    db = await asyncpg.create_pool(os.getenv('DATABASE_URL'))
    
    queries = [
        "Frontend Engineer and React",
        "Database and backend",
        "Machine learning and AI",
    ]
    
    for q in queries:
        print(f"\n--- Query: {q} ---")
        
        # Step 1: Raw retrieval
        raw = await search_chunks(db, q, top_k=10)
        print(f"Raw retrieved {len(raw)} chunks.")
        
        # Step 2: Scoring and ranking
        ranked = score_and_rank(raw, top_k=5)
        print("Top 5 after scoring:")
        
        for i, c in enumerate(ranked):
            print(f" {i+1}. score={c['final_score']:.4f}"
                f" sim={c['similarity']:.4f}"
                f" rec={c['recency_score']:.4f}"
                f" | {c['content'][:70]}"
            )
            
        # Step 3: Build memory context
        mem_text, n_chunks, n_tokens = build_memory_context(ranked)
        print(f"Memory context built with {n_chunks} chunks, {n_tokens} tokens.")
        print(f"Memory text preview: {mem_text[:200]}")
        
    await db.close()
    print("\nAll retrieval tests passed!")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())