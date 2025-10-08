"""
请求处理工具
支持requests和playwright两种方式
"""
import asyncio
import time
import random
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import requests
from fake_useragent import UserAgent
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from utils.logger import logger
from config.settings import CRAWL_CONFIG


class RequestHandler:
    """请求处理器"""

    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.setup_session()

    def setup_session(self):
        """配置requests会话"""
        # 设置重试策略
        retry_strategy = requests.adapters.HTTPAdapter(
            max_retries=CRAWL_CONFIG["MAX_RETRIES"]
        )
        self.session.mount("http://", retry_strategy)
        self.session.mount("https://", retry_strategy)

        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def get(self, url: str, headers: Optional[Dict] = None, **kwargs) -> Optional[requests.Response]:
        """GET请求"""
        try:
            # 合并请求头
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)

            # 随机延迟避免请求过快
            time.sleep(random.uniform(0.5, 1.5))

            response = self.session.get(
                url,
                headers=request_headers,
                timeout=CRAWL_CONFIG["REQUEST_TIMEOUT"],
                **kwargs
            )
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
            return None

    def post(self, url: str, data: Optional[Dict] = None,
             headers: Optional[Dict] = None, **kwargs) -> Optional[requests.Response]:
        """POST请求"""
        try:
            request_headers = self.session.headers.copy()
            if headers:
                request_headers.update(headers)

            time.sleep(random.uniform(0.5, 1.5))

            response = self.session.post(
                url,
                data=data,
                headers=request_headers,
                timeout=CRAWL_CONFIG["REQUEST_TIMEOUT"],
                **kwargs
            )
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"POST请求失败: {url}, 错误: {e}")
            return None


class PlaywrightHandler:
    """Playwright浏览器处理器"""

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None

    async def start_browser(self, headless: bool = True):
        """启动浏览器"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=headless,
                slow_mo=CRAWL_CONFIG["BROWSER_SLOW_MO"]
            )

            # 创建浏览器上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )

            # 创建页面
            self.page = await self.context.new_page()

            # 设置请求头
            await self.page.set_extra_http_headers({
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })

            logger.info("浏览器启动成功")
            return True

        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            return False

    async def get_page(self, url: str, wait_for: Optional[str] = None) -> Optional[str]:
        """获取页面内容"""
        try:
            if not self.page:
                await self.start_browser()

            # 随机延迟
            await asyncio.sleep(random.uniform(1, 3))

            # 访问页面
            await self.page.goto(url, timeout=CRAWL_CONFIG["BROWSER_TIMEOUT"] * 1000)

            # 等待特定元素
            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=10000)

            # 等待页面加载完成
            await self.page.wait_for_load_state('networkidle')

            # 获取页面HTML
            content = await self.page.content()
            return content

        except Exception as e:
            logger.error(f"获取页面失败: {url}, 错误: {e}")
            return None

    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")


# 全局请求处理器实例
request_handler = RequestHandler()
playwright_handler = PlaywrightHandler()