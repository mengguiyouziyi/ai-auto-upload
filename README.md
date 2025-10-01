# 🤖 AI Auto Upload - 智能自媒体自动发布系统

<div align="center">

![AI Auto Upload](https://img.shields.io/badge/AI-Auto%20Upload-blue?style=for-the-badge&logo=artificial-intelligence)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge&logo=python)
![Vue.js](https://img.shields.io/badge/vue.js-3.x-green?style=for-the-badge&logo=vue.js)

**基于 social-auto-upload 的 AI 增强版自媒体运营系统**

一键发布到多个平台 · AI 内容生成 · 智能化管理

[🚀 快速开始](#-快速开始) • [📖 文档](#-文档) • [🤝 贡献](#-贡献) • [⭐ Star](https://github.com/mengguiyouziyi/ai-auto-upload)

</div>

## 📋 项目概述

AI Auto Upload 是一个功能强大的自媒体自动化运营系统，基于成熟的 [social-auto-upload](https://github.com/dreammis/social-auto-upload) 项目，集成 AI 技术实现内容创作、智能调度和多平台自动发布。

### ✨ 核心特性

- 🎯 **多平台支持**: 抖音、B站、小红书、快手、视频号、百家号、TikTok
- 🤖 **AI 内容生成**: 智能文案创作、标题优化、内容策划
- 🕷️ **智能爬虫**: 热点追踪、内容采集、数据分析
- 🎨 **多模态 AI**: 文生视频、图生视频、智能配音
- 📊 **数据化管理**: 发布统计、效果分析、智能调度
- 🌐 **Web 管理界面**: 现代化的 Vue.js 前端界面

### 🏗️ 项目架构

```
ai-auto-upload/
├── 📁 social-auto-upload/     # 核心：多平台视频上传模块 (Git Submodule)
├── 📁 spider/                 # 爬虫模块：数据采集与内容抓取
├── 📁 llm/                    # 大语言模型：文本生成与智能创作
├── 📁 llmvl/                  # 多模态模型：文生视频、图生视频
├── 📄 .gitmodules             # Git 子模块配置
└── 📄 README.md               # 项目文档
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- Chromium/Firefox 浏览器
- 8GB+ RAM (推荐)

### 安装步骤

1. **克隆项目**
   ```bash
   git clone https://github.com/mengguiyouziyi/ai-auto-upload.git
   cd ai-auto-upload
   ```

2. **初始化子模块**
   ```bash
   git submodule update --init --recursive
   ```

3. **配置核心模块**
   ```bash
   cd social-auto-upload
   pip install -r requirements.txt
   cp conf.example.py conf.py
   # 编辑 conf.py 配置文件
   ```

4. **安装浏览器驱动**
   ```bash
   playwright install chromium
   ```

5. **初始化数据库**
   ```bash
   cd db
   python createTable.py
   ```

6. **启动服务**
   ```bash
   # 启动后端服务 (端口 5409)
   python sau_backend.py &

   # 启动前端服务 (端口 5173)
   cd sau_frontend
   npm install
   npm run dev
   ```

7. **访问系统**
   - 前端界面: http://localhost:5173
   - 后端 API: http://localhost:5409

## 📖 详细文档

### 🎯 支持的平台

| 平台 | 状态 | 功能 | Cookie 获取 |
|------|------|------|------------|
| 抖音 | ✅ | 视频上传、定时发布 | [获取教程](social-auto-upload/examples/get_douyin_cookie.py) |
| B站 | ✅ | 视频上传、封面设置 | [获取教程](social-auto-upload/examples/get_bilibili_cookie.py) |
| 小红书 | ✅ | 图文发布、视频上传 | [获取教程](social-auto-upload/examples/get_xiaohongshu_cookie.py) |
| 快手 | ✅ | 视频上传、定时发布 | [获取教程](social-auto-upload/examples/get_kuaishou_cookie.py) |
| 视频号 | ✅ | 视频上传、文案发布 | [获取教程](social-auto-upload/examples/get_tencent_cookie.py) |
| 百家号 | ✅ | 视频上传、文章发布 | [获取教程](social-auto-upload/examples/get_baijiahao_cookie.py) |
| TikTok | ✅ | 国际版抖音支持 | [获取教程](social-auto-upload/examples/get_tk_cookie.py) |

### 🕷️ Spider 模块 (爬虫)

功能特性：
- 🔥 热点内容追踪
- 📊 数据采集与分析
- 🎯 关键词监控
- 📱 平台趋势分析

开发中功能：
- [ ] 自动化内容采集
- [ ] 智能内容分类
- [ ] 竞品分析工具
- [ ] 数据可视化

### 🧠 LLM 模块 (大语言模型)

功能特性：
- ✍️ 智能文案生成
- 🏷️ 标题优化建议
- 📝 内容创意策划
- 💬 评论区自动回复

计划集成模型：
- [ ] OpenAI GPT 系列
- [ ] Claude
- [ ] 本地大模型 (LLaMA, ChatGLM)
- [ ] 国内大模型 (文心一言、通义千问)

### 🎨 LLMVL 模块 (多模态)

功能特性：
- 🎬 文生视频 (Text-to-Video)
- 🖼️ 图生视频 (Image-to-Video)
- 🎙️ 智能配音合成
- 🎵 背景音乐生成

技术栈：
- [ ] Stable Video Diffusion
- [ ] Pika/Luma AI
- [ ] Runway ML
- [ ] 本地部署方案

## 🔧 配置指南

### 基础配置

1. **复制配置文件**
   ```bash
   cp social-auto-upload/conf.example.py social-auto-upload/conf.py
   ```

2. **编辑配置**
   ```python
   # social-auto-upload/conf.py

   # Chrome 浏览器路径
   LOCAL_CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

   # 上传配置
   UPLOAD_CONFIG = {
       "douyin": {
           "enable": True,
           "cookie_file": "cookiesFile/douyin_uploader/account.json"
       },
       # ... 其他平台配置
   }
   ```

3. **创建必要目录**
   ```bash
   mkdir -p cookiesFile videoFile
   ```

### Cookie 配置

每个平台都需要登录后的 Cookie 信息：

```bash
# 获取抖音 Cookie
python social-auto-upload/examples/get_douyin_cookie.py

# 获取 B站 Cookie
python social-auto-upload/examples/get_bilibili_cookie.py
```

## 📊 API 接口

### 后端 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/upload` | POST | 上传视频到指定平台 |
| `/api/accounts` | GET | 获取账号列表 |
| `/api/schedule` | POST | 创建定时发布任务 |
| `/api/status` | GET | 获取系统状态 |

### 前端页面

- 🏠 **仪表板**: 系统概览、统计数据
- 📱 **账号管理**: 多平台账号配置
- 📁 **素材管理**: 视频、图片、文案管理
- 🚀 **发布中心**: 一键发布、批量操作
- ⏰ **定时任务**: 智能调度、自动化发布

## 🛠️ 开发指南

### 本地开发环境

1. **后端开发**
   ```bash
   cd social-auto-upload
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **前端开发**
   ```bash
   cd social-auto-upload/sau_frontend
   npm install
   npm run dev
   ```

3. **模块开发**
   ```bash
   # 开发爬虫模块
   cd spider
   pip install -r requirements.txt

   # 开发 LLM 模块
   cd llm
   pip install -r requirements.txt
   ```

### 贡献指南

我们欢迎所有形式的贡献！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 🤝 社区与支持

- 🐛 **Bug 反馈**: [Issues](https://github.com/mengguiyouziyi/ai-auto-upload/issues)
- 💡 **功能建议**: [Discussions](https://github.com/mengguiyouziyi/ai-auto-upload/discussions)
- 📧 **联系交流**: 欢迎提交 Issue 或 Discussion

## 📜 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [social-auto-upload](https://github.com/dreammis/social-auto-upload) - 核心多平台上传功能
- [Playwright](https://playwright.dev/) - 浏览器自动化框架
- [Vue.js](https://vuejs.org/) - 前端框架
- [Flask](https://flask.palletsprojects.com/) - 后端框架

## 🌟 Star History

如果这个项目对你有帮助，请给我们一个 ⭐ Star！

[![Star History Chart](https://api.star-history.com/svg?repos=mengguiyouziyi/ai-auto-upload&type=Date)](https://star-history.com/#mengguiyouziyi/ai-auto-upload&Date)

---

<div align="center">

**🚀 让 AI 助力你的自媒体创作之旅！**

[![GitHub stars](https://img.shields.io/github/stars/mengguiyouziyi/ai-auto-upload?style=social)](https://github.com/mengguiyouziyi/ai-auto-upload/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/mengguiyouziyi/ai-auto-upload?style=social)](https://github.com/mengguiyouziyi/ai-auto-upload/network/members)
[![GitHub issues](https://img.shields.io/github/issues/mengguiyouziyi/ai-auto-upload)](https://github.com/mengguiyouziyi/ai-auto-upload/issues)

</div>