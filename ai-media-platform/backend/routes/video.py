"""
视频生成API路由
提供文生视频功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
import asyncio
import uuid
import io
from loguru import logger

from services.video.video_service_minimal import VideoService, VideoProvider, VideoRequest, get_video_service
from services.config_service import get_config

router = APIRouter(prefix="/api/v1/video", tags=["视频生成"])

# 请求和响应模型
class VideoGenerateRequest(BaseModel):
    """视频生成请求"""
    prompt: str = Field(..., description="视频生成提示词", min_length=1, max_length=1000)
    provider: str = Field(default="replicate", description="视频生成提供商")
    model: Optional[str] = Field(default=None, description="指定模型")
    duration: int = Field(default=5, ge=1, le=30, description="视频时长(秒)")
    fps: int = Field(default=30, ge=8, le=60, description="帧率")
    width: int = Field(default=1024, ge=256, le=2048, description="视频宽度")
    height: int = Field(default=576, ge=256, le=2048, description="视频高度")
    aspect_ratio: str = Field(default="16:9", description="宽高比")
    quality: str = Field(default="high", description="视频质量")
    seed: Optional[int] = Field(default=None, description="随机种子")

class VideoGenerateResponse(BaseModel):
    """视频生成响应"""
    success: bool
    message: str
    data: Optional[dict] = None

class VideoModelsResponse(BaseModel):
    """可用模型响应"""
    success: bool
    message: str
    data: List[str] = []

class VideoStatusResponse(BaseModel):
    """视频状态响应"""
    success: bool
    message: str
    data: Optional[dict] = None

# 存储生成任务的字典
video_tasks = {}

@router.post("/generate", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """生成视频"""
    try:
        logger.info(f"收到视频生成请求: provider={request.provider}, prompt={request.prompt[:50]}...")

        # 获取配置和服务
        config = get_config()
        video_service = get_video_service(config)

        # 转换提供商字符串为枚举
        try:
            provider = VideoProvider(request.provider)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的提供商: {request.provider}。支持的提供商: {[p.value for p in VideoProvider]}"
            )

        # 创建视频生成请求
        video_request = VideoRequest(
            provider=provider,
            prompt=request.prompt,
            model=request.model,
            duration=request.duration,
            fps=request.fps,
            width=request.width,
            height=request.height,
            aspect_ratio=request.aspect_ratio,
            quality=request.quality,
            seed=request.seed
        )

        # 生成视频
        result = await video_service.generate_video(video_request)

        logger.info(f"视频生成成功: provider={result.provider}, duration={result.duration}s")

        return VideoGenerateResponse(
            success=True,
            message="视频生成成功",
            data={
                "video_url": result.video_url,
                "thumbnail_url": result.thumbnail_url,
                "provider": result.provider,
                "model": result.model,
                "duration": result.duration,
                "fps": result.fps,
                "resolution": result.resolution,
                "generation_time": result.generation_time,
                "prompt": result.prompt,
                "request_id": result.request_id,
                "status": result.status
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"视频生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"视频生成失败: {str(e)}")

@router.get("/models/{provider}", response_model=VideoModelsResponse)
async def get_available_models(provider: str):
    """获取指定提供商的可用模型列表"""
    try:
        # 转换提供商字符串为枚举
        try:
            provider_enum = VideoProvider(provider)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的提供商: {provider}"
            )

        # 获取配置和服务
        config = get_config()
        video_service = get_video_service(config)

        # 获取可用模型
        models = await video_service.get_available_models(provider_enum)

        return VideoModelsResponse(
            success=True,
            message="获取模型列表成功",
            data=models
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模型列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")

@router.get("/providers")
async def get_providers():
    """获取所有支持的视频生成提供商"""
    providers = [
        {
            "value": "comfyui_wan",
            "label": "ComfyUI Wan 2.2 (推荐)",
            "description": "本地部署的Wan 2.2模型，高质量视频生成",
            "models": ["wan-2.2-t2v"],
            "recommended": True
        },
        {
            "value": "local_gpu",
            "label": "本地GPU (免费)",
            "description": "本地双4090显卡，快速生成视频",
            "models": ["basic_video_generator"]
        },
        {
            "value": "modelscope",
            "label": "ModelScope (免费)",
            "description": "阿里云免费文生视频，无需付费",
            "models": ["damo/text-to-video-synthesis"]
        },
        {
            "value": "replicate",
            "label": "Replicate ($5免费额度)",
            "description": "支持多种开源模型，注册送$5信用",
            "models": [
                "stability-ai/stable-video-diffusion-img2vid",
                "anotherjesse/zeroscope-v2-xl",
                "camenduru/text-to-video-ms-1.7b",
                "deforum/deforum_stable_diffusion",
                "lucataco/animatediff-motion"
            ]
        },
        {
            "value": "runway",
            "label": "Runway",
            "description": "专业视频生成平台，付费使用",
            "models": ["gen3a_turbo", "gen3"]
        },
        {
            "value": "pika",
            "label": "Pika Labs",
            "description": "高质量动画视频生成",
            "models": []
        },
        {
            "value": "stability",
            "label": "Stability AI",
            "description": "Stable Video Diffusion",
            "models": []
        }
    ]

    return {
        "success": True,
        "message": "获取提供商列表成功",
        "data": providers
    }

@router.post("/generate-from-optimized")
async def generate_video_from_optimized_text():
    """从优化后的文本生成视频（从localStorage读取）"""
    try:
        import json

        # 这里模拟从存储中获取优化后的文本
        # 实际使用时，前端会通过请求体传递数据
        return {
            "success": True,
            "message": "请使用POST /generate接口并传递优化后的文本",
            "data": None
        }

    except Exception as e:
        logger.error(f"从优化文本生成视频失败: {e}")
        raise HTTPException(status_code=500, detail=f"操作失败: {str(e)}")

@router.get("/status/{task_id}")
async def get_video_status(task_id: str):
    """获取视频生成任务状态"""
    try:
        if task_id not in video_tasks:
            raise HTTPException(status_code=404, detail="任务不存在")

        task = video_tasks[task_id]

        return VideoStatusResponse(
            success=True,
            message="获取任务状态成功",
            data={
                "task_id": task_id,
                "status": task.get("status", "pending"),
                "progress": task.get("progress", 0),
                "video_url": task.get("video_url"),
                "error": task.get("error")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")

@router.delete("/task/{task_id}")
async def delete_video_task(task_id: str):
    """删除视频生成任务"""
    try:
        if task_id in video_tasks:
            del video_tasks[task_id]
            return {"success": True, "message": "任务删除成功"}
        else:
            raise HTTPException(status_code=404, detail="任务不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "success": True,
        "message": "视频生成服务运行正常",
        "data": {
            "service": "video-generation",
            "version": "1.0.0",
            "providers": [p.value for p in VideoProvider]
        }
    }

# 初始化路由时设置配置
def init_video_service():
    """初始化视频服务"""
    try:
        config = get_config()
        get_video_service(config)
        logger.info("视频生成服务初始化成功")
    except Exception as e:
        logger.error(f"视频生成服务初始化失败: {e}")

# 导出初始化函数
__all__ = ["init_video_service"]