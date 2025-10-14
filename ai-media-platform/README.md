# 🎯 AI媒体平台

一个基于FastAPI和Vue.js的现代化AI媒体内容创作与发布平台，集成视频生成、内容优化、多平台发布等功能。

## ✨ 核心功能

- 🤖 **AI视频生成**: 支持多种AI模型生成高质量视频内容
- 📝 **文本优化**: 使用大语言模型优化内容和标题
- 🎬 **素材管理**: 完整的媒体文件管理系统
- 📱 **多平台发布**: 支持抖音、B站、小红书等主流平台
- 🎨 **现代化界面**: 基于Element Plus的响应式UI设计
- 🔄 **实时状态**: WebSocket实时任务状态更新

## 🏗️ 技术架构

### 后端技术栈
- **FastAPI**: 高性能Python Web框架
- **Uvicorn**: ASGI服务器
- **SQLite**: 轻量级数据库
- **Pydantic**: 数据验证和序列化

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

## 🚀 快速开始

### 一键启动
```bash
./start-dev.sh
```

### 手动启动
```bash
# 1. 启动后端
source venv/bin/activate
python complete_backend.py

# 2. 启动前端 (新终端)
cd frontend
npm run dev
```

### 访问地址
- 🎨 **前端界面**: http://localhost:5174
- 🔌 **后端API**: http://localhost:9000
- 📚 **API文档**: http://localhost:9000/docs

## 📁 项目结构

```
ai-media-platform/
├── complete_backend.py          # 主后端服务入口
├── requirements.txt             # Python依赖列表
├── backend/                     # 后端核心模块
│   ├── routes/                  # API路由
│   ├── services/                # 业务逻辑服务
│   └── ...                      # 其他后端模块
├── frontend/                    # 前端Vue应用
│   ├── src/                     # Vue源代码
│   ├── package.json             # 前端依赖配置
│   └── dist/                    # 构建输出目录
├── services/                    # 共享服务模块
├── config/                      # 配置文件
├── venv/                        # Python虚拟环境
├── *.db                         # SQLite数据库文件
├── start-dev.sh                 # 开发环境启动脚本
├── stop-services.sh             # 服务停止脚本
├── health-check.sh              # 健康检查脚本
├── ecosystem.config.js          # PM2生产环境配置
├── .env.example                 # 环境变量模板
├── DEPLOYMENT.md                # 详细部署文档
├── QUICK_START.md               # 快速开始指南
└── README.md                    # 项目说明文档
```

## 🛠️ 开发指南

### 环境要求
- Python 3.13+
- Node.js 18+
- npm 或 yarn

### 依赖安装
```bash
# 后端依赖
source venv/bin/activate
pip install -r requirements.txt

# 前端依赖
cd frontend
npm install
```

### 环境配置
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

### 开发工具脚本
- `./start-dev.sh` - 一键启动开发环境
- `./stop-services.sh` - 停止所有服务
- `./health-check.sh` - 健康状态检查

## 📚 文档

- 📖 **[详细部署文档](./DEPLOYMENT.md)** - 完整的部署和配置指南
- ⚡ **[快速开始指南](./QUICK_START.md)** - 简化的启动步骤
- 🔧 **[API文档](http://localhost:9000/docs)** - 后端API接口文档

## 🌐 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端开发服务器 | 5174 | Vue.js开发环境 |
| 后端API服务 | 9000 | FastAPI服务 |
| API文档 | 9000/docs | Swagger交互式文档 |
| 健康检查 | 9000/health | 服务状态检查 |

## 🔧 生产环境部署

### 使用PM2
```bash
# 安装PM2
npm install -g pm2

# 启动生产服务
pm2 start ecosystem.config.js

# 查看状态
pm2 status
```

### 使用Docker (可选)
```bash
# 构建镜像
docker build -t ai-media-platform .

# 运行容器
docker run -p 9000:9000 -p 5174:5174 ai-media-platform
```

## 🧪 测试

### 健康检查
```bash
./health-check.sh
```

### API测试
```bash
# 后端健康检查
curl http://localhost:9000/health

# 前端访问测试
curl http://localhost:5174/
```

## 🐛 故障排除

### 常见问题
1. **端口被占用**: 运行 `./stop-services.sh`
2. **虚拟环境问题**: 重新创建 `python -m venv venv`
3. **依赖安装失败**: 清除缓存后重新安装

### 日志查看
- 开发环境: 直接查看终端输出
- 生产环境: `pm2 logs ai-media-backend`

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 支持

如有问题或建议，请：
1. 查看 [DEPLOYMENT.md](./DEPLOYMENT.md) 故障排除部分
2. 提交 Issue 描述问题
3. 联系技术支持团队

---

**🎉 感谢使用AI媒体平台！**

如果觉得这个项目有用，请给个 ⭐ Star！