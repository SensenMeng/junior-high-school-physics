from pydantic import BaseModel
from typing import Optional


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    node_type: Optional[str] = None  # chapter, sentence, keyword


class SearchResult(BaseModel):
    id: str
    text: str
    score: float
    metadata: dict
    node_type: str  # chapter, sentence, keyword


class SearchResponse(BaseModel):
    results: list[SearchResult]
    query: str


class RootNodeRequest(BaseModel):
    query: str = ""


class ExpandNodeRequest(BaseModel):
    node_id: str
    node_type: str
    query: Optional[str] = None


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str  # definition, formula, experiment, concept, etc.
    children: list["GraphNode"] = []
    content: Optional[str] = None
    source: Optional[str] = None  # 教材原文
    expanded: bool = False


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[dict]


class LLMRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.3


class LLMResponse(BaseModel):
    content: str
