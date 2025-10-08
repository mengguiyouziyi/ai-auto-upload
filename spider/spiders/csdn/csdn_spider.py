"""
CSDN AI文章爬虫
使用requests + BeautifulSoup实现
"""
import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime

from bs4 import BeautifulSoup
import requests

from utils import logger, request_handler, sqlite_storage
from config.settings import AI_KEYWORDS, WEBSITES


class CSDNSpider:
    """CSDN爬虫类"""

    def __init__(self):
        self.config = WEBSITES["csdn"]
        self.base_url = self.config["base_url"]
        self.search_url = self.config["search_url"]
        self.ai_keywords = AI_KEYWORDS

    def search_articles(self, keyword: str, page: int = 1, limit: int = 20) -> List[str]:
        """
        搜索AI相关文章
        :param keyword: 搜索关键词
        :param page: 页码
        :param limit: 每页数量
        :return: 文章URL列表
        """
        try:
            # 构建搜索URL
            search_params = {
                'q': keyword,
                't': 'blog',
                'p': page,
                'u': '',  # 用户ID，留空表示全部用户
                'r': '',  # 排序方式
                'spm': '1001.2101.3001.7020'
            }

            logger.info(f"搜索CSDN文章: {keyword}, 页码: {page}")

            # 发送请求
            response = request_handler.get(self.search_url, params=search_params)
            if not response:
                logger.error(f"搜索请求失败: {keyword}")
                return []

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取文章链接
            article_urls = []
            article_items = soup.find_all('div', class_='search-list J_search')

            for item in article_items:
                # 获取文章链接
                title_link = item.find('h3') or item.find('h2')
                if title_link:
                    a_tag = title_link.find('a')
                    if a_tag and a_tag.get('href'):
                        url = a_tag['href']
                        # 确保是完整的URL
                        if url.startswith('//'):
                            url = 'https:' + url
                        elif not url.startswith('http'):
                            url = urljoin(self.base_url, url)

                        # 过滤掉非文章页面
                        if '/article/details/' in url or '/blog/' in url:
                            article_urls.append(url)

                # 限制数量
                if len(article_urls) >= limit:
                    break

            logger.info(f"找到 {len(article_urls)} 篇文章")
            return article_urls[:limit]

        except Exception as e:
            logger.error(f"搜索文章失败: {e}")
            return []

    def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        解析单篇文章
        :param url: 文章URL
        :return: 文章数据字典
        """
        try:
            logger.info(f"解析文章: {url}")

            response = request_handler.get(url)
            if not response:
                logger.error(f"获取文章失败: {url}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取文章信息
            article_data = {
                'url': url,
                'source': 'csdn'
            }

            # 标题
            title_elem = soup.find('h1', class_='title-article') or soup.find('h1')
            if title_elem:
                article_data['title'] = title_elem.get_text().strip()
            else:
                logger.warning(f"未找到标题: {url}")
                return None

            # 作者
            author_elem = soup.find('a', class_='follow-nickName')
            if author_elem:
                article_data['author'] = author_elem.get_text().strip()

            # 发布时间
            time_elem = soup.find('span', class_='time') or soup.find('div', class_='article-info-box').find('span', class_='time') if soup.find('div', class_='article-info-box') else None
            if time_elem:
                article_data['publish_time'] = self._parse_time(time_elem.get_text().strip())

            # 阅读量、点赞数、评论数
            stats_elem = soup.find('div', class_='article-info-box')
            if stats_elem:
                # 阅读量
                view_elem = stats_elem.find('span', class_='read-num')
                if view_elem:
                    article_data['view_count'] = self._extract_number(view_elem.get_text())

                # 点赞数
                like_elem = stats_elem.find('span', class_='get-num')
                if like_elem:
                    article_data['like_count'] = self._extract_number(like_elem.get_text())

            # 文章内容
            content_elem = soup.find('div', id='content_views') or soup.find('div', class_='markdown_views')
            if content_elem:
                # 移除不需要的元素
                for unwanted in content_elem.find_all(['script', 'style', 'nav', 'footer']):
                    unwanted.decompose()

                article_data['content'] = content_elem.get_text().strip()
                article_data['summary'] = self._generate_summary(article_data['content'])
            else:
                logger.warning(f"未找到文章内容: {url}")
                article_data['content'] = ""
                article_data['summary'] = ""

            # 提取关键词
            article_data['keywords'] = self._extract_keywords(article_data['title'] + ' ' + article_data['content'])

            # 原始HTML（可选）
            if self.config.get('save_raw_html', False):
                article_data['raw_html'] = response.text

            # 验证数据
            if not article_data['title'] or not article_data['content']:
                logger.warning(f"文章数据不完整: {url}")
                return None

            logger.info(f"解析成功: {article_data['title'][:50]}...")
            return article_data

        except Exception as e:
            logger.error(f"解析文章失败: {url}, 错误: {e}")
            return None

    def crawl_articles(self, keywords: List[str] = None, max_pages: int = 5) -> int:
        """
        爬取文章
        :param keywords: 关键词列表，默认使用AI关键词
        :param max_pages: 最大页数
        :return: 成功爬取的文章数量
        """
        if keywords is None:
            keywords = ['人工智能', '机器学习', '深度学习', 'GPT']

        total_count = 0

        for keyword in keywords:
            logger.info(f"开始爬取关键词: {keyword}")

            for page in range(1, max_pages + 1):
                # 搜索文章
                article_urls = self.search_articles(keyword, page, limit=20)

                if not article_urls:
                    logger.info(f"第 {page} 页没有找到文章，跳过")
                    continue

                # 解析每篇文章
                for url in article_urls:
                    article_data = self.parse_article(url)
                    if article_data and sqlite_storage.save_article(article_data):
                        total_count += 1

                    # 延迟避免请求过快
                    time.sleep(1)

                # 页面间延迟
                time.sleep(2)

            logger.info(f"关键词 '{keyword}' 爬取完成")

        logger.info(f"总共爬取了 {total_count} 篇文章")
        return total_count

    def _parse_time(self, time_str: str) -> str:
        """解析时间字符串"""
        try:
            # 处理相对时间
            if '天前' in time_str:
                days = re.search(r'(\d+)天前', time_str)
                if days:
                    days_ago = int(days.group(1))
                    target_date = datetime.now() - datetime.timedelta(days=days_ago)
                    return target_date.strftime('%Y-%m-%d %H:%M:%S')

            elif '小时前' in time_str or '分钟前' in time_str:
                return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            else:
                # 标准时间格式
                return time_str

        except Exception:
            return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _extract_number(self, text: str) -> int:
        """从文本中提取数字"""
        try:
            match = re.search(r'\d+', text.replace(',', ''))
            return int(match.group()) if match else 0
        except:
            return 0

    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成文章摘要"""
        if not content:
            return ""

        # 移除多余空白字符
        content = re.sub(r'\s+', ' ', content).strip()

        # 简单截取前max_length个字符作为摘要
        if len(content) <= max_length:
            return content
        else:
            return content[:max_length] + '...'

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        keywords = []
        text_lower = text.lower()

        for keyword in self.ai_keywords:
            if keyword.lower() in text_lower:
                keywords.append(keyword)

        return keywords[:10]  # 最多返回10个关键词


# 使用示例
if __name__ == "__main__":
    spider = CSDNSpider()
    spider.crawl_articles(['GPT', '机器学习'], max_pages=2)