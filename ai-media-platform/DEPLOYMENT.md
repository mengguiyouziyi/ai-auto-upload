# AI媒体平台部署指南

## 📋 项目概述

AI媒体平台是一个基于FastAPI后端和Vue.js前端的现代化Web应用，提供AI视频生成、内容优化、社交媒体发布等功能。

### 🏗️ 技术栈
- **后端**: FastAPI + Uvicorn (Python 3.13)
- **前端**: Vue 3 + Vite + Element Plus
- **数据库**: SQLite (accounts.db, files.db, social_auto_upload.db)
- **虚拟环境**: Python venv

### 🌐 服务端口
- **后端API**: http://localhost:9000
- **前端界面**: http://localhost:5174
- **健康检查**: http://localhost:9000/health

## 🚀 快速部署

### 前置要求
- Python 3.13+
- Node.js 18+
- npm 或 yarn

### 1. 项目结构准备
```bash
# 确保项目目录结构如下：
ai-media-platform/
├── complete_backend.py          # 主后端服务
├── requirements.txt             # Python依赖
├── accounts.db                  # 账户数据库
├── files.db                     # 文件数据库
├── social_auto_upload.db        # 社交上传数据库
├── backend/                     # 后端模块
├── frontend/                    # 前端代码
│   ├── package.json            # 前端依赖配置
│   ├── src/                    # Vue源码
│   └── dist/                   # 构建输出目录
├── services/                    # 核心服务
├── routes/                      # API路由
├── config/                      # 配置文件
└── venv/                        # Python虚拟环境
```

### 2. 端口清理（可选）
如果之前有服务占用端口，先清理：

```bash
# 杀死占用相关端口的进程
lsof -ti:5174 | xargs kill -9 2>/dev/null || echo "No process on port 5174"
lsof -ti:9000 | xargs kill -9 2>/dev/null || echo "No process on port 9000"
lsof -ti:3000 | xargs kill -9 2>/dev/null || echo "No process on port 3000"
```

### 3. 后端服务启动

#### 3.1 激活虚拟环境
```bash
# 在项目根目录下执行
source venv/bin/activate
```

#### 3.2 启动后端服务
```bash
# 使用complete_backend.py启动后端
python complete_backend.py
```

**预期输出:**
```
INFO:     Started server process [进程ID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
```

#### 3.3 验证后端服务
```bash
# 健康检查
curl http://localhost:9000/health
# 预期响应: {"status":"healthy","service":"ai-media-platform"}
```

### 4. 前端服务启动

#### 4.1 进入前端目录
```bash
cd frontend
```

#### 4.2 安装依赖（首次部署需要）
```bash
npm install
```

#### 4.3 启动开发服务器
```bash
npm run dev
```

**预期输出:**
```
> sau-admin@0.0.0 dev
> vite

  VITE v6.3.6  ready in 162 ms

  ➜  Local:   http://localhost:5174/
  ➜  Network: use --host to expose
```

#### 4.4 验证前端服务
```bash
# 在浏览器中访问
open http://localhost:5174/
```

## 🔧 生产环境部署

### 后端生产部署

#### 使用PM2进程管理
```bash
# 安装PM2
npm install -g pm2

# 使用PM2启动后端
pm2 start complete_backend.py --name "ai-media-backend" --interpreter python

# 查看状态
pm2 status

# 查看日志
pm2 logs ai-media-backend
```

#### 创建PM2配置文件
创建 `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [{
    name: 'ai-media-backend',
    script: 'complete_backend.py',
    interpreter: 'python',
    interpreter_args: 'venv/bin/python',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PYTHONPATH: './'
    }
  }]
}
```

使用配置启动：
```bash
pm2 start ecosystem.config.js
```

### 前端生产部署

#### 构建生产版本
```bash
cd frontend
npm run build
```

#### 使用nginx部署
创建nginx配置 `/etc/nginx/sites-available/ai-media-platform`:
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

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/ai-media-platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🛠️ 开发环境部署

