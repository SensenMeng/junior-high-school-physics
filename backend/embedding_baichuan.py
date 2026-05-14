"""百川 Embedding API 封装（含自动重试和限速）"""
import asyncio
import httpx
from config import settings

# 百川 API 单次请求最大输入条数
_MAX_BATCH_SIZE = 16  # API上限
_REQUEST_DELAY = 10   # 批次间延迟（秒），免费版约6次/分钟
_MAX_RETRIES = 5      # 最大重试次数


async def _call_embedding_api(texts: list[str]) -> list[list[float]]:
    """调用百川 Embedding API（含自动重试）"""
    url = f"{settings.baichuan_base_url}/v1/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.baichuan_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Baichuan-Text-Embedding",
        "input": texts,
    }

    for attempt in range(_MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 429:
                    wait = 2 ** attempt  # 指数退避: 1, 2, 4, 8, 16秒
                    print(f"    ⏳ 触发限频，等待 {wait}s 后重试 ({attempt+1}/{_MAX_RETRIES})")
                    await asyncio.sleep(wait)
                    continue
                resp.raise_for_status()
                data = resp.json()
                return [item["embedding"] for item in data["data"]]
        except httpx.TimeoutException:
            if attempt < _MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise

    raise Exception(f"Embedding API 请求失败（已重试{_MAX_RETRIES}次）")


async def get_embedding(text: str) -> list[float]:
    """获取单个文本的向量"""
    result = await _call_embedding_api([text])
    return result[0]


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """批量获取文本向量（自动分批+限速）"""
    all_embeddings = []
    total = len(texts)
    for i in range(0, total, _MAX_BATCH_SIZE):
        batch = texts[i : i + _MAX_BATCH_SIZE]
        batch_embeddings = await _call_embedding_api(batch)
        all_embeddings.extend(batch_embeddings)
        if i + _MAX_BATCH_SIZE < total:
            print(f"    ⏸  等待 {_REQUEST_DELAY}s 避免限频...")
            await asyncio.sleep(_REQUEST_DELAY)
    return all_embeddings
