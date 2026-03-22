#!/bin/bash
# 爆款短视频拆解工具 v2.0 - 启动脚本

set -e

echo "======================================"
echo "  🎬 爆款短视频拆解工具 v2.0"
echo "  Dark Theme · Next.js + FastAPI"
echo "======================================"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  未找到 ffmpeg，正在安装..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y ffmpeg
    elif command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "❌ 请手动安装 ffmpeg: https://ffmpeg.org/download.html"
        exit 1
    fi
fi

# 检查 .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📝 请编辑 .env 填入 ANTHROPIC_API_KEY"
fi

mkdir -p static/tasks data

# ── Python 后端 ──────────────────────────────────────────────────────────────
echo ""
echo "📦 安装 Python 依赖..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt

echo "🚀 启动 FastAPI 后端 (port 8000)..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# 等待后端启动
sleep 2

# ── Next.js 前端 ─────────────────────────────────────────────────────────────
echo ""
echo "📦 安装 Node.js 依赖..."
cd frontend

if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请安装 Node.js 18+"
    exit 1
fi

npm install --silent

echo "🚀 启动 Next.js 前端 (port 3000)..."
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

cd ..

echo ""
echo "======================================"
echo "  ✅ 启动完成！"
echo "  🌐 浏览器打开: http://localhost:3000"
echo "  📡 API 文档:   http://localhost:8000/docs"
echo "======================================"
echo ""
echo "  按 Ctrl+C 停止所有服务"
echo ""

# 等待 Ctrl+C
trap "echo ''; echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
