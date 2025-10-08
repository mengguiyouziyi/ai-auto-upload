"""
AI技术文章爬虫配置文件
"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 数据存储配置
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
LOGS_DIR = BASE_DIR / "logs"

# 确保目录存在
for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, LOGS_DIR]:
    dir_path.mkdir(exist_ok=True)

# 爬虫配置
CRAWL_CONFIG = {
    # 请求配置
    "REQUEST_TIMEOUT": 30,
    "MAX_RETRIES": 3,
    "RETRY_DELAY": 2,
    "CONCURRENT_REQUESTS": 5,

    # 浏览器配置
    "BROWSER_TIMEOUT": 30,
    "BROWSER_HEADLESS": True,
    "BROWSER_SLOW_MO": 100,

    # 数据保存配置
    "SAVE_RAW_HTML": True,
    "SAVE_IMAGES": False,
    "DATA_FORMAT": ["json", "csv"],  # 支持的格式

    # 日志配置
    "LOG_LEVEL": "INFO",
    "LOG_ROTATION": "10 MB",
    "LOG_RETENTION": "7 days",
}

# 导出CRAWL_CONFIG到模块级别
REQUEST_TIMEOUT = CRAWL_CONFIG["REQUEST_TIMEOUT"]
MAX_RETRIES = CRAWL_CONFIG["MAX_RETRIES"]
RETRY_DELAY = CRAWL_CONFIG["RETRY_DELAY"]
CONCURRENT_REQUESTS = CRAWL_CONFIG["CONCURRENT_REQUESTS"]
BROWSER_TIMEOUT = CRAWL_CONFIG["BROWSER_TIMEOUT"]
BROWSER_HEADLESS = CRAWL_CONFIG["BROWSER_HEADLESS"]
BROWSER_SLOW_MO = CRAWL_CONFIG["BROWSER_SLOW_MO"]

# AI相关关键词
AI_KEYWORDS = [
    "人工智能", "AI", "机器学习", "深度学习", "神经网络", "GPT", "LLM", "大模型",
    "ChatGPT", "OpenAI", "计算机视觉", "自然语言处理", "NLP", "强化学习",
    "生成式AI", "AIGC", "Stable Diffusion", "Midjourney", "文心一言", "通义千问",
    "自动驾驶", "智能推荐", "知识图谱", "机器翻译", "语音识别", "图像识别",
    "TensorFlow", "PyTorch", "Keras", "scikit-learn", "PaddlePaddle",
    "Prompt Engineering", "Fine-tuning", "模型训练", "数据标注"
]

# 目标网站配置
WEBSITES = {
    "csdn": {
        "name": "CSDN博客",
        "base_url": "https://blog.csdn.net",
        "search_url": "https://so.csdn.net/search",
        "enabled": True,
        "use_browser": False,  # CSDN可以用requests
        "rate_limit": 1,  # 每秒请求数
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    },

    "juejin": {
        "name": "掘金",
        "base_url": "https://juejin.cn",
        "search_url": "https://juejin.cn/search",
        "enabled": True,
        "use_browser": True,  # 掘金需要用playwright
        "rate_limit": 2,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    },

    "infoq": {
        "name": "InfoQ",
        "base_url": "https://www.infoq.cn",
        "search_url": "https://www.infoq.cn/search",
        "enabled": True,
        "use_browser": False,
        "rate_limit": 1,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    },

    "zhihu": {
        "name": "知乎",
        "base_url": "https://www.zhihu.com",
        "search_url": "https://www.zhihu.com/search",
        "enabled": True,
        "use_browser": True,  # 知乎需要用playwright
        "rate_limit": 1,
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    }
}

# 数据库配置
DATABASE = {
    "sqlite": {
        "path": DATA_DIR / "articles.db",
        "enabled": True
    },
    "mongodb": {
        "uri": "mongodb://localhost:27017/",
        "database": "ai_articles",
        "enabled": False  # 需要MongoDB服务
    }
}

# 代理配置（如果需要）
PROXY = {
    "enabled": False,
    "http": None,
    "https": None,
    "rotation": False
}