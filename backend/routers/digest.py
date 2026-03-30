from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query

from models import Entry, Node
from schemas import DigestOut, PersonMention, DayIntensity

router = APIRouter(prefix="/digest", tags=["digest"])

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

REFLECTIONS = [
    "You mention your manager every time you feel invisible. What would it look like to feel seen?",
    "You've felt anxious most days this week. What small thing helped you feel grounded, even briefly?",
    "Work stress keeps coming up. What's one boundary you could set next week?",
    "You mentioned feeling frustrated multiple times. What's underneath that feeling?",
    "Notice any patterns between your habits and your mood this week?",
]


def _week_bounds(week_str: Optional[str]) -> tuple[datetime, datetime]:
    base = datetime.utcnow()
    if week_str:
        try:
            base = datetime.fromisoformat(week_str)
        except ValueError:
            pass
    start = base - timedelta(days=base.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=7)


def _streak(entries: list[Entry]) -> int:
    if not entries:
        return 0
    dates = sorted({e.created_at.date() for e in entries}, reverse=True)
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i - 1] - dates[i]).days == 1:
            streak += 1
        else:
            break
    return streak


@router.get("", response_model=DigestOut)
async def get_digest(week: Optional[str] = Query(None)):
    week_start, week_end = _week_bounds(week)
    prev_start = week_start - timedelta(days=7)

    current = await Entry.find(Entry.created_at >= week_start, Entry.created_at < week_end).to_list()
    prev = await Entry.find(Entry.created_at >= prev_start, Entry.created_at < week_start).to_list()

    # Gather all node ids we need
    all_ids = {nid for e in current + prev for nid in e.node_ids}
    from beanie import PydanticObjectId
    nodes_list = await Node.find({"_id": {"$in": [PydanticObjectId(i) for i in all_ids]}}).to_list()
    node_map = {str(n.id): n for n in nodes_list}

    def emotion_counts(entries: list[Entry]) -> Counter:
        c: Counter = Counter()
        for e in entries:
            for nid in e.node_ids:
                n = node_map.get(nid)
                if n and n.type == "emotion":
                    c[n.name] += 1
        return c

    cur_emo = emotion_counts(current)
    prev_emo = emotion_counts(prev)

    top_emotion = cur_emo.most_common(1)[0][0] if cur_emo else None
    top_count = cur_emo[top_emotion] if top_emotion else 0
    prev_count = prev_emo[top_emotion] if top_emotion else 0
    mood_trend = round(((top_count - prev_count) / prev_count * 100) if prev_count else 0.0, 1)

    node_freq: Counter = Counter()
    for e in current:
        for nid in e.node_ids:
            n = node_map.get(nid)
            if n:
                node_freq[n.name] += 1
    most_conn = node_freq.most_common(1)[0] if node_freq else (None, 0)

    # Per-day
    day_buckets: dict[int, list[Entry]] = defaultdict(list)
    for e in current:
        day_buckets[e.created_at.weekday()].append(e)

    days_out = []
    for i, label in enumerate(DAYS):
        date = week_start + timedelta(days=i)
        day_emo: Counter = Counter()
        for e in day_buckets[i]:
            for nid in e.node_ids:
                n = node_map.get(nid)
                if n and n.type == "emotion":
                    day_emo[n.name] += 1
        dominant = day_emo.most_common(1)[0][0] if day_emo else "neutral"
        days_out.append(DayIntensity(
            day=label,
            date=date.date().isoformat(),
            count=sum(day_emo.values()),
            dominant_type=dominant,
        ))

    people: Counter = Counter()
    for e in current:
        for nid in e.node_ids:
            n = node_map.get(nid)
            if n and n.type == "person":
                people[n.name] += 1

    reflection = REFLECTIONS[week_start.isocalendar()[1] % len(REFLECTIONS)]

    return DigestOut(
        week_start=week_start.date().isoformat(),
        week_end=(week_end - timedelta(days=1)).date().isoformat(),
        top_emotion=top_emotion,
        top_emotion_count=top_count,
        mood_trend_pct=mood_trend,
        most_connected_node=most_conn[0],
        most_connected_count=most_conn[1],
        entry_count=len(current),
        best_streak=_streak(current),
        days=days_out,
        people=[PersonMention(name=n, count=c) for n, c in people.most_common(5)],
        reflection=reflection,
    )
