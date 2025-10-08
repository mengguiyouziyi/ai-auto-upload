#!/bin/bash

# AI技术文章爬虫启动脚本

echo "🕷️  AI技术文章爬虫"
echo "=================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3"
    exit 1
fi

# 检查依赖
echo "🔍 检查依赖..."
if ! python3 -c "import requests, playwright, beautifulsoup4" &> /dev/null; then
    echo "❌ 缺少依赖，正在安装..."
    pip3 install -r requirements.txt

    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# 检查playwright浏览器
echo "🌐 检查浏览器驱动..."
if ! python3 -c "from playwright.async_api import async_playwright" &> /dev/null; then
    echo "⚠️  正在安装playwright浏览器..."
    python3 -m playwright install chromium
fi

# 创建必要的目录
mkdir -p data/raw data/processed logs

# 显示菜单
echo ""
echo "请选择操作:"
echo "1) 爬取所有网站"
echo "2) 爬取CSDN"
echo "3) 爬取掘金"
echo "4) 显示统计信息"
echo "5) 自定义爬取"
echo "6) 退出"
echo ""

read -p "请输入选项 (1-6): " choice

case $choice in
    1)
        echo "🚀 开始爬取所有网站..."
        python3 main.py
        ;;
    2)
        echo "🚀 开始爬取CSDN..."
        python3 main.py --site csdn
        ;;
    3)
        echo "🚀 开始爬取掘金..."
        python3 main.py --site juejin
        ;;
    4)
        echo "📊 显示统计信息..."
        python3 main.py --stats
        ;;
    5)
        echo "⚙️  自定义爬取..."

        # 选择网站
        echo "选择网站:"
        echo "1) CSDN"
        echo "2) 掘金"
        echo "3) 所有网站"
        read -p "请选择 (1-3): " site_choice

        site_arg=""
        case $site_choice in
            1) site_arg="--site csdn" ;;
            2) site_arg="--site juejin" ;;
            3) site_arg="" ;;
        esac

        # 输入关键词
        read -p "请输入关键词 (用空格分隔，直接回车使用默认): " keywords_input
        if [ -n "$keywords_input" ]; then
            keywords_arg="--keywords"
            # 将输入的字符串转换为参数数组
            IFS=' ' read -ra KEYWORDS <<< "$keywords_input"
        else
            keywords_arg=""
        fi

        # 输入页数
        read -p "请输入爬取页数 (默认3): " pages_input
        if [ -n "$pages_input" ]; then
            pages_arg="--pages $pages_input"
        else
            pages_arg="--pages 3"
        fi

        # 是否导出
        read -p "是否导出数据? (y/n): " export_choice
        if [ "$export_choice" = "y" ] || [ "$export_choice" = "Y" ]; then
            echo "选择导出格式:"
            echo "1) JSON"
            echo "2) CSV"
            read -p "请选择 (1-2): " format_choice

            case $format_choice in
                1) export_arg="--export json" ;;
                2) export_arg="--export csv" ;;
                *) export_arg="--export json" ;;
            esac
        else
            export_arg=""
        fi

        # 执行爬取
        echo "🚀 开始自定义爬取..."
        python3 main.py $site_arg $keywords_arg $pages_arg $export_arg
        ;;
    6)
        echo "👋 再见!"
        exit 0
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "✅ 爬取完成!"
echo "📁 数据保存在 data/ 目录"
echo "📋 日志保存在 logs/ 目录"