### 开发模式启动脚本
创建 `start-dev.sh`:
```bash
#!/bin/bash

echo "🚀 启动AI媒体平台开发环境..."

# 清理端口
echo "📋 清理端口..."
lsof -ti:5174 | xargs kill -9 2>/dev/null || echo "端口5174已清空"
lsof -ti:9000 | xargs kill -9 2>/dev/null || echo "端口9000已清空"

# 启动后端
echo "🔧 启动后端服务..."
source venv/bin/activate
python complete_backend.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 验证后端
if curl -s http://localhost:9000/health > /dev/null; then
    echo "✅ 后端服务启动成功 (PID: $BACKEND_PID)"
else
    echo "❌ 后端服务启动失败"
    exit 1
fi

# 启动前端
echo "🎨 启动前端服务..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# 等待前端启动
sleep 5

echo "✅ AI媒体平台启动完成!"
echo "📱 前端地址: http://localhost:5174"
echo "🔌 后端API: http://localhost:9000"
echo "💚 健康检查: http://localhost:9000/health"
echo ""
echo "按 Ctrl+C 停止所有服务..."

# 等待中断信号
trap "echo '🛑 停止服务...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
```

使用脚本：
```bash
chmod +x start-dev.sh
./start-dev.sh
```

## 🔍 故障排除

### 常见问题

#### 1. 后端启动失败
**症状**: `ModuleNotFoundError` 或导入错误
**解决方案**:
```bash
# 检查虚拟环境
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt

# 检查Python版本
python --version  # 需要3.13+
```

#### 2. 端口被占用
**症状**: `Address already in use`
**解决方案**:
```bash
# 查找占用端口的进程
lsof -i:9000
lsof -i:5174

# 杀死进程
kill -9 <进程ID>

# 或者使用不同端口
# 后端: 修改complete_backend.py中的端口配置
# 前端: npm run dev -- --port 3000
```

#### 3. 前端依赖安装失败
**症状**: `npm install` 错误
**解决方案**:
```bash
# 清除npm缓存
npm cache clean --force

# 删除node_modules重新安装
rm -rf node_modules package-lock.json
npm install

# 如果仍有问题，尝试使用yarn
yarn install
```

#### 4. 数据库文件权限问题
**症状**: `PermissionError` 访问.db文件
**解决方案**:
```bash
# 检查文件权限
ls -la *.db

# 修改权限
chmod 664 *.db
chmod 775 .
```

#### 5. 虚拟环境问题
**症状**: 激活虚拟环境失败
**解决方案**:
```bash
# 重新创建虚拟环境
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 服务检查命令

#### 检查服务状态
```bash
# 检查进程
ps aux | grep -E "(python.*complete_backend|npm.*dev)" | grep -v grep

# 检查端口
netstat -tulpn | grep -E ":9000|:5174"

# 检查服务健康状态
curl http://localhost:9000/health
curl http://localhost:5174/
```

#### 查看日志
```bash
# 开发环境直接查看终端输出
# 生产环境查看PM2日志
pm2 logs ai-media-backend

# 查看nginx日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 📊 性能优化

### 后端优化
- 使用Gunicorn替代Uvicorn（生产环境）
- 配置Redis缓存
- 数据库连接池优化
- 异步任务队列（Celery）

### 前端优化
- 代码分割和懒加载
- 静态资源CDN
- Gzip压缩
- 浏览器缓存策略

## 🔒 安全配置

### 后端安全
- API访问频率限制
- 输入验证和清理
- HTTPS配置
- 环境变量管理

### 前端安全
- CSP策略配置
- XSS防护
- 敏感信息环境变量化

## 📝 维护指南

### 日常维护
```bash
# 更新依赖
pip update -r requirements.txt
npm update

# 备份数据库
cp accounts.db backup/accounts_$(date +%Y%m%d).db
cp files.db backup/files_$(date +%Y%m%d).db
cp social_auto_upload.db backup/social_auto_upload_$(date +%Y%m%d).db

# 清理日志
find . -name "*.log" -mtime +7 -delete
```

### 监控建议
- 设置服务健康检查监控
- 配置错误报告通知
- 监控系统资源使用
- 定期备份重要数据

---

## 📞 技术支持

如果在部署过程中遇到问题，请：
1. 查看本文档的故障排除部分
2. 检查服务的错误日志
3. 确认系统环境符合要求
4. 联系技术支持团队

**部署完成后，访问 http://localhost:5174 开始使用AI媒体平台！** 🎉