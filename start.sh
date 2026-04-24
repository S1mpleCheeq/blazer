#!/bin/bash

# 获取脚本所在目录，确保从任意位置都能运行
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 启动多智能体调度系统..."
echo "📁 项目目录: $SCRIPT_DIR"

# ── 环境检查 ──────────────────────────────────────────────

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到Python3，请先安装: https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✔ Python $PYTHON_VERSION"

# 检查Node
if ! command -v node &> /dev/null; then
    echo "❌ 未找到Node.js，请先安装: https://nodejs.org/"
    exit 1
fi
NODE_VERSION=$(node -v)
echo "✔ Node.js $NODE_VERSION"

# 检查.env文件，不存在则自动创建并提示
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo ""
    echo "⚠️  已自动创建 backend/.env，请填入你的 DASHSCOPE_API_KEY："
    echo "    编辑文件: backend/.env"
    echo "    格式: DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx"
    echo ""
    read -p "填好后按 Enter 继续，或 Ctrl+C 退出..."
fi

# 验证API Key不为空
API_KEY=$(grep DASHSCOPE_API_KEY backend/.env | cut -d'=' -f2 | tr -d ' ')
if [ -z "$API_KEY" ] || [ "$API_KEY" = "your_api_key_here" ]; then
    echo "❌ 请在 backend/.env 中填入有效的 DASHSCOPE_API_KEY"
    exit 1
fi
echo "✔ API Key 已配置"

# ── 后端安装 ──────────────────────────────────────────────

echo ""
echo "📦 安装后端依赖..."
cd "$SCRIPT_DIR/backend"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  ✔ 虚拟环境创建完成"
fi

# 安装依赖
./venv/bin/pip install -q -r requirements.txt
echo "  ✔ 后端依赖安装完成"

# ── 前端安装 ──────────────────────────────────────────────

echo "📦 安装前端依赖..."
cd "$SCRIPT_DIR/frontend"
npm install --silent
echo "  ✔ 前端依赖安装完成"

# ── 启动服务 ──────────────────────────────────────────────

cd "$SCRIPT_DIR"

echo ""
echo "🔧 启动后端服务 (端口 8000)..."
cd "$SCRIPT_DIR/backend"
./venv/bin/uvicorn main:app --port 8000 &
BACKEND_PID=$!

# 等待后端就绪
sleep 2
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "❌ 后端启动失败，请检查错误信息"
    exit 1
fi
echo "  ✔ 后端已启动 (PID: $BACKEND_PID)"

echo "🎨 启动前端服务 (端口 5173)..."
cd "$SCRIPT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

sleep 1
echo "  ✔ 前端已启动 (PID: $FRONTEND_PID)"

# ── 完成 ──────────────────────────────────────────────────

echo ""
echo "╔══════════════════════════════════════╗"
echo "║      ✅ 系统启动成功！               ║"
echo "║                                      ║"
echo "║  🌐 前端: http://localhost:5173      ║"
echo "║  🔧 后端: http://localhost:8000      ║"
echo "║                                      ║"
echo "║  按 Ctrl+C 停止所有服务              ║"
echo "╚══════════════════════════════════════╝"

# 捕获Ctrl+C，优雅退出
trap "echo ''; echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '✔ 已停止'; exit 0" INT TERM

wait
