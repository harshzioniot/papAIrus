from datetime import datetime, timezone
from typing import Optional
from beanie import Document, Indexed
from pydantic import Field

# Node type → default colour
NODE_COLOURS: dict[str, str] = {
    "person":   "#7eb8f7",  # blue
    "emotion":  "#f7a07e",  # orange
    "theme":    "#9fd8c4",  # teal
    "event":    "#c4a0f7",  # purple
    "habit":    "#f7d07e",  # yellow
    "place":    "#7ef7a0",  # green
    "decision": "#f77eb8",  # pink
    "outcome":  "#a0c4f7",  # light blue
}

VALID_NODE_TYPES = set(NODE_COLOURS.keys())

# Edge types mirror the knowledge graph schema
VALID_EDGE_TYPES = {
    "involves",
    "caused_feeling",
    "happened_during",
    "connected_to",
    "recurs_with",
    "led_to",
    "correlated_with",
}


class Node(Document):
    name: Indexed(str)
    type: str           # one of VALID_NODE_TYPES
    color_hex: str = "#9fd8c4"

    class Settings:
        name = "nodes"


class Edge(Document):
    from_node_id: str
    from_type: str
    to_node_id: str
    to_type: str
    edge_type: str      # one of VALID_EDGE_TYPES
    entry_id: str       # source entry — for traceability & temporal queries
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_causal: bool = False

    class Settings:
        name = "edges"


class Entry(Document):
    transcript: str = ""
    audio_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    node_ids: list[str] = Field(default_factory=list)

    class Settings:
        name = "entries"
