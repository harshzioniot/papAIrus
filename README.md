# papAIrus

> A voice-first AI journal that turns what you say into a queryable map of your life — and lets you talk to it.

papAIrus is a personal journaling system that combines speech-to-text, transformer-based NLP, a typed knowledge graph, semantic retrieval, and persona-driven LLM chat. You record (or type) journal entries; the system extracts the people, emotions, themes, events, habits, places, decisions, and outcomes you mention; it links them into a graph; and it lets you have grounded conversations with an AI that draws on your own history.

---

## Table of Contents

1. [The Why](#the-why)
2. [Feature Tour](#feature-tour)
3. [System Architecture](#system-architecture)
4. [End-to-End Data Flow](#end-to-end-data-flow)
5. [Data Model](#data-model)
6. [Backend Services — Deep Dive](#backend-services--deep-dive)
7. [Tag Canonicalization](#tag-canonicalization)
8. [API Routes](#api-routes)
9. [Frontend](#frontend)
10. [Tech Stack](#tech-stack)
11. [Configuration](#configuration)
12. [Getting Started](#getting-started)
13. [Production Touches](#production-touches)
14. [Project Structure](#project-structure)
15. [Roadmap](#roadmap)

---

## The Why

Most journaling apps are write-only: you dump words in, and they sit there as a chronological list. The longer you journal, the harder it gets to actually *use* what you wrote.

papAIrus inverts that. The more you write, the more your past becomes:

- **Visual** — a knowledge graph of the people, feelings, themes, and events you keep returning to.
- **Queryable** — semantic search over your entries, not just keyword matching.
- **Conversational** — an AI companion that answers from your own history, not from generic training data.

Patterns that take months of self-reflection to spot ("every time I see X, I feel Y the next day") surface naturally once the graph fills in.

---

## Feature Tour

### Record
The entry point of the app. You can either hit record and just talk — like leaving yourself a voice memo — or type the entry directly if you can't speak out loud. The moment you save, the system takes over: it transcribes the audio, pulls out who and what you talked about, figures out how you felt, and weaves it all into your knowledge graph. You don't do any tagging by hand.

### History
Your full timeline. Every entry, in chronological order, with its original audio playable inline and its transcript readable. At the bottom of each entry is a row of color-coded chips — these are the nodes the system extracted: people in blue, emotions in orange, themes in teal, events in purple, and so on. At a glance you can see what a given day was about.

### Graph
The heart of papAIrus. Every node is something you've talked about; every edge is a relationship the system inferred from your entries. Click a node to see all the entries that mention it and everything it's connected to. As your history grows, clusters form and patterns emerge that you'd never spot by scrolling text — recurring themes, emotions tied to specific people, habits that keep producing the same outcomes.

### Digest
A periodic recap. Instead of you having to mine the graph, the digest tells you what *it* noticed — recurring themes, emotional patterns, decisions that led to outcomes. It's the system reflecting your data back at you in plain language.

### Chat
What sets papAIrus apart from any other journal app. You can actually talk to your journal. Ask "why have I been off this week?" and instead of a generic AI answer, the system retrieves the most relevant past entries via semantic search, pulls related nodes from your graph, and replies in a chosen persona — Stoic, Socratic, or Analyst. Every answer is grounded in things you actually wrote, so it cannot make stuff up about your life.

---

## System Architecture

```
┌────────────────────────────┐         ┌──────────────────────────────────┐
│  Next.js 16 (App Router)   │  HTTP   │  FastAPI (async)                 │
│  TypeScript + Tailwind v4  │ ◄─────► │  + lifespan model preload        │
│                            │         │                                  │
│  /record  /history  /graph │         │  Routers                         │
│  /digest  /chat            │         │  ├── entries                     │
│                            │         │  ├── nodes                       │
│  components/               │         │  ├── graph                       │
│  ├── Sidebar               │         │  ├── digest                      │
│  ├── NodeChip              │         │  └── chat                        │
│  └── ThemeProvider         │         │           │                      │
│                            │         │           ▼                      │
│  lib/api.ts (typed client) │         │  Services Layer                  │
└────────────────────────────┘         │  ├── stt_service     (Whisper)  │
                                       │  ├── nlp_service     (BERT)     │
                                       │  ├── analysis_service(LLM tag)  │
                                       │  ├── embedding_service (MiniLM) │
                                       │  ├── edge_service    (rules)    │
                                       │  ├── graph_service   (NetworkX) │
                                       │  └── chat_service    (RAG+LLM)  │
                                       │           │                      │
                                       │           ▼                      │
                                       │  Beanie ODM (async)              │
                                       └───────────│──────────────────────┘
                                                   ▼
                                         ┌──────────────────────┐
                                         │  MongoDB             │
                                         │  ├── entries         │
                                         │  ├── nodes           │
                                         │  └── edges           │
                                         └──────────────────────┘
```

The system is intentionally split into **layers**, each replaceable in isolation:

- **STT** — cloud or local Whisper, switchable by env.
- **NLP** — local transformers for cheap, deterministic extraction.
- **LLM** — Gemini or OpenAI, used only where reasoning is required.
- **Graph** — rule-based edge inference, NetworkX for analytics.
- **Storage** — schemaless documents in MongoDB, async via Motor + Beanie.

---

## End-to-End Data Flow

What happens when you save an entry:

```
1. Audio uploaded            POST /entries (multipart) → backend/uploads/<uuid>.webm
2. STT transcription          stt_service.transcribe_audio() → transcript string
                              backend = "api" (whisper-1) or "local" (Whisper)

3. Layer 1 NLP (local, fast)  nlp_service.run(transcript)
                              ├── strip filler words ("um", "like", "you know")
                              ├── dslim/bert-base-NER → people (score > 0.80)
                              └── j-hartmann/emotion-english-distilroberta-base
                                   → dominant emotion + score

4. Layer 2 LLM tagging        analysis_service.suggest_tags(transcript, layer1_hints)
                              ├── prompt includes BERT people + emotion as grounding
                              ├── strict naming rules (lowercase, no underscores,
                              │   first names only, reuse common forms)
                              └── returns 8-type tag list (person, emotion, theme,
                                  event, habit, place, decision, outcome)

5. Node upsert + canonicalize  routers/entries._normalize_name() per tag
                               → existing Node found or new one created

6. Rule-based edge inference   edge_service infers typed edges from co-occurring
                               node types in the same entry
                               (event+emotion → caused_feeling, etc.)

7. Embedding                   embedding_service.embed(transcript)
                               → 384-d normalized vector

8. Persist                     Entry saved with transcript, audio_path, node_ids,
                               embedding. Nodes/edges saved to their collections.
```

**Total work**: a 30-second voice memo becomes a fully tagged, embedded, graph-linked entry in a couple of seconds.

---

## Data Model

Three Beanie `Document` collections, defined in [backend/models.py](backend/models.py):

### Entry
| Field | Type | Notes |
|---|---|---|
| `transcript` | `str` | Output of STT (or typed text) |
| `audio_path` | `Optional[str]` | Path under `/uploads`, served as static |
| `created_at` | `datetime` | UTC, default `now` |
| `node_ids` | `list[str]` | IDs of all nodes extracted from this entry |
| `embedding` | `Optional[list[float]]` | 384-d sentence-transformers vector |

### Node
| Field | Type | Notes |
|---|---|---|
| `name` | `Indexed(str)` | Canonicalized display name |
| `type` | `str` | One of 8 node types |
| `color_hex` | `str` | Color associated with the type |

**Eight node types** (with colors):

| Type | Color | Examples |
|---|---|---|
| `person` | `#7eb8f7` blue | Sarah, Mom, Alex |
| `emotion` | `#f7a07e` orange | anxiety, quiet relief |
| `theme` | `#9fd8c4` teal | work-life balance |
| `event` | `#c4a0f7` purple | demo day, sunday call |
| `habit` | `#f7d07e` yellow | late-night scrolling |
| `place` | `#7ef7a0` green | gym, office |
| `decision` | `#f77eb8` pink | quit coffee |
| `outcome` | `#a0c4f7` light blue | better sleep |

### Edge
| Field | Type | Notes |
|---|---|---|
| `from_node_id` / `to_node_id` | `str` | |
| `from_type` / `to_type` | `str` | |
| `edge_type` | `str` | One of 7 typed relations |
| `entry_id` | `str` | Source entry — every edge is **traceable** |
| `timestamp` | `datetime` | For temporal queries |
| `is_causal` | `bool` | Reserved for future LLM causality scoring |

**Seven edge types**, derived from a fixed rule matrix in [backend/services/edge_service.py](backend/services/edge_service.py):

| From → To | Edge Type |
|---|---|
| event → person | `involves` |
| event → emotion | `caused_feeling` |
| event → place | `happened_during` |
| emotion → theme | `connected_to` |
| theme → person / place / habit | `recurs_with` |
| decision → outcome | `led_to` |
| habit → emotion / theme | `correlated_with` |

Every edge stores its `entry_id`, making the graph fully **auditable** — any relationship can be traced back to the entry that produced it.

---

## Backend Services — Deep Dive

All services live in [backend/services/](backend/services/) and are imported as a package via `services/__init__.py`.

### `stt_service.py` — Speech-to-Text

A class with two pluggable backends, switched at runtime by `WHISPER_BACKEND`:

- **API backend** (`api`, default): OpenAI's `whisper-1` cloud model via `AsyncOpenAI`.
- **Local backend** (`local`): the open-source `whisper` Python package, running on CPU or CUDA. Model size is configurable (`WHISPER_MODEL_SIZE=base|small|medium|large`).

Supports both plain transcription and **word-level timestamps** (verbose JSON, `timestamp_granularities=["word"]`). Uses `aiofiles` for async file IO and `loop.run_in_executor` for the local model so the event loop is never blocked.

### `nlp_service.py` — Layer 1 NLP (local, fast)

Loaded once at FastAPI startup via `load_models()`. Two HuggingFace pipelines:

- **NER**: `dslim/bert-base-NER`, aggregated by entity, filtered to `PER` (people) with score > 0.80.
- **Emotion**: `j-hartmann/emotion-english-distilroberta-base`, top-1 dominant label.

Before NER, a regex strips speech fillers (`um`, `uh`, `hmm`, `like`, `you know`, `i mean`, `basically`, `literally`) — a small but meaningful improvement on STT-derived text. Output is truncated to 2000 chars (~400 words) to stay within BERT's safe input window.

The output is a small dict (`people`, `emotion_hint`, `emotion_score`) used to ground the Layer 2 LLM call.

### `analysis_service.py` — Layer 2 LLM Tagging

Calls Gemini (default) or OpenAI to extract the **full 8-type tag set**. The prompt is engineered for **node merging**:

- BERT-detected people are passed in as required exact-spelling tags.
- Strict naming rules: lowercase, no underscores, first-name only for people, no parentheticals, no leading articles.
- Reuse common forms ("anxiety" not "feeling anxious", "office" not "the office").

Why this matters: tag names are the merge keys. Without enforced canonicalization, "Sarah", "sarah", "my colleague sarah", and "Sarah (colleague)" would create four separate nodes, fragmenting the graph and destroying signal. Strict prompting + post-processing (`_normalize_name`) guarantees one node per real-world entity.

### `embedding_service.py` — Sentence Embeddings

Uses `sentence-transformers/all-MiniLM-L6-v2`:

- **384-dim** vectors, ~80MB model, ~50ms per text on CPU.
- **Pre-normalized** (`normalize_embeddings=True`) → cosine similarity reduces to a single dot product, which is faster.
- Includes a `cosine_rank()` helper for top-k retrieval with a similarity threshold.

Embeddings are stored on `Entry.embedding` and used by chat retrieval (and any future RAG path).

### `edge_service.py` — Knowledge Graph Edges (rule-based by design)

A fixed rule matrix maps co-occurring node types in the same entry to typed edges. The file even documents *why* it's rule-based:

> "The graph's signal comes from accumulated co-occurrence across hundreds of entries, not from precision on any single one. If someone mentions a bad meeting AND anxiety in the same entry, that edge IS meaningful data even without LLM confirmation. Centrality and trend algorithms handle the rest."

LLM-based causality scoring is left as a deliberate future hook — it can be layered on top without rewriting anything.

### `graph_service.py` — Graph Analytics

Loads nodes + edges from MongoDB (with optional time filter on edges), builds a weighted **NetworkX `DiGraph`**:

- Repeated edges between the same pair **accumulate weight**.
- Each edge stores its set of `edge_types` and a causal flag.

This is where centrality, clustering, and traversal algorithms run for the graph view and digest analytics.

### `chat_service.py` — Persona-Driven RAG Chat

The full chat flow:

```
user message
  → keyword match against node names (exact + substring)
  → 1-hop subgraph (edges touching matched nodes) → neighbour nodes
  → 2-3 entry snippets linked to matched nodes
  → build LLM context (subgraph + snippets + persona system prompt)
  → call LLM via LLM_PROVIDER (gemini | openai)
  → return reply + context nodes
```

Three personas, all defined in `chat_service.py`:

- **Stoic** — A private philosopher companion. Reflects without judging. Minimal verbal output. Names patterns once, quietly, then lets them sit.
- **Socratic** — Asks exactly **one question per response**. Never gives advice. Deepens the question.
- **Analyst** — Surfaces what the graph has found. Speaks in observations, not prescriptions ("I've noticed..." not "You should..."). Honest when the graph is sparse.

The chat service also distinguishes meaningful messages from generic greetings (`hi`, `yo`, `sup`) and detects temporal cues (`this week`, `lately`, `mood`, `stress`) to widen the retrieval window when needed.

---

## Tag Canonicalization

The `_normalize_name()` function in [backend/routers/entries.py](backend/routers/entries.py) is the second line of defense after the LLM prompt. It runs on every tag before node upsert:

1. Trim whitespace, replace underscores with spaces, collapse internal spaces.
2. Strip parentheticals: `"Sarah (colleague)"` → `"Sarah"`.
3. Strip leading articles: `the`, `a`, `an`, `my`, `our`.
4. For `person` type: take **first name only**, title-case it.
5. For all other types: lowercase.

Result: `"my_colleague_sarah"`, `"Sarah (colleague)"`, `"Sarah"`, and `"sarah"` all collapse to a single canonical node `Sarah`. This is what makes the graph actually connect across hundreds of entries.

---

## API Routes

Mounted in [backend/main.py](backend/main.py):

| Router | Purpose |
|---|---|
| `entries` | Create/list/delete entries. Handles audio upload, runs full extraction pipeline, hydrates entries with their node objects. |
| `nodes` | List/lookup nodes; filter by type. |
| `graph` | Returns nodes + edges for graph rendering; supports time-windowed queries. |
| `digest` | Periodic recap — recurring themes, emotional patterns, decisions → outcomes. |
| `chat` | Persona-driven LLM chat grounded in retrieved nodes + entries. |

OpenAPI docs are auto-generated at `/docs`.

---

## Frontend

Built with **Next.js 16** (App Router) + **TypeScript** + **Tailwind CSS v4**.

Project layout:

```
frontend/
├── app/
│   ├── layout.tsx        # root layout
│   ├── page.tsx          # redirects to /record
│   ├── record/page.tsx   # capture entries (audio or text)
│   ├── history/page.tsx  # chronological timeline
│   ├── graph/page.tsx    # interactive knowledge graph
│   ├── digest/page.tsx   # periodic recap
│   ├── chat/page.tsx     # AI chat
│   └── globals.css       # Tailwind v4 entry (@import "tailwindcss")
├── components/
│   ├── Sidebar.tsx        # main navigation
│   ├── NodeChip.tsx       # color-coded entity chip
│   └── ThemeProvider.tsx  # dark/light theme
└── lib/
    └── api.ts            # typed API client
```

Notes specific to **Next.js 16**:

- Uses `proxy.ts` instead of `middleware.ts`.
- `params` in page components is a `Promise` and must be awaited.
- Tailwind v4 uses `@import "tailwindcss"` (no `tailwind.config.js` required for defaults).

The `lib/api.ts` client is the single source of truth for backend calls — every page uses it instead of raw `fetch`.

---

## Tech Stack

### Backend
| Tool | Version | Role |
|---|---|---|
| FastAPI | 0.115 | Async HTTP framework |
| Uvicorn | 0.30 | ASGI server |
| Beanie | 1.26 | Async MongoDB ODM |
| Motor | 3.6 | Async MongoDB driver |
| Pydantic | 2.9 | Schema validation |
| python-multipart, aiofiles | — | Audio upload handling |

### ML / NLP
| Tool | Role |
|---|---|
| `transformers` | HuggingFace pipelines (NER + emotion) |
| `torch` | Inference backend |
| `sentence-transformers` | 384-d sentence embeddings |
| `numpy` | Vectorized cosine ranking |
| `networkx` | Graph traversal + analytics |
| `openai` | Whisper STT + optional chat LLM |
| `google-generativeai` | Gemini chat LLM (default) |

### Frontend
| Tool | Role |
|---|---|
| Next.js 16 | React framework, App Router |
| TypeScript | Type safety |
| Tailwind CSS v4 | Styling |

### Infra
- **MongoDB** (local on `mongodb://localhost:27017` by default).
- **Docker Compose** for one-command spin-up of backend + frontend + MongoDB.
- Static audio served from `backend/uploads/` under `/uploads`.

---

## Configuration

All runtime config is env-based.

| Variable | Default | Purpose |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DB_NAME` | `papairus` | Database name |
| `WHISPER_BACKEND` | `api` | `api` (cloud `whisper-1`) or `local` (local Whisper) |
| `WHISPER_MODEL_SIZE` | `base` | Local model size (`tiny|base|small|medium|large`) |
| `OPENAI_API_KEY` | — | Required for cloud Whisper and OpenAI chat |
| `GEMINI_API_KEY` | — | Required when `LLM_PROVIDER=gemini` |
| `LLM_PROVIDER` | `gemini` | Chat LLM provider (`gemini` or `openai`) |
| `CHAT_PERSONA` | `stoic` | Default persona (`stoic`, `socratic`, or `analyst`) |

The startup banner in [backend/main.py](backend/main.py) prints all of these at boot so misconfiguration is obvious immediately.

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB running locally on port 27017 (or set `MONGO_URI`)

### Backend
```bash
cd backend
pip install -r requirements.txt
# set env: OPENAI_API_KEY and/or GEMINI_API_KEY, etc.
uvicorn main:app --reload
```

First boot will download the BERT NER, emotion, and sentence-transformers models (~500 MB total). They're cached after that.

### Frontend
```bash
cd frontend
npm install
npm run dev
# open http://localhost:3000
```

### Docker Compose
```bash
docker compose up
```
Brings up MongoDB + backend + frontend in one shot.

---

## Production Touches

The bits that turn a prototype into something that actually ships:

- **Async lifespan model preload** — NLP and embedding models load once at startup, not on first request, so the first user interaction isn't a 5-second cold start.
- **Embedding backfill on startup** — any pre-existing entries without embeddings are embedded automatically at boot, so chat retrieval works retroactively over the full history.
- **Pre-normalized embedding vectors** — cosine similarity becomes a single dot product, doubling top-k speed.
- **Hybrid local + LLM NLP pipeline** — local transformers handle the cheap, high-volume work (NER + emotion); the LLM is only called for the reasoning-heavy tag set. This is faster *and* cheaper than an all-LLM pipeline.
- **Deterministic rule-based graph** — edges are debuggable and reproducible. No "why did this edge appear?" mystery.
- **Strict tag canonicalization** — both prompt-side rules and code-side `_normalize_name`, so the graph stays connected.
- **Fully traceable edges** — every edge stores its source `entry_id`, so any relationship can be inspected.
- **Pluggable backends end-to-end** — STT, LLM, and persona are all env-switchable. You can run papAIrus fully offline (local Whisper + local LLM) or fully cloud.

---

## Project Structure

```
papAIrus/
├── backend/
│   ├── main.py                 # FastAPI app, lifespan, routers, banner
│   ├── models.py               # Beanie Documents: Entry, Node, Edge
│   ├── schemas.py              # Pydantic response/request models
│   ├── seed.py                 # sample data for dev
│   ├── requirements.txt
│   ├── routers/
│   │   ├── entries.py          # entry CRUD + extraction pipeline
│   │   ├── nodes.py
│   │   ├── graph.py
│   │   ├── digest.py
│   │   └── chat.py
│   ├── services/
│   │   ├── stt_service.py      # Whisper API + local
│   │   ├── nlp_service.py      # BERT NER + emotion (Layer 1)
│   │   ├── analysis_service.py # LLM tagging (Layer 2)
│   │   ├── embedding_service.py# sentence-transformers
│   │   ├── edge_service.py     # rule-based edge inference
│   │   ├── graph_service.py    # NetworkX graph algorithms
│   │   └── chat_service.py     # persona-driven RAG chat
│   └── uploads/                # uploaded audio (served as static)
├── frontend/
│   ├── app/                    # Next.js App Router pages
│   ├── components/             # Sidebar, NodeChip, ThemeProvider
│   └── lib/api.ts              # typed API client
├── docker-compose.yml
└── README.md
```

---

## Roadmap

Hooks already designed in, ready to be filled:

- **LLM causality scoring** — score `is_causal` on `caused_feeling` / `led_to` / `correlated_with` edges using an LLM second pass. Hook point: `_CAUSALITY_CANDIDATES` in `edge_service.py`.
- **Vector index in MongoDB** — move from in-memory `cosine_rank` to MongoDB Atlas vector search as entry volume grows.
- **Streaming chat responses** — Server-Sent Events from FastAPI to the chat page.
- **Mobile PWA** — voice-first input on phones, offline draft queue.
- **Weekly email digest** — push the digest into the user's inbox on a schedule.
- **Cross-entry deduplication** — collapse near-duplicate entries (same event, two memos) using embedding similarity.

---
