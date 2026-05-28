# FaithCompass — Architecture Notes

## Overview

FaithCompass is a Christianity-focused AI assistant built around one core constraint: **never let the model invent Scripture**. Every design decision flows from that.

The assignment asks to evaluate prompt engineering, grounding strategies, multimodal workflows, AI safety thinking, hallucination handling, architecture decisions, edge-case handling, and product thinking. Each section below maps directly to one or more of those criteria.

---

## System Architecture

```
User (Browser)
      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│  Next.js Frontend (port 3000)                               │
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
│  │ Stage 2: LLM     │      └────────────────────┘           │
│  │  classifier      │               │                       │
│  └────────┬─────────┘      ┌────────────────────┐           │
│           │                │  Prompt Enhancer   │           │
│           ▼                │  (style tokens)    │           │
│  ┌──────────────────┐      └────────┬───────────┘           │
│  │ Scripture        │               │                       │
│  │ Grounding Layer  │      ┌────────────────────┐           │
│  │                  │      │  Pollinations.ai   │           │
│  │ 1. Regex extract │      │  Flux model        │           │
│  │    verse refs    │      │  (free, no key)    │           │
│  │ 2. bible-api.com │      └────────────────────┘           │
│  │    live lookup   │                                       │
│  │ 3. BM25 RAG      │                                       │
│  │    semantic hits │                                       │
│  └────────┬─────────┘                                       │
│           │                                                 │
│           ▼                                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Gemma 4 31B Instruct (gemma-4-31b-it)               │   │
│  │                                                      │   │
│  │  System prompt contains:                             │   │
│  │  • Base persona + safety instructions                │   │
│  │  • Denomination context block (7 traditions)         │   │
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

## Technology Stack

| Layer               | Technology                              | Why                                                             |
| ------------------- | --------------------------------------- | --------------------------------------------------------------- |
| LLM                 | Gemma 4 31B Instruct (`gemma-4-31b-it`) | Available on Gemini API free tier; strong theological reasoning |
| Safety classifier   | Gemma 4 31B Instruct (`gemma-4-31b-it`) | Same model reused for classification — minimal latency overhead |
| Scripture grounding | bible-api.com                           | Free, no key required, returns KJV JSON, reliable uptime        |
| Semantic RAG        | BM25 (`rank-bm25`)                      | Pure Python, zero model download, fits within 512 MB free tier  |
| Image generation    | Pollinations.ai (Flux model)            | Completely free, no registration, production-quality output     |
| Backend             | FastAPI + Python 3.11                   | Async-native, typed, fast startup                               |
| Frontend            | Next.js + Tailwind CSS v4               | App router, React 19, clean component model                     |

---

## Key Engineering Decisions

### 1. Hallucination Prevention via Two-Pass Verification

_Addresses: hallucination handling, grounding strategies_

The single biggest risk in a scripture-focused AI is fabricating plausible-sounding but wrong Bible verses. The approach is architectural, not just prompt-level:

**Pass 1 — Reference extraction:**
A regex engine scans the user's message for verse patterns (`John 3:16`, `Ps 23:1`, `1 Cor 13:4-8`, etc.) supporting 66 canonical books + 150+ common abbreviations.

**Pass 2 — Live API verification:**
Every extracted reference is fetched from `bible-api.com` **before** the LLM is called. If a verse doesn't exist (`Genesis 3:99`, `Hebrews 14:3`), a correction is injected into the system prompt. The model is instructed:

> _"ONLY cite verses from the [SCRIPTURE CONTEXT] block. Do not quote any verse from memory."_

This eliminates the most common failure mode at the architecture level. The model cannot cite Genesis 3:99 because it has been told it doesn't exist before it generates a single token.

**Known limitation:** This only verifies verses the _user_ cites. A production system would add a second regex pass on the LLM's _response_ to catch any verse the model generates from memory despite instructions.

---

### 2. Scripture Context in System Prompt, Not User Turn

_Addresses: prompt engineering, grounding strategies_

Verified and RAG-retrieved verses are injected into the **system prompt**, not the user message. This is a subtle but important distinction: the model treats system prompt content as operational ground truth, while user-turn content is treated as input that can be questioned or reframed. Injecting scripture into the user turn makes it easier for conversational pressure to override it.

The assembled system prompt structure is:

```
[BASE_PERSONA] + [DENOMINATION_CONTEXT] + [SCRIPTURE CONTEXT] + [CORRECTIONS]
```

---

### 3. RAG for Semantic Scripture Retrieval

_Addresses: grounding strategies, RAG, hybrid systems_

When users ask thematic questions ("What does the Bible say about anxiety?") without citing specific verses, BM25 (`rank-bm25`) retrieves the top-3 most relevant passages from a curated 112-verse KJV corpus. The results are injected as grounded context alongside any directly-cited verses.

**Why BM25 over a vector DB:** Render's free tier has a 512 MB RAM limit. ChromaDB's bundled ONNX model (`all-MiniLM-L6-v2`) downloads ~79 MB compressed and expands to ~200 MB in memory at startup — an OOM kill on the free tier. BM25 is pure Python, needs no model download, uses <5 MB, and performs well on a domain-specific curated corpus where vocabulary overlap is high (theological terms, book names, topics).

**Why curated corpus rather than full Bible:**
For a demo, a carefully selected 112-verse corpus covering key theological topics gives instant cold starts and predictable retrieval quality. The `scripts/fetch_bible_corpus.py` script exists to build a full 31,102-verse index for production (where memory isn't constrained).

**Fallback:** If BM25 initialisation fails (e.g. missing verses file), a simple keyword-overlap scorer keeps the service functional.

---

### 4. Two-Stage Safety Pipeline

_Addresses: AI safety thinking, edge-case handling_

**Stage 1 — Regex rules (zero latency, no API call):**
Catches obvious attacks with 23 patterns across categories:

- Verse rewriting: `rewrite|modify|corrupt|distort|paraphrase` + scripture keywords
- Ideological injection: Bible + harmful ideologies
- Racist theology: Curse of Ham framing, racial hierarchy
- Extremist violence: holy war, kill non-believers
- Prompt injection: DAN, jailbreak variants, "ignore instructions"
- Disrespectful sacred: sexualise/degrade Jesus, Mary, saints

**Stage 2 — LLM classification (~200ms):**
For messages that pass regex, a minimal classification prompt runs against `gemma-4-31b-it` to catch sophisticated adversarial prompts the regex misses. Returns `{category, confidence, reason}`. Threshold: `confidence > 0.75` triggers a redirect.

**Design principle:** Prefer graceful redirection over hard blocks. Every blocked category has a redirect that offers a constructive alternative. A hard "I can't help with that" is both bad UX and bad theology — the model should point toward something better, not just refuse.

**Image safety:** Separate pattern set for image prompts — detects sexualised sacred content, extremist symbol combinations (cross + Nazi imagery), satanic imagery in Christian framing.

---

### 5. Denomination-Aware System Prompts

_Addresses: prompt engineering, product thinking_

7 Christian traditions are supported, each with a doctrinal context block injected at request time:

| Tradition             | Key doctrinal adjustments in prompt                                                           |
| --------------------- | --------------------------------------------------------------------------------------------- |
| Roman Catholic        | Magisterium authority, deuterocanonical books, 7 sacraments, Mariology                        |
| Reformed/Presbyterian | TULIP, covenant theology, Westminster Standards, sola scriptura                               |
| Evangelical           | Biblical inerrancy, born-again conversion, Great Commission, free will                        |
| Lutheran              | Law/Gospel distinction, Real Presence, Book of Concord                                        |
| Eastern Orthodox      | Holy Tradition, theosis/deification, fuller canon, Church Fathers                             |
| Pentecostal           | Baptism in Spirit, continuation of gifts, divine healing                                      |
| Non-denominational    | Shared essentials (Trinity, Incarnation, Atonement); present all views when traditions differ |

The same question ("Is baptism necessary for salvation?") receives a Catholic answer referencing regenerative baptism, a Lutheran answer referencing means of grace, and a Baptist/Evangelical answer referencing ordinance-only theology — without the model guessing which tradition the user belongs to.

---

### 6. Multimodal Workflow: Christian Image Generation

_Addresses: multimodal workflows, product thinking_

**Flow:**

1. Image safety check (regex patterns, stage 1 only — no LLM call for speed)
2. Prompt enhancement: denomination-aware style tokens appended
   - Orthodox/Catholic: `"Byzantine iconography, gold leaf, Orthodox icon style, sacred art"`
   - General: `"Christian sacred art, oil painting style, soft divine luminous light, reverent"`
3. URL construction for Pollinations.ai Flux model with negative prompt (`violence, gore, nudity`)
4. **Backend pre-fetch:** The backend issues an async GET to the image URL before returning to the client, triggering Pollinations.ai's generation pipeline server-side and caching the result. The browser's `<img>` then loads from cache in ~1s instead of timing out on first render.

**Why Pollinations.ai:** Zero cost, zero registration, production-quality Flux model output. The pre-fetch pattern solves the cold-generation latency problem without any additional infrastructure.

---

### 7. Conversation Memory

_Addresses: product thinking, core requirement_

In-process deque per `session_id` (max 20 messages = 10 turns), converted to Gemma's expected `[{role, parts}]` format on each request. Frontend generates a UUID session ID on mount and sends it with every request.

**Production swap:** Redis with a 24h TTL. The session store interface is already abstracted (`session_store.py`) so this is a one-file change.

---

## Request Flow (Chat)

```
1.  User message arrives at POST /api/chat
2.  Stage 1 safety: regex scan (0ms)
    → Blocked? Return graceful redirect immediately — no LLM call
