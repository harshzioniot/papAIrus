import re
import logging

logger = logging.getLogger(__name__)

_FILLERS = re.compile(r'\b(um+|uh+|hmm+|like|you know|i mean|basically|literally)\b', re.IGNORECASE)


def _clean(text: str) -> str:
    """Remove STT filler words that degrade NER accuracy."""
    return re.sub(r' +', ' ', _FILLERS.sub('', text)).strip()

_ner = None
_emotion = None


def load_models():
    global _ner, _emotion
    from transformers import pipeline

    logger.info("Loading NLP models...")

    _ner = pipeline(
        "ner",
        model="dslim/bert-base-NER",
        aggregation_strategy="simple",
    )
    _emotion = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=None,
    )

    logger.info("NLP models ready.")


def run(text: str) -> dict:
    """Layer 1 — fast, local inference. Returns context for GPT prompt."""
    if not text or not text.strip():
        return {"people": [], "emotion_hint": "neutral", "emotion_score": 0.0}

    # Strip STT fillers, then truncate to BERT's safe limit (~2000 chars ≈ 400 words)
    snippet = _clean(text)[:2000]

    # Named entity recognition — extract people only
    ner_results = _ner(snippet)
    people = list({
        e["word"].strip()
        for e in ner_results
        if e["entity_group"] == "PER" and e["score"] > 0.80
    })

    # Emotion — get dominant label as a hint for GPT
    emotion_results = _emotion(snippet)
    top = max(emotion_results[0], key=lambda x: x["score"])

    return {
        "people": people,
        "emotion_hint": top["label"],
        "emotion_score": round(top["score"], 3),
    }
