"""
文生视频服务模块 - 集成多种视频生成API
支持Runway ML、Pika Labs、豆包视频、文心视频、Stable Video Diffusion等
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Union
from enum import Enum
from pathlib import Path
import httpx
from pydantic import BaseModel
from loguru import logger


class VideoProvider(str, Enum):
    """支持的视频生成提供商"""
    RUNWAY = "runway"
    PIKA = "pika"
    DOUBAO = "doubao"
    WENXIN = "wenxin"
    STABLE_VIDEO = "stable_video"
    ANIMATEDIFF = "animatediff"


class VideoRequest(BaseModel):
    """视频生成请求模型"""
    provider: VideoProvider
    prompt: str
    duration: int = 5  # 视频时长（秒）
    width: int = 1280
    height: int = 720
    fps: int = 30
    quality: str = "high"  # low, medium, high
    style: Optional[str] = None  # 视频风格
    seed: Optional[int] = None


class VideoResponse(BaseModel):
    """视频生成响应模型"""
    provider: str
    video_url: str
    video_path: Optional[str] = None
    duration: float
    width: int
    height: int
    fps: int
    file_size: Optional[int] = None
    generation_time: float
    cost: Optional[float] = None


class VideoService:
    """视频生成服务主类"""

    def __init__(self, config: Dict):
        self.config = config
        self.api_keys = config.get("api_keys", {})
        self.models_config = config.get("models", {}).get("video_generation", {})
        self.storage_config = config.get("storage", {})

    async def generate_video(self, request: VideoRequest) -> VideoResponse:
        """生成视频"""
        try:
            if request.provider == VideoProvider.RUNWAY:
                return await self._call_runway(request)
            elif request.provider == VideoProvider.PIKA:
                return await self._call_pika(request)
            elif request.provider == VideoProvider.DOUBAO:
                return await self._call_doubao_video(request)
            elif request.provider == VideoProvider.WENXIN:
                return await self._call_wenxin_video(request)
            elif request.provider == VideoProvider.STABLE_VIDEO:
                return await self._call_stable_video(request)
            elif request.provider == VideoProvider.ANIMATEDIFF:
                return await self._call_animatediff(request)
            else:
                raise ValueError(f"不支持的视频生成提供商: {request.provider}")

        except Exception as e:
            logger.error(f"视频生成失败: {e}")
            raise

    async def _call_runway(self, request: VideoRequest) -> VideoResponse:
        """调用Runway ML API"""
        start_time = time.time()

        config = self.api_keys.get("runway", {})
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.runwayml.com/v1")

        if not api_key:
            raise ValueError("Runway API密钥未配置")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Runway Gen-3 Turbo参数
        payload = {
            "text_prompt": request.prompt,
            "model": "gen3a_turbo",
            "watermark": False,
            "duration": request.duration,
            "ratio": "16:9"
        }

        async with httpx.AsyncClient(timeout=300) as client:
            # 1. 提交生成任务
            response = await client.post(
                f"{base_url}/videos",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            task_data = response.json()
            task_id = task_data.get("id")

            if not task_id:
                raise ValueError("Runway任务创建失败")

            # 2. 轮询任务状态
            video_url = None
            while True:
                await asyncio.sleep(10)  # 每10秒查询一次

                status_response = await client.get(
                    f"{base_url}/videos/{task_id}",
                    headers=headers
                )
                status_response.raise_for_status()
                status_data = status_response.json()

                status = status_data.get("status")
                if status == "succeeded":
                    video_url = status_data.get("url")
                    break
                elif status == "failed":
                    error_msg = status_data.get("failure_reason", "生成失败")
                    raise ValueError(f"Runway视频生成失败: {error_msg}")
                elif status in ["running", "pending"]:
                    continue
                else:
                    raise ValueError(f"未知状态: {status}")

            if not video_url:
                raise ValueError("Runway视频生成失败：未获取到视频URL")

            # 3. 下载视频
            video_path = await self._download_video(video_url, "runway")

            generation_time = time.time() - start_time
            file_size = Path(video_path).stat().st_size if video_path else None

            # Runway计费（约$0.05/秒）
            cost = request.duration * 0.05

            return VideoResponse(
                provider="runway",
                video_url=video_url,
                video_path=video_path,
                duration=float(request.duration),
                width=request.width,
                height=request.height,
                fps=request.fps,
                file_size=file_size,
                generation_time=generation_time,
                cost=cost
            )

    async def _call_pika(self, request: VideoRequest) -> VideoResponse:
        """调用Pika Labs API"""
        start_time = time.time()

        config = self.api_keys.get("pika", {})
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.pika.art/v1")

        if not api_key:
            raise ValueError("Pika API密钥未配置")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": request.prompt,
            "options": {
                "duration": request.duration,
                "aspect_ratio": "16:9",
                "quality": request.quality
            }
        }

        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{base_url}/generate",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            task_id = data.get("task_id")
            if not task_id:
                raise ValueError("Pika任务创建失败")

            # 轮询结果
            while True:
                await asyncio.sleep(8)

                status_response = await client.get(
                    f"{base_url}/task/{task_id}",
                    headers=headers
                )
                status_response.raise_for_status()
                status_data = status_response.json()

                status = status_data.get("status")
                if status == "completed":
                    video_url = status_data.get("video_url")
                    break
                elif status == "failed":
                    raise ValueError("Pika视频生成失败")
                else:
                    continue

            video_path = await self._download_video(video_url, "pika")
            generation_time = time.time() - start_time
            file_size = Path(video_path).stat().st_size if video_path else None

            # Pika计费（约$0.03/秒）
            cost = request.duration * 0.03

            return VideoResponse(
                provider="pika",
                video_url=video_url,
                video_path=video_path,
                duration=float(request.duration),
                width=request.width,
                height=request.height,
                fps=request.fps,
                file_size=file_size,
                generation_time=generation_time,
                cost=cost
            )

    async def _call_doubao_video(self, request: VideoRequest) -> VideoResponse:
        """调用豆包视频生成API"""
        # 豆包视频API的具体实现需要根据实际API文档调整
        start_time = time.time()

        config = self.api_keys.get("doubao", {})
        api_key = config.get("api_key")

        if not api_key:
            raise ValueError("豆包API密钥未配置")

        # 这里是模拟实现，实际需要调用豆包的视频生成API
        logger.info(f"豆包视频生成: {request.prompt}")

        # 模拟生成时间
        await asyncio.sleep(30)

        # 模拟返回结果
        generation_time = time.time() - start_time

        return VideoResponse(
            provider="doubao",
            video_url="https://example.com/doubao-video.mp4",
            video_path=None,
            duration=float(request.duration),
            width=request.width,
            height=request.height,
            fps=request.fps,
            generation_time=generation_time,
            cost=0.0
        )

    async def _call_wenxin_video(self, request: VideoRequest) -> VideoResponse:
        """调用文心一言视频生成API"""
        start_time = time.time()

        config = self.api_keys.get("wenxin", {})
        api_key = config.get("api_key")

        if not api_key:
            raise ValueError("文心API密钥未配置")

        # 模拟实现
        logger.info(f"文心视频生成: {request.prompt}")
        await asyncio.sleep(30)

        generation_time = time.time() - start_time

        return VideoResponse(
            provider="wenxin",
            video_url="https://example.com/wenxin-video.mp4",
            video_path=None,
            duration=float(request.duration),
            width=request.width,
            height=request.height,
            fps=request.fps,
            generation_time=generation_time,
            cost=0.0
        )

    async def _call_stable_video(self, request: VideoRequest) -> VideoResponse:
        """调用Stable Video Diffusion（本地部署）"""
        start_time = time.time()

        try:
            # 这里需要本地部署Stable Video Diffusion模型
            # 需要GPU支持，推荐配置RTX 3080以上

            # 模拟本地生成过程
            logger.info("本地Stable Video Diffusion生成中...")
            await asyncio.sleep(120)  # 本地生成需要更长时间

            # 这里应该是实际的模型推理代码
            video_path = f"./temp/stable_video_{int(time.time())}.mp4"

            generation_time = time.time() - start_time
            file_size = Path(video_path).stat().st_size if Path(video_path).exists() else None

            return VideoResponse(
                provider="stable_video",
                video_url="",
                video_path=video_path,
                duration=float(request.duration),
                width=request.width,
                height=request.height,
                fps=request.fps,
                file_size=file_size,
                generation_time=generation_time,
                cost=0.0  # 本地部署无直接成本
            )

        except Exception as e:
            logger.error(f"Stable Video Diffusion生成失败: {e}")
            raise

    async def _call_animatediff(self, request: VideoRequest) -> VideoResponse:
        """调用AnimateDiff（本地部署）"""
        start_time = time.time()

        try:
            # AnimateDiff本地部署实现
            logger.info("本地AnimateDiff生成中...")
            await asyncio.sleep(90)

            video_path = f"./temp/animatediff_{int(time.time())}.mp4"
            generation_time = time.time() - start_time
            file_size = Path(video_path).stat().st_size if Path(video_path).exists() else None

            return VideoResponse(
                provider="animatediff",
                video_url="",
                video_path=video_path,
                duration=float(request.duration),
                width=request.width,
                height=request.height,
                fps=request.fps,
                file_size=file_size,
                generation_time=generation_time,
                cost=0.0
            )

        except Exception as e:
            logger.error(f"AnimateDiff生成失败: {e}")
            raise

    async def _download_video(self, video_url: str, provider: str) -> str:
        """下载视频文件"""
        try:
            # 确保临时目录存在
            temp_dir = Path("./temp")
            temp_dir.mkdir(exist_ok=True)

            # 生成文件名
            timestamp = int(time.time())
            filename = f"{provider}_video_{timestamp}.mp4"
            file_path = temp_dir / filename

            # 下载文件
            async with httpx.AsyncClient(timeout=300) as client:
                async with client.stream("GET", video_url) as response:
                    response.raise_for_status()
                    with open(file_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=8192):
                            f.write(chunk)

            logger.info(f"视频下载完成: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"视频下载失败: {e}")
            raise

    async def generate_video_from_scenes(self, scenes: List[str], provider: VideoProvider = VideoProvider.RUNWAY) -> List[VideoResponse]:
        """批量生成场景视频"""
        tasks = []
        for i, scene in enumerate(scenes):
            request = VideoRequest(
                provider=provider,
                prompt=scene,
                duration=5  # 每个场景5秒
            )
            tasks.append(self.generate_video(request))

        # 并行生成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        videos = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"场景{i+1}生成失败: {result}")
            else:
                videos.append(result)

        return videos

    async def merge_videos(self, video_paths: List[str], output_path: str) -> str:
        """合并多个视频文件"""
        try:
            import subprocess

            # 创建文件列表
            file_list_path = "./temp/file_list.txt"
            with open(file_list_path, "w") as f:
                for path in video_paths:
                    f.write(f"file '{path}'\n")

            # 使用FFmpeg合并视频
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", file_list_path,
                "-c", "copy",
                "-y",  # 覆盖输出文件
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise ValueError(f"视频合并失败: {stderr.decode()}")

            # 清理临时文件
            Path(file_list_path).unlink(missing_ok=True)

            logger.info(f"视频合并完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"视频合并失败: {e}")
            raise


# 全局视频服务实例
_video_service: Optional[VideoService] = None


def get_video_service(config: Dict) -> VideoService:
    """获取视频服务实例"""
    global _video_service
    if _video_service is None:
        _video_service = VideoService(config)
    return _video_service


# 测试代码
async def main():
    """测试视频生成服务"""
    config = {
        "api_keys": {
            "runway": {
                "api_key": "your-runway-key"
            },
            "pika": {
                "api_key": "your-pika-key"
            }
        }
    }

    service = get_video_service(config)

    # 测试视频生成
    request = VideoRequest(
        provider=VideoProvider.RUNWAY,
        prompt="一只可爱的小猫在花园里玩耍，阳光明媚，花朵盛开",
        duration=5
    )

    try:
        response = await service.generate_video(request)
        print(f"视频生成成功: {response.video_url}")
        print(f"生成时间: {response.generation_time:.2f}秒")
        print(f"文件大小: {response.file_size / (1024*1024):.2f}MB")
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())