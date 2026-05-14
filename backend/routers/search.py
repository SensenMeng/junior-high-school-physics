"""搜索接口：RAG 多粒度检索"""
from fastapi import APIRouter, HTTPException, Query
from models import SearchRequest, SearchResponse, SearchResult, LLMRequest, LLMResponse
from database import get_chapter_collection, get_sentence_collection, get_keyword_collection
from llm import classify_intent
import uuid

router = APIRouter()


def _search_collection(collection, query_embedding, top_k: int, where: dict = None):
    """在指定集合中搜索"""
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": top_k,
    }
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    """多粒度 RAG 搜索"""
    from embedding import get_embedding

    # 1. 获取查询向量
    query_vector = await get_embedding(req.query)

    # 2. 判断意图类型（可选过滤）
    intent = None
    if not req.node_type:
        try:
            intent = await classify_intent(req.query)
        except Exception:
            intent = None

    # 3. 多集合搜索
    all_results = []
    collections = {
        "chapter": get_chapter_collection(),
        "sentence": get_sentence_collection(),
        "keyword": get_keyword_collection(),
    }

    for node_type, collection in collections.items():
        if req.node_type and req.node_type != node_type:
            continue
        try:
            # 如果判断出意图，在句子级按类型过滤
            where = None
            if node_type == "sentence" and intent and intent != "concept":
                where = {"type": intent}

            results = _search_collection(
                collection, query_vector,
                top_k=max(3, req.top_k // len(collections)),
                where=where,
            )
            ids = results["ids"][0] if results["ids"] else []
            distances = results["distances"][0] if results["distances"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []
            documents = results["documents"][0] if results["documents"] else []

            for i in range(len(ids)):
                all_results.append(SearchResult(
                    id=ids[i],
                    text=documents[i] if i < len(documents) else "",
                    score=1.0 - distances[i] if i < len(distances) else 0.0,
                    metadata=metadatas[i] if i < len(metadatas) else {},
                    node_type=node_type,
                ))
        except Exception as e:
            print(f"搜索集合 {node_type} 失败: {e}")
            continue

    # 4. 按分数排序
    all_results.sort(key=lambda r: r.score, reverse=True)
    all_results = all_results[: req.top_k]

    return SearchResponse(results=all_results, query=req.query)


@router.post("/llm", response_model=LLMResponse)
async def call_llm(req: LLMRequest):
    """调用 DeepSeek 大模型"""
    from llm import chat_completion

    messages = []
    if req.system_prompt:
        messages.append({"role": "system", "content": req.system_prompt})
    messages.append({"role": "user", "content": req.prompt})

    content = await chat_completion(messages, temperature=req.temperature)
    return LLMResponse(content=content)
