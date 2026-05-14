"""教材文本处理：PDF提取、三粒度切分"""
import re
import jieba
from typing import Optional


def extract_text_from_pdf(pdf_path: str) -> str:
    """从PDF提取纯文本（使用pdfplumber）"""
    import pdfplumber
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def _extract_pages(pdf_path: str) -> list[tuple[int, str]]:
    """逐页提取文本，返回 [(页码, 文本)] 列表"""
    import pdfplumber
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            t = page.extract_text() or ""
            pages.append((i, t))
    return pages


def _find_chapter_pages(pages: list[tuple[int, str]]) -> list[tuple[int, str, str]]:
    """检测每页第一个有意义的行，找出章节起始页

    返回 [(pdf页码, 章节名, 类型)]，类型为 chapter / section
    """
    # 同时支持中文数字和阿拉伯数字：第1节 / 第2节 / 第一章
    chapter_pat = re.compile(
        r"第\s*([一二三四五六七八九十]+)\s*章\s*(.+)"
    )
    section_pat = re.compile(
        r"第\s*([一二三四五六七八九十\d]+)\s*节\s*(.+)"
    )

    result = []
    # 确定正文起始页（跳过封面/版权/目录）
    content_start_idx = None
    for idx, text in pages:
        if not text.strip():
            continue
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        first_line = lines[0] if lines else ""
        # 找到"致同学们"或"科学之旅"就说明正文开始了
        if "致同学们" in first_line or "科学之旅" in first_line or "探索物理" in first_line:
            content_start_idx = idx
            break

    if content_start_idx is None:
        content_start_idx = 0

    for idx, text in pages:
        if idx < content_start_idx:
            continue
        if not text.strip():
            continue

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            continue
        first_line = lines[0]
        # 跳过只有页码的行
        if re.match(r"^\d+$", first_line):
            continue

        # 避免将含有"第X章"和页码的行当作章节开头（如TOC里的"第四章 光现象 68"）
        # 真正的章节开头页不应该在同一行出现页码（页码是页眉单独出现的）
        cm = chapter_pat.match(first_line)
        if cm:
            ch_num = cm.group(1)
            ch_name = cm.group(2).strip()
            title = f"第{ch_num}章 {ch_name}" if ch_name else f"第{ch_num}章"
            # 过滤：如果章节名后面跟数字（页码），可能是TOC残留
            if re.search(r"\d{2,}$", ch_name):
                continue
            result.append((idx, title.strip(), "chapter"))
            continue

        sm = section_pat.match(first_line)
        if sm:
            sec_num = sm.group(1)
            sec_name = sm.group(2).strip()
            title = f"第{sec_num}节 {sec_name}" if sec_name else f"第{sec_num}节"
            result.append((idx, title.strip(), "section"))

    return result


def split_into_chapters(full_text: str) -> list[dict]:
    """将教材文本按章和节拆分

    在pdfplumber逐页提取的基础上，检测章节边界，按页分组。
    """
    return split_pdf_by_chapters(None, full_text)


def split_pdf_by_chapters(pdf_path: str, full_text: str = "") -> list[dict]:
    """从pdf路径直接拆分章节（最可靠的方式）"""
    if pdf_path:
        pages = _extract_pages(pdf_path)
    else:
        # 降级：从全文解析
        return _simple_split(full_text)

    # 找章节边界
    boundaries = _find_chapter_pages(pages)

    # 按边界分组
    if not boundaries:
        return _simple_split("\n".join(t for _, t in pages))

    # 构建章节条目：每个 chapter/section 包含从它到下一个之间的页面内容
    result = []
    current_chapter = None

    for i, (page_idx, title, btype) in enumerate(boundaries):
        # 确定这个章节的结束页（下一个章节的前一页）
        end_page = len(pages)
        if i + 1 < len(boundaries):
            end_page = boundaries[i + 1][0]

        # 收集这个章节内的所有页文本
        section_texts = []
        for p in range(page_idx, end_page):
            _, txt = pages[p]
            if txt.strip():
                section_texts.append(txt.strip())

        combined = "\n".join(section_texts)
        if len(combined) < 20:
            continue

        if btype == "chapter":
            current_chapter = title

        result.append({
            "title": title,
            "text": combined,
            "type": btype,
            "chapter": current_chapter if btype == "section" else None,
        })

    return result


def _simple_split(full_text: str) -> list[dict]:
    """简单按章节标题切分（保底方案）"""
    lines = full_text.split("\n")
    chapters = []
    current_title = "正文"
    current_text = []
    pat = re.compile(r"第[一二三四五六七八九十]+[章节]\s+\S+")

    for line in lines:
        line = line.strip()
        if pat.match(line):
            if current_text:
                chapters.append({
                    "title": current_title,
                    "text": "\n".join(current_text),
                    "type": "section",
                    "chapter": None,
                })
                current_text = []
            current_title = line
        current_text.append(line)

    if current_text:
        chapters.append({
            "title": current_title,
            "text": "\n".join(current_text),
            "type": "section",
            "chapter": None,
        })
    return chapters


def extract_sentences(text: str) -> list[str]:
    """将文本拆分为完整句子

    方案B：不按\\n切分，只按句末标点（。！？；）切分，
    避免PDF换行导致句子断裂。同时过滤编号引用片段。
    """
    # 合并换行：PDF中的换行是版式换行，不是句子边界
    text = text.replace("\n", "").replace("\r", "")

    # 按句末标点切分（保留标点本身）
    parts = re.split(r"(?<=[。！？；])", text)

    result = []
    for s in parts:
        s = s.strip()
        if len(s) <= 5:
            continue
        # 排除纯编号引用（如图1.2-1、表2.1）
        if re.match(r"^[图表]\s*\d+[.．\-]\d+", s):
            continue
        result.append(s)

    return result


def extract_keywords(text: str) -> list[str]:
    """使用jieba提取关键词"""
    import jieba.posseg as pseg
    try:
        jieba.load_userdict("physics_dict.txt")
    except (FileNotFoundError, OSError):
        pass
    words = pseg.cut(text)
    keywords = []
    for word, pos in words:
        if pos.startswith(("n", "v", "x")) and len(word) >= 2:
            keywords.append(word)
    return list(set(keywords))


_DEFINITION_PATTERNS = [
    "是", "称为", "叫做", "定义为", "表示", "是指", "即", "就是",
    "等于", "的单位是", "的公式是", "的计算公式为",
]
_FORMULA_PATTERNS = ["公式", "＝", "=", "表达式", "关系式"]
_EXPERIMENT_PATTERNS = ["实验", "探究", "测量", "观察"]


def classify_sentence_type(sentence: str) -> str:
    """判断句子类型：definition, formula, experiment, concept"""
    if any(p in sentence for p in _DEFINITION_PATTERNS) and len(sentence) < 100:
        return "definition"
    if any(p in sentence for p in _FORMULA_PATTERNS) and ("＝" in sentence or "=" in sentence):
        return "formula"
    if any(p in sentence for p in _EXPERIMENT_PATTERNS):
        return "experiment"
    return "concept"
