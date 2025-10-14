#!/bin/bash

# AI媒体平台健康检查脚本
# 作者: Claude Code
# 创建时间: 2025-10-14

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    local status=$1
    local message=$2

    if [[ $status == "OK" ]]; then
        echo -e "${GREEN}✅ $message${NC}"
    elif [[ $status == "WARNING" ]]; then
        echo -e "${YELLOW}⚠️  $message${NC}"
    elif [[ $status == "ERROR" ]]; then
        echo -e "${RED}❌ $message${NC}"
    else
        echo -e "${BLUE}ℹ️  $message${NC}"
    fi
}

check_backend() {
    print_status "INFO" "检查后端服务..."

    if curl -s http://localhost:9000/health > /dev/null 2>&1; then
        local response=$(curl -s http://localhost:9000/health)
        print_status "OK" "后端服务正常 (响应: $response)"
        return 0
    else
        print_status "ERROR" "后端服务无法访问"
        return 1
    fi
}

check_frontend() {
    print_status "INFO" "检查前端服务..."

    if curl -s http://localhost:5174/ > /dev/null 2>&1; then
        print_status "OK" "前端服务正常"
        return 0
    else
        print_status "ERROR" "前端服务无法访问"
        return 1
    fi
}

check_processes() {
    print_status "INFO" "检查进程状态..."

    local backend_running=false
    local frontend_running=false

    # 检查通过PID文件启动的进程
    if [[ -f ".backend.pid" ]]; then
        local backend_pid=$(cat .backend.pid)
        if kill -0 $backend_pid 2>/dev/null; then
            print_status "OK" "后端进程运行中 (PID: $backend_pid)"
            backend_running=true
        else
            print_status "WARNING" "后端PID文件存在但进程不存在"
        fi
    fi

    if [[ -f ".frontend.pid" ]]; then
        local frontend_pid=$(cat .frontend.pid)
        if kill -0 $frontend_pid 2>/dev/null; then
            print_status "OK" "前端进程运行中 (PID: $frontend_pid)"
            frontend_running=true
        else
            print_status "WARNING" "前端PID文件存在但进程不存在"
        fi
    fi

    # 检查端口占用
    local backend_port=$(lsof -ti:9000 2>/dev/null || true)
    local frontend_port=$(lsof -ti:5174 2>/dev/null || true)

    if [[ -n "$backend_port" ]] && [[ "$backend_running" == false ]]; then
        print_status "WARNING" "端口9000被其他进程占用 (PID: $backend_port)"
    fi

    if [[ -n "$frontend_port" ]] && [[ "$frontend_running" == false ]]; then
        print_status "WARNING" "端口5174被其他进程占用 (PID: $frontend_port)"
    fi
}

check_environment() {
    print_status "INFO" "检查环境配置..."

    # 检查Python版本
    if command -v python &> /dev/null; then
        local python_version=$(python --version 2>&1 | cut -d' ' -f2)
        print_status "OK" "Python版本: $python_version"
    else
        print_status "ERROR" "Python未安装"
    fi

    # 检查虚拟环境
    if [[ -d "venv" ]] && [[ -f "venv/bin/activate" ]]; then
        print_status "OK" "虚拟环境存在"
    else
        print_status "ERROR" "虚拟环境不存在"
    fi

    # 检查Node.js
    if command -v node &> /dev/null; then
        local node_version=$(node --version)
        print_status "OK" "Node.js版本: $node_version"
    else
        print_status "ERROR" "Node.js未安装"
    fi

    # 检查npm
    if command -v npm &> /dev/null; then
        local npm_version=$(npm --version)
        print_status "OK" "npm版本: $npm_version"
    else
        print_status "ERROR" "npm未安装"
    fi
}

check_dependencies() {
    print_status "INFO" "检查依赖文件..."

    if [[ -f "requirements.txt" ]]; then
        print_status "OK" "requirements.txt存在"
    else
        print_status "ERROR" "requirements.txt不存在"
    fi

    if [[ -f "frontend/package.json" ]]; then
        print_status "OK" "package.json存在"
    else
        print_status "ERROR" "package.json不存在"
    fi

    if [[ -f "complete_backend.py" ]]; then
        print_status "OK" "complete_backend.py存在"
    else
        print_status "ERROR" "complete_backend.py不存在"
    fi
}

show_summary() {
    echo ""
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}健康检查完成${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
    echo -e "${GREEN}服务地址:${NC}"
    echo -e "  前端: http://localhost:5174"
    echo -e "  后端: http://localhost:9000"
    echo -e "  API文档: http://localhost:9000/docs"
    echo ""
    echo -e "${YELLOW}如遇问题，请查看:${NC}"
    echo -e "  部署文档: DEPLOYMENT.md"
    echo -e "  快速开始: QUICK_START.md"
    echo ""
}

# 主函数
main() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}AI媒体平台健康检查${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""

    local exit_code=0

    # 执行各项检查
    check_environment
    check_dependencies
    check_processes
    check_backend || exit_code=1
    check_frontend || exit_code=1

    show_summary

    exit $exit_code
}

# 运行主函数
main "$@"