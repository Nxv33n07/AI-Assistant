# FaithCompass — Architecture Notes

## Overview

FaithCompass is a Christianity-focused AI assistant built around one core constraint: **never let the model invent Scripture**. Every design decision flows from that.

---

## System Architecture

```
User (Browser)
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Next.js 15 Frontend (port 3000)                            │
│  • DenominationSelector  • ChatInterface  • ImagePanel      │
│  • ScriptureCard UI      • MessageBubble with safety banners│
└────────────────────────┬────────────────────────────────────┘
                         │ REST (fetch)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Backend (port 8000)                                │
│                                                             │
│  POST /api/chat                POST /api/generate-image     │
│       │                               │                     │
│       ▼                               ▼                     │
│  ┌──────────────────┐      ┌────────────────────┐           │
│  │ Safety Guardian  │      │ Safety Guardian    │           │
│  │ Stage 1: regex   │      │ (image patterns)   │           │
│  │ Stage 2: Gemini  │      └────────────────────┘           │
│  │  (LLM classify)  │               │                       │
│  └────────┬─────────┘      ┌────────────────────┐           │
│           │                │  Prompt Enhancer   │           │
│           ▼                │  (style tokens)    │           │
│  ┌──────────────────┐      └────────┬───────────┘           │
│  │ Scripture        │               │                       │
│  │ Grounding Layer  │      ┌────────────────────┐           │
│  │                  │      │  Pollinations.ai   │           │
│  │ 1. Regex extract │      │  (free, no key)    │           │
│  │    verse refs    │      └────────────────────┘           │ 
│  │ 2. bible-api.com │                                       │
│  │    live lookup   │                                       │
│  │ 3. ChromaDB RAG  │                                       │
│  │    semantic hits │                                       │
│  └────────┬─────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Gemini 2.5 Flash Lite (gemini-2.5-flash-lite)       │   │
│  │                                                      │   │
│  │  System prompt contains:                             │   │
│  │  • Base persona + safety instructions                │   │
│  │  • Denomination context block                        │   │
│  │  • [SCRIPTURE CONTEXT] — verified verses only        │   │
│  │  • [CORRECTIONS] — flagged bad references            │   │
│  │                                                      │   │
│  │  Messages: conversation history + user turn          │   │
│  └──────────────────────────────────────────────────────┘   │
│           │                                                 │
│           ▼                                                 │
│  ┌──────────────────┐                                       │
│  │ Session Store    │  (in-memory deque, per session_id)    │
│  │ last 10 turns    │                                       │
│  └──────────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Engineering Decisions

### 1. Hallucination Prevention via Two-Pass Verification

The single biggest risk in a scripture-focused AI is fabricating Bible verses. The approach:

**Pass 1 — Reference extraction:**
A regex engine scans the user's message for verse patterns (`John 3:16`, `Ps 23:1`, `1 Cor 13:4-8`, etc.) supporting 66 canonical books + 150+ common abbreviations.

**Pass 2 — Live API verification:**
Every extracted reference is fetched from `bible-api.com` (free, no key) **before** the LLM is called. If a verse doesn't exist (`Genesis 3:99`, `Hebrews 14:3`), a correction is injected into the system prompt. The model is instructed:

> _"ONLY cite verses from the [SCRIPTURE CONTEXT] block. Do not quote any verse from memory."_

This eliminates the most common failure mode — plausible-sounding but wrong verse text — at the architecture level, not just the prompt level.

### 2. RAG for Semantic Scripture Retrieval

When users ask thematic questions ("What does the Bible say about forgiveness?") without citing specific verses, a ChromaDB collection of 112 curated KJV passages is queried using `sentence-transformers/all-MiniLM-L6-v2` embeddings. The top-3 semantic hits are injected as grounded context alongside any directly-cited verses.

Fallback: If ChromaDB is unavailable, a keyword-overlap scorer provides degraded-but-functional retrieval.

### 3. Two-Stage Safety Pipeline

**Stage 1 — Regex rules (zero latency, no API call):**
Catches obvious attacks: verse rewriting, prompt injection, hateful content, extremist violence, DAN jailbreak variants, racist theology (Curse of Ham misuse).

**Stage 2 — LLM classification (Gemini 2.5 Flash Lite, ~200ms):**
For messages that pass regex, a minimal classification prompt runs to catch sophisticated adversarial prompts the regex misses. Threshold: `confidence > 0.75` triggers a redirect.

**Design principle:** Prefer graceful redirection over hard blocks. Every blocked category has a redirect that offers a constructive alternative rather than a dead-end refusal. This is better UX and better theology.

### 4. Denomination-Aware System Prompts

The system prompt is assembled dynamically at request time:

- Base persona + safety instructions
- A denomination context block (Catholic / Reformed / Lutheran / Orthodox / Pentecostal / Evangelical / Non-denominational)

Each denomination block adjusts: canonical scope (deuterocanonical books for Catholic/Orthodox), doctrinal emphasis (TULIP for Reformed, theosis for Orthodox), and authority framework (Magisterium for Catholic, Sola Scriptura for Protestants).

The same question ("Is baptism necessary for salvation?") receives substantively different, tradition-appropriate answers.

### 5. Scripture Context as System Prompt, Not User Turn

A subtle but important decision: grounded verses are injected into the **system prompt**, not the user message. This means the model treats them as operational ground truth rather than contextual information that could be "overridden" by conversational pressure.

### 6. Image Generation via Pollinations.ai

Free, no API key, production-quality via Flux model. A prompt enhancer adds denomination-appropriate style tokens:

- General: oil painting, soft divine light, reverent atmosphere
- Orthodox/Catholic: Byzantine iconography, gold leaf, icon painting style

The backend **pre-fetches** the image URL (triggering Pollinations.ai's generation pipeline) before returning to the client, so the browser's `<img>` loads from cache in ~1s instead of timing out after 30–60s.

Image safety uses pattern matching for: sexualized sacred content, extremist symbols, desecration imagery.

### 7. Conversation Memory

In-process deque per `session_id` (max 20 messages = 10 turns). Fast, zero dependencies. Production swap: Redis with a 24h TTL.

---

## Technology Stack

| Layer               | Technology                       | Why                                                          |
| ------------------- | -------------------------------- | ------------------------------------------------------------ |
| LLM                 | Gemini 2.5 Flash Lite            | Free tier, fast, handles theological nuance well             |
| Safety classifier   | Gemini 2.5 Flash Lite            | Same model, minimal latency for short classification prompts |
| Scripture grounding | bible-api.com                    | Free, no key, returns KJV JSON, 100% uptime                  |
| Semantic RAG        | ChromaDB + sentence-transformers | Local, free, persistent index, no API dependency             |
| Image generation    | Pollinations.ai (Flux)           | Completely free, no registration, production-quality         |
| Backend             | FastAPI + Python 3.9             | Async, typed, fast                                           |
| Frontend            | Next.js 15 + Tailwind CSS v4     | App router, React 19, full SSR                               |

---

## Request Flow (Chat)

```
1. User message arrives at POST /api/chat
2. Stage 1 safety: regex scan (0ms)
   → Blocked? Return redirect immediately
