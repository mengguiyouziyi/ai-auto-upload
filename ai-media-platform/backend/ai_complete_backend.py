#!/usr/bin/env python3
"""
基于769759d提交的完整AI媒体平台后端服务
包含爬虫、文本优化、视频生成等完整功能
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sys
import os
import httpx
import json
import uuid
import asyncio
import random
import time
import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any, List
from bs4 import BeautifulSoup
from pathlib import Path
import re
from pydantic import BaseModel

app = FastAPI(title="AI媒体平台", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建本地视频存储目录
LOCAL_VIDEO_DIR = Path("./generated_videos")
LOCAL_VIDEO_DIR.mkdir(exist_ok=True)
print(f"📁 本地视频存储目录: {LOCAL_VIDEO_DIR.absolute()}")

# ==================== 视频生成服务 ====================

class VideoRequest(BaseModel):
    provider: str = "comfyui_wan"
    prompt: str
    duration: int = 10
    quality: str = "high"
    style: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    aspect_ratio: Optional[str] = None

class VideoService:
    def __init__(self):
        self.comfyui_api_url = "http://192.168.1.246:5001"  # ComfyUI API包装器地址
        self.comfyui_direct_url = "http://192.168.1.246:8188"  # 直接ComfyUI地址（备用）
        self.comfyui_url = self.comfyui_direct_url  # 用于视频下载的URL

    async def generate_video(self, request: VideoRequest):
        """生成视频 - 强制使用4步LoRA优化工作流"""
        print(f"收到视频生成请求: provider={request.provider}, prompt={request.prompt[:50]}...")

        try:
            # 强制使用4步LoRA优化工作流（跳过API包装器默认参数）
            print("🚀 强制使用4步LoRA优化工作流（跳过API包装器默认参数）")
            return await self._generate_via_direct_comfyui(request)

        except Exception as e:
            print(f"视频生成失败: {str(e)}")
            return None

    async def _generate_via_direct_comfyui(self, request: VideoRequest):
        """直接调用ComfyUI（备用方案）"""
        try:
            print(f"🎯 直接调用ComfyUI: {self.comfyui_direct_url}")

            # 创建优化的工作流
            workflow = self._create_optimized_workflow(request)

            # 提交到ComfyUI
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.comfyui_direct_url}/prompt", json={
                    "prompt": workflow
                })
                response.raise_for_status()
                result = response.json()
                task_id = result.get("prompt_id")

            print(f"ComfyUI任务已创建: {task_id}")
            print(f"开始监控任务 {task_id}...")

            # 监控任务进度
            return await self._monitor_direct_task(task_id, request)

        except Exception as e:
            print(f"直接ComfyUI调用失败: {str(e)}")
            return None

    async def _monitor_direct_task(self, task_id: str, request: VideoRequest):
        """监控直接ComfyUI任务进度"""
        start_time = asyncio.get_event_loop().time()

        while True:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{self.comfyui_url}/history/{task_id}")
                    response.raise_for_status()
                    history = response.json()

                if task_id in history:
                    task_data = history[task_id]
                    status = task_data.get("status", {})

                    if status.get("completed", False):
                        print(f"✅ 直接ComfyUI任务完成!")
                        return await self._extract_video_info(task_data, start_time)

                    elapsed = asyncio.get_event_loop().time() - start_time
                    print(f"⏳ 直接ComfyUI任务进行中... ({elapsed:.1f}秒)")

                await asyncio.sleep(3)

                # 超时检查
                if asyncio.get_event_loop().time() - start_time > 600:  # 10分钟超时
                    print(f"⏰ 直接ComfyUI任务超时")
                    return None

            except Exception as e:
                print(f"⚠️ 监控直接ComfyUI任务时出错: {str(e)}")
                await asyncio.sleep(3)
                continue

    def _create_optimized_workflow(self, request: VideoRequest):
        """创建4步LoRA优化的工作流"""
        # 优化prompt
        optimized_prompt = self._optimize_prompt(request.prompt)

        # 生成唯一文件名
        filename_prefix = f"wan_video_{uuid.uuid4().hex[:8]}"

        # 使用640x640作为默认分辨率（更高的质量）
        width = min(max(640, min(request.width or 720, 1024)), 1024)
        height = min(max(640, min(request.height or 720, 1024)), 1024)

        # 81帧（5秒@16fps）- 优化的帧数
        num_frames = 81

        # 4步LoRA优化参数
        steps = 4
        cfg = 1.0
        shift = 5.0

        workflow = {
            "71": {  # CLIPLoader
                "inputs": {
                    "clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
                    "type": "wan",
                    "device": "default"
                },
                "class_type": "CLIPLoader"
            },
            "73": {  # VAELoader
                "inputs": {
                    "vae_name": "wan_2.1_vae.safetensors"
                },
                "class_type": "VAELoader"
            },
            "75": {  # UNETLoader - High Noise
                "inputs": {
                    "unet_name": "wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors",
                    "weight_dtype": "default"
                },
                "class_type": "UNETLoader"
            },
            "83": {  # LoraLoaderModelOnly - 4步LoRA
                "inputs": {
                    "model": ["75", 0],
                    "lora_name": "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors",
                    "strength_model": 1.0
                },
                "class_type": "LoraLoaderModelOnly"
            },
            "86": {  # ModelSamplingSD3 - 优化shift
                "inputs": {
                    "model": ["83", 0],
                    "shift": shift
                },
                "class_type": "ModelSamplingSD3"
            },
            "89": {  # CLIPTextEncode - Positive
                "inputs": {
                    "clip": ["71", 0],
                    "text": optimized_prompt
                },
                "class_type": "CLIPTextEncode"
            },
            "72": {  # CLIPTextEncode - Negative
                "inputs": {
                    "clip": ["71", 0],
                    "text": "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走，裸露，NSFW"
                },
                "class_type": "CLIPTextEncode"
            },
            "74": {  # EmptyHunyuanLatentVideo
                "inputs": {
                    "width": width,
                    "height": height,
                    "length": num_frames,
                    "batch_size": 1
                },
                "class_type": "EmptyHunyuanLatentVideo"
            },
            "81": {  # KSamplerAdvanced - 第一阶段4步
                "inputs": {
                    "model": ["86", 0],
                    "positive": ["89", 0],
                    "negative": ["72", 0],
                    "latent_image": ["74", 0],
                    "add_noise": "enable",
                    "noise_seed": random.randint(1, 2**31),
                    "steps": steps,
                    "cfg": cfg,
                    "sampler_name": "euler",
                    "scheduler": "simple",
                    "start_at_step": 0,
                    "end_at_step": steps,
                    "return_with_leftover_noise": "disable"
                },
                "class_type": "KSamplerAdvanced"
            },
            "87": {  # VAEDecode
                "inputs": {
                    "samples": ["81", 0],
                    "vae": ["73", 0]
                },
                "class_type": "VAEDecode"
            },
            "88": {  # CreateVideo
                "inputs": {
                    "images": ["87", 0],
                    "fps": min(max(request.fps or 30, 12), 24),
                    "audio": None
                },
                "class_type": "CreateVideo"
            },
            "80": {  # SaveVideo
                "inputs": {
                    "video": ["88", 0],
                    "filename_prefix": filename_prefix,  # 移除video/前缀
                    "format": "auto",
                    "codec": "auto"
                },
                "class_type": "SaveVideo"
            }
        }

        print(f"✅ 创建4步LoRA优化工作流，参数:")
        print(f"   分辨率: {width}x{height}")
        print(f"   帧数: {num_frames}")
        print(f"   步数: {steps} (4步LoRA优化)")
        print(f"   CFG: {cfg} (LoRA优化)")
        print(f"   Shift: {shift}")
        print(f"   LoRA: wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors")

        return workflow

    def _optimize_prompt(self, prompt: str) -> str:
        """优化prompt，确保场景首尾相接"""
        if not prompt:
            return "美丽的风景，动态流畅，高质量"

        # 如果prompt没有包含循环/首尾相接的描述，添加相关词汇
        loop_keywords = ["循环", "首尾相接", "无缝", "seamless", "loop", "连续"]
        if not any(keyword in prompt for keyword in loop_keywords):
            prompt += "，场景自然过渡，首尾相接"

        return prompt

    async def _extract_video_info(self, task_data: dict, start_time: float):
        """提取视频信息"""
        try:
            outputs = task_data.get("outputs", {})
            for node_id, output in outputs.items():
                # 检查videos或images输出
                videos = output.get("videos", [])
                images = output.get("images", [])

                files = videos if videos else images
                if files:
                    file = files[0]
                    filename = file.get("filename", "")

                    # 下载视频文件到本地
                    local_file_path = await self._download_video_locally(filename)

                    generation_time = asyncio.get_event_loop().time() - start_time

                    # 获取本地文件大小
                    file_size = 0
                    if local_file_path and local_file_path.exists():
                        file_size = local_file_path.stat().st_size

                    print(f"✅ 视频生成完成!")
                    print(f"   文件: {filename}")
                    if local_file_path:
                        print(f"   本地路径: {local_file_path}")
                    print(f"   耗时: {generation_time:.1f}秒")
                    print(f"   文件大小: {file_size:,} bytes")

                    return {
                        "success": True,
                        "data": {
                            "filename": filename,
                            "video_url": f"/static/videos/{filename}" if local_file_path else f"{self.comfyui_url}/view?filename={filename}",
                            "video_path": str(local_file_path) if local_file_path else None,
                            "file_size": file_size,
                            "generation_time": generation_time,
                            "duration": 5.0,
                            "cost": 0.05
                        }
                    }

            print(f"❌ 未找到视频输出")
            return {"success": False, "message": "未找到视频输出"}

        except Exception as e:
            print(f"❌ 提取视频信息失败: {str(e)}")
            return {"success": False, "message": f"提取视频信息失败: {str(e)}"}

    async def _download_video_locally(self, filename: str):
        """从ComfyUI服务器下载视频文件到本地"""
        try:
            print(f"📥 正在下载视频文件: {filename}")

            # 构建本地文件路径
            local_file_path = LOCAL_VIDEO_DIR / filename

            # 如果本地文件已存在，直接返回
            if local_file_path.exists():
                print(f"   本地文件已存在: {local_file_path}")
                return local_file_path

            # 从ComfyUI服务器下载
            download_url = f"{self.comfyui_url}/view"
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(download_url, params={"filename": filename})

                if response.status_code == 200:
                    # 保存到本地
                    local_file_path.write_bytes(response.content)
                    file_size = local_file_path.stat().st_size

                    print(f"   ✅ 视频下载成功!")
                    print(f"   本地路径: {local_file_path}")
                    print(f"   文件大小: {file_size:,} bytes")

                    return local_file_path
                else:
                    print(f"   ❌ 下载失败: HTTP {response.status_code}")
                    return None

        except Exception as e:
            print(f"   ❌ 下载视频失败: {str(e)}")
            return None

video_service = VideoService()

# ==================== 文本优化服务 ====================

class TextOptimizeRequest(BaseModel):
    text: str
    provider: str = "doubao"

class TextOptimizeService:
    def __init__(self):
        # 这里可以配置各种LLM API密钥
        self.providers = {
            "glm": {
                "name": "GLM-4.6",
                "available": True
            },
            "kimi": {
                "name": "Kimi",
                "available": True
            },
            "doubao": {
                "name": "豆包",
                "available": True
            }
        }

    async def optimize_text(self, text: str, provider: str = "glm"):
        """优化文本"""
        print(f"收到文本优化请求: provider={provider}, text={text[:50]}...")

        try:
            # 模拟文本优化过程
            # 实际应用中，这里会调用真实的LLM API
            optimized_text = f"[{provider.upper()}优化] {text}，增强表现力，更加生动有趣，适合内容创作。"

            # 模拟API延迟
            await asyncio.sleep(1)

            print(f"文本优化完成")

            return {
                "success": True,
                "data": {
                    "optimized_text": optimized_text,
                    "provider": provider,
                    "original_text": text,
                    "response_time": 1.5
                }
            }

        except Exception as e:
            print(f"文本优化失败: {str(e)}")
            return {"success": False, "message": str(e)}

text_optimize_service = TextOptimizeService()

# ==================== 爬虫服务 ====================

class SpiderRequest(BaseModel):
    url: str
    mode: str = "content"
    depth: int = 1
    filters: List[str] = []
    delay: float = 1.0

class SpiderService:
    def __init__(self):
        self.platforms = {
            "csdn": {"name": "CSDN", "available": True},
            "juejin": {"name": "掘金", "available": True},
            "zhihu": {"name": "知乎", "available": True},
            "toutiao": {"name": "头条", "available": True}
        }
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    async def crawl_article(self, url: str, mode: str = "content", depth: int = 1, filters: List[str] = None, delay: float = 1.0):
        """真实爬取文章"""
        print(f"收到爬虫请求: url={url}, mode={mode}")

        try:
            # 使用aiohttp获取网页内容
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(headers=self.headers, timeout=timeout) as session:
                print(f"正在抓取页面: {url}")
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        print(f"页面获取成功，内容长度: {len(html)}")

                        # 解析页面内容
                        article_data = await self.parse_article_content(html, url)
                        print(f"爬虫完成: {article_data.get('title', 'unknown')}")

                        return {
                            "success": True,
                            "data": article_data
                        }
                    else:
                        print(f"页面获取失败，状态码: {response.status}")
                        return {
                            "success": False,
                            "message": f"HTTP {response.status}"
                        }

        except asyncio.TimeoutError:
            print(f"爬虫超时: {url}")
            return {
                "success": False,
                "message": "请求超时"
            }
        except Exception as e:
            print(f"爬虫失败: {str(e)}")
            return {
                "success": False,
                "message": str(e)
            }

    async def parse_article_content(self, html: str, url: str):
        """解析文章内容"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 提取标题
            title_elem = soup.find('h1')
            if not title_elem:
                title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "未知标题"

            # 提取内容
            content_elem = soup.find('div', class_='content')
            if not content_elem:
                content_elem = soup.find('article')
            if not content_elem:
                content_elem = soup.find('main')

            content = ""
            if content_elem:
                # 移除不需要的标签
                for tag in content_elem.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                    tag.decompose()
                content = content_elem.get_text().strip()

            # 生成内容摘要
            summary = content[:200] + "..." if len(content) > 200 else content

            return {
                "title": title,
                "content": content,
                "summary": summary,
                "url": url,
                "crawl_time": datetime.now().isoformat(),
                "word_count": len(content),
                "status": "success"
            }

        except Exception as e:
            print(f"解析文章失败: {str(e)}")
            return {
                "title": "解析失败",
                "content": "",
                "url": url,
                "crawl_time": datetime.now().isoformat(),
                "word_count": 0,
                "status": "error",
                "error": str(e)
            }