3.  Stage 2 safety: LLM classification (~200ms)
    → confidence > 0.75 in harmful category? Return redirect
4.  Scripture extraction: regex finds all verse refs in message
5.  Live verification: fetch each ref from bible-api.com
    → 404 / invalid? Add to [CORRECTIONS] block
6.  RAG search: BM25 top-3 hits from curated 112-verse corpus
7.  System prompt assembly:
    [BASE_PERSONA] + [DENOMINATION_CONTEXT] + [SCRIPTURE_CONTEXT] + [CORRECTIONS]
8.  Gemma 4 31B call with assembled system prompt + session history
9.  Response stored in session deque
10. Return: response + scripture_references + corrections + safety_flag + thinking
```

---

## Edge Cases Handled

| Scenario                                                     | Handling                                                                                           |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Non-existent verse (Genesis 3:99)                            | bible-api.com 404 → correction injected → model informs user                                       |
| Misattributed quote ("God helps those who help themselves")  | No verse ref extracted → model uses training knowledge to flag as non-biblical (Benjamin Franklin) |
| Wrong verse text supplied by user                            | Live fetch reveals actual text → correction injected → model gently corrects                       |
| Gospel of Thomas presented as Scripture                      | Model instructed to clarify canonical vs apocryphal status                                         |
| Hebrews "chapter 14" (book only has 13)                      | 404 → flagged as non-existent                                                                      |
| Verse rewrite attack                                         | Stage 1 regex → immediate graceful block                                                           |
| Prompt injection / DAN                                       | Stage 1 regex → immediate redirect                                                                 |
| Racist theology (Curse of Ham framing)                       | Stage 1 regex → blocked with corrective historical context                                         |
| Contradictory theology (faith vs works, Eph 2:8 vs Jas 2:17) | Not blocked — genuine theological debate → complementary explanation                               |
| Imprecatory Psalms                                           | Not blocked — Scripture — but contextualized with NT teaching on forgiveness                       |
| Orthodox deuterocanonical books (Sirach, Wisdom)             | Denomination context flags these as in-scope for Catholic/Orthodox                                 |
| Hallucinated historical claim (Jesus in India)               | Not blocked — but model instructed to flag lack of biblical/historical evidence                    |
| Image: extremist symbols (cross + swastika)                  | Pattern matching → blocked with redirect                                                           |
| Image: disrespectful sacred content                          | Pattern matching → blocked with constructive redirect                                              |
| Science/faith tension (Genesis vs evolution)                 | Not blocked — multiple Christian interpretive traditions presented (YEC, OEC, Theistic Evolution)  |
| Sincere faith doubt                                          | Not blocked — pastoral warmth, honest engagement, no dismissiveness                                |

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

## Assignment Requirements Coverage

| Requirement                                | Implementation                                                                                   |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| Chat interface                             | Next.js frontend with ChatInterface component                                                    |
| Scripture-aware responses                  | Two-pass verification + RAG injection into system prompt                                         |
| Bible verse grounding/citations            | bible-api.com live lookup before every LLM call                                                  |
| Christian image generation flow            | Pollinations.ai Flux + denomination style tokens + backend pre-fetch                             |
| Conversation memory                        | In-memory deque per session (max 10 turns)                                                       |
| Basic moderation/safety layer              | Two-stage pipeline: regex (0ms) + LLM classifier (~200ms)                                        |
| Denomination-aware handling                | Dynamic system prompt blocks for 7 Christian traditions                                          |
| Difficult theological questions gracefully | Graceful redirects + multi-perspective presentation                                              |
| Evaluation dataset                         | 31 test cases: normal, fake_verse, adversarial, denomination, image, edge_case                   |
| Edge-case prompts                          | 5 edge cases: imprecatory psalms, doubt, science/faith, sola scriptura tension, memory           |
| Adversarial prompts                        | 8 adversarial: verse rewrite, DAN, prompt injection, racist theology, extremism                  |
| Hallucination test cases                   | 5 fake_verse cases: non-existent chapter, misattribution, wrong text, apocryphal, plausible fake |

---

## What Would Be Added in Production

1. **Output verse verification** — Second regex pass on the LLM's _response_ to catch any verse the model generates from memory despite instructions, re-verified against bible-api.com
2. **Full Bible RAG** — Switch to ChromaDB + neural embeddings on a paid tier with sufficient RAM; index all 31,102 verses (fetch script at `scripts/fetch_bible_corpus.py`); current BM25 over 112 verses covers key theology but misses obscure passages
3. **Persistent sessions** — Redis with a 24h TTL instead of in-process memory
4. **Bible API caching** — Redis cache for bible-api.com responses to avoid redundant lookups on repeated verses
5. **Rate limiting** — Per-session limits on image generation endpoint
6. **Verse cross-references** — When a verse is cited, suggest thematically related passages
7. **Audio** — TTS for devotional content (Web Speech API)
