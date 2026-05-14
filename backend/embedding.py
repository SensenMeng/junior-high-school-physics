"""
BGE 本地 Embedding 版本（替换 embedding.py）
使用 bge-large-zh-v1.5 本地模型，免费，数据不出校园

用法：把这个文件重命名为 embedding.py 即可

支持从本地路径加载模型（避免从 HuggingFace 在线下载）
如果学校网慢，可以在有网环境先下载好模型，然后拷贝到本地路径
"""
from sentence_transformers import SentenceTransformer
import torch

# 模型路径配置
# 如果 BGE_MODEL_PATH 环境变量设置了，从本地路径加载
# 否则从 HuggingFace 在线下载（首次需要联网）
import os

# 本地模型路径（防止网络不好时去 HuggingFace 验证）
_MODEL_PATH = "D:/bge-large-zh-v1.5"

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"BGE 使用设备: {device}")
print(f"BGE 模型路径: {_MODEL_PATH}")

model = SentenceTransformer(_MODEL_PATH, device=device)


async def get_embedding(text: str) -> list[float]:
    """获取单个文本的向量"""
    return model.encode(text, convert_to_numpy=True).tolist()


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """批量获取文本向量（本地模型，不限速不限量）"""
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    return embeddings.tolist()
