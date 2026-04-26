"""
Conversation layer — persona-driven LLM responses grounded in the user's knowledge graph.

Flow:
  user message
  → keyword match against node names → matched nodes
  → 1-hop subgraph (edges touching matched nodes) → neighbour nodes
  → 2-3 entry snippets linked to matched nodes
  → build LLM context (subgraph + snippets + persona system prompt)
  → call LLM via LLM_PROVIDER
  → return reply + context nodes
"""

import os
import logging
import re

from models import Node, Edge, Entry

logger = logging.getLogger(__name__)

# ── persona system prompts (Section 7 of architecture doc) ───────────────────

PERSONAS = {
    "stoic": (
        "You are a Stoic Listener — a private philosopher companion.\n"
        "You never judge. You reflect back what you hear with calm clarity.\n"
        "Your verbal output is minimal. You let silence do the work.\n"
        "Speak only when it genuinely adds value — never to fill space.\n"
        "You do not tell the user what to do. You do not give unsolicited advice.\n"
        "You observe. You reflect. The decision is always the user's.\n"
        "If the graph has surfaced a pattern, name it once, quietly — then let it sit."
    ),
    "socratic": (
        "You are a Socratic questioner — a private philosopher companion.\n"
        "You ask exactly one question per response. Never more.\n"
        "You do not provide answers. You deepen the question.\n"
        "Your question should make the user think harder about what they already said.\n"
        "Notice what they've said twice, what they've avoided, what sits beneath the surface.\n"
        "You do not tell the user what to do. You do not give advice.\n"
        "End every response with a single, precise question."
    ),
    "analyst": (
        "You are a Pattern Analyst — a private philosopher companion.\n"
        "You surface what the knowledge graph has found.\n"
        "Name patterns the user may not have consciously noticed.\n"
        "Speak in observations, not prescriptions: 'I've noticed...' not 'You should...'\n"
        "Ground every insight in the graph context provided — do not speculate beyond the data.\n"
        "If the graph is sparse, say so honestly.\n"
        "You do not tell the user what to do. You surface. They decide."
    ),
}


# ── subgraph retrieval ────────────────────────────────────────────────────────

async def _find_relevant_nodes(message: str, limit: int = 8) -> list[Node]:
    """Match message keywords against node names via case-insensitive substring search."""
    words = [w.strip(".,!?;:\"'()") for w in message.lower().split() if len(w.strip(".,!?;:\"'()")) > 3]
    if not words:
        return await Node.find().sort(-Node.id).limit(limit).to_list()

    matched: dict[str, Node] = {}
    for word in words:
        nodes = await Node.find({"name": {"$regex": re.escape(word), "$options": "i"}}).to_list()
        for n in nodes:
            matched[str(n.id)] = n
        if len(matched) >= limit:
            break

    return list(matched.values())[:limit]


async def _build_subgraph_context(matched_nodes: list[Node]) -> tuple[list[Node], list[Edge]]:
    """Pull 1-hop edges touching matched nodes; return all involved nodes + edges."""
    if not matched_nodes:
        return [], []

    matched_ids = [str(n.id) for n in matched_nodes]
    edges = await Edge.find(
        {"$or": [
            {"from_node_id": {"$in": matched_ids}},
            {"to_node_id": {"$in": matched_ids}},
        ]}
    ).limit(30).to_list()

    neighbour_ids = set()
    for e in edges:
        neighbour_ids.add(e.from_node_id)
        neighbour_ids.add(e.to_node_id)
    neighbour_ids -= set(matched_ids)

    neighbours: list[Node] = []
    if neighbour_ids:
        from beanie import PydanticObjectId
        neighbours = await Node.find(
            {"_id": {"$in": [PydanticObjectId(i) for i in neighbour_ids]}}
        ).to_list()

    return matched_nodes + neighbours, edges


async def _fetch_entry_snippets(matched_node_ids: list[str], limit: int = 3) -> list[str]:
    """Fetch recent entry transcripts that contain any of the matched nodes."""
    entries = await Entry.find(
        {"node_ids": {"$in": matched_node_ids}}
    ).sort(-Entry.created_at).limit(limit).to_list()
    return [e.transcript for e in entries if e.transcript.strip()]


# ── context formatter ─────────────────────────────────────────────────────────

def _format_context(all_nodes: list[Node], edges: list[Edge], snippets: list[str]) -> str:
    if not all_nodes and not snippets:
        return "No relevant graph context found yet — the graph builds as you add more journal entries."

    parts = []

    if all_nodes:
        node_lines = ", ".join(f"{n.name} ({n.type})" for n in all_nodes[:15])
        parts.append(f"RELEVANT NODES:\n{node_lines}")

    if edges:
        node_map = {str(n.id): n.name for n in all_nodes}
        edge_lines = [
            f"  {node_map.get(e.from_node_id, e.from_node_id)} —[{e.edge_type}]→ {node_map.get(e.to_node_id, e.to_node_id)}"
            for e in edges[:12]
        ]
        parts.append("CONNECTIONS:\n" + "\n".join(edge_lines))

    if snippets:
        snip_lines = "\n\n".join(
            f'"{s[:300]}..."' if len(s) > 300 else f'"{s}"'
            for s in snippets
        )
        parts.append(f"RECENT ENTRY SNIPPETS:\n{snip_lines}")

    return "\n\n".join(parts)


# ── LLM providers (same pattern as analysis_service.py) ──────────────────────

async def _call_gemini(system_prompt: str, message: str) -> str:
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        generation_config={"temperature": 0.7, "max_output_tokens": 600},
        system_instruction=system_prompt,
    )
    response = await model.generate_content_async(message)
    return response.text.strip()


async def _call_openai(system_prompt: str, message: str) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        temperature=0.7,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()


async def _call_ollama(system_prompt: str, message: str) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key="ollama",
    )
    response = await client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL", "mistral"),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        temperature=0.7,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()


_LLM_PROVIDERS = {
    "gemini": _call_gemini,
    "openai": _call_openai,
    "ollama": _call_ollama,
}


# ── public interface ──────────────────────────────────────────────────────────

async def chat(message: str, persona: str) -> dict:
    """
    Core chat function.
    Returns {"reply": str, "context_nodes": [...], "persona": str}.
    """
    persona = persona.lower()
    if persona not in PERSONAS:
        persona = "stoic"

    matched_nodes = await _find_relevant_nodes(message)
    all_nodes, edges = await _build_subgraph_context(matched_nodes)
    snippets = await _fetch_entry_snippets([str(n.id) for n in matched_nodes])

    graph_context = _format_context(all_nodes, edges, snippets)

    system_prompt = (
        f"{PERSONAS[persona]}\n\n"
        "---\n"
        "KNOWLEDGE GRAPH CONTEXT (derived from the user's own journal entries):\n"
        f"{graph_context}\n"
        "---\n\n"
        "Respond only to what the user has just said. "
        "Ground your response in the context above when relevant. "
        "Treat this data as private and personal."
    )

    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    fn = _LLM_PROVIDERS.get(provider)
    if fn is None:
        raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Valid: gemini, openai, ollama")

    try:
        reply = await fn(system_prompt, message)
    except Exception as e:
        logger.error("[chat/%s] LLM call failed: %s", provider, e)
        raise

    return {
        "reply": reply,
        "context_nodes": [{"id": str(n.id), "name": n.name, "type": n.type} for n in all_nodes[:10]],
        "persona": persona,
    }
