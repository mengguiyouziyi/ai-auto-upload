#!/bin/bash

# AI媒体平台服务停止脚本
# 作者: Claude Code
# 创建时间: 2025-10-14

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 停止通过PID文件启动的服务
stop_services_via_pid() {
    if [[ -f ".backend.pid" ]]; then
        local backend_pid=$(cat .backend.pid)
        if kill -0 $backend_pid 2>/dev/null; then
            print_message "停止后端服务 (PID: $backend_pid)..."
            kill $backend_pid
            sleep 2
            # 强制杀死如果还在运行
            if kill -0 $backend_pid 2>/dev/null; then
                print_warning "强制停止后端服务..."
                kill -9 $backend_pid
            fi
        else
            print_warning "后端服务进程 $backend_pid 已不存在"
        fi
        rm -f .backend.pid
    fi

    if [[ -f ".frontend.pid" ]]; then
        local frontend_pid=$(cat .frontend.pid)
        if kill -0 $frontend_pid 2>/dev/null; then
            print_message "停止前端服务 (PID: $frontend_pid)..."
            kill $frontend_pid
            sleep 2
            # 强制杀死如果还在运行
            if kill -0 $frontend_pid 2>/dev/null; then
                print_warning "强制停止前端服务..."
                kill -9 $frontend_pid
            fi
        else
            print_warning "前端服务进程 $frontend_pid 已不存在"
        fi
        rm -f .frontend.pid
    fi
}

# 停止通过端口查找的服务
stop_services_via_port() {
    print_message "检查并停止端口占用的服务..."

    local ports=(5174 9000 3000)
    for port in "${ports[@]}"; do
        local pids=$(lsof -ti:$port 2>/dev/null || true)
        if [[ -n "$pids" ]]; then
            for pid in $pids; do
                print_warning "停止占用端口 $port 的进程 $pid..."
                kill $pid 2>/dev/null || true
            done
            sleep 1

            # 强制杀死仍在运行的进程
            pids=$(lsof -ti:$port 2>/dev/null || true)
            if [[ -n "$pids" ]]; then
                for pid in $pids; do
                    print_warning "强制停止进程 $pid..."
                    kill -9 $pid 2>/dev/null || true
                done
            fi
        else
            print_message "端口 $port 没有被占用"
        fi
    done
}

# 停止PM2管理的服务
stop_pm2_services() {
    if command -v pm2 &> /dev/null; then
        print_message "检查PM2管理的服务..."
        if pm2 list | grep -q "ai-media-backend"; then
            print_message "停止PM2管理的后端服务..."
            pm2 stop ai-media-backend
            pm2 delete ai-media-backend
        fi
    fi
}

# 清理临时文件
cleanup_temp_files() {
    print_message "清理临时文件..."
    rm -f .backend.pid .frontend.pid
    rm -f backend.log frontend.log
}

# 主函数
main() {
    print_header "🛑 停止AI媒体平台服务"

    # 停止各种方式启动的服务
    stop_services_via_pid
    stop_services_via_port
    stop_pm2_services
    cleanup_temp_files

    print_message "✅ 所有服务已停止"
}

# 运行主函数
main "$@"