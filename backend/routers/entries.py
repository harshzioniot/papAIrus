import os
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Form, UploadFile, File, status
import aiofiles

from models import Entry, Node
from schemas import EntryOut, NodeOut, AutoTagOut, TagSuggestion
from services import stt_service, nlp_service, analysis_service

router = APIRouter(prefix="/entries", tags=["entries"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
    from beanie import PydanticObjectId
    entry = await Entry.get(PydanticObjectId(entry_id))
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if not entry.transcript or not entry.transcript.strip():
        raise HTTPException(status_code=400, detail="Entry has no transcript to analyze")

    # Layer 1 — local transformer inference (sync, run in thread)
    import asyncio
    layer1 = await asyncio.to_thread(nlp_service.run, entry.transcript)

    # Layer 2 — GPT-4o-mini enriched with Layer 1 context
    suggestions = await analysis_service.analyze(entry.transcript, layer1)

    return AutoTagOut(suggestions=suggestions)


@router.post("/{entry_id}/transcribe", response_model=EntryOut)
async def transcribe_entry(entry_id: str, language: Optional[str] = None):
    """
    Transcribe the audio file associated with an entry using OpenAI Whisper.
    Updates the entry's transcript field with the transcription result.
    """
    from beanie import PydanticObjectId
    
    entry = await Entry.get(PydanticObjectId(entry_id))
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    if not entry.audio_path:
        raise HTTPException(status_code=400, detail="No audio file associated with this entry")
    
    audio_full_path = os.path.join(UPLOAD_DIR, entry.audio_path)
    if not os.path.exists(audio_full_path):
        raise HTTPException(status_code=404, detail="Audio file not found on disk")
    
    try:
        transcript = await stt_service.transcribe_audio(
            audio_file_path=audio_full_path,
            language=language
        )
        
        entry.transcript = transcript
        await entry.save()
        
        return await _hydrate(entry)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Transcription failed: {str(e)}"
        )


@router.post("/transcribe-upload", response_model=dict)
async def transcribe_upload(
    audio: UploadFile = File(...),
    language: Optional[str] = None,
    with_timestamps: bool = False
):
    """
    Transcribe an uploaded audio file without creating an entry.
    Useful for testing or getting quick transcriptions.
    """
    if not audio.filename:
        raise HTTPException(status_code=400, detail="No audio file provided")
    
    ext = os.path.splitext(audio.filename)[1] or ".webm"
    temp_fname = f"temp_{uuid.uuid4().hex}{ext}"
    temp_path = os.path.join(UPLOAD_DIR, temp_fname)
    
    try:
        async with aiofiles.open(temp_path, "wb") as f:
            await f.write(await audio.read())
        
        if with_timestamps:
            result = await stt_service.transcribe_with_timestamps(
                audio_file_path=temp_path,
                language=language
            )
        else:
            transcript = await stt_service.transcribe_audio(
                audio_file_path=temp_path,
                language=language
            )
            result = {"text": transcript}
        
        os.remove(temp_path)
        
        return result
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )
