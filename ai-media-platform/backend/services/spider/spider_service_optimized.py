"""
智能爬虫服务 - 基于真实抓取功能
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from pathlib import Path


class SpiderService:
    """智能爬虫服务类"""

    def __init__(self, config: Dict = None):
        """初始化爬虫服务"""
        self.config = config or {}

        # 支持的平台配置
        self.platforms = {
            "csdn": {
                "name": "CSDN",
                "available": True,
                "base_url": "https://blog.csdn.net"
            },
            "juejin": {
                "name": "掘金",
                "available": True,
                "base_url": "https://juejin.cn"
            },
            "zhihu": {
                "name": "知乎",
                "available": True,
                "base_url": "https://www.zhihu.com"
            },
            "toutiao": {
                "name": "今日头条",
                "available": True,
                "base_url": "https://www.toutiao.com"
            },
            "xiaohongshu": {
                "name": "小红书",
                "available": True,
                "base_url": "https://www.xiaohongshu.com"
            },
            "weibo": {
                "name": "微博",
                "available": True,
                "base_url": "https://weibo.com"
            }
        }

        # 通用请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }

        print("🕷️ 智能爬虫服务初始化完成")

    async def crawl_article(self, url: str, mode: str = "content", depth: int = 1,
                          filters: List[str] = None, delay: float = 1.0) -> Dict[str, Any]:
        """抓取文章内容"""
        print(f"🎯 开始抓取: {url}")
        print(f"   模式: {mode}")
        print(f"   深度: {depth}")
        print(f"   过滤器: {filters or []}")

        # 自动识别平台
        platform = self._identify_platform(url)
        print(f"   识别平台: {platform} ({self.platforms.get(platform, {}).get('name', '通用')})")

        try:
            # 添加延迟
            if delay > 0:
                await asyncio.sleep(delay)

            # 获取网页内容
            content = await self._fetch_content(url)
            if not content:
                return self._create_error_response(url, platform, "无法获取页面内容")

            # 解析内容
            article_data = await self._parse_content(content, url, platform, mode)

            # 应用过滤器
            if filters:
                article_data = self._apply_filters(article_data, filters)

            # 统计信息
            article_data.update({
                "crawl_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "platform": platform,
                "mode": mode,
                "depth": depth,
                "filters": filters or [],
                "word_count": len(article_data.get("content", "")),
                "image_count": len(article_data.get("images", [])),
                "link_count": len(article_data.get("links", []))
            })

            print(f"✅ 抓取完成: {article_data.get('title', 'unknown')}")
            print(f"   字数: {article_data['word_count']}")
            print(f"   图片: {article_data['image_count']}张")
            print(f"   链接: {article_data['link_count']}个")

            return article_data

        except Exception as e:
            print(f"❌ 抓取失败: {str(e)}")
            return self._create_error_response(url, platform, str(e))

    def _identify_platform(self, url: str) -> str:
        """根据URL识别平台"""
        domain = urlparse(url).netloc.lower()

        for platform_id, platform_info in self.platforms.items():
            if platform_id in domain or platform_info["base_url"].split("//")[1] in domain:
                return platform_id

        return "general"

    async def _fetch_content(self, url: str) -> Optional[str]:
        """获取网页内容"""
        timeout = aiohttp.ClientTimeout(total=30)

        try:
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"📄 页面获取成功，内容长度: {len(content)}")
                        return content
                    else:
                        print(f"⚠️ 页面获取失败，状态码: {response.status}")
                        return None

        except asyncio.TimeoutError:
            print(f"⏰ 请求超时: {url}")
            return None
        except Exception as e:
            print(f"🌐 网络请求失败: {str(e)}")
            return None

    async def _parse_content(self, html: str, url: str, platform: str, mode: str) -> Dict[str, Any]:
        """解析页面内容"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 根据平台选择解析策略
            if platform == "csdn":
                return await self._parse_csdn(soup, url, mode)
            elif platform == "juejin":
                return await self._parse_juejin(soup, url, mode)
            elif platform == "zhihu":
                return await self._parse_zhihu(soup, url, mode)
            elif platform == "toutiao":
                return await self._parse_toutiao(soup, url, mode)
            elif platform == "xiaohongshu":
                return await self._parse_xiaohongshu(soup, url, mode)
            else:
                return await self._parse_general(soup, url, mode)

        except Exception as e:
            print(f"🔍 内容解析失败: {str(e)}")
            return self._create_error_response(url, platform, f"解析失败: {str(e)}")

    async def _parse_csdn(self, soup: BeautifulSoup, url: str, mode: str) -> Dict[str, Any]:
        """解析CSDN文章"""
        # 标题
        title_elem = soup.find('h1', class_='article-title') or soup.find('h1') or soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "未知标题"

        # 作者
        author_elem = soup.find('a', class_='author') or soup.find('span', class_='author-name')
        author = author_elem.get_text().strip() if author_elem else "未知作者"

        # 发布时间
        time_elem = soup.find('span', class_='time') or soup.find('div', class_='article-info-box')
        publish_time = time_elem.get_text().strip() if time_elem else datetime.now().strftime('%Y-%m-%d')

        # 内容
        content_elem = soup.find('div', class_='article-content') or soup.find('div', id='content_views') or soup.find('article')
        content = self._extract_text(content_elem) if content_elem else ""

        # 图片和链接
        images = self._extract_images(soup, url)
        links = self._extract_links(soup, url)

        # 关键词
        keywords = self._extract_keywords(soup)

        return {
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "content": content,
            "images": images,
            "links": links,
            "keywords": keywords,
            "url": url,
            "platform": "csdn"
        }

    async def _parse_juejin(self, soup: BeautifulSoup, url: str, mode: str) -> Dict[str, Any]:
        """解析掘金文章"""
        # 标题
        title_elem = soup.find('h1', class_='article-title') or soup.find('h1')
        title = title_elem.get_text().strip() if title_elem else "未知标题"

        # 作者
        author_elem = soup.find('span', class_='username') or soup.find('a', class_='user-name')
        author = author_elem.get_text().strip() if author_elem else "未知作者"

        # 发布时间
        time_elem = soup.find('span', class_='meta-time') or soup.find('time')
        publish_time = time_elem.get_text().strip() if time_elem else datetime.now().strftime('%Y-%m-%d')

        # 内容
        content_elem = soup.find('div', class_='article-content') or soup.find('div', class_='markdown-body')
        content = self._extract_text(content_elem) if content_elem else ""

        # 图片和链接
        images = self._extract_images(soup, url)
        links = self._extract_links(soup, url)

        # 关键词
        keywords = self._extract_keywords(soup)

        return {
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "content": content,
            "images": images,
            "links": links,
            "keywords": keywords,
            "url": url,
            "platform": "juejin"
        }

    async def _parse_zhihu(self, soup: BeautifulSoup, url: str, mode: str) -> Dict[str, Any]:
        """解析知乎文章"""
        # 标题
        title_elem = soup.find('h1', class_='QuestionHeader-title') or soup.find('h1')
        title = title_elem.get_text().strip() if title_elem else "未知标题"

        # 作者
        author_elem = soup.find('span', class_='UserLink-link') or soup.find('a', class_='author-link')
        author = author_elem.get_text().strip() if author_elem else "未知作者"

        # 发布时间
        time_elem = soup.find('span', class_='ContentItem-time') or soup.find('time')
        publish_time = time_elem.get_text().strip() if time_elem else datetime.now().strftime('%Y-%m-%d')

        # 内容
        content_elem = soup.find('div', class_='RichText') or soup.find('div', class_='Post-RichText')
        content = self._extract_text(content_elem) if content_elem else ""

        # 图片和链接
        images = self._extract_images(soup, url)
        links = self._extract_links(soup, url)

        # 关键词
        keywords = self._extract_keywords(soup)

        return {
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "content": content,
            "images": images,
            "links": links,
            "keywords": keywords,
            "url": url,
            "platform": "zhihu"
        }

    async def _parse_toutiao(self, soup: BeautifulSoup, url: str, mode: str) -> Dict[str, Any]:
        """解析今日头条文章"""
        # 标题
        title_elem = soup.find('h1', class_='article-title') or soup.find('h1')
        title = title_elem.get_text().strip() if title_elem else "未知标题"

        # 作者
        author_elem = soup.find('a', class_='user-name') or soup.find('span', class_='name')
        author = author_elem.get_text().strip() if author_elem else "未知作者"

        # 发布时间
        time_elem = soup.find('time') or soup.find('span', class_='time')
        publish_time = time_elem.get_text().strip() if time_elem else datetime.now().strftime('%Y-%m-%d')

        # 内容
        content_elem = soup.find('div', class_='article-content') or soup.find('div', class_='content')
        content = self._extract_text(content_elem) if content_elem else ""

        # 图片和链接
        images = self._extract_images(soup, url)
        links = self._extract_links(soup, url)

        # 关键词
        keywords = self._extract_keywords(soup)

        return {
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "content": content,
            "images": images,
            "links": links,
            "keywords": keywords,
            "url": url,
            "platform": "toutiao"
        }

    async def _parse_xiaohongshu(self, soup: BeautifulSoup, url: str, mode: str) -> Dict[str, Any]:
        """解析小红书内容"""
        # 标题
        title_elem = soup.find('div', class_='title') or soup.find('h1')
        title = title_elem.get_text().strip() if title_elem else "未知标题"

        # 作者
        author_elem = soup.find('span', class_='username') or soup.find('a', class_='author')
        author = author_elem.get_text().strip() if author_elem else "未知作者"

        # 发布时间
        time_elem = soup.find('span', class_='publish-time') or soup.find('time')
        publish_time = time_elem.get_text().strip() if time_elem else datetime.now().strftime('%Y-%m-%d')

        # 内容
        content_elem = soup.find('div', class_='content') or soup.find('div', class_='desc')
        content = self._extract_text(content_elem) if content_elem else ""

        # 图片和链接
        images = self._extract_images(soup, url)
        links = self._extract_links(soup, url)

        # 关键词
        keywords = self._extract_keywords(soup)

        return {
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "content": content,
            "images": images,
            "links": links,
            "keywords": keywords,
            "url": url,
            "platform": "xiaohongshu"
        }

    async def _parse_general(self, soup: BeautifulSoup, url: str, mode: str) -> Dict[str, Any]:
        """通用解析器"""
        # 标题
        title_elem = soup.find('title') or soup.find('h1')
        title = title_elem.get_text().strip() if title_elem else "未知标题"

        # 尝试提取作者
        author_selectors = ['author', 'byline', 'username', 'user-name', 'writer']
        author = "未知作者"
        for selector in author_selectors:
            author_elem = soup.find('span', class_=selector) or soup.find('div', class_=selector) or soup.find('a', class_=selector)
            if author_elem:
                author = author_elem.get_text().strip()
                break

        # 尝试提取发布时间
        time_selectors = ['time', 'publish-time', 'date', 'timestamp', 'meta-time']
        publish_time = datetime.now().strftime('%Y-%m-%d')
        for selector in time_selectors:
            time_elem = soup.find('time') or soup.find('span', class_=selector) or soup.find('div', class_=selector)
            if time_elem:
                publish_time = time_elem.get_text().strip()
                break

        # 内容提取
        content_selectors = ['content', 'article-content', 'post-content', 'entry-content', 'main-content']
        content = ""
        for selector in content_selectors:
            content_elem = soup.find('div', class_=selector) or soup.find('article') or soup.find('main')
            if content_elem:
                content = self._extract_text(content_elem)
                break

        # 如果没有找到内容，尝试提取body文本
        if not content:
            body_elem = soup.find('body')
            if body_elem:
                content = self._extract_text(body_elem)

        # 图片和链接
        images = self._extract_images(soup, url)
        links = self._extract_links(soup, url)

        # 关键词
        keywords = self._extract_keywords(soup)

        return {
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "content": content,
            "images": images,
            "links": links,
            "keywords": keywords,
            "url": url,
            "platform": "general"
        }

    def _extract_text(self, element) -> str:
        """提取元素中的纯文本"""
        if not element:
            return ""

        # 移除script和style标签
        for script in element(["script", "style"]):
            script.decompose()

        # 获取文本内容
        text = element.get_text()

        # 清理空白字符
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """提取图片信息"""
        images = []
        img_elements = soup.find_all('img')

        for img in img_elements:
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            alt = img.get('alt', '')

            if src:
                # 转换为绝对URL
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)

                images.append({
                    "url": src,
                    "alt": alt
                })

        return images

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """提取链接信息"""
        links = []
        link_elements = soup.find_all('a', href=True)

        for link in link_elements:
            href = link.get('href')
            text = link.get_text().strip()

            if href and text:
                # 转换为绝对URL
                if href.startswith('/'):
                    href = urljoin(base_url, href)
                elif not href.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                    href = urljoin(base_url, href)

                links.append({
                    "url": href,
                    "text": text
                })

        return links

    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """提取关键词"""
        keywords = []

        # 从meta标签提取
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            content = meta_keywords.get('content', '')
            keywords.extend([kw.strip() for kw in content.split(',') if kw.strip()])

        # 从标签云或分类提取
        tag_elements = soup.find_all(['span', 'a'], class_=re.compile(r'tag|category|label'))
        for tag_elem in tag_elements:
            tag_text = tag_elem.get_text().strip()
            if tag_text and len(tag_text) < 20:  # 避免长文本
                keywords.append(tag_text)

        return list(set(keywords))  # 去重

    def _apply_filters(self, data: Dict[str, Any], filters: List[str]) -> Dict[str, Any]:
        """应用过滤器"""
        if not filters:
            return data

        # 过滤广告
        if 'ads' in filters:
            content = data.get('content', '')
            # 移除常见的广告文本模式
            ad_patterns = [
                r'广告.*?推广',
                r'赞助.*?内容',
                r'点击.*?购买',
                r'立即.*?下单',
                r'优惠.*?活动'
            ]
            for pattern in ad_patterns:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            data['content'] = content

        # 过滤脚本和样式
        if 'scripts' in filters or 'styles' in filters:
            # 在文本提取阶段已经处理了脚本和样式
            pass

        # 过滤评论
        if 'comments' in filters:
            content = data.get('content', '')
            # 移除常见的评论模式
            comment_patterns = [
                r'网友说.*? ',
                r'用户评论.*? ',
                r'大家觉得.*? ',
                r'我觉得.*? '
            ]
            for pattern in comment_patterns:
                content = re.sub(pattern, '', content, flags=re.IGNORECASE)
            data['content'] = content

        return data

    def _create_error_response(self, url: str, platform: str, error_msg: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "title": "抓取失败",
            "author": "未知",
            "publish_time": datetime.now().strftime('%Y-%m-%d'),
            "content": "",
            "images": [],
            "links": [],
            "keywords": [],
            "url": url,
            "platform": platform,
            "error": error_msg,
            "crawl_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "word_count": 0,
            "image_count": 0,
            "link_count": 0
        }

    def get_supported_platforms(self) -> List[Dict[str, Any]]:
        """获取支持的平台列表"""
        return [
            {
                "id": platform_id,
                "name": info["name"],
                "available": info["available"],
                "base_url": info["base_url"]
            }
            for platform_id, info in self.platforms.items()
        ]

    async def batch_crawl(self, urls: List[str], **kwargs) -> List[Dict[str, Any]]:
        """批量抓取"""
        results = []

        for i, url in enumerate(urls):
            print(f"🔄 批量抓取进度: {i+1}/{len(urls)} - {url}")

            try:
                result = await self.crawl_article(url, **kwargs)
                results.append({
                    "index": i + 1,
                    "url": url,
                    "status": "success" if result.get("error") is None else "error",
                    "data": result
                })
            except Exception as e:
                results.append({
                    "index": i + 1,
                    "url": url,
                    "status": "error",
                    "error": str(e)
                })

        return results


def get_spider_service(config: Dict = None) -> SpiderService:
    """获取爬虫服务实例"""
    return SpiderService(config)