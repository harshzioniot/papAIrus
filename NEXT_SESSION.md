# papAIrus — Next Session Handoff

## What was built this session

### Full pipeline (now automatic)
```
journal entry submitted
  → Layer 1: local BERT NER + DistilRoBERTa emotion (nlp_service.py)
  → Layer 2: Gemini/OpenAI/Ollama LLM — extracts 8 node types (analysis_service.py)
  → edge_service.py: rule-based typed edge inference
  → nodes upserted to MongoDB, entry.node_ids updated
  → edges persisted to MongoDB edges collection
  → [background task — non-blocking]
```

### Graph algorithms (graph_service.py)
- **PageRank centrality** — most influential nodes
- **Community detection** — clusters of related nodes (greedy modularity)
- **Trend detection** — nodes growing/fading vs previous period
- **Path finding** — shortest causal chain between two nodes
- **Reflection generator** — graph-informed Socratic prompt for weekly digest

### New endpoints
| Method | Path | What it does |
|--------|------|--------------|
| POST | `/entries` | Create entry → auto-triggers pipeline in background |
| POST | `/entries/{id}/transcribe` | Transcribe audio → auto-triggers pipeline in background |
| POST | `/entries/{id}/auto-tag` | Manual re-tag trigger |
| GET | `/graph/insights` | Centrality + communities + trending |
| GET | `/graph/path?from_id=&to_id=` | Causal path between two nodes |
| GET | `/graph` | Visualisation graph (now uses typed Edge collection) |

### LLM provider swap
Set `LLM_PROVIDER` in `.env`:
- `gemini` (default) — needs `GEMINI_API_KEY`
- `openai` — needs `OPENAI_API_KEY`
- `ollama` — fully local, no key needed, run `ollama pull mistral`

---

## What is NOT built yet — the conversation layer

This is the core missing piece. The graph is built and algorithms run, but **nothing talks back to the user yet**.

### The gap
When the user speaks to the philosopher, the LLM needs to receive:
```
system prompt (persona: Stoic / Socratic / Analyst)
  + relevant subgraph  ← pulled from graph based on what the user just said
  + 2-3 raw transcript snippets  ← entries linked to those nodes
  + current user message
→ LLM responds as the philosopher
```

Right now there is no `/chat` endpoint, no persona prompt, and no subgraph retrieval.

### What needs to be built

#### 1. Subgraph retrieval
Given the user's message:
- Match keywords against node names in the graph
- Pull their 1-hop neighbourhood from the Edge collection
- Fetch 2-3 most recent journal entries linked to those nodes
- Build a compact context string (not the full history — just the relevant slice)

#### 2. `chat_service.py`
- Builds context payload: subgraph summary + entry snippets
- Sends to LLM with persona system prompt
- Returns response text

#### 3. `POST /chat` endpoint
```json
Request:  { "message": "I've been feeling anxious lately", "persona": "socratic" }
Response: { "reply": "You've mentioned anxiety 7 times this week...", "nodes_used": [...] }
```

#### 4. Persona system prompts (from architecture doc)
Three modes, user-configurable:

**Stoic Listener** — never judges, reflects back, minimal output, speaks only when significant
**Socratic Mode** — asks one question that makes the user think harder, never provides the answer
**Pattern Analyst** — surfaces what the graph found, e.g. "I've noticed you mention anxiety every time you have back-to-back meetings"

---

## Testing the current build

### Prerequisites
```bash
pip install -r backend/requirements.txt
# MongoDB running on localhost:27017
# .env file with GEMINI_API_KEY (or OPENAI_API_KEY / Ollama)
```

### Run server
```bash
cd backend && uvicorn main:app --reload
```

### Test the pipeline (no server needed)
```bash
cd backend && python test_analysis.py
```
Expected: tags printed by type, then inferred edges with types

### Test full pipeline via API
1. Go to `http://localhost:8000/docs`
2. `POST /entries` with a transcript text
3. Wait ~2-3 seconds for background pipeline to complete
4. `GET /entries/{id}` — should show nodes populated
5. `GET /graph/insights` — centrality + communities + trending

### Key files changed this session
```
backend/services/analysis_service.py   — LLM provider swap (gemini/openai/ollama)
backend/services/edge_service.py       — NEW: rule-based edge inference
backend/services/graph_service.py      — NEW: NetworkX algorithms
backend/services/nlp_service.py        — unchanged (Layer 1, local BERT)
backend/routers/entries.py             — pipeline now fires automatically on create + transcribe
backend/routers/graph.py               — uses Edge collection, adds /insights and /path
backend/routers/digest.py              — most_connected_node now PageRank, reflection graph-informed
backend/models.py                      — Edge document added, all 8 node types + colours
backend/schemas.py                     — CentralNode, TrendNode, InsightsOut, PathNode added
backend/requirements.txt               — networkx, google-generativeai added
```
