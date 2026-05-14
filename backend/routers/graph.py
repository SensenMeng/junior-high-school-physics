"""思维导图接口：动态节点展开"""
from fastapi import APIRouter, HTTPException, Body
from models import ExpandNodeRequest, GraphNode, GraphResponse, RootNodeRequest
from database import get_chapter_collection, get_sentence_collection, get_keyword_collection
from llm import generate_summary

router = APIRouter()


@router.post("/graph/expand", response_model=GraphResponse)
async def expand_node(req: ExpandNodeRequest):
    """按关键词增量展开思维导图节点"""
    from embedding import get_embedding

    query = req.query or req.node_id
    query_vector = await get_embedding(query)

    nodes = []
    edges = []

    # 先从句子级检索
    sentence_col = get_sentence_collection()
    try:
        results = sentence_col.query(
            query_embeddings=[query_vector],
            n_results=8,
        )
        ids = results["ids"][0] if results["ids"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        documents = results["documents"][0] if results["documents"] else []

        seen_types = set()
        for i in range(len(ids)):
            meta = metadatas[i] if i < len(metadatas) else {}
            doc = documents[i] if i < len(documents) else ""
            doc_type = meta.get("type", "concept")

            type_key = f"{doc_type}_{i // 2}"
            if type_key in seen_types:
                continue
            seen_types.add(type_key)

            node_id = f"node_{ids[i]}"
            nodes.append(GraphNode(
                id=node_id,
                label=doc[:30] + "..." if len(doc) > 30 else doc,
                node_type=doc_type,
                content=doc,
                source=meta.get("source", ""),
                expanded=False,
            ))
            edges.append({
                "source": req.node_id,
                "target": node_id,
                "label": doc_type,
            })
    except Exception as e:
        print(f"句子级检索失败: {e}")

    # 如果句子级无结果（尚未导入），尝试从章节集合按标题检索子节
    if not nodes:
        chapter_col = get_chapter_collection()
        try:
            results = chapter_col.query(
                query_embeddings=[query_vector],
                n_results=10,
            )
            for i, ch_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                doc = results["documents"][0][i] if results["documents"] else ""
                title = meta.get("title", "")
                # 跳过与源节点同名的结果，避免自环
                if title == req.query or title == req.node_id:
                    continue
                node_id = f"ch_{ch_id}"
                nodes.append(GraphNode(
                    id=node_id,
                    label=title or doc[:30],
                    node_type="chapter",
                    content=doc,
                    source=meta.get("textbook", ""),
                    expanded=False,
                ))
                edges.append({
                    "source": req.node_id,
                    "target": node_id,
                    "label": "章节",
                })
        except Exception as e:
            print(f"章节级检索失败: {e}")

    return GraphResponse(nodes=nodes, edges=edges)


@router.post("/graph/root", response_model=GraphResponse)
async def get_root_nodes(req: RootNodeRequest):
    """获取根节点（首次加载）"""
    from embedding import get_embedding

    query = req.query

    # 用查询获取根节点的子节点
    if not query:
        # 如果没有查询，返回物理学的几大模块
        root_modules = [
            {"id": "力学", "label": "力学", "node_type": "module"},
            {"id": "热学", "label": "热学", "node_type": "module"},
            {"id": "光学", "label": "光学", "node_type": "module"},
            {"id": "电学", "label": "电学", "node_type": "module"},
            {"id": "声学", "label": "声学", "node_type": "module"},
            {"id": "运动与能量", "label": "运动与能量", "node_type": "module"},
        ]
        nodes = [GraphNode(**m) for m in root_modules]
        return GraphResponse(nodes=nodes, edges=[])

    # 有查询时，从章节和关键词检索
    query_vector = await get_embedding(query)
    chapter_col = get_chapter_collection()
    keyword_col = get_keyword_collection()

    nodes = []
    edges = []

    # 检索章节
    try:
        ch_results = chapter_col.query(
            query_embeddings=[query_vector],
            n_results=5,
        )
        for i, ch_id in enumerate(ch_results["ids"][0]):
            meta = ch_results["metadatas"][0][i] if ch_results["metadatas"] else {}
            doc = ch_results["documents"][0][i] if ch_results["documents"] else ""
            nodes.append(GraphNode(
                id=f"ch_{ch_id}",
                label=meta.get("title", doc[:30]),
                node_type="chapter",
                content=doc,
                source=meta.get("textbook", ""),
                expanded=False,
            ))
    except Exception:
        pass

    # 检索关键词作为叶子节点提示
    try:
        kw_results = keyword_col.query(
            query_embeddings=[query_vector],
            n_results=5,
        )
        for i, kw_id in enumerate(kw_results["ids"][0]):
            doc = kw_results["documents"][0][i] if kw_results["documents"] else ""
            nodes.append(GraphNode(
                id=f"kw_{kw_id}",
                label=doc,
                node_type="keyword",
                expanded=False,
            ))
    except Exception:
        pass

    return GraphResponse(nodes=nodes, edges=edges)
