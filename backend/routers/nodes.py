from typing import Optional
from fastapi import APIRouter, HTTPException, status

from models import Node
from schemas import NodeOut, NodeCreate

router = APIRouter(prefix="/nodes", tags=["nodes"])

TYPE_COLORS = {
    "emotion": "#c4bff5",
    "person":  "#b8d0f5",
    "theme":   "#9fd8c4",
    "habit":   "#f5c878",
}


@router.get("", response_model=list[NodeOut])
async def list_nodes(type: Optional[str] = None):
    q = Node.find()
    if type:
        q = Node.find(Node.type == type)
    nodes = await q.sort(Node.name).to_list()
    return [NodeOut(id=str(n.id), name=n.name, type=n.type, color_hex=n.color_hex) for n in nodes]


@router.post("", response_model=NodeOut, status_code=status.HTTP_201_CREATED)
async def create_node(payload: NodeCreate):
    valid = {"emotion", "person", "theme", "habit"}
    if payload.type not in valid:
        raise HTTPException(status_code=422, detail=f"type must be one of {valid}")

    existing = await Node.find_one(Node.name == payload.name, Node.type == payload.type)
    if existing:
        return NodeOut(id=str(existing.id), name=existing.name, type=existing.type, color_hex=existing.color_hex)

    color = payload.color_hex or TYPE_COLORS.get(payload.type, "#cccccc")
    node = Node(name=payload.name, type=payload.type, color_hex=color)
    await node.insert()
    return NodeOut(id=str(node.id), name=node.name, type=node.type, color_hex=node.color_hex)
