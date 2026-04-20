"""
Standalone test for the full extraction pipeline:
  Layer 1 (local NER + emotion) → Layer 2 (LLM tags) → Edge inference

Run from the backend/ directory:

    python test_analysis.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from services.analysis_service import analyze
from services.edge_service import infer, summarise

SAMPLE_TRANSCRIPT = (
    "Had a really rough day. Back-to-back meetings with Sarah at the office drained me. "
    "I decided to finally quit coffee after the 3pm crash hit me hard again — hoping that fixes my sleep. "
    "I keep doom-scrolling at night instead of sleeping and I know it's making things worse. "
    "The project deadline is next week and I'm spiraling about whether I can pull it off. "
    "Talked to Marcus at the gym briefly — that helped actually. Better mood after."
)

SAMPLE_LAYER1 = {
    "people": ["Sarah", "Marcus"],
    "emotion_hint": "fear",
    "emotion_score": 0.72,
}

FAKE_ENTRY_ID = "test_entry_001"


async def main():
    provider = os.getenv("LLM_PROVIDER", "gemini")
    print(f"Provider  : {provider}")
    print(f"Transcript: {SAMPLE_TRANSCRIPT[:80]}...")
    print()

    # ── Layer 2 ───────────────────────────────────────────────────────────────
    tags = await analyze(SAMPLE_TRANSCRIPT, SAMPLE_LAYER1)

    if not tags:
        print("No tags returned — check your API key and LLM_PROVIDER setting.")
        return

    print(f"{'TYPE':<12} NAME")
    print("-" * 45)
    for t in tags:
        print(f"{t.type:<12} {t.name}")

    # ── Edge inference ────────────────────────────────────────────────────────
    tag_dicts = [{"name": t.name, "type": t.type} for t in tags]
    edges = infer(tag_dicts, entry_id=FAKE_ENTRY_ID)

    print()
    print(f"{'FROM':<25} {'EDGE TYPE':<20} {'TO'}")
    print("-" * 75)
    for e in edges:
        from_label = f"{e.from_name} ({e.from_type})"
        to_label   = f"{e.to_name} ({e.to_type})"
        causal     = " *" if e.is_causal else ""
        print(f"{from_label:<25} {e.edge_type + causal:<20} {to_label}")

    stats = summarise(edges)
    print()
    print(f"Total edges: {stats['total']}  (* = causal candidate for future LLM scoring)")
    print(f"By type: {stats['by_type']}")


if __name__ == "__main__":
    asyncio.run(main())
