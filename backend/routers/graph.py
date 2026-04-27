from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query

from models import Entry, Node, Edge, NODE_COLOURS
from schemas import GraphOut, GraphNode, GraphEdge, InsightsOut, CentralNode, TrendNode, PathNode, NodeOut
from services import graph_service

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphOut)
async def get_graph(
    type: Optional[str] = Query(None),
    since: Optional[str] = Query(None),
):
    """
    Graph for visualisation. Nodes sized by entry_count; edges typed + weighted
    by how many times that pair appears in the Edge collection.
    """
    since_dt = None
    if since:
        try:
            parsed = datetime.fromisoformat(since)
            since_dt = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    # Node entry counts (how many entries mention each node)
    entry_q = Entry.find(Entry.created_at >= since_dt) if since_dt else Entry.find()
    entries = await entry_q.to_list()
    node_entry_count: dict[str, int] = defaultdict(int)
    for entry in entries:
        for nid in entry.node_ids:
            node_entry_count[nid] += 1

    # Typed edges from the Edge collection (weight = recurrence count)
    edge_q = Edge.find(Edge.timestamp >= since_dt) if since_dt else Edge.find()
    raw_edges = await edge_q.to_list()

    edge_agg: dict[tuple[str, str, str], int] = defaultdict(int)
    for e in raw_edges:
        edge_agg[(e.from_node_id, e.to_node_id, e.edge_type)] += 1

    # Nodes
    node_q = Node.find(Node.type == type) if type else Node.find()
    all_nodes = await node_q.to_list()

    if since_dt:
        relevant = set(node_entry_count.keys())
        all_nodes = [n for n in all_nodes if str(n.id) in relevant]

    visible = {str(n.id) for n in all_nodes}

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

    graph_edges = [
        GraphEdge(source=src, target=tgt, weight=w, edge_type=et)
        for (src, tgt, et), w in edge_agg.items()
        if src in visible and tgt in visible
    ]

    return GraphOut(nodes=graph_nodes, edges=graph_edges)


@router.get("/insights", response_model=InsightsOut)
async def get_insights(since: Optional[str] = Query(None)):
    """
    Graph algorithm results:
      - centrality: PageRank — most influential nodes
      - communities: clusters of related nodes
      - trending_up / trending_down: nodes growing or fading vs prev period
    """
    since_dt = None
    if since:
        try:
            parsed = datetime.fromisoformat(since)
            since_dt = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    nodes, edges = await graph_service.load(since=since_dt)
    G = graph_service.build_digraph(nodes, edges)

    centrality = graph_service.get_centrality(G)
    communities = graph_service.get_communities(G)
    trending = graph_service.get_trending(nodes, edges)

    return InsightsOut(
        centrality=[CentralNode(**c) for c in centrality],
        communities=[
            [
                NodeOut(
                    id=m["id"],
                    name=m["name"],
                    type=m["type"],
                    color_hex=NODE_COLOURS.get(m["type"], "#cccccc"),
                )
                for m in cluster
            ]
            for cluster in communities
        ],
        trending_up=[TrendNode(**t) for t in trending["up"]],
        trending_down=[TrendNode(**t) for t in trending["down"]],
    )


@router.get("/path", response_model=list[PathNode])
async def get_path(from_id: str = Query(...), to_id: str = Query(...)):
    """
    Shortest causal path between two nodes.
    Returns the chain of nodes connecting them, or [] if no path exists.
    """
    nodes, edges = await graph_service.load()
    G = graph_service.build_digraph(nodes, edges)
    path = graph_service.find_path(G, from_id, to_id)
    return [PathNode(**p) for p in path]
