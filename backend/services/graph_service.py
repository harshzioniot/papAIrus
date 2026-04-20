"""
NetworkX graph algorithm layer.

Load pipeline:
  MongoDB (Node + Edge collections) → NetworkX DiGraph → algorithms

All compute functions are synchronous (NetworkX is CPU-bound).
Use asyncio.to_thread() if calling from a hot async path.
"""

import networkx as nx
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from models import Node, Edge


# ── data loading ──────────────────────────────────────────────────────────────

async def load(since: datetime | None = None) -> tuple[list[Node], list[Edge]]:
    """Fetch nodes + edges from MongoDB. Optional time filter on edges."""
    nodes = await Node.find().to_list()
    q = Edge.find(Edge.timestamp >= since) if since else Edge.find()
    edges = await q.to_list()
    return nodes, edges


def build_digraph(nodes: list[Node], edges: list[Edge]) -> nx.DiGraph:
    """Build a weighted DiGraph. Repeated edges between the same pair accumulate weight."""
    G = nx.DiGraph()

    for n in nodes:
        G.add_node(str(n.id), name=n.name, type=n.type)

    for e in edges:
        u, v = e.from_node_id, e.to_node_id
        if G.has_edge(u, v):
            G[u][v]["weight"] += 1
        else:
            G.add_edge(u, v, edge_type=e.edge_type, weight=1, is_causal=e.is_causal)

    return G


# ── algorithms ────────────────────────────────────────────────────────────────

def get_centrality(G: nx.DiGraph, top_n: int = 10) -> list[dict]:
    """
    PageRank centrality — most influential nodes.
    High score = many other nodes route through it.
    """
    if len(G) == 0:
        return []
    scores = nx.pagerank(G, alpha=0.85, weight="weight")
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [
        {
            "id": nid,
            "name": G.nodes[nid].get("name", ""),
            "type": G.nodes[nid].get("type", ""),
            "score": round(score, 4),
        }
        for nid, score in ranked
        if nid in G.nodes
    ]


def get_communities(G: nx.DiGraph) -> list[list[dict]]:
    """
    Greedy modularity community detection on undirected projection.
    Returns clusters (≥2 nodes) sorted by size descending.
    """
    if len(G) < 3:
        return []
    from networkx.algorithms.community import greedy_modularity_communities
    UG = G.to_undirected()
    comms = sorted(greedy_modularity_communities(UG), key=len, reverse=True)
    result = []
    for comm in comms:
        if len(comm) < 2:
            continue
        members = [
            {
                "id": nid,
                "name": G.nodes[nid].get("name", ""),
                "type": G.nodes[nid].get("type", ""),
            }
            for nid in comm
            if nid in G.nodes
        ]
        result.append(members)
    return result


def get_trending(nodes: list[Node], edges: list[Edge], days: int = 7) -> dict:
    """
    Compare node activity (edge appearances) in last `days` vs the prev `days`.
    Returns top 5 trending up and top 5 trending down.
    """
    now = datetime.now(timezone.utc)
    cutoff_recent = now - timedelta(days=days)
    cutoff_prev   = now - timedelta(days=days * 2)

    node_map = {str(n.id): {"name": n.name, "type": n.type} for n in nodes}
    recent:   dict[str, int] = defaultdict(int)
    previous: dict[str, int] = defaultdict(int)

    for e in edges:
        ts = e.timestamp.replace(tzinfo=timezone.utc) if e.timestamp.tzinfo is None else e.timestamp
        for nid in (e.from_node_id, e.to_node_id):
            if ts >= cutoff_recent:
                recent[nid] += 1
            elif ts >= cutoff_prev:
                previous[nid] += 1

    up, down = [], []
    for nid in set(recent) | set(previous):
        r, p = recent.get(nid, 0), previous.get(nid, 0)
        if r == 0 and p == 0:
            continue
        delta = round(((r - p) / p * 100) if p else 100.0, 1)
        meta = node_map.get(nid, {"name": nid, "type": ""})
        entry = {"id": nid, "name": meta["name"], "type": meta["type"],
                 "recent": r, "previous": p, "delta_pct": delta}
        (up if delta > 0 else down).append(entry)

    up.sort(key=lambda x: x["delta_pct"], reverse=True)
    down.sort(key=lambda x: x["delta_pct"])
    return {"up": up[:5], "down": down[:5]}


def find_path(G: nx.DiGraph, from_id: str, to_id: str) -> list[dict]:
    """Shortest path between two nodes — traces causal chains through the graph."""
    try:
        path = nx.shortest_path(G, from_id, to_id)
        return [
            {"id": nid, "name": G.nodes[nid].get("name", ""), "type": G.nodes[nid].get("type", "")}
            for nid in path
            if nid in G.nodes
        ]
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


# ── reflection generator ──────────────────────────────────────────────────────

def generate_reflection(centrality: list[dict], top_emotion: str | None) -> str:
    """
    Graph-informed Socratic reflection for the weekly digest.
    Falls back gracefully when the graph is sparse.
    """
    if not centrality:
        return "What patterns do you notice in your week?"

    top = centrality[0]
    name, ntype = top["name"], top["type"]

    templates = {
        "emotion":  f"'{name}' has been your most connected emotional state this week. What's underneath it?",
        "person":   f"'{name}' keeps showing up at the centre of your week. What is that relationship asking of you?",
        "theme":    f"'{name}' is the most recurring theme right now. What would shift if you addressed it directly?",
        "habit":    f"Your habit '{name}' is deeply wired into how you feel this week. Is it serving you?",
        "event":    f"The event '{name}' has had the most ripple effects this week. What's it still asking you to process?",
        "place":    f"'{name}' keeps appearing in your most significant moments. What does that place mean to you?",
        "decision": f"The decision around '{name}' seems to be shaping a lot. Are you at peace with where it's going?",
        "outcome":  f"'{name}' is the outcome that connects the most threads this week. Was it what you expected?",
    }
    return templates.get(ntype, f"'{name}' is the most significant pattern this week. Worth sitting with.")