3. Stage 2 safety: Gemini classification (if stage 1 passed)
   → confidence > 0.75 in harmful category? Return redirect
4. Scripture extraction: regex finds all verse refs in message
5. Live verification: fetch each ref from bible-api.com
   → 404 / invalid? Add to [CORRECTIONS] block
6. RAG search: ChromaDB top-3 semantic hits for message
7. System prompt assembly:
   [BASE_PERSONA] + [DENOMINATION_CONTEXT] + [SCRIPTURE_CONTEXT] + [CORRECTIONS]
8. Gemini call with assembled system prompt + session history
9. Response stored in session deque
10. Return: response + scripture_references + corrections + safety_flag
```

---

## Edge Cases Handled

| Scenario                                                    | Handling                                                                                             |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Non-existent verse (Genesis 3:99)                           | bible-api.com 404 → correction injected → model informs user                                         |
| Misattributed quote ("God helps those who help themselves") | No verse ref extracted → no verification → model relies on training knowledge to flag misattribution |
| Wrong verse text supplied by user                           | Live fetch reveals actual text → correction injected → model gently corrects                         |
| Gospel of Thomas presented as Scripture                     | Model instructed to clarify canonical vs apocryphal status                                           |
| Hebrews "chapter 14" (book only has 13)                     | 404 → flagged as non-existent                                                                        |
| Verse rewrite attack                                        | Stage 1 regex → immediate graceful block                                                             |
| Prompt injection / DAN                                      | Stage 1 regex → immediate redirect                                                                   |
| Racist theology (Curse of Ham)                              | Stage 1 regex → blocked with corrective historical context                                           |
| Contradictory theology (faith vs works)                     | Not blocked — genuine theological debate → complementary explanation                                 |
| Imprecatory Psalms                                          | Not blocked — Scripture — but contextualized with NT teaching                                        |
| Orthodox deuterocanonical books                             | Denomination context flags these as in-scope for Catholic/Orthodox                                   |
| Image: extremist symbols                                    | Pattern matching → blocked with redirect to appropriate Christian imagery                            |

---

## Evaluation Dataset

`backend/eval/test_cases.json` — 31 test cases across 7 categories.

Run with:

```bash
cd backend
source venv/bin/activate
python -m eval.evaluate
```

| Category     | Count | What it tests                                                                               |
| ------------ | ----- | ------------------------------------------------------------------------------------------- |
| normal       | 4     | Standard theological Q&A, semantic search, devotional generation, problem of evil           |
| fake_verse   | 5     | Non-existent refs, famous misattributions, wrong text, non-canonical texts                  |
| adversarial  | 8     | Verse rewrites, ideological injection, prompt injection, racist theology, DAN, extremism    |
| denomination | 5     | Catholic purgatory, Orthodox theosis, Reformed TULIP, cross-tradition baptism question      |
| image        | 4     | Normal generation, Byzantine icon, disrespectful blocked, extremist symbol blocked          |
| edge_case    | 5     | Imprecatory Psalms, sincere doubt, sola scriptura tension, multi-turn memory, science/faith |

---

## What Would Be Added in Production

1. **Persistent sessions** — Redis with session TTL instead of in-process memory
2. **Full Bible RAG** — Index all 31,102 verses (fetch script at `scripts/fetch_bible_corpus.py`)
3. **Output verse verification** — Second regex pass on the LLM's _response_ to catch any verses generated from memory despite instructions
4. **Verse cross-reference** — When a verse is cited, suggest related passages
5. **Audio** — TTS for devotional content (Web Speech API)
6. **Caching** — Redis cache for bible-api.com responses to avoid redundant lookups
7. **Rate limiting** — Per-session limits on the image generation endpoint
