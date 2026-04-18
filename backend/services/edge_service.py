"""
Rule-based edge inference for the knowledge graph.

Takes the flat tag list from Layer 2 and produces typed, timestamped edges
based on which node types co-occur in the same entry.

Why rule-based (not LLM):
  The graph's signal comes from *accumulated* co-occurrence across hundreds of
  entries, not from precision on any single one. If someone mentions a bad
  meeting AND anxiety in the same entry, that edge IS meaningful data even
  without LLM confirmation. Centrality and trend algorithms handle the rest.

  LLM causality enrichment (e.g. scoring "did X actually cause Y?") can be
  layered on top later — see _CAUSALITY_CANDIDATES below for the hook point.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ── edge rule matrix ──────────────────────────────────────────────────────────
# (from_type, to_type, edge_type)
# Order matters for readability but not correctness.

_RULES: list[tuple[str, str, str]] = [
    ("event",    "person",   "involves"),
    ("event",    "emotion",  "caused_feeling"),
    ("event",    "place",    "happened_during"),
    ("emotion",  "theme",    "connected_to"),
    ("theme",    "person",   "recurs_with"),
    ("theme",    "place",    "recurs_with"),
    ("theme",    "habit",    "recurs_with"),
    ("decision", "outcome",  "led_to"),
    ("habit",    "emotion",  "correlated_with"),
    ("habit",    "theme",    "correlated_with"),
]

# These edge types benefit most from LLM causality scoring in a future pass.
# Hook: pass InferredEdges w/ these types through an LLM scorer that adds a
# confidence float and flips directionality if needed.
_CAUSALITY_CANDIDATES = {"caused_feeling", "led_to", "correlated_with"}


# ── data types ────────────────────────────────────────────────────────────────

@dataclass
class TagNode:
    name: str
    type: str


@dataclass
class InferredEdge:
    from_name: str
    from_type: str
    to_name: str
    to_type: str
    edge_type: str
    entry_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_causal: bool = False   # True for caused_feeling / led_to / correlated_with


# ── public interface ──────────────────────────────────────────────────────────

def infer(
    tags: list[dict],
    entry_id: str,
    timestamp: Optional[datetime] = None,
) -> list[InferredEdge]:
    """
    Infer typed edges from a flat list of extracted tags.

    Args:
        tags:      list of {"name": str, "type": str} dicts (Layer 2 output)
        entry_id:  MongoDB entry ID — stored on every edge for traceability
        timestamp: entry creation time; defaults to now

    Returns:
        list of InferredEdge, deduplicated
    """
    ts = timestamp or datetime.now(timezone.utc)

    # Group node names by type
    by_type: dict[str, list[str]] = {}
    for tag in tags:
        t = tag.get("type", "").lower().strip()
        n = tag.get("name", "").strip()
        if t and n:
            by_type.setdefault(t, []).append(n)

    seen: set[tuple] = set()
    edges: list[InferredEdge] = []

    for from_type, to_type, edge_type in _RULES:
        for from_name in by_type.get(from_type, []):
            for to_name in by_type.get(to_type, []):
                key = (from_name, from_type, to_name, to_type, edge_type)
                if key in seen:
                    continue
                seen.add(key)
                edges.append(InferredEdge(
                    from_name=from_name,
                    from_type=from_type,
                    to_name=to_name,
                    to_type=to_type,
                    edge_type=edge_type,
                    entry_id=entry_id,
                    timestamp=ts,
                    is_causal=edge_type in _CAUSALITY_CANDIDATES,
                ))

    return edges


def summarise(edges: list[InferredEdge]) -> dict:
    """Quick stats — useful for test output and debug logging."""
    by_type: dict[str, int] = {}
    for e in edges:
        by_type[e.edge_type] = by_type.get(e.edge_type, 0) + 1
    return {"total": len(edges), "by_type": by_type}
