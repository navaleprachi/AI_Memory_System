# AI Memory Compression System

A conversational AI system that solves the **long-context / token limit problem** through intelligent memory compression, semantic retrieval, and hierarchical summarization.

Built as a hands-on study project to learn GenAI and LLM engineering — covering embeddings, vector search, RAG, importance scoring, and multi-level memory compression.

---

## Live Demo

- Frontend Demo: https://ai-memory-compression-system.vercel.app
- Backend API: https://aimemorysystem-production.up.railway.app (docs: /docs)

---

## Website Preview

![AI Memory System Web Page](frontend/src/assets/AIMemoryWebPage.png)

---

## What It Does

Standard LLM chatbots forget old messages or overflow the context window. This system instead:

1. **Chunks and embeds** every message into a vector database
2. **Retrieves** the most semantically relevant past memories for each new query
3. **Scores** retrieved chunks by relevance + recency + importance — not just similarity
4. **Compresses** old messages into bullet-point summaries when they accumulate (Level 1)
5. **Re-compresses** those summaries into higher-level summaries as the conversation grows (Level 2)
6. **Injects** only the most relevant compressed context into each prompt, keeping token usage low

The result: the AI remembers things from 100+ messages ago while using a fraction of the tokens.

---

## Architecture and System Design

### Diagram

![Architecture Diagram](frontend/src/assets/Architecture_Diagram.png)

### Runtime Flow

1. User message is saved in `messages` and chunked into `chunks`.
2. Query embedding runs vector search over message and summary chunks.
3. Candidate memories are re-ranked by relevance, recency, and importance.
4. Top memories are injected into prompt + recent turns.
5. LLM reply is saved, chunked, and scored in background.
6. Compression job periodically converts older messages to L1/L2 summaries.

### Scale Notes

- Compute: API is stateless and horizontally scalable behind a load balancer.
- Storage: Postgres remains source of truth; pgvector indexes enable semantic lookup.
- Latency: Use async background tasks for importance scoring and compression.
- Throughput: Keep retrieval token budget fixed to prevent prompt growth over time.
- Reliability: Add retries/timeouts for external LLM calls and log retrieval fallbacks.
- Data lifecycle: Raw messages are preserved, but marked compressed when summarized.

---

## Tech Stack

| Layer          | Technology                                  |
| -------------- | ------------------------------------------- |
| Backend        | Python 3.11 + FastAPI + asyncpg             |
| Frontend       | React 19 + TypeScript + Vite + Tailwind CSS |
| LLM            | OpenAI GPT-4o-mini                          |
| Embeddings     | OpenAI text-embedding-3-small (1536 dims)   |
| Database       | PostgreSQL + pgvector extension             |
| Token counting | tiktoken                                    |

---

## Key Features

### Multi-Factor Memory Retrieval

Retrieved chunks are ranked by a weighted combination of three signals, not just vector similarity:

```
final_score = 0.5 × relevance + 0.3 × recency + 0.2 × importance
```

### Hierarchical Compression

- **Level 1:** Every 20 raw messages → compressed into bullet-point summary
- **Level 2:** Every 5 Level-1 summaries → merged into a single higher-level summary
- Compressed summaries are embedded and remain searchable via vector search
- Original messages are marked `is_compressed = TRUE`; L1 summaries get a `parent_id` when absorbed into L2

### LLM Importance Scoring

Each message is scored 0.0–1.0 by GPT-4o-mini in the background:

- `0.9–1.0` — critical facts (names, goals, decisions)
- `0.7–0.9` — important context (preferences, skills)
- `0.4–0.7` — useful context (questions, explanations)
- `0.1–0.4` — low value (greetings, filler)

### Memory Inspector UI

The right panel shows exactly what the system retrieved and why:

- **Raw chunk** vs **Summary** badges
- Visual score bars for relevance, recency, and importance
- Compressed Memory section showing full bullet-point summaries
- Compression stats (total messages, compressed count, summary count)

---

## Database Schema

![Database Schema](frontend/src/assets/Database_Schema.png)

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL with pgvector extension

### 1. Clone and install backend dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up environment variables

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/memorydb
```

### 3. Initialize the database

```bash
cd backend
python -m src.database.init_db
```

### 4. Start the backend

```bash
cd backend
uvicorn src.main:app --reload
```

### 5. Install and start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## API Endpoints

| Method | Endpoint                        | Description                                |
| ------ | ------------------------------- | ------------------------------------------ |
| `POST` | `/conversations`                | Create a new conversation                  |
| `GET`  | `/conversations`                | List all conversations                     |
| `GET`  | `/conversations/{id}`           | Get full message history                   |
| `GET`  | `/conversations/{id}/summaries` | Get all compressed summaries               |
| `POST` | `/chat/{id}`                    | Send a message, get a reply                |
| `POST` | `/chat-with-debug/{id}`         | Send a message with memory inspection data |

---

## Development Phases

This project was built incrementally across 6 phases:

| Phase | Feature                                           |
| ----- | ------------------------------------------------- |
| 1     | Basic LLM chat with token counting                |
| 2     | Persistent conversations with PostgreSQL          |
| 3     | Sentence-level chunking and embeddings            |
| 4     | Vector search with 3-factor scoring and retrieval |
| 5     | LLM-based importance scoring                      |
| 6     | Hierarchical memory compression and summarization |

---

## What I Learned

- How RAG (Retrieval-Augmented Generation) works end-to-end
- Vector embeddings and similarity search with pgvector
- Designing multi-signal ranking beyond simple cosine similarity
- Async Python patterns for non-blocking LLM and DB operations
- How to use LLMs as classifiers (importance scoring)
- Hierarchical data compression strategies for long conversations

---

Copyright &copy; 2026 Prachi Navale. All rights reserved.
