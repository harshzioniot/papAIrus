"""
Smoke test for the conversation layer.

Hits MongoDB for subgraph retrieval and the configured LLM provider for the reply.
Run from the backend/ directory:

    python test_chat.py "I've been feeling anxious about the deadline" socratic

If no args are given, sends a default message with the env-default persona.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models import Entry, Node, Edge
from services import chat_service


async def main():
    message = sys.argv[1] if len(sys.argv) > 1 else "I've been feeling anxious about the deadline."
    persona = sys.argv[2] if len(sys.argv) > 2 else os.getenv("CHAT_PERSONA", "stoic")

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("DB_NAME", "papairus")
    client = AsyncIOMotorClient(mongo_uri)
    await init_beanie(database=client[db_name], document_models=[Entry, Node, Edge])

    print(f"Provider : {os.getenv('LLM_PROVIDER', 'gemini')}")
    print(f"Persona  : {persona}")
    print(f"Message  : {message}\n")

    # Inspect what the retrieval layer found before calling the LLM
    matched = await chat_service._find_relevant_nodes(message)
    print(f"Matched nodes ({len(matched)}): {[n.name for n in matched] or '— none, graph may be empty'}")

    result = await chat_service.chat(message, persona)

    print("\n--- REPLY ---")
    print(result["reply"])
    print("\n--- CONTEXT NODES ---")
    for n in result["context_nodes"]:
        print(f"  {n['name']:<25} ({n['type']})")

    client.close()


if __name__ == "__main__":
    asyncio.run(main())
