"""
数据库存储工具
支持SQLite和MongoDB
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.settings import DATABASE
from utils.logger import logger


class SQLiteStorage:
    """SQLite数据库存储"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 创建文章表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS articles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        url TEXT UNIQUE NOT NULL,
                        content TEXT,
                        author TEXT,
                        publish_time TEXT,
                        source TEXT,
                        keywords TEXT,
                        summary TEXT,
                        view_count INTEGER DEFAULT 0,
                        like_count INTEGER DEFAULT 0,
                        comment_count INTEGER DEFAULT 0,
                        raw_html TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 创建索引
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_articles_publish_time ON articles(publish_time)
                ''')

                conn.commit()
                logger.info("SQLite数据库初始化完成")

        except Exception as e:
            logger.error(f"初始化数据库失败: {e}")

    def save_article(self, article_data: Dict[str, Any]) -> bool:
        """保存文章"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 检查文章是否已存在
                cursor.execute("SELECT id FROM articles WHERE url = ?", (article_data['url'],))
                if cursor.fetchone():
                    logger.debug(f"文章已存在: {article_data['url']}")
                    return False

                # 插入新文章
                cursor.execute('''
                    INSERT INTO articles (
                        title, url, content, author, publish_time, source,
                        keywords, summary, view_count, like_count, comment_count, raw_html
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_data.get('title'),
                    article_data.get('url'),
                    article_data.get('content'),
                    article_data.get('author'),
                    article_data.get('publish_time'),
                    article_data.get('source'),
                    json.dumps(article_data.get('keywords', [])),
                    article_data.get('summary'),
                    article_data.get('view_count', 0),
                    article_data.get('like_count', 0),
                    article_data.get('comment_count', 0),
                    article_data.get('raw_html')
                ))

                conn.commit()
                logger.info(f"文章保存成功: {article_data['title'][:50]}...")
                return True

        except Exception as e:
            logger.error(f"保存文章失败: {e}")
            return False

    def get_articles(self, source: Optional[str] = None,
                    limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取文章列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if source:
                    cursor.execute('''
                        SELECT * FROM articles WHERE source = ?
                        ORDER BY publish_time DESC
                        LIMIT ? OFFSET ?
                    ''', (source, limit, offset))
                else:
                    cursor.execute('''
                        SELECT * FROM articles
                        ORDER BY publish_time DESC
                        LIMIT ? OFFSET ?
                    ''', (limit, offset))

                articles = []
                for row in cursor.fetchall():
                    article = dict(row)
                    # 解析JSON字段
                    if article['keywords']:
                        article['keywords'] = json.loads(article['keywords'])
                    articles.append(article)

                return articles

        except Exception as e:
            logger.error(f"获取文章失败: {e}")
            return []

    def get_article_count(self, source: Optional[str] = None) -> int:
        """获取文章总数"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                if source:
                    cursor.execute("SELECT COUNT(*) FROM articles WHERE source = ?", (source,))
                else:
                    cursor.execute("SELECT COUNT(*) FROM articles")

                return cursor.fetchone()[0]

        except Exception as e:
            logger.error(f"获取文章总数失败: {e}")
            return 0

    def export_to_json(self, file_path: Path, source: Optional[str] = None):
        """导出数据到JSON文件"""
        try:
            articles = self.get_articles(source=source, limit=10000)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"数据导出成功: {file_path}")

        except Exception as e:
            logger.error(f"导出数据失败: {e}")

    def export_to_csv(self, file_path: Path, source: Optional[str] = None):
        """导出数据到CSV文件"""
        try:
            import pandas as pd

            articles = self.get_articles(source=source, limit=10000)
            df = pd.DataFrame(articles)

            # 处理特殊字段
            if 'keywords' in df.columns:
                df['keywords'] = df['keywords'].apply(lambda x: ', '.join(x) if x else '')

            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            logger.info(f"数据导出成功: {file_path}")

        except Exception as e:
            logger.error(f"导出CSV失败: {e}")


# 数据库实例
sqlite_storage = SQLiteStorage(DATABASE["sqlite"]["path"])