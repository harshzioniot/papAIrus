import json
import os
import logging

from schemas import TagSuggestion

logger = logging.getLogger(__name__)


# ── shared prompt builder ─────────────────────────────────────────────────────

def _build_prompt(transcript: str, layer1: dict) -> str:
    people_str = ", ".join(layer1["people"]) if layer1["people"] else "none"
    emotion_hint = layer1["emotion_hint"]
    return f"""Analyze this journal entry & extract tags.

Hints (grounding only):
- People (BERT-detected, USE THESE EXACT NAMES): {people_str}
- Emotion signal: {emotion_hint}

Return ONLY a raw JSON array, no markdown. Each item: {{"name":"...","type":"..."}}

CRITICAL — name standardization rules:
- person tags MUST use the EXACT name from the BERT-detected list above (e.g. "Sarah", not "my_colleague_sarah" or "Sarah (colleague)")
- person tag = first name only when possible. No descriptors, no underscores, no parentheticals.
- All other tag names: lowercase, plain English noun phrases (e.g. "project deadline" not "the_project_deadline")
- No underscores anywhere. Use spaces.
- Reuse common forms: "anxiety" not "feeling anxious"; "office" not "the office"; "running" not "going running".
- These names will be UPSERTED across many entries — consistency is critical for graph connectivity.

Types & counts (max):
- emotion: short noun phrase, lowercase (e.g. "anxiety", "quiet relief") — 2-4
- theme: abstract life concept, lowercase (e.g. "work-life balance") — 1-3
- habit: recurring behavior, lowercase (e.g. "late-night scrolling") — 0-2
- person: from BERT hints, exact spelling — include all hints if in text
- event: specific occurrence, lowercase (e.g. "demo day") — 0-3
- place: location, lowercase single word/phrase (e.g. "gym", "office") — 0-2
- decision: choice made, lowercase verb phrase (e.g. "quit coffee") — 0-2
- outcome: result, lowercase (e.g. "better sleep") — 0-2

Entry:
{transcript}"""


def _parse(raw: str) -> list[TagSuggestion]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    return [
        TagSuggestion(name=item["name"], type=item["type"])
        for item in data
        if "name" in item and "type" in item
    ]


# ── provider implementations ──────────────────────────────────────────────────

async def _analyze_gemini(prompt: str) -> list[TagSuggestion]:
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        generation_config={"temperature": 0.3, "max_output_tokens": 400},
    )
    response = await model.generate_content_async(prompt)
    return _parse(response.text)


async def _analyze_openai(prompt: str) -> list[TagSuggestion]:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = await client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=400,
    )
    return _parse(response.choices[0].message.content.strip())


async def _analyze_ollama(prompt: str) -> list[TagSuggestion]:
    from openai import AsyncOpenAI  # Ollama exposes an OpenAI-compatible API
    client = AsyncOpenAI(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1"),
        api_key="ollama",  # required by the client but not used by Ollama
    )
    response = await client.chat.completions.create(
        model=os.getenv("OLLAMA_MODEL", "mistral"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=400,
    )
    return _parse(response.choices[0].message.content.strip())


# ── public interface ──────────────────────────────────────────────────────────

_PROVIDERS = {
    "gemini": _analyze_gemini,
    "openai": _analyze_openai,
    "ollama": _analyze_ollama,
}


async def analyze(transcript: str, layer1: dict) -> list[TagSuggestion]:
    """Layer 2 — LLM enrichment using Layer 1 context. Provider set by LLM_PROVIDER env var."""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    fn = _PROVIDERS.get(provider)
    if fn is None:
        raise ValueError(f"Unknown LLM_PROVIDER '{provider}'. Valid options: gemini, openai, ollama")

    prompt = _build_prompt(transcript, layer1)
    try:
        return await fn(prompt)
    except Exception as e:
        logger.error("[%s] Layer 2 analysis failed: %s", provider, e)
        return []
