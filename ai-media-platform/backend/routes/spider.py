"""
智能爬虫API路由
提供真实的网页爬取功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
from loguru import logger
import asyncio
import time
from datetime import datetime

# 导入爬虫模块
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 导入优化的爬虫服务
try:
    from services.spider.spider_service_optimized import get_spider_service
    SPIDER_SERVICE_AVAILABLE = True
    logger.info("优化爬虫服务导入成功")
except ImportError as e:
    logger.warning(f"优化爬虫服务导入失败: {e}，使用模拟服务")
    SPIDER_SERVICE_AVAILABLE = False

router = APIRouter(prefix="/api/v1/spider", tags=["智能爬虫"])

# 全局爬虫服务实例
_spider_service = None

def get_spider_service_instance():
    """获取爬虫服务实例"""
    global _spider_service
    if _spider_service is None and SPIDER_SERVICE_AVAILABLE:
        # 这里可以从app.state.config获取配置
        config = {}
        _spider_service = get_spider_service(config)
    return _spider_service


class SpiderRequest(BaseModel):
    """爬虫请求模型"""
    url: HttpUrl
    mode: str = "content"  # full, content, title, images, videos, social
    depth: int = 1
    filters: List[str] = ["ads", "scripts"]
    delay: float = 1.0


class SpiderResponse(BaseModel):
    """爬虫响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class BatchSpiderRequest(BaseModel):
    """批量爬虫请求模型"""
    urls: List[HttpUrl]
    mode: str = "content"
    depth: int = 1
    filters: List[str] = ["ads", "scripts"]
    delay: float = 1.0


async def crawl_single_url(url: str, mode: str = "content") -> Dict[str, Any]:
    """爬取单个URL"""
    try:
        logger.info(f"开始爬取: {url}")

        # 根据不同的网站选择不同的爬虫策略
        if "csdn.net" in url:
            # 使用我们已经测试过的CSDN爬虫
            result = await asyncio.to_thread(crawl_csdn_article, url)
        elif "zhihu.com" in url:
            # 知乎爬虫
            result = await asyncio.to_thread(crawl_general_article, url)
        elif "juejin.cn" in url:
            # 掘金爬虫
            result = await asyncio.to_thread(crawl_general_article, url)
        else:
            # 通用爬虫
            result = await asyncio.to_thread(crawl_general_article, url)

        return result

    except Exception as e:
        logger.error(f"爬取失败 {url}: {e}")
        return {
            "success": False,
            "error": str(e),
            "url": url
        }


def crawl_csdn_article(url: str) -> Dict[str, Any]:
    """爬取CSDN文章 - 基于我们测试过的代码"""
    import requests
    from bs4 import BeautifulSoup
    import json
    import re

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.csdn.net/',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取标题
        title_elem = soup.find('h1', class_='title-article') or soup.find('h1')
        title = title_elem.get_text().strip() if title_elem else "无标题"

        # 提取作者
        author_elem = soup.find('a', class_='follow-nickName')
        author = author_elem.get_text().strip() if author_elem else "未知作者"

        # 提取发布时间
        time_elem = soup.find('span', class_='time')
        publish_time = time_elem.get_text().strip() if time_elem else datetime.now().strftime('%Y-%m-%d')

        # 提取内容
        content_elem = soup.find('div', id='content_views') or soup.find('div', class_='markdown_views')
        if content_elem:
            # 移除不需要的元素
            for unwanted in content_elem.find_all(['script', 'style', 'nav', 'footer', 'iframe']):
                unwanted.decompose()

            content = content_elem.get_text().strip()

            # 提取图片
            images = []
            for img in content_elem.find_all('img'):
                img_src = img.get('src') or img.get('data-src')
                if img_src:
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    elif not img_src.startswith('http'):
                        img_src = f"https:{img_src}"

                    images.append({
                        "url": img_src,
                        "alt": img.get('alt', '')
                    })

            # 提取链接
            links = []
            for link in content_elem.find_all('a'):
                href = link.get('href')
                if href and href.startswith('http'):
                    links.append({
                        "url": href,
                        "text": link.get_text().strip()
                    })
        else:
            content = ""
            images = []
            links = []

        # 提取关键词
        content_lower = content.lower()
        ai_keywords = ['人工智能', 'ai', '机器学习', '深度学习', '神经网络', 'python', '算法', '数据科学', '编程', '技术']
        found_keywords = [kw for kw in ai_keywords if kw.lower() in content_lower]

        return {
            "success": True,
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "content": content,
            "word_count": len(content),
            "image_count": len(images),
            "link_count": len(links),
            "images": images[:10],  # 限制图片数量
            "links": links[:20],   # 限制链接数量
            "keywords": found_keywords[:10],
            "crawl_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "url": url
        }

    except Exception as e:
        logger.error(f"CSDN爬取失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "url": url
        }


