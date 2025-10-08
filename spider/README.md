# AI技术文章爬虫

一个专业的AI技术文章爬虫项目，支持从多个技术博客平台抓取AI相关的技术文章。

## 功能特性

- 🎯 **精准定位**: 专门爬取AI、机器学习、深度学习相关的技术文章
- 🌐 **多平台支持**: 支持CSDN、掘金、InfoQ、知乎等主流技术平台
- 🔧 **混合爬取**: 结合requests和playwright，处理静态和动态内容
- 💾 **数据存储**: 支持SQLite本地存储和数据导出
- 🛡️ **反爬措施**: 内置随机延迟、User-Agent轮换等反爬策略
- 📊 **数据统计**: 实时显示爬取进度和统计信息
- 🚀 **异步支持**: 高效的异步爬取，提升爬取效率

## 项目结构

```
spider/
├── config/
│   └── settings.py          # 配置文件
├── spiders/
│   ├── csdn/
│   │   └── csdn_spider.py   # CSDN爬虫
│   ├── juejin/
│   │   └── juejin_spider.py # 掘金爬虫
│   ├── infoq/               # InfoQ爬虫(待实现)
│   └── zhihu/               # 知乎爬虫(待实现)
├── utils/
│   ├── logger.py            # 日志配置
│   ├── request_handler.py   # 请求处理
│   └── storage/
│       └── database.py      # 数据库存储
├── data/
│   ├── raw/                 # 原始数据
│   └── processed/           # 处理后数据
├── logs/                    # 日志文件
├── main.py                  # 主程序入口
├── requirements.txt         # 依赖包
└── README.md               # 项目文档
```

## 安装和配置

### 1. 安装依赖

```bash
cd /Users/sunyouyou/Desktop/projects/bzhi/ai-auto-upload/spider

# 安装Python依赖
pip install -r requirements.txt

# 安装playwright浏览器驱动
playwright install chromium
```

### 2. 配置设置

编辑 `config/settings.py` 文件，根据需要修改配置：

- **AI关键词**: 自定义要爬取的AI相关关键词
- **网站配置**: 启用/禁用特定网站，调整爬取参数
- **存储设置**: 配置数据库路径和数据格式
- **请求参数**: 调整超时时间、重试次数等

## 使用方法

### 基本用法

```bash
# 爬取所有网站
python main.py

# 爬取指定网站
python main.py --site csdn
python main.py --site juejin

# 指定关键词
python main.py --keywords "GPT" "ChatGPT" "大模型"

# 设置爬取页数
python main.py --pages 5

# 显示统计信息
python main.py --stats

# 导出数据
python main.py --export json
python main.py --export csv
```

### 高级用法

```bash
# 爬取CSDN的GPT相关文章，前3页
python main.py --site csdn --keywords "GPT" --pages 3

# 爬取所有网站的前端AI文章，并导出CSV
python main.py --keywords "前端AI" "AI工具" --export csv

# 组合使用多个参数
python main.py --site juejin --keywords "机器学习" "深度学习" --pages 2 --export json
```

## 命令行参数

| 参数 | 说明 | 默认值 | 选项 |
|------|------|--------|------|
| `--site`, `-s` | 指定爬取的网站 | `all` | `csdn`, `juejin`, `all` |
| `--keywords`, `-k` | 搜索关键词 | AI相关 | 字符串列表 |
| `--pages`, `-p` | 每个关键词爬取页数 | `3` | 整数 |
| `--export`, `-e` | 导出数据格式 | 无 | `json`, `csv` |
| `--stats` | 显示统计信息 | False | 布尔值 |

## 支持的网站

### 已实现

1. **CSDN博客** (https://blog.csdn.net)
   - 使用 requests + BeautifulSoup
   - 支持文章搜索、内容解析
   - 提取阅读量、点赞数等统计数据

2. **掘金** (https://juejin.cn)
   - 使用 Playwright (处理动态内容)
   - 支持文章搜索、内容解析
   - 自动滚动加载更多内容

### 计划支持

- InfoQ (https://www.infoq.cn)
- 知乎专栏 (https://zhuanlan.zhihu.com)
- 博客园 (https://www.cnblogs.com)
- 开源中国 (https://www.oschina.net)

## 数据字段

每篇文章包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 文章ID |
| `title` | String | 文章标题 |
| `url` | String | 文章链接 |
| `content` | Text | 文章内容 |
| `author` | String | 作者 |
| `publish_time` | String | 发布时间 |
| `source` | String | 来源网站 |
| `keywords` | Array | 关键词列表 |
| `summary` | String | 文章摘要 |
| `view_count` | Integer | 阅读量 |
| `like_count` | Integer | 点赞数 |
| `comment_count` | Integer | 评论数 |
| `created_at` | Timestamp | 创建时间 |

## 反爬措施

1. **随机延迟**: 请求间随机延迟1-3秒
2. **User-Agent轮换**: 随机选择User-Agent
3. **请求频率控制**: 限制每秒请求数
4. **浏览器模拟**: 使用真实浏览器环境
5. **错误重试**: 自动重试失败的请求

## 注意事项

1. **遵守robots.txt**: 请尊重网站的爬虫协议
2. **控制爬取频率**: 避免对目标网站造成过大压力
3. **数据用途**: 仅用于学习和研究目的
4. **法律合规**: 确保爬取行为符合相关法律法规

## 故障排除

### 常见问题

1. **安装playwright失败**
   ```bash
   # 手动安装浏览器驱动
   python -m playwright install chromium
   ```

2. **网络连接问题**
   - 检查网络连接
   - 考虑使用代理

3. **数据库权限问题**
   - 确保data目录有写入权限
   - 检查SQLite文件是否被占用

4. **爬虫被封IP**
   - 降低爬取频率
   - 增加请求延迟
   - 考虑使用代理IP

## 开发和扩展

### 添加新网站爬虫

1. 在 `spiders/` 目录下创建新文件夹
2. 实现爬虫类，继承基本结构
3. 在 `config/settings.py` 中添加网站配置
4. 在 `main.py` 中注册新爬虫

### 自定义数据处理

1. 修改 `utils/storage/database.py`
2. 添加新的数据导出格式
3. 实现数据清洗和分析功能

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！
