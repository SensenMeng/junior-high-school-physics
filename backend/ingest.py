"""
教材数据导入脚本
将PDF教材按三粒度切分 → 向量化 → 存入Chroma
（已优化：去掉DeepSeek摘要，纯本地+Embedding API，省时省钱）

用法: python ingest.py <pdf_path> [教材名称] [--full]
示例: python ingest.py path/to/八上.pdf "人教版物理2024八年级上册"
      python ingest.py path/to/八上.pdf "人教版物理2024八年级上册" --full   # 含句子和关键词
"""
import sys
import asyncio
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from text_processor import (
    extract_text_from_pdf,
    split_into_chapters,
    split_pdf_by_chapters,
    extract_sentences,
    extract_keywords,
    classify_sentence_type,
)
from embedding import get_embeddings
from database import (
    get_chapter_collection,
    get_sentence_collection,
    get_keyword_collection,
)


def _sanitize_metadata(md: dict) -> dict:
    """确保 metadata 所有值都是 Chroma 支持的类型（str/int/float/bool）"""
    cleaned = {}
    for k, v in md.items():
        if v is None:
            cleaned[k] = ""
        elif isinstance(v, (str, int, float, bool)):
            cleaned[k] = v
        else:
            cleaned[k] = str(v)
    return cleaned


