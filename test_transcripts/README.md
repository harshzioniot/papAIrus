# Test transcripts

Ten journal entries designed to produce a **well-connected** knowledge graph.

## How to use
1. Start backend + frontend (see QUICK_START.md).
2. Open `http://localhost:3000/record`.
3. For each `entry_NN.txt`, paste the body into the textarea, hit **Save entry**, wait ~3s for the background pipeline.
4. Repeat in order (01 → 10). Order matters for trend detection (`/graph/insights`).
5. Open `/graph` to see the network, `/digest` for weekly insights, `/chat` to talk to it.

## Why these specifically
Recurring entities are seeded across entries so edges actually form:

| Entity | Type | Appears in |
|---|---|---|
| Sarah | person | 01, 03, 06, 09 |
| Marcus | person | 02, 05, 08, 10 |
| Mom | person | 04, 07 |
| anxiety | emotion | 01, 03, 06, 09 |
| relief / calm | emotion | 02, 05, 08, 10 |
| project deadline | theme | 01, 03, 06, 09 |
| sleep | theme/habit | 01, 04, 07 |
| running | habit | 02, 05, 08, 10 |
| coffee | habit | 01, 03, 06 |
| office | place | 01, 03, 06, 09 |
| gym | place | 02, 05, 08, 10 |
| quit coffee | decision | 03 |
| started running | decision | 02 |
| better sleep | outcome | 05, 08 |

Two clusters should emerge: a **stress cluster** (Sarah / office / anxiety / project / coffee) and a **recovery cluster** (Marcus / gym / running / relief / better sleep). Mom bridges the two via family/sleep entries.
