#!/bin/bash
# 初中物理知识检索系统 - 启动脚本

echo "🚀 启动初中物理知识检索系统..."
echo ""

# 获取脚本所在目录
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 启动后端
echo "📡 启动后端 (FastAPI)..."
cd "$DIR/backend"
"$DIR/backend/venv/Scripts/python" -m uvicorn main:app --reload --host 0.0.0.0 --port 8765 &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"

# 等待后端启动
sleep 2

# 启动前端
echo "🎨 启动前端 (React + Vite)..."
cd "$DIR/frontend"
npm run dev &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"

echo ""
echo "✅ 系统启动中!"
echo "   访问地址: http://localhost:8765"
echo "   API文档: http://localhost:8765/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待任一进程结束
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
