"""初中物理知识检索系统 - FastAPI 主入口"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config import settings
from routers import search, graph


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    print(f"[启动] {settings.app_title} v{settings.app_version} 启动中...")
    # 检查API Key
    if not settings.deepseek_api_key:
        print("[警告] 未设置 DEEPSEEK_API_KEY，请在 .env 文件中配置")
    if not settings.baichuan_api_key:
        print("[警告] 未设置 BAICHUAN_API_KEY，请在 .env 文件中配置")
    yield
    # 关闭时
    print("[关闭] 服务关闭")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS 允许前端跨域访问（托管模式和开发模式）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(search.router, prefix="/api", tags=["搜索"])
app.include_router(graph.router, prefix="/api", tags=["思维导图"])


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "deepseek_configured": bool(settings.deepseek_api_key),
        "baichuan_configured": bool(settings.baichuan_api_key),
    }


# 托管前端静态文件（直接访问 http://localhost:8765 即可使用）
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
    print(f"[前端] 托管模式: http://localhost:8765")
else:
    print(f"[前端] 未找到构建文件 ({_frontend_dir})，请先 cd frontend && npm run build")
