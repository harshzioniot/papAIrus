import os
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Form, UploadFile, File, status
import aiofiles

from models import Entry, Node
from schemas import EntryOut, NodeOut, AutoTagOut, TagSuggestion

router = APIRouter(prefix="/entries", tags=["entries"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

STUB_SUGGESTIONS = [
    TagSuggestion(name="anxious", type="emotion"),
    TagSuggestion(name="frustrated", type="emotion"),
    TagSuggestion(name="work stress", type="theme"),
    TagSuggestion(name="manager", type="person"),
]


async def _hydrate(entry: Entry) -> EntryOut:
    nodes: list[NodeOut] = []
    if entry.node_ids:
        from beanie import PydanticObjectId
        db_nodes = await Node.find(
            {"_id": {"$in": [PydanticObjectId(i) for i in entry.node_ids]}}
        ).to_list()
        nodes = [NodeOut(id=str(n.id), name=n.name, type=n.type, color_hex=n.color_hex) for n in db_nodes]
    return EntryOut(
        id=str(entry.id),
        transcript=entry.transcript,
        audio_path=entry.audio_path,
        created_at=entry.created_at,
        nodes=nodes,
    )


@router.post("", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
async def create_entry(
    transcript: str = Form(default=""),
    node_ids: str = Form(default=""),
    audio: Optional[UploadFile] = File(None),
):
    audio_path = None
    if audio and audio.filename:
        ext = os.path.splitext(audio.filename)[1] or ".webm"
        fname = f"{uuid.uuid4().hex}{ext}"
        dest = os.path.join(UPLOAD_DIR, fname)
        async with aiofiles.open(dest, "wb") as f:
            await f.write(await audio.read())
        audio_path = fname

    ids = [i.strip() for i in node_ids.split(",") if i.strip()]
    entry = Entry(transcript=transcript, audio_path=audio_path, node_ids=ids)
    await entry.insert()
    return await _hydrate(entry)


@router.get("", response_model=list[EntryOut])
async def list_entries(skip: int = 0, limit: int = 50):
    entries = await Entry.find().sort(-Entry.created_at).skip(skip).limit(limit).to_list()
    return [await _hydrate(e) for e in entries]


@router.get("/{entry_id}", response_model=EntryOut)
async def get_entry(entry_id: str):
    from beanie import PydanticObjectId
    entry = await Entry.get(PydanticObjectId(entry_id))
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return await _hydrate(entry)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(entry_id: str):
    from beanie import PydanticObjectId
    entry = await Entry.get(PydanticObjectId(entry_id))
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await entry.delete()


@router.post("/{entry_id}/tags", response_model=EntryOut)
async def set_tags(entry_id: str, node_ids: list[str]):
    from beanie import PydanticObjectId
    entry = await Entry.get(PydanticObjectId(entry_id))
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry.node_ids = node_ids
    await entry.save()
    return await _hydrate(entry)


@router.post("/{entry_id}/auto-tag", response_model=AutoTagOut)
async def auto_tag(entry_id: str):
    """Stub — replace with LLM/Whisper call later."""
    from beanie import PydanticObjectId
    entry = await Entry.get(PydanticObjectId(entry_id))
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return AutoTagOut(suggestions=STUB_SUGGESTIONS)
