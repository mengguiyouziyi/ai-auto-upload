#!/bin/bash

# AI媒体平台开发环境启动脚本
# 作者: Claude Code
# 创建时间: 2025-10-14

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# 检查是否在正确的目录
check_directory() {
    if [[ ! -f "complete_backend.py" ]] || [[ ! -d "frontend" ]]; then
        print_error "请在ai-media-platform项目根目录下运行此脚本"
        exit 1
    fi
}

# 清理端口占用
cleanup_ports() {
    print_message "清理端口占用..."

    local ports=(5174 9000 3000)
    for port in "${ports[@]}"; do
        local pid=$(lsof -ti:$port 2>/dev/null || true)
        if [[ -n "$pid" ]]; then
            print_warning "端口 $port 被进程 $pid 占用，正在终止..."
            kill -9 $pid 2>/dev/null || true
            sleep 1
        else
            print_message "端口 $port 已清空"
        fi
    done
}

# 检查虚拟环境
check_venv() {
    if [[ ! -d "venv" ]]; then
        print_error "虚拟环境不存在，请先创建虚拟环境"
        print_message "运行: python -m venv venv"
        exit 1
    fi

    if [[ ! -f "venv/bin/activate" ]]; then
        print_error "虚拟环境激活脚本不存在"
        exit 1
    fi
}

# 检查后端依赖
check_backend_deps() {
    print_message "检查后端依赖..."
    source venv/bin/activate

    if ! python -c "import fastapi" 2>/dev/null; then
        print_error "FastAPI未安装，正在安装依赖..."
        pip install -r requirements.txt
    else
        print_message "后端依赖检查通过"
    fi
}

# 检查前端依赖
check_frontend_deps() {
    print_message "检查前端依赖..."
    cd frontend

    if [[ ! -d "node_modules" ]] || [[ ! -f "node_modules/vue/package.json" ]]; then
        print_warning "前端依赖未安装，正在安装..."
        npm install
    else
        print_message "前端依赖检查通过"
    fi

    cd ..
}

# 启动后端服务
start_backend() {
    print_message "启动后端服务..."
    source venv/bin/activate

    # 在后台启动后端
    python complete_backend.py > backend.log 2>&1 &
    BACKEND_PID=$!

    # 保存PID到文件
    echo $BACKEND_PID > .backend.pid

    print_message "后端服务已启动 (PID: $BACKEND_PID)"

    # 等待后端启动
    local retry_count=0
    local max_retries=10

    while [[ $retry_count -lt $max_retries ]]; do
        if curl -s http://localhost:9000/health > /dev/null 2>&1; then
            print_message "✅ 后端服务启动成功!"
            break
        fi

        print_warning "等待后端服务启动... ($((retry_count + 1))/$max_retries)"
        sleep 2
        ((retry_count++))
    done

    if [[ $retry_count -eq $max_retries ]]; then
        print_error "后端服务启动超时，请检查日志: tail -f backend.log"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
}

# 启动前端服务
start_frontend() {
    print_message "启动前端服务..."
    cd frontend

    # 在后台启动前端
    npm run dev > ../frontend.log 2>&1 &
    FRONTEND_PID=$!

    # 保存PID到文件
    echo $FRONTEND_PID > ../.frontend.pid

    print_message "前端服务已启动 (PID: $FRONTEND_PID)"

    # 等待前端启动
    local retry_count=0
    local max_retries=15

    while [[ $retry_count -lt $max_retries ]]; do
        if curl -s http://localhost:5174/ > /dev/null 2>&1; then
            print_message "✅ 前端服务启动成功!"
            break
        fi

        print_warning "等待前端服务启动... ($((retry_count + 1))/$max_retries)"
        sleep 2
        ((retry_count++))
    done

    if [[ $retry_count -eq $max_retries ]]; then
        print_error "前端服务启动超时，请检查日志: tail -f frontend.log"
        kill $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi

    cd ..
}

# 显示服务信息
show_service_info() {
    print_header "🎉 AI媒体平台启动完成!"

    echo -e "${GREEN}📱 前端地址:${NC} http://localhost:5174"
    echo -e "${GREEN}🔌 后端API:${NC} http://localhost:9000"
    echo -e "${GREEN}💚 健康检查:${NC} http://localhost:9000/health"
    echo -e "${GREEN}📋 API文档:${NC} http://localhost:9000/docs"
    echo ""
    echo -e "${YELLOW}进程信息:${NC}"
    echo -e "  后端PID: $BACKEND_PID"
    echo -e "  前端PID: $FRONTEND_PID"
    echo ""
    echo -e "${YELLOW}日志文件:${NC}"
    echo -e "  后端日志: backend.log"
    echo -e "  前端日志: frontend.log"
    echo ""
    echo -e "${RED}停止服务:${NC} ./stop-services.sh 或 Ctrl+C"
    echo ""
}

# 设置信号处理
setup_signal_handlers() {
    # 优雅退出函数
    graceful_shutdown() {
        print_message "接收到退出信号，正在优雅关闭服务..."

        if [[ -f ".backend.pid" ]]; then
            local backend_pid=$(cat .backend.pid)
            if kill -0 $backend_pid 2>/dev/null; then
                print_message "停止后端服务 (PID: $backend_pid)..."
                kill $backend_pid
            fi
            rm -f .backend.pid
        fi

        if [[ -f ".frontend.pid" ]]; then
            local frontend_pid=$(cat .frontend.pid)
            if kill -0 $frontend_pid 2>/dev/null; then
                print_message "停止前端服务 (PID: $frontend_pid)..."
                kill $frontend_pid
            fi
            rm -f .frontend.pid
        fi

        print_message "所有服务已停止"
        exit 0
    }

    # 注册信号处理
    trap graceful_shutdown INT TERM
}

# 主函数
main() {
    print_header "🚀 AI媒体平台开发环境启动"

    # 环境检查
    check_directory
    cleanup_ports
    check_venv
    check_backend_deps
    check_frontend_deps

    # 设置信号处理
    setup_signal_handlers

    # 启动服务
    start_backend
    start_frontend

    # 显示信息
    show_service_info

    # 保持脚本运行
    print_message "服务正在运行中，按 Ctrl+C 停止所有服务..."

    # 持续监控服务状态
    while true; do
        sleep 30

        # 检查后端服务
        if [[ -f ".backend.pid" ]]; then
            local backend_pid=$(cat .backend.pid)
            if ! kill -0 $backend_pid 2>/dev/null; then
                print_error "后端服务意外停止 (PID: $backend_pid)"
                print_message "尝试重启后端服务..."
                start_backend
            fi
        fi

        # 检查前端服务
        if [[ -f ".frontend.pid" ]]; then
            local frontend_pid=$(cat .frontend.pid)
            if ! kill -0 $frontend_pid 2>/dev/null; then
                print_error "前端服务意外停止 (PID: $frontend_pid)"
                print_message "尝试重启前端服务..."
                start_frontend
            fi
        fi
    done
}

# 运行主函数
main "$@"