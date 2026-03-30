from datetime import datetime, timezone
from typing import Optional
from beanie import Document, Link, Indexed
from pydantic import Field


class Node(Document):
    name: Indexed(str)
    type: str           # emotion | person | theme | habit
    color_hex: str = "#9fd8c4"

    class Settings:
        name = "nodes"


class Entry(Document):
    transcript: str = ""
    audio_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    node_ids: list[str] = Field(default_factory=list)  # Node id strings

    class Settings:
        name = "entries"