def crawl_general_article(url: str) -> Dict[str, Any]:
    """通用文章爬虫"""
    import requests
    from bs4 import BeautifulSoup
    import re

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # 提取标题
        title_elem = soup.find('h1')
        if not title_elem:
            title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "无标题"

        # 提取内容
        content_elem = soup.find('article') or soup.find('div', class_=re.compile(r'content|article|post')) or soup.find('main')
        if content_elem:
            # 移除不需要的元素
            for unwanted in content_elem.find_all(['script', 'style', 'nav', 'footer', 'aside', 'iframe']):
                unwanted.decompose()

            content = content_elem.get_text().strip()
        else:
            # 如果没找到主要内容区域，使用body
            body = soup.find('body')
            if body:
                for unwanted in body.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                    unwanted.decompose()
                content = body.get_text().strip()
            else:
                content = ""

        # 提取图片
        images = []
        for img in soup.find_all('img')[:10]:
            img_src = img.get('src') or img.get('data-src')
            if img_src and (img_src.startswith('http') or img_src.startswith('//')):
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                images.append({
                    "url": img_src,
                    "alt": img.get('alt', '')
                })

        # 提取链接
        links = []
        for link in soup.find_all('a')[:20]:
            href = link.get('href')
            if href and href.startswith('http'):
                links.append({
                    "url": href,
                    "text": link.get_text().strip()[:50]
                })

        return {
            "success": True,
            "title": title,
            "content": content,
            "word_count": len(content),
            "image_count": len(images),
            "link_count": len(links),
            "images": images,
            "links": links,
            "keywords": [],
            "crawl_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "url": url
        }

    except Exception as e:
        logger.error(f"通用爬取失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "url": url
        }


@router.post("/crawl", response_model=SpiderResponse)
async def crawl_url(request: SpiderRequest):
    """爬取单个URL"""
    try:
        if not request.url:
            raise HTTPException(status_code=400, detail="URL不能为空")

        # 优先使用优化服务
        spider_service = get_spider_service_instance()
        if spider_service:
            logger.info("使用优化爬虫服务")
            result = await spider_service.crawl_article(
                url=str(request.url),
                mode=request.mode,
                depth=request.depth,
                filters=request.filters,
                delay=request.delay
            )

            if result and not result.get("error"):
                return SpiderResponse(
                    success=True,
                    message="爬取成功",
                    data=result
                )
            else:
                return SpiderResponse(
                    success=False,
                    message=f"爬取失败: {result.get('error', '未知错误') if result else '服务不可用'}",
                    data=result
                )
        else:
            # 回退到原始实现
            logger.info("使用原始爬虫实现")
            await asyncio.sleep(request.delay)
            result = await crawl_single_url(str(request.url), request.mode)

            if result["success"]:
                return SpiderResponse(
                    success=True,
                    message="爬取成功",
                    data=result
                )
            else:
                return SpiderResponse(
                    success=False,
                    message=f"爬取失败: {result.get('error', '未知错误')}",
                    data=result
                )

    except Exception as e:
        logger.error(f"爬虫API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-crawl")
async def batch_crawl_urls(request: BatchSpiderRequest, background_tasks: BackgroundTasks):
    """批量爬取URLs"""
    if not request.urls:
        raise HTTPException(status_code=400, detail="URL列表不能为空")

    if len(request.urls) > 10:
        raise HTTPException(status_code=400, detail="一次最多批量爬取10个URL")

    results = []

    for i, url in enumerate(request.urls):
        try:
            # 每个请求之间添加延迟
            if i > 0:
                await asyncio.sleep(request.delay)

            result = await crawl_single_url(str(url), request.mode)
            results.append(result)

        except Exception as e:
            logger.error(f"批量爬取失败 {url}: {e}")
            results.append({
                "success": False,
                "error": str(e),
                "url": str(url)
            })

    success_count = sum(1 for r in results if r.get("success", False))

    return {
        "success": True,
        "message": f"批量爬取完成，成功 {success_count}/{len(request.urls)} 个",
        "data": {
            "results": results,
            "summary": {
                "total": len(request.urls),
                "success": success_count,
                "failed": len(request.urls) - success_count
            }
        }
    }


@router.get("/recommend-sites")
async def get_recommend_sites():
    """获取推荐网站"""
    sites = [
        {
            "name": "CSDN",
            "url": "https://blog.csdn.net",
            "description": "专业技术博客平台",
            "category": "技术"
        },
        {
            "name": "知乎热榜",
            "url": "https://www.zhihu.com/hot",
            "description": "热门话题讨论",
            "category": "热点"
        },
        {
            "name": "掘金",
            "url": "https://juejin.cn/hot/articles/1",
            "description": "技术文章分享",
            "category": "技术"
        },
        {
            "name": "今日头条",
            "url": "https://www.toutiao.com",
            "description": "新闻资讯平台",
            "category": "新闻"
        }
    ]

    return {
        "success": True,
        "data": sites
    }


@router.get("/health")
async def spider_health():
    """爬虫服务健康检查"""
    return {
        "status": "healthy",
        "service": "spider",
        "timestamp": datetime.now().isoformat(),
        "supported_sites": ["csdn.net", "zhihu.com", "juejin.cn", "general"],
        "features": ["single_crawl", "batch_crawl", "content_extraction", "image_extraction"]
    }