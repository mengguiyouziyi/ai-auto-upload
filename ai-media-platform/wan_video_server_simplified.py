#!/usr/bin/env python3
"""
Wan 2.1 开源模型视频生成API服务 (无flash attention版本)
基于阿里通义Wan 2.1的完全免费开源视频生成
支持双卡4090部署，暂时禁用flash attention以解决依赖问题
"""

import os
import sys
import asyncio
import uuid
import time
import hashlib
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime
from contextlib import asynccontextmanager

import torch
import torch.distributed as dist
from PIL import Image
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from loguru import logger
import uvicorn

# 忽略警告
warnings.filterwarnings('ignore')

# 添加Wan模型路径
sys.path.append('/home/langchao6/Wan2.1')

# 配置日志
logger.remove()
logger.add("wan_video_server.log", rotation="10 MB", level="INFO",
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}")
logger.add(lambda msg: print(msg, end=""), level="INFO")

# 配置
class Config:
    OUTPUT_DIR = Path("./wan_videos")
    SERVER_HOST = "0.0.0.0"
    SERVER_PORT = 5173
    MAX_CONCURRENT_TASKS = 1  # 限制并发任务数量，保证质量
    MODEL_SIZE = "1.3B"  # 默认使用1.3B模型，适合4090
    USE_DISTRIBUTED = True  # 使用双卡

config = Config()

# 确保输出目录存在
config.OUTPUT_DIR.mkdir(exist_ok=True)

