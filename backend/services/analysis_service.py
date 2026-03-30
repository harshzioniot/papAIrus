import json
import os
import logging
from openai import AsyncOpenAI

from schemas import TagSuggestion

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


async def analyze(transcript: str, layer1: dict) -> list[TagSuggestion]:
    """Layer 2 — GPT-4o-mini enriched with Layer 1 context."""
    people_str = ", ".join(layer1["people"]) if layer1["people"] else "none detected"
    emotion_hint = layer1["emotion_hint"]

    prompt = f"""You are analyzing a personal journal entry. Extract meaningful tags.

NLP pre-analysis context (use as grounding, not a constraint):
- Detected people: {people_str}
- Dominant emotion signal: {emotion_hint}

Return ONLY a raw JSON array — no markdown, no explanation. Each item: {{"name": "...", "type": "..."}}

Tag rules:
- emotion: descriptive phrases, not single words (e.g. "quiet anxiety", "bittersweet relief") — 2 to 4 tags
- theme: abstract life concepts (e.g. "work-life balance", "creative block") — 1 to 3 tags
- habit: recurring behaviors explicitly mentioned (e.g. "late-night scrolling") — 0 to 2 tags
- person: people referred to by name — include all from detected list if they appear in the text

Journal entry:
{transcript}"""

    client = _get_client()
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=400,
    )

    raw = response.choices[0].message.content.strip()

    try:
        data = json.loads(raw)
        return [
            TagSuggestion(name=item["name"], type=item["type"])
            for item in data
            if "name" in item and "type" in item
        ]
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to parse GPT response: %r — %s", raw, e)
        return []
