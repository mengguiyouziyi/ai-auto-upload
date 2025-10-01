# AI Auto Upload

基于 social-auto-upload 项目的人工智能自媒体自动发布系统

## 项目结构

- **social-auto-upload**: 多平台视频自动上传核心模块 (Git Submodule)
- **spider**: 爬虫相关模块 - 数据采集、内容抓取
- **llm**: 大语言模型相关模块 - 文本生成、内容创作
- **llmvl**: 多模态大模型相关模块 - 文生视频、图生视频

## 功能特性

- 支持多平台自动上传 (抖音、B站、小红书、快手、视频号、百家号、TikTok)
- AI 内容生成与发布
- 智能化媒体管理

## 快速开始

1. 初始化子模块：
   ```bash
   git submodule update --init --recursive
   ```

2. 配置 social-auto-upload：
   ```bash
   cd social-auto-upload
   pip install -r requirements.txt
   cp conf.example.py conf.py
   # 配置 conf.py 中的相关参数
   ```

3. 启动服务：
   ```bash
   cd social-auto-upload
   python sau_backend.py &  # 后端服务
   cd sau_frontend
   npm install && npm run dev  # 前端服务
   ```

## 开发计划

- [ ] 集成 AI 内容生成功能
- [ ] 开发智能爬虫模块
- [ ] 集成多模态大模型
- [ ] 实现全自动化内容生产流程
