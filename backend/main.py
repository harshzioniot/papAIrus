import asyncio
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models import Entry, Node, Edge
from routers import entries, nodes, graph, digest, chat
from services import nlp_service, embedding_service

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "papairus")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def _print_banner():
    stt = os.getenv("WHISPER_BACKEND", "api").upper()
    model = os.getenv("WHISPER_MODEL_SIZE", "base") if stt == "LOCAL" else "whisper-1 (cloud)"
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_gemini = bool(os.getenv("GEMINI_API_KEY"))
    llm_provider = os.getenv("LLM_PROVIDER", "gemini")
    chat_persona = os.getenv("CHAT_PERSONA", "stoic")
    print("\n" + "=" * 44)
    print("  papAIrus backend")
    print("=" * 44)
    print(f"  MongoDB  : {MONGO_URI}")
    print(f"  Database : {DB_NAME}")
    print(f"  STT      : {stt} ({model})")
    print(f"  LLM      : {llm_provider}")
    print(f"  Persona  : {chat_persona}")
    print(f"  OpenAI   : {'set' if has_openai else 'NOT SET'}")
    print(f"  Gemini   : {'set' if has_gemini else 'NOT SET'}")
    print("=" * 44 + "\n")


async def _backfill_embeddings():
    """Embed any entries that pre-date the embedding column."""
    pending = await Entry.find({"embedding": None, "transcript": {"$ne": ""}}).to_list()
    if not pending:
        return
    print(f"  Backfilling embeddings for {len(pending)} existing entries…")
    for e in pending:
        if not e.transcript.strip():
            continue
        e.embedding = await asyncio.to_thread(embedding_service.embed, e.transcript)
        await e.save()
    print(f"  ✓ Embedded {len(pending)} entries.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _print_banner()
    client = AsyncIOMotorClient(MONGO_URI)
    await init_beanie(database=client[DB_NAME], document_models=[Entry, Node, Edge])
    await asyncio.to_thread(nlp_service.load_models)
    await asyncio.to_thread(embedding_service.load_model)
    await _backfill_embeddings()
    yield
    client.close()


app = FastAPI(title="papAIrus API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(entries.router)
app.include_router(nodes.router)
app.include_router(graph.router)
app.include_router(digest.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}
