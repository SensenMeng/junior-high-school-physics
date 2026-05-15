# 初中物理知识检索系统

一个面向初中物理教学与复习场景的 RAG 项目：将教材内容按多粒度（章节 / 句子 / 关键词）向量化存储，提供语义检索与动态思维导图展示。

## 功能特性

- 📚 **多粒度知识库**：章节级、句子级、关键词级三层结构
- 🔎 **语义检索**：基于向量相似度召回教材相关内容
- 🧠 **动态思维导图**：按节点增量展开，支持知识点追踪
- 🏷️ **意图识别**：根据问题类型优先召回定义/公式/实验等内容
- 🧾 **教材导入脚本**：支持 PDF 拆分、句子抽取、关键词去重与入库

## 技术栈

- 后端：FastAPI、ChromaDB、Pydantic、jieba、pdfplumber
- 前端：React + TypeScript + Vite、AntV G6
- 向量模型：
  - 默认：本地 BGE（`backend/embedding.py`）
  - 可选：百川 Embedding API（`backend/embedding_baichuan.py`）
- 大模型接口：DeepSeek（用于意图识别/摘要能力）

## 项目结构

```text
junior-high-school-physics/
├── backend/
│   ├── main.py                 # FastAPI 入口
│   ├── routers/                # /api/search /api/graph 接口
│   ├── ingest.py               # 教材导入脚本
│   ├── text_processor.py       # PDF 解析与文本切分
│   ├── embedding*.py           # 向量模型实现
│   ├── database.py             # Chroma 集合管理
│   └── .env.example            # 环境变量示例
├── frontend/
│   ├── src/components/         # SearchBar / MindMap / ContentPanel
│   └── src/services/api.ts     # 前端 API 调用
├── start.bat                   # Windows 启动脚本（推荐）
└── start.sh                    # Bash 启动脚本
```

## 快速开始

### 1) 安装依赖

后端：

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

前端：

```bash
cd frontend
npm install
```

### 2) 配置环境变量

复制示例文件：

```bash
cd backend
cp .env.example .env
```

可配置项（节选）：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `BAICHUAN_API_KEY`
- `BAICHUAN_BASE_URL`
- `CHROMA_PERSIST_DIR`（默认 `../data/chroma_db`）

### 3) 导入教材 PDF

```bash
cd backend
python ingest.py <pdf_path> [教材名称] [--full] [--keywords-only]
```

示例：

```bash
python ingest.py "../data/textbooks/八上.pdf" "人教版物理2024八年级上册" --full
```

参数说明：

- 默认：仅导入章节摘要
- `--full`：导入章节 + 句子 + 关键词
- `--keywords-only`：仅重导关键词

### 4) 启动服务

#### Windows（推荐）

```bat
start.bat
```

#### 手动启动（通用）

```bash
# 终端1：启动后端
cd backend
# Windows:
venv\Scripts\python -m uvicorn main:app --reload --host 0.0.0.0 --port 8765
# macOS/Linux:
venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8765

# 终端2：启动前端开发服务器
cd frontend
npm run dev
```

后端健康检查：`http://127.0.0.1:8765/api/health`

> 若已构建前端（`frontend/dist` 存在），后端会托管静态文件，可直接访问 `http://127.0.0.1:8765`。

## API 概览

- `POST /api/search`：多粒度检索
- `POST /api/llm`：调用大模型对话接口
- `POST /api/graph/root`：获取根节点
- `POST /api/graph/expand`：按节点增量展开
- `GET /api/health`：服务健康状态

接口文档：`http://127.0.0.1:8765/docs`

## 向量模型切换说明

当前 `backend/embedding.py` 为本地 BGE 版本，模型路径由该文件内 `_MODEL_PATH` 控制，请按你的机器环境自行设置。

若需使用百川 API 版本，请参考 `embedding_baichuan.py` 的实现并在 `.env` 中配置 `BAICHUAN_API_KEY`（建议通过配置化方式切换，避免手工改名文件）。

## 许可证

本项目基于仓库中的 [LICENSE](./LICENSE)。
