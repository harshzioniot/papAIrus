from collections import defaultdict
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query
from beanie import PydanticObjectId

from models import Entry, Node
from schemas import GraphOut, GraphNode, GraphEdge

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphOut)
async def get_graph(
    type: Optional[str] = Query(None),
    since: Optional[str] = Query(None),
):
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
        except ValueError:
            pass

    # Fetch entries
    q = Entry.find()
    if since_dt:
        q = Entry.find(Entry.created_at >= since_dt)
    entries = await q.to_list()

    node_entry_count: dict[str, int] = defaultdict(int)
    edge_weight: dict[tuple[str, str], int] = defaultdict(int)

    for entry in entries:
        ids = entry.node_ids
        for nid in ids:
            node_entry_count[nid] += 1
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = tuple(sorted((ids[i], ids[j])))
                edge_weight[(a, b)] += 1

    # Fetch nodes
    if type:
        all_nodes = await Node.find(Node.type == type).to_list()
    else:
        all_nodes = await Node.find().to_list()

    if since_dt:
        relevant = set(node_entry_count.keys())
        all_nodes = [n for n in all_nodes if str(n.id) in relevant]

    graph_nodes = [
        GraphNode(
            id=str(n.id),
            name=n.name,
            type=n.type,
            color_hex=n.color_hex,
            entry_count=node_entry_count.get(str(n.id), 0),
        )
        for n in all_nodes
    ]

    visible = {str(n.id) for n in all_nodes}
    graph_edges = [
        GraphEdge(source=a, target=b, weight=w)
        for (a, b), w in edge_weight.items()
        if a in visible and b in visible
    ]

    return GraphOut(nodes=graph_nodes, edges=graph_edges)
