#!/usr/bin/env python3
"""
完整的AI媒体平台后端服务
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
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from pathlib import Path
import re

app = FastAPI(title="AI媒体平台", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建本地视频存储目录
LOCAL_VIDEO_DIR = Path("./generated_videos")
LOCAL_VIDEO_DIR.mkdir(exist_ok=True)
print(f"📁 本地视频存储目录: {LOCAL_VIDEO_DIR.absolute()}")

# ==================== 视频生成服务 ====================

class VideoRequest:
    def __init__(self, provider: str, prompt: str, duration: int = 8, width: int = 512, height: int = 512, fps: int = 16, seed: Optional[int] = None):
        self.provider = provider
        self.prompt = prompt
        self.duration = duration
        self.width = width
        self.height = height
        self.fps = fps
        self.seed = seed

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

            # 原来的代码：先尝试API包装器，失败后使用直接调用
            # # 优先使用API包装器
            # video_info = await self._generate_via_api_wrapper(request)
            # if video_info:
            #     return video_info

            # print("API包装器失败，尝试直接调用ComfyUI...")
            # # 如果API包装器失败，回退到直接调用
            # return await self._generate_via_direct_comfyui(request)

        except Exception as e:
            print(f"视频生成失败: {str(e)}")
            return None

    async def _generate_via_api_wrapper(self, request: VideoRequest):
        """通过API包装器生成视频"""
        try:
            print(f"🌐 调用ComfyUI API包装器: {self.comfyui_api_url}")

            # 构建API包装器请求
            api_request = {
                "prompt": request.prompt,
                "width": request.width,
                "height": request.height,
                "duration": request.duration,
                "fps": request.fps,
                "seed": request.seed,
                "negative_prompt": "static, still, frozen, motionless, blurry, low quality, distorted, watermark, text, error, ugly, deformed"
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as session:
                # 提交视频生成任务
                async with session.post(f"{self.comfyui_api_url}/api/generate_video", json=api_request) as response:
                    if response.status != 200:
                        print(f"API包装器请求失败: {response.status}")
                        return None

                    result = await response.json()
                    # API包装器成功状态：status为"submitted"或存在task_id
                    if result.get("status") != "submitted" and not result.get("task_id"):
                        print(f"API包装器返回错误: {result.get('message', 'unknown error')}")
                        return None

                    task_id = result.get("task_id")
                    if not task_id:
                        print("API包装器未返回task_id")
                        return None

            print(f"✅ API包装器任务已创建: {task_id}")
            print(f"开始监控任务 {task_id}...")

            # 监控任务进度
            return await self._monitor_api_wrapper_task(task_id, request)

        except Exception as e:
            print(f"API包装器调用失败: {str(e)}")
            return None

    async def _monitor_api_wrapper_task(self, task_id: str, request: VideoRequest):
        """监控API包装器任务进度"""
        try:
            max_wait_time = 600  # 10分钟超时
            check_interval = 5   # 5秒检查一次
            elapsed_time = 0

            async with aiohttp.ClientSession() as session:
                while elapsed_time < max_wait_time:
                    # 查询任务状态
                    async with session.get(f"{self.comfyui_api_url}/api/task_status/{task_id}") as response:
                        if response.status == 200:
                            status_data = await response.json()
                            status = status_data.get("status", "unknown")

                            print(f"任务状态: {status} (已等待 {elapsed_time}s)")

                            if status == "completed":
                                # 任务完成，获取视频信息
                                video_info = await self._get_completed_video_info(session, task_id)
                                if video_info:
                                    print(f"✅ 视频生成完成!")
                                    print(f"   文件: {video_info.get('filename', 'unknown')}")
                                    print(f"   耗时: {elapsed_time}秒")
                                    print(f"   文件大小: {video_info.get('file_size', 0)} bytes")

                                    # 检查文件大小，如果太小可能生成不完整
                                    file_size = video_info.get('file_size', 0)
                                    if file_size < 5000:  # 小于5KB可能有问题
                                        print(f"   ⚠️ 警告: MP4文件过小，可能生成不完整")

                                return video_info

                            elif status == "failed":
                                error_msg = status_data.get("error", "未知错误")
                                print(f"❌ 任务失败: {error_msg}")
                                return None

                            elif status in ["pending", "processing"]:
                                # 继续等待
                                pass

                            else:
                                print(f"未知状态: {status}")

                        await asyncio.sleep(check_interval)
                        elapsed_time += check_interval

            print(f"⏰ 任务超时 ({max_wait_time}秒)")
            return None

        except Exception as e:
            print(f"监控任务失败: {str(e)}")
            return None

    async def _get_completed_video_info(self, session: aiohttp.ClientSession, task_id: str):
        """获取完成的视频信息"""
        try:
            async with session.get(f"{self.comfyui_api_url}/api/download_video/{task_id}") as response:
                if response.status == 200:
                    # 获取视频文件信息
                    content_length = response.headers.get('content-length', '0')
                    content_disposition = response.headers.get('content-disposition', '')

                    # 从Content-Disposition中提取文件名
                    filename = f"wan_video_{task_id[:8]}_.mp4"
                    if 'filename=' in content_disposition:
                        filename = content_disposition.split('filename=')[-1].strip('"')

                    return {
                        "filename": filename,
                        "file_path": f"/tmp/{filename}",  # API包装器的视频存储路径
                        "file_size": int(content_length),
                        "task_id": task_id,
                        "download_url": f"{self.comfyui_api_url}/api/download_video/{task_id}"
                    }
                else:
                    print(f"获取视频信息失败: {response.status}")
                    return None
        except Exception as e:
            print(f"获取视频信息异常: {str(e)}")
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
                    response = await client.get(f"{self.comfyui_direct_url}/history/{task_id}")
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
        width = min(max(640, min(request.width, 1024)), 1024)
        height = min(max(640, min(request.height, 1024)), 1024)

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
                    "noise_seed": request.seed or random.randint(1, 2**31),
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
                    "fps": min(max(request.fps, 12), 24),
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

    async def _monitor_task(self, task_id: str, request: VideoRequest):
        """监控ComfyUI任务进度"""
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
                        print(f"✅ 任务完成!")
                        return await self._extract_video_info(task_data, start_time)

                    elapsed = asyncio.get_event_loop().time() - start_time
                    print(f"⏳ 任务进行中... ({elapsed:.1f}秒)")

                await asyncio.sleep(3)

                # 超时检查
                if asyncio.get_event_loop().time() - start_time > 600:  # 10分钟超时
                    print(f"⏰ 任务超时")
                    return None

            except Exception as e:
                print(f"⚠️ 监控任务时出错: {str(e)}")
                await asyncio.sleep(3)
                continue

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

                    if file_size > 0:
                        if file_size > 500000:  # 500KB
                            print(f"   ✅ 文件大小很好，应该是高质量视频")
                        elif file_size > 100000:  # 100KB
                            print(f"   ✅ 文件大小良好，应该是正常视频")
                        elif file_size > 10000:  # 10KB
                            print(f"   ⚠️ 文件较小，可能是低质量或短时长的视频")
                        else:
                            print(f"   ⚠️ 警告: MP4文件过小，可能生成不完整")

                    return {
                        "filename": filename,
                        "local_file_path": str(local_file_path) if local_file_path else None,
                        "file_size": file_size,
                        "generation_time": generation_time
                    }

            print(f"❌ 未找到视频输出")
            return None

        except Exception as e:
            print(f"❌ 提取视频信息失败: {str(e)}")
            return None

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
                "optimized_text": optimized_text,
                "provider": provider,
                "original_text": text
            }

        except Exception as e:
            print(f"文本优化失败: {str(e)}")
            return None

text_optimize_service = TextOptimizeService()

# ==================== 爬虫服务 ====================

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

    async def crawl_article(self, platform: str, url: str):
        """真实爬取文章"""
        print(f"收到爬虫请求: platform={platform}, url={url}")

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
                        article_data = await self.parse_article_content(html, url, platform)
                        print(f"爬虫完成: {article_data.get('title', 'unknown')}")
                        return article_data
                    else:
                        print(f"页面获取失败，状态码: {response.status}")
                        return self.create_error_response(url, platform, f"HTTP {response.status}")

        except asyncio.TimeoutError:
            print(f"爬虫超时: {url}")
            return self.create_error_response(url, platform, "请求超时")
        except Exception as e:
            print(f"爬虫失败: {str(e)}")
            return self.create_error_response(url, platform, str(e))

    async def parse_article_content(self, html: str, url: str, platform: str):
        """解析文章内容"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 根据不同平台使用不同的解析策略
            if platform == "csdn":
                return await self.parse_csdn_article(soup, url)
            elif platform == "juejin":
                return await self.parse_juejin_article(soup, url)
            elif platform == "zhihu":
                return await self.parse_zhihu_article(soup, url)
            else:
                return await self.parse_general_article(soup, url, platform)

        except Exception as e:
            print(f"解析文章失败: {str(e)}")
            return self.create_error_response(url, platform, f"解析失败: {str(e)}")

    async def parse_csdn_article(self, soup: BeautifulSoup, url: str):
        """解析CSDN文章"""
        # 提取标题
        title_elem = soup.find('h1', class_='article-title')
        if not title_elem:
            title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "未知标题"

        # 提取作者
        author_elem = soup.find('a', class_='author')
        if not author_elem:
            author_elem = soup.find('span', class_='author-name')
        author = author_elem.get_text().strip() if author_elem else "未知作者"

        # 提取发布时间
        time_elem = soup.find('span', class_='time')
        if not time_elem:
            time_elem = soup.find('div', class_='article-info-box').find('span') if soup.find('div', class_='article-info-box') else None
        publish_time = time_elem.get_text().strip() if time_elem else datetime.now().strftime('%Y-%m-%d')

        # 提取内容
        content_elem = soup.find('div', class_='article-content')
        if not content_elem:
            content_elem = soup.find('div', id='content_views')
        if not content_elem:
            content_elem = soup.find('article')

        content = ""
        if content_elem:
            # 移除不需要的标签
            for tag in content_elem.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                tag.decompose()
            content = content_elem.get_text().strip()

        # 提取标签
        tags = []
        tag_elems = soup.find_all('a', class_='tag')
        for tag_elem in tag_elems:
            tag_text = tag_elem.get_text().strip()
            if tag_text:
                tags.append(tag_text)

        # 提取阅读量
        read_count = 0
        read_elem = soup.find('span', class_='read-count')
        if read_elem:
            try:
                read_text = read_elem.get_text().strip()
                read_num = re.findall(r'\d+', read_text)
                if read_num:
                    read_count = int(read_num[0])
            except:
                pass

        # 生成内容摘要
        summary = content[:200] + "..." if len(content) > 200 else content

        return {
            "title": title,
            "content": content,
            "summary": summary,
            "author": author,
            "publish_time": publish_time,
            "url": url,
            "platform": "csdn",
            "tags": tags,
            "read_count": read_count,
            "like_count": 0,
            "crawl_time": datetime.now().isoformat(),
            "word_count": len(content),
            "status": "success"
        }

    async def parse_juejin_article(self, soup: BeautifulSoup, url: str):
        """解析掘金文章"""
        # 提取标题
        title_elem = soup.find('h1', class_='article-title')
        if not title_elem:
            title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "未知标题"

        # 提取作者
        author_elem = soup.find('a', class_='username')
        if not author_elem:
            author_elem = soup.find('span', class_='user-name')
        author = author_elem.get_text().strip() if author_elem else "未知作者"

        # 提取发布时间
        time_elem = soup.find('time')
        publish_time = time_elem.get_text().strip() if time_elem else datetime.now().strftime('%Y-%m-%d')

        # 提取内容
        content_elem = soup.find('div', class_='article-content')
        if not content_elem:
            content_elem = soup.find('div', class_='markdown-body')

        content = ""
        if content_elem:
            for tag in content_elem.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                tag.decompose()
            content = content_elem.get_text().strip()

        # 提取标签
        tags = []
        tag_elems = soup.find_all('a', class_='tag')
        for tag_elem in tag_elems:
            tag_text = tag_elem.get_text().strip()
            if tag_text:
                tags.append(tag_text)

        # 生成摘要
        summary = content[:200] + "..." if len(content) > 200 else content

        return {
            "title": title,
            "content": content,
            "summary": summary,
            "author": author,
            "publish_time": publish_time,
            "url": url,
            "platform": "juejin",
            "tags": tags,
            "read_count": 0,
            "like_count": 0,
            "crawl_time": datetime.now().isoformat(),
            "word_count": len(content),
            "status": "success"
        }

    async def parse_zhihu_article(self, soup: BeautifulSoup, url: str):
        """解析知乎文章"""
        # 提取标题
        title_elem = soup.find('h1', class_='Post-Title')
        if not title_elem:
            title_elem = soup.find('h1')
        if not title_elem:
            title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "未知标题"

        # 提取作者
        author_elem = soup.find('span', class_='UserLink-link')
        if not author_elem:
            author_elem = soup.find('a', class_='author-link')
        author = author_elem.get_text().strip() if author_elem else "未知作者"

        # 提取发布时间
        time_elem = soup.find('time')
        publish_time = time_elem.get_text().strip() if time_elem else datetime.now().strftime('%Y-%m-%d')

        # 提取内容
        content_elem = soup.find('div', class_='Post-RichText')
        if not content_elem:
            content_elem = soup.find('div', class_='RichText')

        content = ""
        if content_elem:
            for tag in content_elem.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                tag.decompose()
            content = content_elem.get_text().strip()

        # 生成摘要
        summary = content[:200] + "..." if len(content) > 200 else content

        return {
            "title": title,
            "content": content,
            "summary": summary,
            "author": author,
            "publish_time": publish_time,
            "url": url,
            "platform": "zhihu",
            "tags": [],
            "read_count": 0,
            "like_count": 0,
            "crawl_time": datetime.now().isoformat(),
            "word_count": len(content),
            "status": "success"
        }

    async def parse_general_article(self, soup: BeautifulSoup, url: str, platform: str):
        """通用文章解析"""
        # 提取标题
        title_elem = soup.find('title')
        title = title_elem.get_text().strip() if title_elem else "未知标题"

        # 提取内容 - 通用方法
        content = ""

        # 尝试多种常见的内容选择器
        content_selectors = [
            'article',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.content',
            '#content',
            '.main-content',
            'main'
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # 移除不需要的标签
                for tag in content_elem.find_all(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                    tag.decompose()
                content = content_elem.get_text().strip()
                if len(content) > 100:  # 内容长度合理
                    break

        # 如果没有找到合适的内容，尝试获取body文本
        if not content:
            body_elem = soup.find('body')
            if body_elem:
                for tag in body_elem.find_all(['script', 'style', 'nav', 'footer', 'aside', 'header']):
                    tag.decompose()
                content = body_elem.get_text().strip()

        # 生成摘要
        summary = content[:200] + "..." if len(content) > 200 else content

        return {
            "title": title,
            "content": content,
            "summary": summary,
            "author": "未知作者",
            "publish_time": datetime.now().strftime('%Y-%m-%d'),
            "url": url,
            "platform": platform,
            "tags": [],
            "read_count": 0,
            "like_count": 0,
            "crawl_time": datetime.now().isoformat(),
            "word_count": len(content),
            "status": "success"
        }

    def create_error_response(self, url: str, platform: str, error_msg: str):
        """创建错误响应"""
        return {
            "title": f"爬取失败",
            "content": f"无法爬取文章内容。错误：{error_msg}。URL: {url}",
            "summary": "爬取失败",
            "author": "未知",
            "publish_time": datetime.now().strftime('%Y-%m-%d'),
            "url": url,
            "platform": platform,
            "tags": [],
            "read_count": 0,
            "like_count": 0,
            "crawl_time": datetime.now().isoformat(),
            "word_count": 0,
            "status": "failed",
            "error": error_msg
        }

spider_service = SpiderService()

# ==================== API端点 ====================

@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy", "service": "ai-media-platform"}

# 视频生成API
@app.post("/api/v1/video/generate")
async def generate_video(request: dict):
    """生成视频API"""
    try:
        # 解析请求数据
        video_request = VideoRequest(
            provider=request.get("provider", "comfyui_wan"),
            prompt=request.get("prompt", ""),
            duration=request.get("duration", 8),
            width=request.get("width", 512),
            height=request.get("height", 512),
            fps=request.get("fps", 16),
            seed=request.get("seed")
        )

        # 生成视频
        video_info = await video_service.generate_video(video_request)

        if video_info:
            # 添加本地视频URL
            if video_info.get("local_file_path"):
                # 从完整路径中提取文件名
                local_file_path = Path(video_info["local_file_path"])
                video_url = f"http://localhost:9000/api/v1/video/file/{local_file_path.name}"
                video_info["local_video_url"] = video_url
                print(f"🎬 本地视频URL: {video_url}")

            return {
                "success": True,
                "data": {
                    "video_info": video_info
                }
            }
        else:
            return {
                "success": False,
                "message": "视频生成失败"
            }

    except Exception as e:
        print(f"API错误: {str(e)}")
        return {
            "success": False,
            "message": f"API错误: {str(e)}"
        }

@app.get("/api/v1/video/providers")
async def get_providers():
    """获取视频生成提供商列表"""
    return {
        "success": True,
        "data": {
            "providers": [
                {
                    "id": "comfyui_wan",
                    "name": "ComfyUI Wan 2.2",
                    "description": "基于ComfyUI的Wan 2.2视频生成模型",
                    "status": "available"
                }
            ]
        }
    }

# 文本优化API
@app.post("/api/v1/llm/optimize-text")
async def optimize_text(request: dict):
    """文本优化API"""
    try:
        text = request.get("text", "")
        provider = request.get("provider", "glm")

        if not text:
            return {
                "success": False,
                "message": "文本内容不能为空"
            }

        result = await text_optimize_service.optimize_text(text, provider)

        if result:
            return {
                "success": True,
                "data": result
            }
        else:
            return {
                "success": False,
                "message": "文本优化失败"
            }

    except Exception as e:
        print(f"API错误: {str(e)}")
        return {
            "success": False,
            "message": f"API错误: {str(e)}"
        }

@app.get("/api/v1/llm/providers")
async def get_llm_providers():
    """获取LLM提供商列表"""
    return {
        "success": True,
        "data": {
            "providers": [
                {"id": provider_id, "name": info["name"], "available": info["available"]}
                for provider_id, info in text_optimize_service.providers.items()
            ]
        }
    }

# 爬虫API
@app.post("/api/v1/spider/crawl")
async def crawl_article(request: dict):
    """爬取文章API"""
    try:
        # 支持两种参数格式：
        # 1. { "platform": "csdn", "url": "..." } - 兼容测试格式
        # 2. { "url": "...", "mode": "...", "depth": ..., "filters": [...], "delay": ... } - 前端格式

        url = request.get("url", "")

        # 如果没有提供URL，返回错误
        if not url:
            return {
                "success": False,
                "message": "URL不能为空"
            }

        # 自动识别平台，或者使用提供的platform参数
        platform = request.get("platform", "")

        if not platform:
            # 根据URL自动识别平台
            if "csdn.net" in url:
                platform = "csdn"
            elif "juejin.cn" in url:
                platform = "juejin"
            elif "zhihu.com" in url:
                platform = "zhihu"
            elif "toutiao.com" in url:
                platform = "toutiao"
            elif "xiaohongshu.com" in url:
                platform = "xiaohongshu"
            else:
                platform = "general"  # 通用爬虫

        print(f"爬虫请求: platform={platform}, url={url}")

        result = await spider_service.crawl_article(platform, url)

        if result:
            return {
                "success": True,
                "data": result
            }
        else:
            return {
                "success": False,
                "message": "爬虫失败"
            }

    except Exception as e:
        print(f"API错误: {str(e)}")
        return {
            "success": False,
            "message": f"API错误: {str(e)}"
        }

@app.get("/api/v1/spider/platforms")
async def get_spider_platforms():
    """获取爬虫平台列表"""
    return {
        "success": True,
        "data": {
            "platforms": [
                {"id": platform_id, "name": info["name"], "available": info["available"]}
                for platform_id, info in spider_service.platforms.items()
            ]
        }
    }

# ==================== 账号管理服务 ====================

class AccountService:
    def __init__(self):
        # 模拟账号数据
        self.accounts = [
            {
                "id": 1,
                "platform": "csdn",
                "username": "csdn_developer",
                "status": "active",
                "created_at": "2025-10-01",
                "last_login": "2025-10-07"
            },
            {
                "id": 2,
                "platform": "xiaohongshu",
                "username": "xhs_creator",
                "status": "active",
                "created_at": "2025-10-01",
                "last_login": "2025-10-07"
            },
            {
                "id": 3,
                "platform": "juejin",
                "username": "juejin_dev",
                "status": "inactive",
                "created_at": "2025-10-01",
                "last_login": "2025-10-05"
            }
        ]

    async def get_all_accounts(self):
        """获取所有账号"""
        return self.accounts

    async def get_accounts_by_platform(self, platform: str):
        """根据平台获取账号"""
        return [acc for acc in self.accounts if acc["platform"] == platform]

    async def add_account(self, account_data: dict):
        """添加新账号"""
        new_account = {
            "id": len(self.accounts) + 1,
            "platform": account_data.get("platform"),
            "username": account_data.get("username"),
            "status": account_data.get("status", "active"),
            "created_at": "2025-10-07",
            "last_login": None
        }
        self.accounts.append(new_account)
        return new_account

account_service = AccountService()

# ==================== 素材管理服务 ====================

class MaterialService:
    def __init__(self):
        # 模拟素材数据
        self.materials = [
            {
                "id": 1,
                "type": "video",
                "title": "AI生成科技视频",
                "content": "wan_video_test.mp4",
                "file_size": 2500,
                "tags": ["AI", "科技", "视频生成"],
                "created_at": "2025-10-07",
                "source": "comfyui"
            },
            {
                "id": 2,
                "type": "text",
                "title": "优化后的技术文章",
                "content": "这是经过AI优化的技术文章内容...",
                "tags": ["技术", "AI优化", "文章"],
                "created_at": "2025-10-07",
                "source": "glm"
            },
            {
                "id": 3,
                "type": "image",
                "title": "科技感配图",
                "content": "tech_image.png",
                "file_size": 1024,
                "tags": ["科技", "配图", "AI生成"],
                "created_at": "2025-10-07",
                "source": "midjourney"
            }
        ]

    async def get_all_materials(self):
        """获取所有素材"""
        return self.materials

    async def get_materials_by_type(self, material_type: str):
        """根据类型获取素材"""
        return [mat for mat in self.materials if mat["type"] == material_type]

    async def search_materials(self, keyword: str):
        """搜索素材"""
        keyword = keyword.lower()
        return [
            mat for mat in self.materials
            if keyword in mat["title"].lower() or
               any(keyword in tag.lower() for tag in mat["tags"])
        ]

    async def add_material(self, material_data: dict):
        """添加新素材"""
        new_material = {
            "id": len(self.materials) + 1,
            "type": material_data.get("type"),
            "title": material_data.get("title"),
            "content": material_data.get("content"),
            "tags": material_data.get("tags", []),
            "created_at": "2025-10-07",
            "source": material_data.get("source", "user_upload"),
            "file_size": material_data.get("file_size", len(str(material_data.get("content", "")))),
            "original_url": material_data.get("original_url")
        }
        self.materials.append(new_material)
        return new_material

material_service = MaterialService()

# ==================== 账号管理API ====================

@app.get("/api/v1/accounts")
async def get_all_accounts():
    """获取所有账号"""
    try:
        accounts = await account_service.get_all_accounts()
        return {
            "success": True,
            "data": {
                "accounts": accounts,
                "total": len(accounts)
            }
        }
    except Exception as e:
        print(f"获取账号列表失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取账号列表失败: {str(e)}"
        }

@app.get("/api/v1/accounts/{platform}")
async def get_accounts_by_platform(platform: str):
    """根据平台获取账号"""
    try:
        accounts = await account_service.get_accounts_by_platform(platform)
        return {
            "success": True,
            "data": {
                "accounts": accounts,
                "platform": platform,
                "total": len(accounts)
            }
        }
    except Exception as e:
        print(f"获取平台账号失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取平台账号失败: {str(e)}"
        }

@app.post("/api/v1/accounts")
async def add_account(request: dict):
    """添加新账号"""
    try:
        required_fields = ["platform", "username"]
        for field in required_fields:
            if not request.get(field):
                return {
                    "success": False,
                    "message": f"缺少必填字段: {field}"
                }

        new_account = await account_service.add_account(request)
        return {
            "success": True,
            "message": "账号添加成功",
            "data": {
                "account": new_account
            }
        }
    except Exception as e:
        print(f"添加账号失败: {str(e)}")
        return {
            "success": False,
            "message": f"添加账号失败: {str(e)}"
        }

# ==================== 素材管理API ====================

@app.get("/api/v1/materials")
async def get_all_materials():
    """获取所有素材"""
    try:
        materials = await material_service.get_all_materials()
        return {
            "success": True,
            "data": {
                "materials": materials,
                "total": len(materials)
            }
        }
    except Exception as e:
        print(f"获取素材列表失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取素材列表失败: {str(e)}"
        }

@app.get("/api/v1/materials/search")
async def search_materials(keyword: str = ""):
    """搜索素材"""
    try:
        if not keyword:
            materials = await material_service.get_all_materials()
        else:
            materials = await material_service.search_materials(keyword)

        return {
            "success": True,
            "data": {
                "materials": materials,
                "total": len(materials),
                "keyword": keyword
            }
        }
    except Exception as e:
        print(f"搜索素材失败: {str(e)}")
        return {
            "success": False,
            "message": f"搜索素材失败: {str(e)}"
        }

@app.post("/api/v1/materials")
async def add_material(request: dict):
    """添加新素材"""
    try:
        required_fields = ["type", "title", "content"]
        for field in required_fields:
            if not request.get(field):
                return {
                    "success": False,
                    "message": f"缺少必填字段: {field}"
                }

        new_material = await material_service.add_material(request)
        return {
            "success": True,
            "message": "素材添加成功",
            "data": {
                "material": new_material
            }
        }
    except Exception as e:
        print(f"添加素材失败: {str(e)}")
        return {
            "success": False,
            "message": f"添加素材失败: {str(e)}"
        }

# 社交发布API（简化版本）
@app.post("/postVideo")
async def post_video(request: dict):
    """发布视频到社交平台"""
    try:
        print(f"收到视频发布请求: {request}")

        # 模拟发布过程
        await asyncio.sleep(2)

        # 模拟发布结果
        result = {
            "success": True,
            "message": "发布成功",
            "data": {
                "platform": request.get("platform", "unknown"),
                "status": "published"
            }
        }

        print(f"视频发布完成")

        return result

    except Exception as e:
        print(f"发布失败: {str(e)}")
        return {
            "code": 500,
            "message": f"发布失败: {str(e)}"
        }

# ==================== 视频状态检查 ====================

@app.get("/api/v1/video/status/{task_id}")
async def get_video_status(task_id: str):
    """获取视频生成任务状态"""
    try:
        print(f"收到视频状态查询请求: task_id={task_id}")

        # 调用ComfyUI API包装器查询任务状态
        comfyui_api_url = "http://192.168.1.246:5001"

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{comfyui_api_url}/api/task_status/{task_id}",
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    print(f"ComfyUI API包装器状态查询成功: {result}")

                    # 解析并返回状态信息
                    status = result.get("status", "unknown")
                    message = result.get("message", "")

                    if status == "completed":
                        return {
                            "success": True,
                            "status": "completed",
                            "message": "视频生成完成",
                            "data": result.get("data", {})
                        }
                    elif status == "failed":
                        return {
                            "success": False,
                            "status": "failed",
                            "message": f"视频生成失败: {message}",
                            "error": result.get("error", "unknown error")
                        }
                    elif status in ["submitted", "processing", "pending"]:
                        return {
                            "success": True,
                            "status": status,
                            "message": f"任务正在处理中: {message}" if message else f"任务状态: {status}"
                        }
                    else:
                        return {
                            "success": True,
                            "status": status,
                            "message": f"未知状态: {status}"
                        }

                elif response.status == 404:
                    return {
                        "success": False,
                        "status": "not_found",
                        "message": f"任务不存在: {task_id}"
                    }
                else:
                    error_text = await response.text()
                    print(f"ComfyUI API包装器状态查询失败: {response.status}, {error_text}")
                    return {
                        "success": False,
                        "status": "error",
                        "message": f"状态查询失败: HTTP {response.status}"
                    }

    except asyncio.TimeoutError:
        return {
            "success": False,
            "status": "timeout",
            "message": "状态查询超时"
        }
    except Exception as e:
        print(f"视频状态查询失败: {str(e)}")
        return {
            "success": False,
            "status": "error",
            "message": f"状态查询失败: {str(e)}"
        }

# ==================== 视频文件服务 ====================

@app.get("/api/v1/video/file/{filename}")
async def get_video_file(filename: str):
    """获取本地视频文件"""
    try:
        # 安全检查：确保文件名不包含路径遍历字符
        safe_filename = filename.replace("..", "").replace("/", "").replace("\\", "")
        file_path = LOCAL_VIDEO_DIR / safe_filename

        if not file_path.exists():
            return {
                "success": False,
                "message": f"视频文件不存在: {filename}"
            }

        if not file_path.suffix.lower() == '.mp4':
            return {
                "success": False,
                "message": "只支持MP4格式的视频文件"
            }

        # 返回视频文件
        return FileResponse(
            path=str(file_path),
            media_type="video/mp4",
            filename=safe_filename
        )

    except Exception as e:
        print(f"获取视频文件失败: {str(e)}")
        return {
            "success": False,
            "message": f"获取视频文件失败: {str(e)}"
        }

# ==================== 补充的路由（解决405错误）====================

@app.get("/publish/test")
async def test_publish():
    """测试发布功能"""
    return {
        "status": "success",
        "message": "发布功能测试正常",
        "service": "ai-media-platform",
        "features": ["video_generate", "text_optimize", "spider_crawl", "social_publish"]
    }

@app.get("/api/v1/social/platforms")
async def get_social_platforms():
    """获取社交媒体平台列表"""
    return {
        "success": True,
        "data": {
            "platforms": [
                {"id": "douyin", "name": "抖音", "available": True},
                {"id": "xiaohongshu", "name": "小红书", "available": True},
                {"id": "csdn", "name": "CSDN", "available": True},
                {"id": "juejin", "name": "掘金", "available": True}
            ]
        }
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

if __name__ == "__main__":
    import uvicorn
    print("启动完整AI媒体平台服务...")
    print("服务地址: http://localhost:9000")
    print("API文档: http://localhost:9000/docs")
    print("支持的功能:")
    print("  - 视频生成")
    print("  - 文本优化")
    print("  - 文章爬取")
    print("  - 社交发布")

    uvicorn.run(app, host="0.0.0.0", port=9000)