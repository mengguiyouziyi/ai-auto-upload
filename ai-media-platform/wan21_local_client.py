#!/usr/bin/env python3
"""
Wan2.1本地客户端服务 - 5174端口
调用远程246服务器5173端口的真正Wan2.1模型服务
为本地提供完整的文生视频功能
"""

import asyncio
import uuid
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import json

import cv2
import numpy as np
import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import uvicorn

# 配置
class Config:
    REMOTE_WAN_URL = "http://192.168.1.246:5173"  # 远程Wan2.1服务地址
    LOCAL_PORT = 5174
    OUTPUT_DIR = Path("./generated_videos")
    MAX_CACHE_DAYS = 7

config = Config()

# 确保输出目录存在
config.OUTPUT_DIR.mkdir(exist_ok=True)

# 请求模型
class VideoRequest(BaseModel):
    prompt: str
    width: int = 832
    height: int = 480
    num_frames: int = 16
    fps: int = 16
    seed: Optional[int] = None

# 响应模型
class VideoResponse(BaseModel):
    success: bool
    task_id: str
    message: str
    video_url: Optional[str] = None
    video_filename: Optional[str] = None
    generation_time: Optional[float] = None
    error: Optional[str] = None

# 任务状态模型
class TaskStatus(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    video_filename: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    updated_at: str

class Wan21LocalClient:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.cache_dir = config.OUTPUT_DIR

        logger.info("Wan2.1本地客户端初始化完成")
        logger.info(f"远程服务地址: {config.REMOTE_WAN_URL}")
        logger.info(f"本地端口: {config.LOCAL_PORT}")
        logger.info(f"输出目录: {config.OUTPUT_DIR}")
        logger.info("特性: 基于真正Wan2.1模型、调用远程服务、本地缓存")

    def _generate_task_id(self) -> str:
        """生成唯一的任务ID"""
        return uuid.uuid4().hex[:8]

    def _generate_filename(self, task_id: str, prompt: str) -> str:
        """生成视频文件名"""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"wan21_video_{prompt_hash}_{task_id}_{timestamp}.mp4"

    async def generate_video(self, request: VideoRequest) -> VideoResponse:
        """生成视频 - 调用远程Wan2.1服务"""
        task_id = self._generate_task_id()
        filename = self._generate_filename(task_id, request.prompt)

        # 创建任务记录
        self.tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": 0,
            "message": "任务已创建，准备调用远程Wan2.1服务...",
            "video_filename": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "request": request.model_dump()
        }

        logger.info(f"本地视频生成任务已创建 - ID: {task_id}")
        logger.info(f"提示词: {request.prompt[:100]}...")
        logger.info("将调用远程Wan2.1服务生成视频")

        # 异步处理视频生成
        asyncio.create_task(self._process_remote_video_generation(task_id, request, filename))

        return VideoResponse(
            success=True,
            task_id=task_id,
            message="Wan2.1视频生成任务已创建，正在调用远程服务...",
            video_filename=filename
        )

    async def _process_remote_video_generation(self, task_id: str, request: VideoRequest, filename: str):
        """处理远程视频生成任务"""
        try:
            start_time = time.time()

            # 更新任务状态
            self.tasks[task_id]["status"] = "processing"
            self.tasks[task_id]["progress"] = 20
            self.tasks[task_id]["message"] = "正在调用远程Wan2.1服务..."
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            # 准备远程请求数据
            remote_data = {
                "prompt": request.prompt,
                "width": request.width,
                "height": request.height,
                "num_frames": request.num_frames,
                "fps": request.fps
            }
            if request.seed:
                remote_data["seed"] = request.seed

            # 调用远程服务
            logger.info(f"调用远程Wan2.1服务生成视频 - 任务ID: {task_id}")

            response = requests.post(
                f"{config.REMOTE_WAN_URL}/generate",
                headers={"Content-Type": "application/json"},
                json=remote_data,
                timeout=300  # 5分钟超时
            )

            if response.status_code != 200:
                raise Exception(f"远程服务返回错误: {response.status_code} - {response.text}")

            remote_result = response.json()

            if not remote_result.get("success", False):
                raise Exception(f"远程服务生成失败: {remote_result.get('message', '未知错误')}")

            remote_task_id = remote_result.get("task_id")
            if not remote_task_id:
                raise Exception("远程服务未返回任务ID")

            # 更新进度
            self.tasks[task_id]["progress"] = 50
            self.tasks[task_id]["message"] = "远程Wan2.1服务正在生成视频..."
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            # 轮询远程任务状态
            video_url = await self._poll_remote_task(remote_task_id)

            if not video_url:
                raise Exception("远程任务完成但未返回视频URL")

            # 下载视频到本地
            self.tasks[task_id]["progress"] = 80
            self.tasks[task_id]["message"] = "正在下载视频到本地..."
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            video_path = await self._download_video(video_url, filename)

            generation_time = time.time() - start_time

            # 更新任务完成状态
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["progress"] = 100
            self.tasks[task_id]["message"] = "视频生成完成"
            self.tasks[task_id]["video_filename"] = filename
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            logger.info(f"Wan2.1视频生成完成 - 任务ID: {task_id}")
            logger.info(f"本地文件路径: {video_path}")
            logger.info(f"生成时间: {generation_time:.2f}秒")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Wan2.1视频生成失败 - 任务ID: {task_id}, 错误: {error_msg}")

            # 更新任务失败状态
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["error"] = error_msg
            self.tasks[task_id]["message"] = f"生成失败: {error_msg}"
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

    async def _poll_remote_task(self, remote_task_id: str, max_attempts: int = 120, interval: int = 5) -> Optional[str]:
        """轮询远程任务状态"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{config.REMOTE_WAN_URL}/task/{remote_task_id}",
                    timeout=30
                )

                if response.status_code == 200:
                    task_data = response.json()
                    status = task_data.get("status")

                    logger.info(f"远程任务 {remote_task_id} 状态: {status} (尝试 {attempt + 1}/{max_attempts})")

                    if status == "completed":
                        # 检查多个可能的返回字段
                        video_filename = task_data.get("video_filename") or task_data.get("filename")
                        download_url = task_data.get("download_url")

                        if download_url:
                            return f"{config.REMOTE_WAN_URL}{download_url}"
                        elif video_filename:
                            return f"{config.REMOTE_WAN_URL}/download/{video_filename}"
                        else:
                            # 如果都没有返回字段，构造默认下载URL
                            return f"{config.REMOTE_WAN_URL}/download/wan21_video_{remote_task_id}.mp4"
                    elif status == "failed":
                        error_msg = task_data.get("error", "未知错误")
                        raise Exception(f"远程任务失败: {error_msg}")
                    # 继续等待

                await asyncio.sleep(interval)

            except requests.RequestException as e:
                logger.warning(f"查询远程任务状态失败 (尝试 {attempt + 1}/{max_attempts}): {e}")
                if attempt < max_attempts - 1:
                    await asyncio.sleep(interval)

        return None

    async def _download_video(self, video_url: str, filename: str) -> str:
        """下载视频文件到本地"""
        try:
            response = requests.get(video_url, stream=True, timeout=300)
            response.raise_for_status()

            video_path = config.OUTPUT_DIR / filename

            with open(video_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"视频下载完成: {video_path} ({video_path.stat().st_size / 1024:.1f}KB)")
            return str(video_path)

        except Exception as e:
            logger.error(f"视频下载失败: {e}")
            raise

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return None

        task_data = self.tasks[task_id]
        return TaskStatus(**task_data)

    def download_video(self, filename: str) -> Optional[Path]:
        """下载视频文件"""
        video_path = config.OUTPUT_DIR / filename
        if video_path.exists():
            return video_path
        return None

    def cleanup_old_files(self):
        """清理超过期限的缓存文件"""
        try:
            now = datetime.now()
            for file_path in config.OUTPUT_DIR.glob("wan21_video_*.mp4"):
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                age = (now - file_time).days
                if age > config.MAX_CACHE_DAYS:
                    file_path.unlink()
                    logger.info(f"清理过期文件: {file_path}")
        except Exception as e:
            logger.error(f"清理缓存文件失败: {e}")

# 创建服务实例
service = Wan21LocalClient()

# 创建FastAPI应用
app = FastAPI(
    title="Wan2.1本地客户端API",
    description="调用远程Wan2.1服务的本地文生视频API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Wan2.1本地客户端API",
        "version": "1.0.0",
        "description": "调用远程246服务器Wan2.1服务的本地文生视频接口",
        "remote_service": config.REMOTE_WAN_URL,
        "local_port": config.LOCAL_PORT,
        "features": [
            "真正Wan2.1模型视频生成",
            "本地缓存管理",
            "自动文件清理",
            "异步任务处理"
        ]
    }

@app.post("/generate", response_model=VideoResponse)
async def generate_video(request: VideoRequest):
    """生成视频接口"""
    # 定期清理旧文件
    service.cleanup_old_files()

    return await service.generate_video(request)

@app.get("/task/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """获取任务状态"""
    status = service.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

@app.get("/download/{filename}")
async def download_video(filename: str):
    """下载视频文件"""
    video_path = service.download_video(filename)
    if not video_path:
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        path=video_path,
        filename=filename,
        media_type="video/mp4"
    )

@app.get("/tasks")
async def list_tasks():
    """列出所有任务"""
    return {"tasks": list(service.tasks.values())}

@app.get("/health")
async def health_check():
    """健康检查"""
    # 检查远程服务状态
    remote_healthy = False
    try:
        response = requests.get(f"{config.REMOTE_WAN_URL}/health", timeout=10)
        remote_healthy = response.status_code == 200
    except:
        pass

    return {
        "status": "healthy",
        "remote_service": config.REMOTE_WAN_URL,
        "remote_healthy": remote_healthy,
        "processing_tasks": len([t for t in service.tasks.values() if t["status"] == "processing"]),
        "total_tasks": len(service.tasks),
        "cached_files": len(list(config.OUTPUT_DIR.glob("wan21_video_*.mp4")))
    }

@app.get("/cache/info")
async def cache_info():
    """缓存信息"""
    files = list(config.OUTPUT_DIR.glob("wan21_video_*.mp4"))
    total_size = sum(f.stat().st_size for f in files) / 1024 / 1024  # MB

    return {
        "cache_directory": str(config.OUTPUT_DIR),
        "file_count": len(files),
        "total_size_mb": round(total_size, 2),
        "max_cache_days": config.MAX_CACHE_DAYS
    }

if __name__ == "__main__":
    logger.info("启动Wan2.1本地客户端API服务...")
    logger.info(f"远程Wan2.1服务: {config.REMOTE_WAN_URL}")
    logger.info(f"本地服务地址: http://0.0.0.0:{config.LOCAL_PORT}")
    logger.info("特性: 真正Wan2.1模型、本地缓存、自动清理")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.LOCAL_PORT,
        log_level="info"
    )