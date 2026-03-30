<div align="center">

# 🧠 AI Memory Compression System

**Solving the long-context problem for LLMs through intelligent memory compression, semantic retrieval, and hierarchical summarization.**

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Visit_App-6366f1?style=for-the-badge)](https://ai-memory-compression-system.vercel.app)
[![API Docs](https://img.shields.io/badge/📖_API_Docs-Railway-0ea5e9?style=for-the-badge)](https://aimemorysystem-production.up.railway.app/docs)
[![Python](https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL_+_pgvector-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![OpenAI](https://img.shields.io/badge/OpenAI_GPT--4o--mini-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com)

<br/>

![App Preview](frontend/src/assets/AIMemoryWebPage.png)

</div>

---

## 💡 The Problem

Standard LLM chatbots either **forget old messages** or **overflow the context window** as conversations grow longer. There's no memory — every new session starts from scratch.

## ✅ The Solution

A production-grade memory engine that **compresses, stores, and retrieves** conversation history intelligently — so the AI remembers things from 100+ messages ago while using a **fraction of the tokens**.

```
Token reduction:  ████████████████████░░░░░░░░░░   85% fewer tokens
Context accuracy: ████████████████████████████████  preserved via RAG
```

---

## 🏗️ Architecture

![Architecture Diagram](frontend/src/assets/Architecture_Diagram.png)

### How It Works — Runtime Flow

```
User Message
     │
     ▼
┌─────────────────────────────────────────┐
│  1. Save message → chunk → embed        │
│  2. Vector search over chunks + summaries│
│  3. Re-rank by relevance + recency +    │
│     importance (weighted scoring)       │
│  4. Inject top memories into prompt     │
│  5. Get LLM reply → save + score        │
│  6. Background: compress old messages   │
│     into L1 → L2 summaries             │
└─────────────────────────────────────────┘
     │
     ▼
  LLM Reply (with long-term memory)
```

---

## ✨ Key Features

### 🔢 Multi-Factor Memory Scoring

Retrieved chunks are ranked by a **weighted combination of three signals** — not just vector similarity:

```
final_score = 0.5 × relevance + 0.3 × recency + 0.2 × importance
```

| Signal | Weight | Description |
|---|:---:|---|
| Relevance | 50% | Cosine similarity via pgvector |
| Recency | 30% | How recently the message occurred |
| Importance | 20% | LLM-assigned importance score (0.0–1.0) |

### 🗜️ Hierarchical Compression

| Level | Trigger | Action |
|---|---|---|
| **Level 1** | Every 20 raw messages | Compressed into bullet-point summary |
| **Level 2** | Every 5 Level-1 summaries | Merged into a single higher-level summary |

- Compressed summaries remain **fully searchable** via vector search
- Original messages marked `is_compressed = TRUE` — never deleted, always recoverable
- L1 summaries get a `parent_id` when absorbed into L2

### 🤖 LLM Importance Scoring

Each message is scored **0.0–1.0** by GPT-4o-mini in the background:

| Score Range | Classification | Examples |
|---|---|---|
| `0.9 – 1.0` | Critical facts | Names, goals, key decisions |
| `0.7 – 0.9` | Important context | Preferences, skills, constraints |
| `0.4 – 0.7` | Useful context | Questions, explanations |
| `0.1 – 0.4` | Low value | Greetings, filler |

### 🔍 Memory Inspector UI

The right panel gives full transparency into what the system retrieved and why:

- **Raw chunk** vs **Summary** source badges
- Visual score bars for relevance, recency, and importance
- Compressed Memory section with full bullet-point summaries
- Live compression stats: total messages, compressed count, summary count

---

## 🗄️ Database Schema

![Database Schema](frontend/src/assets/Database_Schema.png)

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11 + FastAPI + asyncpg |
| Frontend | React 19 + TypeScript + Vite + Tailwind CSS |
| LLM | OpenAI GPT-4o-mini |
| Embeddings | OpenAI text-embedding-3-small (1536 dims) |
| Vector DB | PostgreSQL + pgvector extension |
| Token counting | tiktoken |
| Deployment | Railway (backend) + Vercel (frontend) |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL with pgvector extension

### 1. Clone the repository

```bash
git clone https://github.com/navaleprachi/AI_Memory_System.git
cd AI_Memory_System
```

### 2. Set up environment variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/memorydb
```

### 3. Install backend dependencies and initialize the database

```bash
pip install -r requirements.txt
cd backend
python -m src.database.init_db
```

### 4. Start the backend

```bash
uvicorn src.main:app --reload
```

### 5. Install and start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) — Backend API docs at [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/conversations` | Create a new conversation |
| `GET` | `/conversations` | List all conversations |
| `GET` | `/conversations/{id}` | Get full message history |
| `GET` | `/conversations/{id}/summaries` | Get all compressed summaries |
| `POST` | `/chat/{id}` | Send a message, get a reply |
| `POST` | `/chat-with-debug/{id}` | Send a message with full memory inspection data |

---

## 📈 Development Phases

This project was built incrementally across 7 phases:

| Phase | Feature | Status |
|---|---|:---:|
| 1 | Basic LLM chat with token counting | ✅ |
| 2 | Persistent conversations with PostgreSQL | ✅ |
| 3 | Sentence-level chunking and embeddings | ✅ |
| 4 | Vector search with 3-factor scoring and retrieval | ✅ |
| 5 | LLM-based importance scoring | ✅ |
| 6 | Hierarchical memory compression and summarization | ✅ |
| 7 | React + Vite frontend with Tailwind CSS | ✅ |

---

## 🧠 What I Learned

- How **RAG (Retrieval-Augmented Generation)** works end-to-end in a production system
- Vector embeddings and semantic similarity search with **pgvector**
- Designing **multi-signal ranking** beyond simple cosine similarity
- Async Python patterns for non-blocking LLM and database operations
- Using **LLMs as classifiers** for importance scoring
- Hierarchical data compression strategies for long conversations
- Building a **React + Vite + Tailwind CSS** frontend that integrates with a FastAPI backend

---

## 👩‍💻 Author

**Prachi Navale** — Frontend Engineer · MS Information Systems, Northeastern University

[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/prachi-navale/)
[![Portfolio](https://img.shields.io/badge/Portfolio-FF5722?style=flat-square&logo=firefox&logoColor=white)](https://prachinavale-portfolio.netlify.app/)
[![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/navaleprachi)

---

<div align="center">
  <i>Built as a hands-on deep-dive into GenAI engineering — embeddings, vector search, RAG, and LLM memory systems.</i>

  <br/><br/>

  Copyright © 2026 Prachi Navale · All rights reserved.
</div>
