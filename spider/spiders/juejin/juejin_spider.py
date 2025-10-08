"""
掘金AI文章爬虫
使用playwright实现，处理动态加载内容
"""
import asyncio
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils import logger, playwright_handler, sqlite_storage
from config.settings import AI_KEYWORDS, WEBSITES


class JuejinSpider:
    """掘金爬虫类"""

    def __init__(self):
        self.config = WEBSITES["juejin"]
        self.base_url = self.config["base_url"]
        self.search_url = self.config["search_url"]
        self.ai_keywords = AI_KEYWORDS

    async def search_articles(self, keyword: str, page: int = 1, limit: int = 20) -> List[str]:
        """
        搜索AI相关文章
        :param keyword: 搜索关键词
        :param page: 页码
        :param limit: 每页数量
        :return: 文章URL列表
        """
        try:
            # 构建搜索URL
            search_url = f"{self.search_url}?query={keyword}&type=article&sort=default"

            logger.info(f"搜索掘金文章: {keyword}, 页码: {page}")

            # 启动浏览器
            if not playwright_handler.browser:
                await playwright_handler.start_browser(headless=True)

            # 获取搜索页面
            content = await playwright_handler.get_page(search_url)
            if not content:
                logger.error(f"获取搜索页面失败: {keyword}")
                return []

            # 等待文章列表加载
            await asyncio.sleep(2)

            # 滚动加载更多内容
            await self._scroll_to_load()

            # 提取文章链接
            article_urls = await self._extract_article_urls(limit)

            logger.info(f"找到 {len(article_urls)} 篇文章")
            return article_urls[:limit]

        except Exception as e:
            logger.error(f"搜索文章失败: {e}")
            return []

    async def _scroll_to_load(self):
        """滚动页面加载更多内容"""
        try:
            # 模拟滚动加载
            for _ in range(3):
                await playwright_handler.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
        except Exception as e:
            logger.warning(f"滚动加载失败: {e}")

    async def _extract_article_urls(self, limit: int) -> List[str]:
        """从页面提取文章URL"""
        article_urls = []

        try:
            # 等待文章列表加载
            await playwright_handler.page.wait_for_selector('.article-item', timeout=10000)

            # 获取所有文章链接
            links = await playwright_handler.page.query_selector_all('.article-item a[href*="/post/"]')

            for link in links[:limit]:
                try:
                    href = await link.get_attribute('href')
                    if href:
                        # 确保是完整的URL
                        if href.startswith('//'):
                            url = 'https:' + href
                        elif href.startswith('/'):
                            url = self.base_url + href
                        else:
                            url = href

                        article_urls.append(url)
                except Exception as e:
                    logger.warning(f"提取链接失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"提取文章URL失败: {e}")

        return article_urls

    async def parse_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        解析单篇文章
        :param url: 文章URL
        :return: 文章数据字典
        """
        try:
            logger.info(f"解析文章: {url}")

            # 获取文章页面
            content = await playwright_handler.get_page(url)
            if not content:
                logger.error(f"获取文章失败: {url}")
                return None

            # 等待内容加载
            await asyncio.sleep(2)

            # 提取文章信息
            article_data = {
                'url': url,
                'source': 'juejin'
            }

            # 标题
            try:
                title_elem = await playwright_handler.page.query_selector('h1.article-title')
                if title_elem:
                    article_data['title'] = await title_elem.text_content()
                else:
                    # 备用选择器
                    title_elem = await playwright_handler.page.query_selector('h1')
                    if title_elem:
                        article_data['title'] = await title_elem.text_content()
            except:
                logger.warning(f"未找到标题: {url}")
                return None

            if not article_data.get('title'):
                logger.warning(f"标题为空: {url}")
                return None

            article_data['title'] = article_data['title'].strip()

            # 作者信息
            try:
                author_elem = await playwright_handler.page.query_selector('.author-info a')
                if author_elem:
                    article_data['author'] = await author_elem.text_content()
            except:
                pass

            # 发布时间
            try:
                time_elem = await playwright_handler.page.query_selector('.meta-container time')
                if time_elem:
                    article_data['publish_time'] = await time_elem.get_attribute('datetime')
            except:
                pass

            # 阅读量、点赞数、评论数
            try:
                # 阅读量
                view_elem = await playwright_handler.page.query_selector('.view-count')
                if view_elem:
                    view_text = await view_elem.text_content()
                    article_data['view_count'] = self._extract_number(view_text)

                # 点赞数
                like_elem = await playwright_handler.page.query_selector('.like-count')
                if like_elem:
                    like_text = await like_elem.text_content()
                    article_data['like_count'] = self._extract_number(like_text)

                # 评论数
                comment_elem = await playwright_handler.page.query_selector('.comment-count')
                if comment_elem:
                    comment_text = await comment_elem.text_content()
                    article_data['comment_count'] = self._extract_number(comment_text)
            except:
                pass

            # 文章内容
            try:
                content_elem = await playwright_handler.page.query_selector('.article-content')
                if content_elem:
                    article_data['content'] = await content_elem.text_content()
                    article_data['content'] = article_data['content'].strip()
                    article_data['summary'] = self._generate_summary(article_data['content'])
                else:
                    logger.warning(f"未找到文章内容: {url}")
                    article_data['content'] = ""
                    article_data['summary'] = ""
            except:
                article_data['content'] = ""
                article_data['summary'] = ""

            # 提取关键词
            full_text = f"{article_data['title']} {article_data['content']}"
            article_data['keywords'] = self._extract_keywords(full_text)

            # 验证数据
            if not article_data['title'] or not article_data['content']:
                logger.warning(f"文章数据不完整: {url}")
                return None

            logger.info(f"解析成功: {article_data['title'][:50]}...")
            return article_data

        except Exception as e:
            logger.error(f"解析文章失败: {url}, 错误: {e}")
            return None

    async def crawl_articles(self, keywords: List[str] = None, max_pages: int = 3) -> int:
        """
        爬取文章
        :param keywords: 关键词列表，默认使用AI关键词
        :param max_pages: 最大页数
        :return: 成功爬取的文章数量
        """
        if keywords is None:
            keywords = ['AI', 'GPT', '机器学习', '前端']

        total_count = 0

        try:
            # 启动浏览器
            await playwright_handler.start_browser(headless=True)

            for keyword in keywords:
                logger.info(f"开始爬取关键词: {keyword}")

                for page in range(1, max_pages + 1):
                    # 搜索文章
                    article_urls = await self.search_articles(keyword, page, limit=15)

                    if not article_urls:
                        logger.info(f"第 {page} 页没有找到文章，跳过")
                        continue

                    # 解析每篇文章
                    for url in article_urls:
                        article_data = await self.parse_article(url)
                        if article_data and sqlite_storage.save_article(article_data):
                            total_count += 1

                        # 延迟避免请求过快
                        await asyncio.sleep(2)

                    # 页面间延迟
                    await asyncio.sleep(3)

                logger.info(f"关键词 '{keyword}' 爬取完成")

        except Exception as e:
            logger.error(f"爬取过程出错: {e}")

        finally:
            # 关闭浏览器
            await playwright_handler.close_browser()

        logger.info(f"总共爬取了 {total_count} 篇文章")
        return total_count

    def _extract_number(self, text: str) -> int:
        """从文本中提取数字"""
        try:
            if not text:
                return 0

            # 处理带单位的数字
            text = text.replace(',', '').replace('k', '000').replace('w', '0000')
            match = re.search(r'\d+', text)
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
    async def main():
        spider = JuejinSpider()
        await spider.crawl_articles(['AI', 'GPT'], max_pages=2)

    asyncio.run(main())