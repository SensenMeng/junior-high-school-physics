"""Chroma 向量数据库操作"""
import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.errors import NotFoundError
from config import settings

# 确保持久化目录存在
os.makedirs(settings.chroma_persist_dir, exist_ok=True)

_client = None


def get_client() -> chromadb.Client:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_or_create_collection(name: str):
    """获取或创建集合"""
    client = get_client()
    try:
        return client.get_collection(name)
    except (ValueError, NotFoundError, chromadb.errors.InvalidCollectionException):
        return client.create_collection(name)


# 三粒度集合名称
COLLECTION_CHAPTER = "physics_chapters"  # 章节级
COLLECTION_SENTENCE = "physics_sentences"  # 句子级
COLLECTION_KEYWORD = "physics_keywords"  # 关键词级


def get_chapter_collection():
    return get_or_create_collection(COLLECTION_CHAPTER)


def get_sentence_collection():
    return get_or_create_collection(COLLECTION_SENTENCE)


def get_keyword_collection():
    return get_or_create_collection(COLLECTION_KEYWORD)
