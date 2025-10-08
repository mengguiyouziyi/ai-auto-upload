# 🚀 AI媒体智能平台

一个集成多种AI能力的媒体内容生成平台，支持LLM文本处理、TTS语音合成、文生图、文生视频、语音识别等功能。

## 🎯 系统架构

### 📁 目录结构
```
ai-media-platform/
├── backend/              # FastAPI后端服务
├── frontend/             # Web前端界面
├── services/             # AI服务模块
│   ├── llm/             # 大语言模型服务
│   ├── tts/             # 语音合成服务
│   ├── image-generation/ # 文生图服务
│   ├── video-generation/ # 文生视频服务
│   └── voice-recognition/ # 语音识别服务
├── config/              # 配置文件
├── logs/                # 日志文件
├── temp/                # 临时文件
└── tests/               # 测试文件
```

## 🔌 集成的AI服务

### 🤖 LLM文本处理
- **豆包API**: 字节跳动大语言模型
- **文心一言API**: 百度大语言模型
- **OpenAI API**: GPT系列模型
- **功能**: 文本改写、优化、剧本生成

### 🗣️ TTS语音合成
- **Azure TTS**: 微软语音服务
- **阿里云TTS**: 阿里语音合成
- **腾讯云TTS**: 腾讯语音服务
- **功能**: 文本转语音，多种音色选择

### 🎨 文生图服务
- **Stable Diffusion**: 开源图像生成
- **Midjourney API**: 商业图像生成
- **DALL-E API**: OpenAI图像生成
- **功能**: 文本描述生成高质量图像

### 🎬 文生视频服务
- **Runway ML API**: 商业视频生成
- **Pika Labs API**: AI视频创作
- **Stable Video Diffusion**: 开源视频生成
- **豆包/文心视频**: 国内大模型视频生成
- **功能**: 文本转视频，多种风格选择

### 🎤 语音识别
- **Whisper API**: OpenAI语音转文本
- **Azure Speech**: 微软语音识别
- **百度语音**: 中文语音识别
- **功能**: 音频转文本，多语言支持

## 🚀 快速开始

### 1. 环境配置
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥
```bash
# 复制配置文件
cp config/config.example.yaml config/config.yaml

# 编辑配置文件，添加你的API密钥
vim config/config.yaml
```

### 3. 启动服务
```bash
# 启动后端服务
python backend/main.py

# 启动前端服务
cd frontend && npm run dev
```

### 4. 访问界面
- 前端界面: http://localhost:3000
- API文档: http://localhost:8000/docs
- 监控面板: http://localhost:8000/admin

## 📊 功能特性

### 🎯 媒体内容生成流程
1. **文本输入**: 用户输入原始文本或上传文档
2. **LLM处理**: 使用大模型优化和改写文本
3. **内容分割**: 自动分割为适合的视频场景
4. **多媒体生成**: 并行生成图像、视频、音频
5. **智能合成**: 自动合成最终媒体内容

### 🔧 核心功能
- ✅ 批量文章处理
- ✅ 智能文本优化
- ✅ 多模型并行处理
- ✅ 实时进度监控
- ✅ 质量自动评分
- ✅ 云端存储集成
- ✅ API接口调用
- ✅ 用户权限管理

## 🛠️ 技术栈

### 后端技术
- **FastAPI**: 高性能Web框架
- **Celery**: 分布式任务队列
- **Redis**: 缓存和消息队列
- **PostgreSQL**: 主数据库
- **Docker**: 容器化部署

### 前端技术
- **React**: 现代前端框架
- **TypeScript**: 类型安全
- **Ant Design**: UI组件库
- **Zustand**: 状态管理
- **Vite**: 构建工具

### AI集成
- **Transformers**: Hugging Face模型库
- **Diffusers**: 图像/视频生成
- **OpenAI SDK**: OpenAI API集成
- **Azure SDK**: 微软服务集成

## 📈 部署方案

### 🏠 本地部署
- 适用于开发和小规模使用
- 支持CPU和GPU加速
- 本地文件存储

### ☁️ 云端部署
- 支持AWS、阿里云、腾讯云
- 自动扩缩容
- 高可用架构
- CDN加速

### 🐳 Docker部署
```bash
# 构建镜像
docker build -t ai-media-platform .

# 运行容器
docker run -p 8000:8000 -p 3000:3000 ai-media-platform
```

## 📞 支持与反馈

- 📧 邮箱: support@ai-media-platform.com
- 💬 微信群: AI媒体技术交流
- 🐛 问题反馈: GitHub Issues
- 📖 文档: https://docs.ai-media-platform.com

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件