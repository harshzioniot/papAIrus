"""
Seed MongoDB with sample entries and nodes.
  python seed.py
"""
import asyncio
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from models import Entry, Node

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "papairus")

NODES_DATA = [
    ("anxious",     "emotion", "#c4bff5"),
    ("frustrated",  "emotion", "#f5b8b8"),
    ("calm",        "emotion", "#9fd8c4"),
    ("low mood",    "emotion", "#f5b8b8"),
    ("hopeful",     "emotion", "#9fd8c4"),
    ("manager",     "person",  "#b8d0f5"),
    ("Rohan",       "person",  "#9fd8c4"),
    ("Shreya",      "person",  "#f5c878"),
    ("work stress", "theme",   "#9fd8c4"),
    ("sleep",       "theme",   "#c4bff5"),
    ("goals",       "theme",   "#9fd8c4"),
    ("no run",      "habit",   "#f5c878"),
    ("gym",         "habit",   "#9fd8c4"),
    ("late nights", "habit",   "#f5c878"),
]

ENTRIES_DATA = [
    (0,  "Had a really rough meeting today, my manager kept cutting me off and I just felt so invisible the whole time...",
         ["anxious", "frustrated", "work stress", "manager"]),
    (1,  "Couldn't sleep again. Stayed up till 2am scrolling. Feeling low today.",
         ["low mood", "sleep", "late nights"]),
    (2,  "Rohan and I had a great chat, felt genuinely seen for the first time in a while.",
         ["hopeful", "calm", "Rohan"]),
    (3,  "Another sprint review where my work got attributed to someone else. So frustrated.",
         ["frustrated", "work stress", "manager"]),
    (4,  "Skipped the gym again. Tried to justify it but deep down I know I'm avoiding things.",
         ["anxious", "no run", "low mood"]),
    (5,  "Had coffee with Shreya. Talked about switching teams. Feeling hopeful.",
         ["hopeful", "Shreya", "goals"]),
    (6,  "Presentation went okay. Manager actually nodded a few times. Small win.",
         ["calm", "work stress", "manager"]),
    (8,  "Really anxious about the performance review coming up. Can't focus.",
         ["anxious", "work stress", "manager"]),
    (9,  "Hit the gym! First time this week. Felt good after.",
         ["hopeful", "gym"]),
    (10, "Long day. Manager cancelled our 1:1 again. Feeling invisible.",
         ["frustrated", "work stress", "manager", "anxious"]),
    (11, "Slept 9 hours. Felt surprisingly okay today.",
         ["calm", "sleep"]),
    (12, "Rohan got promoted. Happy for him but also kind of sad.",
         ["low mood", "hopeful", "Rohan"]),
    (13, "Feeling stuck. Goals feel far away.",
         ["anxious", "low mood", "goals"]),
]


async def main():
    client = AsyncIOMotorClient(MONGO_URI)
    await init_beanie(database=client[DB_NAME], document_models=[Entry, Node])

    # Drop existing data for clean seed
    await Node.delete_all()
    await Entry.delete_all()

    # Insert nodes
    node_map: dict[str, Node] = {}
    for name, ntype, color in NODES_DATA:
        n = Node(name=name, type=ntype, color_hex=color)
        await n.insert()
        node_map[name] = n

    now = datetime.utcnow()
    for days_ago, transcript, node_names in ENTRIES_DATA:
        ts = now - timedelta(days=days_ago)
        ids = [str(node_map[n].id) for n in node_names if n in node_map]
        entry = Entry(transcript=transcript, created_at=ts, node_ids=ids)
        await entry.insert()

    print(f"✓ Seeded {len(NODES_DATA)} nodes and {len(ENTRIES_DATA)} entries into '{DB_NAME}'.")
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
