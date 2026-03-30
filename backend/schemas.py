from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ── Node ──────────────────────────────────────────────────────────────────────

class NodeOut(BaseModel):
    id: str
    name: str
    type: str
    color_hex: str


class NodeCreate(BaseModel):
    name: str
    type: str
    color_hex: Optional[str] = None


# ── Entry ─────────────────────────────────────────────────────────────────────

class EntryOut(BaseModel):
    id: str
    transcript: str
    audio_path: Optional[str]
    created_at: datetime
    nodes: list[NodeOut] = []


# ── Graph ─────────────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    name: str
    type: str
    color_hex: str
    entry_count: int


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: int


class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# ── Digest ────────────────────────────────────────────────────────────────────

class PersonMention(BaseModel):
    name: str
    count: int


class DayIntensity(BaseModel):
    day: str
    date: str
    count: int
    dominant_type: str


class DigestOut(BaseModel):
    week_start: str
    week_end: str
    top_emotion: Optional[str]
    top_emotion_count: int
    mood_trend_pct: float
    most_connected_node: Optional[str]
    most_connected_count: int
    entry_count: int
    best_streak: int
    days: list[DayIntensity]
    people: list[PersonMention]
    reflection: str


# ── Auto-tag stub ─────────────────────────────────────────────────────────────

class TagSuggestion(BaseModel):
    name: str
    type: str


class AutoTagOut(BaseModel):
    suggestions: list[TagSuggestion]
