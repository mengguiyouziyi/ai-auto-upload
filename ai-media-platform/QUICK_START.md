# 🚀 AI媒体平台快速启动指南

## ⚡ 一键启动

在项目根目录下运行：

```bash
./start-dev.sh
```

## 📋 前置要求

- Python 3.13+
- Node.js 18+
- 确保在 `ai-media-platform` 目录下

## 🛑 停止服务

```bash
./stop-services.sh
```

## 🌐 访问地址

- **前端界面**: http://localhost:5174
- **后端API**: http://localhost:9000
- **API文档**: http://localhost:9000/docs

## 🔧 手动启动步骤

如果自动脚本失败，可以手动执行：

### 1. 清理端口
```bash
lsof -ti:5174 | xargs kill -9 2>/dev/null || true
lsof -ti:9000 | xargs kill -9 2>/dev/null || true
```

### 2. 启动后端
```bash
source venv/bin/activate
python complete_backend.py
```

### 3. 启动前端 (新终端)
```bash
cd frontend
npm run dev
```

## ✅ 验证部署

```bash
# 检查后端
curl http://localhost:9000/health

# 检查前端
curl http://localhost:5174/
```

## 📝 配置文件

- `.env.example` - 环境变量模板
- `ecosystem.config.js` - PM2生产环境配置
- `DEPLOYMENT.md` - 详细部署文档

## 🆘 常见问题

1. **端口被占用**: 运行 `./stop-services.sh` 清理
2. **虚拟环境问题**: 删除 `venv` 重新创建
3. **依赖问题**: 重新安装 `pip install -r requirements.txt`

---

📖 详细文档请查看 [DEPLOYMENT.md](./DEPLOYMENT.md)