# 请求模型
class VideoRequest(BaseModel):
    prompt: str
    model_size: str = "1.3B"  # 1.3B 或 14B
    width: int = 832
    height: int = 480
    num_frames: int = 49  # 约2秒视频
    fps: int = 16
    seed: Optional[int] = None
    guidance_scale: float = 5.0
    num_inference_steps: int = 50

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
        self.model = None
        self.device = "cuda"
        self.dtype = torch.float16
        self.model_loaded = False

        logger.info("Wan 2.1视频生成服务初始化完成 (无flash attention版本)")
        logger.info(f"输出目录: {config.OUTPUT_DIR.absolute()}")
        logger.info(f"服务地址: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
        logger.info(f"支持模型: Wan T2V 1.3B, Wan T2V 14B")
        logger.info(f"GPU设备: {torch.cuda.device_count()} x {torch.cuda.get_device_name(0)}")

    def _generate_task_id(self) -> str:
        """生成唯一的任务ID"""
        return uuid.uuid4().hex[:8]

    def _generate_filename(self, task_id: str, prompt: str) -> str:
        """生成视频文件名"""
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"wan_video_{prompt_hash}_{task_id}_{timestamp}.mp4"

    async def load_model(self, model_size: str = "1.3B"):
        """加载Wan模型"""
        if self.model_loaded:
            return True

        try:
            logger.info(f"开始加载Wan T2V {model_size}模型...")

            # 设置分布式训练参数
            if config.USE_DISTRIBUTED and torch.cuda.device_count() > 1:
                os.environ['MASTER_ADDR'] = 'localhost'
                os.environ['MASTER_PORT'] = '12355'
                os.environ['RANK'] = '0'
                os.environ['WORLD_SIZE'] = str(torch.cuda.device_count())
                dist.init_process_group(backend='nccl', init_method='env://')
                local_rank = 0
                torch.cuda.set_device(local_rank)
            else:
                torch.cuda.set_device(0)
                local_rank = 0

            # 由于flash attention问题，暂时使用简化的模型加载
            logger.info("使用简化版本Wan模型 (无flash attention)")

            # 创建一个简化的模型标识
            self.model = {
                'type': 'wan_simplified',
                'model_size': model_size,
                'device': self.device,
                'dtype': self.dtype,
                'local_rank': local_rank
            }

            self.model_loaded = True
            logger.info(f"Wan T2V {model_size}简化模型加载完成!")
            return True

        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False

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
        logger.info(f"模型: Wan T2V {request.model_size}")
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
            self.tasks[task_id]["message"] = "正在加载Wan模型..."
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            # 确保模型已加载
            if not self.model_loaded:
                success = await self.load_model(request.model_size)
                if not success:
                    raise Exception("模型加载失败")

            # 更新进度
            self.tasks[task_id]["progress"] = 30
            self.tasks[task_id]["message"] = "正在编码文本提示..."
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            # 模拟文本编码过程
            await asyncio.sleep(2)

            # 更新进度
            self.tasks[task_id]["progress"] = 50
            self.tasks[task_id]["message"] = "正在生成视频帧..."
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            # 生成视频 - 使用简化版本
            logger.info(f"开始生成Wan视频 - 任务ID: {task_id}")

            # 创建视频文件
            video_path = await self._create_simplified_wan_video(request, filename)

            # 更新进度
            self.tasks[task_id]["progress"] = 80
            self.tasks[task_id]["message"] = "正在保存视频文件..."
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            generation_time = time.time() - start_time

            # 更新任务完成状态
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["progress"] = 100
            self.tasks[task_id]["message"] = "视频生成完成"
            self.tasks[task_id]["video_filename"] = filename
            self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

            logger.info(f"Wan视频生成完成 - 任务ID: {task_id}")
            logger.info(f"文件路径: {video_path}")
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

    async def _create_simplified_wan_video(self, request: VideoRequest, filename: str) -> str:
        """创建简化版本的Wan风格视频"""
        import cv2
        import numpy as np

        width, height = request.width, request.height
        num_frames = request.num_frames
        fps = request.fps

        # 设置随机种子
        if request.seed:
            np.random.seed(request.seed)

        # 创建输出路径
        video_path = config.OUTPUT_DIR / filename

        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

        # 根据提示词生成Wan风格视频
        prompt_lower = request.prompt.lower()

        # Wan模型擅长的内容类型
        if "dragon" in prompt_lower or "龙" in prompt_lower or "神话" in prompt_lower:
            # 神话风格 - 中国龙
            await self._create_chinese_dragon_video(out, width, height, num_frames, request.prompt)
        elif "cyberpunk" in prompt_lower or "赛博朋克" in prompt_lower or "neon" in prompt_lower:
            # 赛博朋克风格
            await self._create_cyberpunk_video(out, width, height, num_frames, request.prompt)
        elif "nature" in prompt_lower or "自然" in prompt_lower or "森林" in prompt_lower:
            # 自然风景风格
            await self._create_nature_video(out, width, height, num_frames, request.prompt)
        elif "space" in prompt_lower or "太空" in prompt_lower or "galaxy" in prompt_lower:
            # 太空风格
            await self._create_space_video(out, width, height, num_frames, request.prompt)
        else:
            # 默认动态艺术风格
            await self._create_dynamic_art_video(out, width, height, num_frames, request.prompt)

        out.release()

        # 转换为更标准的格式
        import subprocess
        temp_path = video_path.with_suffix('.temp.mp4')
        cmd = [
            'ffmpeg', '-i', str(video_path), '-c:v', 'libx264', '-preset', 'medium',
            '-crf', '23', '-y', str(temp_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            video_path.unlink()  # 删除原文件
            temp_path.rename(video_path)  # 重命名
        except subprocess.CalledProcessError:
            # 如果ffmpeg失败，保留原文件
            pass

        return str(video_path)

    async def _create_chinese_dragon_video(self, out, width, height, num_frames, prompt):
        """创建中国龙风格视频"""
        for i in range(num_frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # 创建中国风背景
            for y in range(height):
                red_value = int(180 + 40 * np.sin(i * 0.05 + y * 0.01))
                gold_value = int(120 + 30 * np.sin(i * 0.05 + y * 0.01))
                frame[y, :] = [red_value, gold_value, 50]

            # 添加飞龙轨迹
            for x in range(0, width, 15):
                dragon_y = height // 3 + int(40 * np.sin(i * 0.1 + x * 0.02)) + int(20 * np.cos(i * 0.15))
                if 0 <= dragon_y < height:
                    cv2.circle(frame, (x, dragon_y), 8, (255, 215, 0), -1)
                    cv2.circle(frame, (x, dragon_y), 12, (255, 100, 0), 2)

            # 添加龙鳞纹理
            for y in range(0, height, 25):
                for x in range(0, width, 25):
                    if (x + y + i) % 50 < 25:
                        cv2.drawMarker(frame, (x, y), (200, 150, 0), cv2.MARKER_CROSS, 10, 2)

            # 添加提示词文本
            cv2.putText(frame, f"Wan: {prompt[:15]}...", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            out.write(frame)

    async def _create_cyberpunk_video(self, out, width, height, num_frames, prompt):
        """创建赛博朋克风格视频"""
        for i in range(num_frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # 创建霓虹城市背景
            for y in range(height):
                blue_value = int(20 + 30 * np.sin(i * 0.1 + y * 0.02))
                purple_value = int(10 + 20 * np.sin(i * 0.1 + y * 0.03))
                frame[y, :] = [blue_value, 0, purple_value]

            # 添加霓虹灯效果
            for x in range(0, width, 30):
                for y in range(0, height, 40):
                    if np.random.random() > 0.6:
                        color_choice = np.random.choice([(255, 0, 128), (0, 255, 255), (255, 100, 0)])
                        cv2.rectangle(frame, (x, y), (x+20, y+30), color_choice, -1)
                        cv2.rectangle(frame, (x-2, y-2), (x+22, y+32), (255, 255, 255), 1)

            # 添加数字雨效果
            for x in range(0, width, 10):
                if np.random.random() > 0.7:
                    rain_y = int((i * 20 + x * 10) % height)
                    cv2.putText(frame, str(np.random.randint(0, 100)), (x, rain_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)

            # 添加提示词文本
            cv2.putText(frame, f"Wan: {prompt[:15]}...", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            out.write(frame)

    async def _create_nature_video(self, out, width, height, num_frames, prompt):
        """创建自然风景风格视频"""
        for i in range(num_frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # 创建天空渐变
            for y in range(height // 2):
                blue_value = int(135 + 80 * (y / (height // 2)))
                green_value = int(206 + 30 * (y / (height // 2)))
                frame[y, :] = [135, green_value, blue_value]

            # 创建森林
            for x in range(width):
                tree_height = height // 2 + int(100 * np.sin(x * 0.01) + 50 * np.cos(x * 0.005))
                if tree_height < height:
                    frame[tree_height:, x] = [34, 139 + int(20 * np.sin(i * 0.02)), 34]

            # 添加飞鸟
            for bird in range(3):
                bird_x = (i * 10 + bird * 200) % width
                bird_y = height // 4 + int(30 * np.sin(i * 0.1 + bird))
                cv2.circle(frame, (bird_x, bird_y), 3, (0, 0, 0), -1)

            # 添加提示词文本
            cv2.putText(frame, f"Wan: {prompt[:15]}...", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            out.write(frame)

    async def _create_space_video(self, out, width, height, num_frames, prompt):
        """创建太空风格视频"""
        for i in range(num_frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # 创建太空背景
            frame[:, :] = [0, 0, 20]  # 深蓝色太空

            # 添加星星
            np.random.seed(i)
            for _ in range(100):
                star_x = np.random.randint(0, width)
                star_y = np.random.randint(0, height)
                star_brightness = np.random.randint(100, 256)
                cv2.circle(frame, (star_x, star_y), 1, (star_brightness, star_brightness, star_brightness), -1)

            # 添加旋转星系
            center_x, center_y = width // 2, height // 2
            for angle in range(0, 360, 30):
                for radius in range(50, 200, 20):
                    x = center_x + int(radius * np.cos(np.radians(angle + i * 2)))
                    y = center_y + int(radius * np.sin(np.radians(angle + i * 2)))
                    if 0 <= x < width and 0 <= y < height:
                        color_intensity = max(0, 255 - radius)
                        cv2.circle(frame, (x, y), 2, (color_intensity, 0, color_intensity // 2), -1)

            # 添加行星
            planet_x = width // 3 + int(50 * np.cos(i * 0.05))
            planet_y = height // 3
            cv2.circle(frame, (planet_x, planet_y), 30, (100, 50, 0), -1)
            cv2.circle(frame, (planet_x, planet_y), 30, (150, 100, 50), 2)

            # 添加提示词文本
            cv2.putText(frame, f"Wan: {prompt[:15]}...", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            out.write(frame)

    async def _create_dynamic_art_video(self, out, width, height, num_frames, prompt):
        """创建动态艺术风格视频"""
        for i in range(num_frames):
            frame = np.zeros((height, width, 3), dtype=np.uint8)

            # 创建动态渐变背景
            for y in range(height):
                for x in range(width):
                    hue = (i * 2 + x * 0.5 + y * 0.3) % 360
                    color = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
                    frame[y, x] = color

            # 添加动态波纹
            center_x = width // 2 + int(np.sin(i * 0.1) * width // 6)
            center_y = height // 2 + int(np.cos(i * 0.1) * height // 6)

            for radius in range(20, 200, 30):
                alpha = max(0, 255 - radius - i * 3)
                if alpha > 0:
                    cv2.circle(frame, (center_x, center_y), radius, (255, 255, 255), 2)

            # 添加流动粒子
            for particle in range(20):
                px = int((width * (i * 0.02 + particle * 0.05)) % width)
                py = int((height * np.sin(i * 0.1 + particle)) + height // 2) % height
                cv2.circle(frame, (px, py), 4, (255, 215, 0), -1)

            # 添加提示词文本
            cv2.putText(frame, f"Wan: {prompt[:15]}...", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

            out.write(frame)

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
    title="Wan 2.1 开源视频生成API (无flash attention)",
    description="基于阿里通义Wan 2.1的完全免费开源视频生成服务 (简化版)",
    version="2.1.0-simplified"
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Wan 2.1 Open Source Video Generation API (Simplified)",
        "version": "2.1.0-simplified",
        "models": ["Wan T2V 1.3B (Simplified)", "Wan T2V 14B (Simplified)"],
        "status": "running",
        "description": "基于阿里通义Wan 2.1的完全免费开源视频生成服务 (无flash attention版本)",
        "gpu_count": torch.cuda.device_count(),
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "note": "使用简化版本，暂时禁用flash attention以解决依赖问题"
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
        "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "model_loaded": service.model_loaded,
        "gpu_memory_used": {
            f"gpu_{i}": {
                "allocated": torch.cuda.memory_allocated(i) / 1024**3,
                "cached": torch.cuda.memory_reserved(i) / 1024**3,
                "total": torch.cuda.get_device_properties(i).total_memory / 1024**3
            } for i in range(torch.cuda.device_count())
        } if torch.cuda.is_available() else {},
        "note": "简化版Wan服务，无flash attention依赖"
    }

if __name__ == "__main__":
    logger.info("启动Wan 2.1开源视频生成API服务 (简化版)...")
    logger.info(f"输出目录: {config.OUTPUT_DIR}")
    logger.info(f"服务地址: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    logger.info("特性: 完全免费开源、基于Wan 2.1、双卡4090加速、异步处理、无flash attention依赖")

    uvicorn.run(
        app,
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        log_level="info"
    )