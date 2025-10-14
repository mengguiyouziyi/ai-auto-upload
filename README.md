# 🎯 AI媒体平台

<div align="center">

![AI Media Platform](https://img.shields.io/badge/AI-Media%20Platform-blue?style=for-the-the-badge&logo=artificial-intelligence)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Python](https://img.shields.io/badge/python-3.13+-blue?style=for-the-badge&logo=python)
![Vue.js](https://img.shields.io/badge/vue.js-3.x-green?style=for-the-badge&logo=vue.js)
![FastAPI](https://img.shields.io/badge/FastAPI-red?style=for-the-badge&logo=fastapi)

**现代化AI媒体内容创作与发布平台**

视频生成 · 内容优化 · 多平台发布 · 智能管理

[🚀 快速开始](#-快速开始) • [📖 文档](#-文档) • [🤝 贡献](#-贡献) • [⭐ Star](https://github.com/mengguiyouziyi/ai-auto-upload)

</div>

## 📋 项目概述

AI媒体平台是一个功能强大的AI驱动媒体内容创作与发布系统，集成先进的AI技术实现智能内容创作、自动化视频生成和多平台一键发布。基于FastAPI后端和Vue.js前端构建的现代化Web应用。

### ✨ 核心功能

- 🤖 **AI视频生成**: 支持多种AI模型生成高质量视频内容
- 📝 **文本优化**: 使用大语言模型优化内容和标题
- 🎬 **素材管理**: 完整的媒体文件管理系统
- 📱 **多平台发布**: 支持抖音、B站、小红书等主流平台
- 🎨 **现代化界面**: 基于Element Plus的响应式UI设计
- 🔄 **实时状态**: WebSocket实时任务状态更新
- 🤖 **智能调度**: 自动化内容分发和时间管理

## 🏗️ 技术架构

### 后端技术栈
- **FastAPI**: 高性能Python Web框架
- **Uvicorn**: ASGI服务器
- **SQLite**: 轻量级数据库
- **Pydantic**: 数据验证和序列化
- **WebSocket**: 实时通信

### 前端技术栈
- **Vue 3**: 渐进式JavaScript框架
- **Vite**: 快速构建工具
- **Element Plus**: Vue 3 UI组件库
- **Axios**: HTTP客户端
- **Pinia**: 状态管理

### AI集成
- **OpenAI GPT**: 文本生成和优化
- **GLM系列**: 智谱AI语言模型
- **ComfyUI**: 视频生成工作流
- **多种视频模型**: 支持不同风格的视频生成

## 🏗️ 项目架构

```
ai-auto-upload/
├── 📁 ai-media-platform/          # 🎯 主项目：AI媒体平台
│   ├── complete_backend.py          # 主后端服务入口
│   ├── requirements.txt             # Python依赖列表
│   ├── backend/                     # 后端核心模块
│   │   ├── routes/                  # API路由
│   │   ├── services/                # 业务逻辑服务
│   │   └── ...                      # 其他后端模块
│   ├── frontend/                    # 前端Vue应用
│   │   ├── src/                     # Vue源代码
│   │   ├── package.json             # 前端依赖配置
│   │   └── dist/                    # 构建输出目录
│   ├── services/                    # 共享服务模块
│   ├── config/                      # 配置文件
│   ├── venv/                        # Python虚拟环境
│   ├── *.db                         # SQLite数据库文件
│   ├── start-dev.sh                 # 开发环境启动脚本
│   ├── stop-services.sh             # 服务停止脚本
│   ├── health-check.sh              # 健康检查脚本
│   ├── ecosystem.config.js          # PM2生产环境配置
│   ├── .env.example                 # 环境变量模板
│   ├── DEPLOYMENT.md                # 详细部署文档
│   ├── QUICK_START.md               # 快速开始指南
│   ├── BRANCH_GUIDELINES.md         # 分支管理指南
│   └── README.md                    # AI媒体平台说明
├── 📁 social-auto-upload/          # 🔗 社交媒体上传模块
├── 📄 .gitignore                  # Git忽略配置
├── 📄 .gitmodules                 # Git子模块配置
├── 📄 BRANCH_GUIDELINES.md         # 项目分支管理指南
└── 📄 README.md                   # 项目根说明文档
```

## 🚀 快速开始

### 一键启动
```bash
./ai-media-platform/start-dev.sh
```

### 手动启动
```bash
# 1. 进入项目目录
cd ai-media-platform

# 2. 启动后端
source venv/bin/activate
python complete_backend.py

# 3. 启动前端 (新终端)
cd frontend
npm run dev
```

### 访问地址
- 🎨 **前端界面**: http://localhost:5174
- 🔌 **后端API**: http://localhost:9000
- 📚 **API文档**: http://localhost:9000/docs
- 💚 **健康检查**: http://localhost:9000/health

## 📚 文档系统

### 📖 核心文档
- 📋 **[详细部署文档](./ai-media-platform/DEPLOYMENT.md)** - 完整的部署和配置指南
- ⚡ **[快速开始指南](./ai-media-platform/QUICK_START.md)** - 简化的启动步骤
- 🌿 **[分支管理指南](./BRANCH_GUIDELINES.md)** - Git工作流程和分支策略

### 🔧 开发文档
- 🏗️ **项目架构说明**
- 🔌 **API接口文档** (运行后可访问)
- 🛠️ **环境配置指南**
- 🧪 **测试和调试**

## 🌐 服务端口

| 服务 | 端口 | 说明 | 状态 |
|------|------|------|------|
| 前端开发服务器 | 5174 | Vue.js开发环境 | ✅ |
| 后端API服务 | 9000 | FastAPI服务 | ✅ |
| API文档 | 9000/docs | Swagger交互式文档 | ✅ |
| 健康检查 | 9000/health | 服务状态检查 | ✅ |

## 🔧 环境要求

### 系统要求
- Python 3.13+
- Node.js 18+
- npm 或 yarn
- 8GB+ RAM (推荐)

### 依赖安装
```bash
# 后端依赖
cd ai-media-platform
source venv/bin/activate
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

## 🛠️ 开发工具

### 自动化脚本
- `./ai-media-platform/start-dev.sh` - 一键启动开发环境
- `./ai-media-platform/stop-services.sh` - 优雅停止所有服务
- `./ai-media-platform/health-check.sh` - 完整健康状态检查

### 环境配置
```bash
# 复制环境变量模板
cp ai-media-platform/.env.example ai-media-platform/.env

# 编辑配置文件
vim ai-media-platform/.env
```

## 🏭 生产环境部署

### PM2部署 (推荐)
```bash
# 安装PM2
npm install -g pm2

# 启动生产服务
cd ai-media-platform
pm2 start ecosystem.config.js

# 查看状态
pm2 status
```

### Docker部署
```bash
# 构建镜像
docker build -t ai-media-platform .

# 运行容器
docker run -p 9000:9000 -p 5174:5174 ai-media-platform
```

### Nginx反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/ai-media-platform/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API代理到后端
    location /api/ {
        proxy_pass http://localhost:9000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 🧪 测试验证

### 自动化健康检查
```bash
./ai-media-platform/health-check.sh
```

### 手动验证
```bash
# 后端健康检查
curl http://localhost:9000/health

# 前端访问测试
curl http://localhost:5174/

# API文档访问
curl http://localhost:9000/docs
```

## 🐛 故障排除

### 常见问题解决方案
1. **端口被占用**: 运行 `./ai-media-platform/stop-services.sh`
2. **虚拟环境问题**: 重新创建 `python -m venv ai-media-platform/venv`
3. **依赖安装失败**: 清除npm缓存后重新安装
4. **服务启动失败**: 检查日志文件和依赖完整性

### 日志查看
- **开发环境**: 直接查看终端输出
- **生产环境**: `pm2 logs ai-media-backend`
- **日志文件**: `ai-media-platform/logs/`

## 🌟 核心模块

### AI内容生成
- 🎬 **视频生成**: 多种AI模型支持
- 📝 **文本优化**: 大语言模型智能优化
- 🎵 **智能配音**: 自动配音和背景音乐

### 媒体管理
- 📁 **文件上传**: 支持多种媒体格式
- 🏷️ **分类管理**: 智能标签和分类
- 🔄 **版本控制**: 文件版本管理

### 多平台发布
- 📱 **平台支持**: 抖音、B站、小红书等
- ⏰ **定时发布**: 智能调度和时间管理
- 📊 **状态监控**: 实时发布状态跟踪

## 🤝 贡献指南

### 开发流程
1. Fork 项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 开发并测试功能
4. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
5. 推送分支 (`git push origin feature/AmazingFeature`)
6. 创建Pull Request

### 分支策略
- **master**: 🏭 生产环境，稳定版本
- **develop**: 🔧 开发环境，最新代码
- **feature/***: 🆕 功能开发分支

参考: [分支管理指南](./BRANCH_GUIDELINES.md)

## 📈 项目特色

### 🚀 技术亮点
- ✅ **现代化技术栈**: FastAPI + Vue 3 + Element Plus
- ✅ **AI深度集成**: 多种AI模型和算法
- ✅ **实时通信**: WebSocket支持
- ✅ **容器化部署**: Docker支持
- ✅ **生产就绪**: PM2进程管理

### 🎯 用户体验
- ✅ **一键启动**: 完整的自动化脚本
- ✅ **健康监控**: 完善的状态检查
- ✅ **详细文档**: 从部署到使用的完整指南
- ✅ **响应式设计**: 支持多设备访问

## 📄 许可证

本项目采用 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- **FastAPI**: 现代化的Python Web框架
- **Vue.js**: 渐进式JavaScript框架
- **Element Plus**: 优秀的Vue组件库
- **OpenAI**: 强大的AI能力
- **GLM**: 国产大语言模型

## 📞 社区支持

- 🐛 **Bug反馈**: [Issues](https://github.com/mengguiyouziyi/ai-auto-upload/issues)
- 💡 **功能建议**: [Discussions](https://github.com/mengguiyouziyi/ai-auto-upload/discussions)
- 📧 **联系交流**: 欢迎提交Issue或讨论

如有问题或建议，请：
1. 查看详细文档的故障排除部分
2. 提交Issue描述具体问题
3. 联系技术支持团队

---

<div align="center">

**🚀 让AI助力你的媒体创作之旅！**

[![GitHub stars](https://img.shields.io/github/stars/mengguiyouziyi/ai-auto-upload?style=social)](https://github.com/mengguiyouziyi/ai-auto-upload/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/mengguiyouziyi/ai-auto-upload?style=social)](https://github.com/mengguiyouziyi/ai-auto-upload/network/members)
[![GitHub issues](https://img.shields.io/github/issues/mengguiyouziyi/ai-auto-upload)](https://github.com/mengguiyouziyi/ai-auto-upload/issues)
[![GitHub license](https://img.shields.io/github/license/mengguiyouziyi/ai-auto-upload?style=social)](https://github.com/mengguiyouziyi/ai-auto-upload/blob/master/LICENSE)

</div>