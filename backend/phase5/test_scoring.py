import asyncio, sys
sys.path.insert(0, "")
from dotenv import load_dotenv
load_dotenv()
from src.scoring import score_importance

async def test():
    test_cases = [
        ("My name is Prachi and I am building an AI memory system", "user", "high"),
        ("I work as a frontend engineer at Nooon using React", "user", "high"),
        ("How does cosine similarity work in vector search?", "user", "mid"),
        ("Can you explain the difference between RAG and fine-tuning?","user", "mid"),
        ("Hi!", "user", "low"),
        ("Thank you!", "user", "low"),
        ("Ok", "user", "low"),
        ("lol", "user", "low"),
    ]
    
    print("\nImportance scoring test\n")
    print(" score expected message")
    print(" " + "-" * 55)
    passed = 0
    
    for content, role, expected in test_cases:
        score = await score_importance(content, role)
        ok = (
            (expected == "high" and score >= 0.65)
            or (expected == "mid" and 0.35 <= score < 0.70)
            or (expected == "low" and score < 0.40)
        )
        status = "PASS" if ok else "FAIL"
        passed += 1 if ok else 0
        preview = content[:45] + "..." if len(content) > 45 else content
        print(f"{status} | score={score:.2f} | expected={expected:>8} | {preview}")
    
    print(f"\n{passed}/{len(test_cases)} tests passed.")

if __name__ == "__main__":
    asyncio.run(test())