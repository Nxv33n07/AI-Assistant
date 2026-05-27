# FaithCompass AI

A Christianity-focused AI assistant — scripture-grounded, denomination-aware, and safety-first.

Built with Gemini 2.5 Flash, React Three Fiber, and Framer Motion.

## Quick Start

### 1. Backend

```bash
cd backend

# Create virtual environment (Python 3.9+)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set your GEMINI_API_KEY (free at aistudio.google.com)

# Fetch the Bible verse corpus (run once — takes ~2 min)
python scripts/fetch_bible_corpus.py

# Start the API server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

---

## Features

| Feature                      | Implementation                                                                                    |
| ---------------------------- | ------------------------------------------------------------------------------------------------- |
| Scripture-verified responses | Live bible-api.com lookup before every LLM call                                                   |
| Hallucination prevention     | Verses injected into system prompt; model forbidden from citing from memory                       |
| Semantic Bible search        | ChromaDB + sentence-transformers RAG over 112 key KJV passages                                    |
| Denomination-aware           | 7 traditions: Catholic, Orthodox, Reformed, Evangelical, Lutheran, Pentecostal, Nondenominational |
| Two-stage safety             | Fast regex rules + Gemini classifier for nuanced/adversarial prompts                              |
| Christian image generation   | Pollinations.ai (free, no key) with style enhancement and content safety                          |
| Conversation memory          | Per-session rolling history (last 10 turns)                                                       |
| Graceful corrections         | Detects fake/incorrect verses and informs the user                                                |

## Architecture

```
User ──► Next.js 15 (React Three Fiber + Framer Motion)
              │
              ▼
         FastAPI (Python)
              │
    ┌─────────┼─────────────┐
    │         │             │
    ▼         ▼             ▼
Safety    Scripture      Gemini
Guard     Grounding    2.5-flash-lite
(regex    (bible-api +  (response
 + LLM)   ChromaDB RAG) generation)
```

**Hallucination prevention pipeline:**

1. Extract all verse references from user message (regex)
2. Fetch actual verse text from bible-api.com
3. Inject verified text into system prompt
4. Instruct model: "Only cite from [SCRIPTURE CONTEXT] — never from memory"
5. Unverifiable references shown to user as corrections

**Safety pipeline:**

1. Stage 1: Regex rules (0ms) — verse rewrites, racist theology, DAN jailbreaks
2. Stage 2: Gemini classifier — sophisticated/ambiguous attacks, hate speech
3. Blocked responses include a constructive redirect (never just a hard "no")

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full design notes.

## Evaluation

`backend/eval/test_cases.json` — 30 test cases covering:

- Normal Q&A with real scripture
- Fake/non-existent verse detection
- Adversarial prompt injection
- Denomination-specific doctrinal questions
- Image generation safety
- Edge cases (misattributed quotes, "God helps those who help themselves", etc.)

## Tech Stack

| Layer      | Technology                                   |
| ---------- | -------------------------------------------- |
| LLM        | Gemini 2.5 Flash Lite (free tier)            |
| Vector DB  | ChromaDB (local)                             |
| Embeddings | sentence-transformers all-MiniLM-L6-v2       |
| Bible data | bible-api.com (KJV, free, no key)            |
| Image gen  | Pollinations.ai Flux (free, no key)          |
| Backend    | FastAPI + uvicorn                            |
| Frontend   | Next.js 15, React Three Fiber, Framer Motion |
| Styling    | Tailwind CSS v4                              |
