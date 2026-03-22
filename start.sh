#!/bin/bash
# 爆款短视频拆解工具 - 启动脚本

set -e

echo "======================================"
echo "  🎬 爆款短视频拆解工具"
echo "======================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.9+"
    exit 1
fi

# 检查 ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  未找到 ffmpeg，正在尝试安装..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get install -y ffmpeg
    elif command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "❌ 请手动安装 ffmpeg: https://ffmpeg.org/download.html"
        exit 1
    fi
fi

# 安装依赖
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

echo "📦 激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  未找到 .env 文件，从模板创建..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件，填入你的 API Key"
    echo "   nano .env"
    echo ""
fi

# 创建必要目录
mkdir -p static/{covers,keyframes,reports} uploads data

echo ""
echo "✅ 启动完成！"
echo "🌐 浏览器打开: http://localhost:8501"
echo ""

# 启动 Streamlit
streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.maxUploadSize 500 \
    --browser.gatherUsageStats false
