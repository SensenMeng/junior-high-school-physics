"""DeepSeek API 封装"""
import httpx
from config import settings


async def chat_completion(
    messages: list[dict],
    model: str = "deepseek-chat",
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """调用 DeepSeek Chat API"""
    url = f"{settings.deepseek_base_url}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def generate_summary(text: str, max_length: int = 150) -> str:
    """为章节生成摘要"""
    messages = [
        {
            "role": "system",
            "content": "你是一个初中物理教材分析助手。请用100字以内为以下教材章节内容生成摘要，要求概括核心知识点，语言简洁易懂，适合初中生阅读。",
        },
        {"role": "user", "content": text},
    ]
    return await chat_completion(messages, max_tokens=max_length)


async def classify_intent(query: str) -> str:
    """判断用户查询的意图类型：definition, formula, experiment, concept"""
    messages = [
        {
            "role": "system",
            "content": (
                "判断用户问题的类型，只返回一个词：\n"
                '- definition: 用户问「是什么」「什么是」「定义」等\n'
                '- formula: 用户问公式、计算、表达式等\n'
                '- experiment: 用户问实验、探究、操作等\n'
                '- concept: 其他概念性问题\n'
                '只返回一个词，不要返回其他内容。'
            ),
        },
        {"role": "user", "content": query},
    ]
    result = await chat_completion(messages, max_tokens=20, temperature=0.1)
    return result.strip().lower()