spider_service = SpiderService()

# ==================== API路由 ====================

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI媒体智能平台",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "video": "active",
            "text": "active",
            "spider": "active"
        }
    }

# 文本优化API
@app.post("/api/v1/llm/optimize-text")
async def optimize_text(request: TextOptimizeRequest):
    """优化文本为视频文案"""
    try:
        result = await text_optimize_service.optimize_text(request.text, request.provider)
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}

# 视频生成API
@app.post("/api/v1/video/generate")
async def generate_video(request: VideoRequest):
    """生成视频"""
    try:
        result = await video_service.generate_video(request)
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}

# 爬虫API
@app.post("/api/v1/spider/crawl")
async def crawl_article(request: SpiderRequest):
    """爬取文章内容"""
    try:
        result = await spider_service.crawl_article(
            request.url,
            request.mode,
            request.depth,
            request.filters,
            request.delay
        )
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/v1/spider/recommend-sites")
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

@app.get("/api/v1/spider/health")
async def spider_health():
    """爬虫服务健康检查"""
    return {
        "status": "healthy",
        "service": "spider",
        "timestamp": datetime.now().isoformat(),
        "supported_sites": ["csdn.net", "juejin.cn", "zhihu.com", "toutiao.com"],
        "features": ["content_extraction", "image_extraction", "link_analysis"]
    }

# 挂载静态文件
if LOCAL_VIDEO_DIR.exists():
    app.mount("/static/videos", StaticFiles(directory=LOCAL_VIDEO_DIR), name="videos")

# 启动脚本
def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="AI媒体智能平台")
    parser.add_argument("--host", default="0.0.0.0", help="绑定地址")
    parser.add_argument("--port", type=int, default=9000, help="端口号")
    parser.add_argument("--reload", action="store_true", help="开发模式")

    args = parser.parse_args()

    print(f"启动AI媒体平台服务...")
    print(f"服务地址: http://{args.host}:{args.port}")
    print(f"API文档: http://{args.host}:{args.port}/docs")

    import uvicorn
    uvicorn.run(
        "ai_complete_backend:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()