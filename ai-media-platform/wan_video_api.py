#!/usr/bin/env python3
"""
Wan视频生成API服务
在246服务器5173端口部署，提供高质量AI视频生成
"""

import os
import asyncio
import uuid
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

import torch
import replicate
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from loguru import logger
import uvicorn

# 配置日志
logger.remove()
logger.add("wan_video.log", rotation="10 MB", level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}")
logger.add(lambda msg: print(msg, end=""), level="INFO")

# 配置
class Config:
    REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "r8_7KJc81M47hKxvIYd5xZJQpRrH6u4hL2MnPqGv")
    OUTPUT_DIR = Path("./wan_videos")
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 5173
    MAX_CONCURRENT_TASKS = 2

config = Config()

# 确保输出目录存在
config.OUTPUT_DIR.mkdir(exist_ok=True)

# 请求模型
class VideoRequest(BaseModel):
    prompt: str
    model: str = "wan-video/wan-2.5-t2v"  # 默认使用最新版本
    width: int = 1024
    height: int = 576
    num_frames: int = 49  # 约2秒视频
    fps: int = 24
    seed: Optional[int] = None
    guidance_scale: float = 7.5
    num_inference_steps: int = 30

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

class WanVideoService:
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.processing_tasks = 0

        # 设置Replicate API token
        os.environ["REPLICATE_API_TOKEN"] = config.REPLICATE_API_TOKEN

        logger.info("Wan视频生成服务初始化完成")
        logger.info(f"输出目录: {config.OUTPUT_DIR.absolute()}")
        logger.info(f"服务地址: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
        logger.info(f"支持模型: wan-video/wan-2.5-t2v, wan-video/wan-2.5-t2v-fast")

    def _generate_task_id(self) -> str:
        """生成唯一的任务ID"""
        return uuid.uuid4().hex[:8]

    def _generate_filename(self, task_id: str, prompt: str) -> str:
        """生成视频文件名"""
        # 使用prompt前8个字符的hash + task_id + 时间戳
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"wan_video_{prompt_hash}_{task_id}_{timestamp}.mp4"

    async def generate_video(self, request: VideoRequest) -> VideoResponse:
        """生成视频"""
        if self.processing_tasks >= config.MAX_CONCURRENT_TASKS:
            return VideoResponse(
                success=False,
                task_id="",
                message="服务器繁忙，请稍后重试",
                error="Too many concurrent tasks"
            )

        task_id = self._generate_task_id()
        filename = self._generate_filename(task_id, request.prompt)

        # 创建任务记录
        self.tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "message": "任务已创建，等待处理",
            "video_filename": None,
            "error": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "request": request.dict()
        }

        logger.info(f"Wan视频生成任务已创建 - ID: {task_id}")
        logger.info(f"模型: {request.model}")
        logger.info(f"提示词: {request.prompt[:100]}...")

        # 异步处理视频生成
        asyncio.create_task(self._process_video_generation(task_id, request, filename))

        return VideoResponse(
            success=True,
            task_id=task_id,
            message="Wan视频生成任务已创建，正在处理中...",
            video_filename=filename
        )

    async def _process_video_generation(self, task_id: str, request: VideoRequest, filename: str):
        """处理视频生成任务"""
        try:
            self.processing_tasks += 1
            start_time = time.time()

            # 更新任务状态
            self.tasks[task_id]["status"] = "processing"
            self.tasks[task_id]["progress"] = 10
            self.tasks[task_id]["message"] = "正在初始化Wan模型..."
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            # 准备输入参数
            input_params = {
                "prompt": request.prompt,
                "width": min(request.width, 1280),  # 限制最大宽度
                "height": min(request.height, 720),  # 限制最大高度
                "num_frames": request.num_frames,
                "fps": request.fps,
                "seed": request.seed,
                "guidance_scale": request.guidance_scale,
                "num_inference_steps": request.num_inference_steps
            }

            # 移除None值
            input_params = {k: v for k, v in input_params.items() if v is not None}

            logger.info(f"开始生成Wan视频 - 任务ID: {task_id}")
            logger.info(f"参数: {input_params}")

            # 更新进度
            self.tasks[task_id]["progress"] = 30
            self.tasks[task_id]["message"] = "正在调用Wan模型生成视频..."
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            # 调用Replicate API
            output = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: replicate.run(request.model, input=input_params)
            )

            logger.info(f"Wan模型生成完成 - 任务ID: {task_id}")
            logger.info(f"输出: {output}")

            # 更新进度
            self.tasks[task_id]["progress"] = 80
            self.tasks[task_id]["message"] = "正在下载和保存视频..."
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            # 下载视频
            video_path = config.OUTPUT_DIR / filename

            # 如果output是URL，下载视频
            if isinstance(output, str) and output.startswith(('http://', 'https://')):
                import httpx
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.get(output)
                    response.raise_for_status()

                    with open(video_path, 'wb') as f:
                        f.write(response.content)
            else:
                # 如果output是本地路径或其他格式，尝试直接处理
                logger.warning(f"未知的输出格式: {output}")
                raise ValueError(f"无法处理输出格式: {type(output)}")

            # 检查文件是否成功创建
            if not video_path.exists():
                raise FileNotFoundError("视频文件保存失败")

            # 获取文件大小
            file_size = video_path.stat().st_size

            generation_time = time.time() - start_time

            # 更新任务完成状态
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["progress"] = 100
            self.tasks[task_id]["message"] = "视频生成完成"
            self.tasks[task_id]["video_filename"] = filename
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            logger.info(f"Wan视频生成完成 - 任务ID: {task_id}")
            logger.info(f"文件路径: {video_path}")
            logger.info(f"文件大小: {file_size / (1024*1024):.2f} MB")
            logger.info(f"生成时间: {generation_time:.2f}秒")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Wan视频生成失败 - 任务ID: {task_id}, 错误: {error_msg}")

            # 更新任务失败状态
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["error"] = error_msg
            self.tasks[task_id]["message"] = f"生成失败: {error_msg}"
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

        finally:
            self.processing_tasks -= 1

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

# 创建服务实例
service = WanVideoService()

# 创建FastAPI应用
app = FastAPI(
    title="Wan视频生成API",
    description="基于Replicate Wan模型的高质量AI视频生成服务",
    version="1.0.0"
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Wan Video Generation API",
        "version": "1.0.0",
        "models": ["wan-video/wan-2.5-t2v", "wan-video/wan-2.5-t2v-fast"],
        "status": "running",
        "description": "基于阿里通义Wan模型的高质量AI视频生成服务"
    }

@app.post("/generate", response_model=VideoResponse)
async def generate_video(request: VideoRequest):
    """生成视频接口"""
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

@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务"""
    if task_id in service.tasks:
        del service.tasks[task_id]
        return {"message": "Task deleted successfully"}
    raise HTTPException(status_code=404, detail="Task not found")

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "processing_tasks": service.processing_tasks,
        "total_tasks": len(service.tasks),
        "gpu_available": torch.cuda.is_available(),
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
    }

if __name__ == "__main__":
    logger.info("启动Wan视频生成API服务...")
    logger.info(f"输出目录: {config.OUTPUT_DIR}")
    logger.info(f"服务地址: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    logger.info("特性: 高质量AI视频生成、支持Wan 2.5模型、异步处理")

    uvicorn.run(
        app,
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level="info"
    )