async def ingest_pdf(pdf_path: str, textbook_name: str = "人教版物理2024", full: bool = False, keywords_only: bool = False):
    print(f"📖 开始处理教材: {textbook_name}")
    print(f"📄 PDF路径: {pdf_path}")
    if keywords_only:
        print(f"🔧 模式: 仅重新导入关键词")
    elif full:
        print(f"🔧 模式: 完整导入（含句子和关键词）")
    else:
        print(f"🔧 模式: 仅章节摘要（句子和关键词跳过）")

    # 1. 提取文本
    print("🔍 提取PDF文本...")
    full_text = extract_text_from_pdf(pdf_path)
    print(f"   提取到 {len(full_text)} 字符")

    # 2. 分章节（使用page-level检测，更精确）
    print("📑 拆分章节...")
    chapters = split_pdf_by_chapters(pdf_path, full_text)
    print(f"   共 {len(chapters)} 个章节/节")

    if not keywords_only:
        # 3. 处理章节级（用原文前80字作摘要，不调DeepSeek省时省钱）
        print("📚 处理章节级向量...")
    chapter_col = get_chapter_collection()
    chapter_data = []
    for ch in chapters:
        ch_id = str(uuid.uuid4())
        summary = ch["text"][:80] + "..." if len(ch["text"]) > 80 else ch["text"]
        chapter_data.append({
            "id": ch_id,
            "text": summary,
            "metadata": _sanitize_metadata({
                "title": ch["title"],
                "type": ch["type"],
                "chapter": ch.get("chapter"),
                "textbook": textbook_name,
                "source": ch["text"][:200],
            }),
        })

    if chapter_data:
        texts = [d["text"] for d in chapter_data]
        embeddings = await get_embeddings(texts)
        chapter_col.add(
            ids=[d["id"] for d in chapter_data],
            embeddings=embeddings,
            documents=[d["text"] for d in chapter_data],
            metadatas=[d["metadata"] for d in chapter_data],
        )
        print(f"   ✅ 已导入 {len(chapter_data)} 个章节摘要")

    # 4. 处理句子级
    if not keywords_only and full:
        print("📝 处理句子级向量...")
        sentence_col = get_sentence_collection()
        sentence_data = []
        for ch in chapters:
            sentences = extract_sentences(ch["text"])
            for s in sentences:
                s_id = str(uuid.uuid4())
                s_type = classify_sentence_type(s)
                sentence_data.append({
                    "id": s_id,
                    "text": s,
                    "metadata": _sanitize_metadata({
                        "type": s_type,
                        "chapter": ch.get("chapter") or ch["title"],
                        "section": ch["title"],
                        "textbook": textbook_name,
                    }),
                })

        if sentence_data:
            texts = [d["text"] for d in sentence_data]
            embeddings = await get_embeddings(texts)
            # 分批添加，避免 Chroma batch size 限制
            batch_size = 5000
            for i in range(0, len(sentence_data), batch_size):
                end = i + batch_size
                sentence_col.add(
                    ids=[d["id"] for d in sentence_data[i:end]],
                    embeddings=embeddings[i:end],
                    documents=[d["text"] for d in sentence_data[i:end]],
                    metadatas=[d["metadata"] for d in sentence_data[i:end]],
                )
        print(f"   ✅ 已导入 {len(sentence_data)} 个句子")
    elif not keywords_only:
        print("📝 处理句子级向量...（跳过，使用 --full 可开启）")
        sentence_data = []
    else:
        sentence_data = []

    # 5. 处理关键词级
    deduped = []
    if full or keywords_only:
        print("🔑 处理关键词级向量...")
        keyword_col = get_keyword_collection()
        keyword_entries = []
        for ch in chapters:
            kws = extract_keywords(ch["text"])
            for kw in kws:
                kw_id = str(uuid.uuid4())
                keyword_entries.append({
                    "id": kw_id,
                    "text": kw,
                    "metadata": _sanitize_metadata({
                        "keyword": kw,
                        "chapter": ch.get("chapter") or ch["title"],
                        "section": ch["title"],
                        "textbook": textbook_name,
                    }),
                })

        if keyword_entries:
            # 跨教材去重：检查Chroma中已有的关键词，避免重复
            existing_kws = set()
            try:
                all_kw = keyword_col.get(include=["documents"])
                if all_kw and all_kw["documents"]:
                    existing_kws = set(all_kw["documents"])
            except Exception:
                pass

            # 本教材内去重 + 跨教材去重
            kw_texts = [e["text"] for e in keyword_entries]
            cross_dedup = len(existing_kws & set(kw_texts))
            seen = {}
            for entry in keyword_entries:
                kw = entry["text"]
                if kw in existing_kws:
                    continue
                if kw not in seen:
                    seen[kw] = entry
            deduped = list(seen.values())
            inner_dedup = len(kw_texts) - len(deduped) - cross_dedup
            print(f"   🔗 关键词去重: {len(keyword_entries)} → {len(deduped)}（跨教材去重 {cross_dedup}，本教材去重 {inner_dedup} 个）")

            texts = [d["text"] for d in deduped]
            embeddings = await get_embeddings(texts)
            # 分批添加，避免 Chroma batch size 限制
            batch_size = 5000
            for i in range(0, len(deduped), batch_size):
                end = i + batch_size
                keyword_col.add(
                    ids=[d["id"] for d in deduped[i:end]],
                    embeddings=embeddings[i:end],
                    documents=[d["text"] for d in deduped[i:end]],
                    metadatas=[d["metadata"] for d in deduped[i:end]],
                )
        print(f"   ✅ 已导入 {len(deduped)} 个关键词（去重后）")
    elif not keywords_only:
        print("🔑 处理关键词级向量...（跳过，使用 --full 可开启）")
        keyword_entries = []
    else:
        keyword_entries = []

    print(f"\n🎉 教材处理完成!")
    ch_count = len(chapter_data) if not keywords_only else 0
    s_count = len(sentence_data) if not keywords_only else 0
    kw_count = len(deduped) if deduped else (len(keyword_entries) if keyword_entries else 0)
    print(f"   - 章节摘要: {ch_count} 条{'（跳过）' if keywords_only else ''}")
    print(f"   - 句子: {s_count} 条{'（跳过）' if keywords_only else ('（使用 --full 导入）' if full else '（跳过）')}")
    print(f"   - 关键词: {kw_count} 个{'（去重后）' if deduped else ('（跳过）' if keywords_only else '')}")


async def main():
    if len(sys.argv) < 2:
        print("用法: python ingest.py <pdf_path> [教材名称] [--full] [--keywords-only]")
        print("示例: python ingest.py ../data/textbooks/八上物理.pdf \"人教版物理2024八年级上册\"")
        print("      python ingest.py ../data/textbooks/八上物理.pdf \"人教版物理2024八年级上册\" --full")
        print("      python ingest.py ../data/textbooks/八上物理.pdf \"人教版物理2024八年级上册\" --keywords-only")
        return

    pdf_path = sys.argv[1]
    full = "--full" in sys.argv
    keywords_only = "--keywords-only" in sys.argv

    # 排除标记参数，取第一个非标记参数作教材名称
    skip_flags = {"--full", "--keywords-only"}
    textbook_name = "人教版物理2024"
    for arg in sys.argv[2:]:
        if arg not in skip_flags:
            textbook_name = arg
            break

    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return

    await ingest_pdf(pdf_path, textbook_name, full=full, keywords_only=keywords_only)


if __name__ == "__main__":
    asyncio.run(main())
