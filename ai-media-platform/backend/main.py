"""
AI媒体智能平台主服务
FastAPI后端服务，集成所有AI功能
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import yaml
from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 将 social-auto-upload 项目目录加入 Python 路径，复用上传相关模块
project_root = Path(__file__).resolve().parents[2]
legacy_social_dir = project_root / 'social-auto-upload'
if legacy_social_dir.exists() and str(legacy_social_dir) not in sys.path:
    sys.path.insert(0, str(legacy_social_dir))

# 导入服务模块
from services.llm.llm_service import get_llm_service, LLMProvider, LLMRequest, Message
from services.tts.tts_service import get_tts_service, TTSProvider, TTSRequest
from services.video.video_service_minimal import get_video_service, VideoProvider, VideoRequest, VideoService
from routes.legacy_social import router as legacy_social_router
from routes.spider import router as spider_router
from routes.video import router as video_router, init_video_service
from routes.douyin_publish import router as douyin_publish_router
from services.social_upload.social_upload_service import (
    get_social_upload_service,
    SocialPlatform,
    UploadRequest,
    BatchUploadRequest
)


# 配置日志
logger.add("logs/app.log", rotation="1 day", retention="30 days", level="INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("AI媒体平台启动中...")

    # 加载配置
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    if not config_path.exists():
        config_path = Path(__file__).parent.parent / "config" / "config.example.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    app.state.config = config

    # 初始化服务
    app.state.llm_service = get_llm_service(config)
    app.state.tts_service = get_tts_service(config)
    app.state.video_service = get_video_service(config)
    app.state.social_upload_service = get_social_upload_service(config)

    # 创建必要的目录
    Path("temp").mkdir(exist_ok=True)
    Path("storage").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    logger.info("AI媒体平台启动完成")

    yield

    # 关闭时清理
    logger.info("AI媒体平台关闭中...")


# 创建FastAPI应用
app = FastAPI(
    title="AI媒体智能平台",
    description="集成多种AI能力的媒体内容生成平台",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(legacy_social_router, tags=["Social Auto Upload"])
app.include_router(spider_router, tags=["智能爬虫"])
app.include_router(video_router, tags=["视频生成"])
app.include_router(douyin_publish_router, tags=["抖音发布"])

# 配置CORS
config = {}
config_path = Path(__file__).parent.parent / "config" / "config.yaml"
if config_path.exists():
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

cors_origins = config.get("security", {}).get("cors_origins", ["http://localhost:3000", "http://localhost:5174"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def handle_error(e: Exception, context: str = "操作") -> str:
    """统一处理错误信息，防止[object Object]问题"""
    error_msg = str(e).strip()
    if not error_msg:
        error_msg = "未知错误"
    elif error_msg == "[object Object]" or error_msg.startswith("<"):
        # 处理无法序列化的错误对象
        error_msg = f"{context}服务错误 ({type(e).__name__})"

    logger.error(f"{context}失败: {e}")
    return f"{context}失败: {error_msg}"

# 挂载静态文件
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


# 请求/响应模型
class TextOptimizeRequest(BaseModel):
    """文本优化请求"""
    text: str
    provider: LLMProvider = LLMProvider.DOUBAO


class TextOptimizeResponse(BaseModel):
    """文本优化响应"""
    optimized_text: str
    provider: str
    response_time: float


class VideoGenerateRequest(BaseModel):
    """视频生成请求"""
    prompt: str
    provider: VideoProvider = VideoProvider.COMFYUI_WAN
    duration: int = 5
    quality: str = "high"
    style: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[int] = None
    aspect_ratio: Optional[str] = None


class VideoGenerateResponse(BaseModel):
    """视频生成响应"""
    video_url: str
    video_path: Optional[str]
    duration: float
    file_size: Optional[int]
    generation_time: float
    cost: Optional[float]


class AudioGenerateRequest(BaseModel):
    """音频生成请求"""
    text: str
    provider: TTSProvider = TTSProvider.AZURE
    voice: Optional[str] = None
    speed: float = 1.0


class AudioGenerateResponse(BaseModel):
    """音频生成响应"""
    audio_path: str
    duration: float
    file_size: int
    generation_time: float


class MediaGenerateRequest(BaseModel):
    """完整媒体生成请求"""
    text: str
    llm_provider: LLMProvider = LLMProvider.DOUBAO
    video_provider: VideoProvider = VideoProvider.COMFYUI_WAN
    tts_provider: TTSProvider = TTSProvider.AZURE
    video_duration: int = 5
    voice: Optional[str] = None


class MediaGenerateResponse(BaseModel):
    """完整媒体生成响应"""
    video_path: str
    audio_path: str
    final_media_path: str
    total_time: float
    scenes_count: int
    cost_breakdown: Dict[str, float]


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI媒体智能平台",
        "version": "1.0.0",
        "docs": "/docs",
        "admin": "/admin"
    }


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "llm": "active",
            "tts": "active",
            "video": "active"
        }
    }


# LLM相关接口
@app.post("/api/v1/llm/optimize-text", response_model=TextOptimizeResponse)
async def optimize_text(request: TextOptimizeRequest):
    """优化文本为视频文案"""
    try:
        optimized_text = await app.state.llm_service.optimize_text_for_video(
            request.text,
            request.provider
        )

        return TextOptimizeResponse(
            optimized_text=optimized_text,
            provider=request.provider,
            response_time=1.5
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=handle_error(e, "文本优化"))


@app.post("/api/v1/llm/generate-script")
async def generate_script(topic: str, duration: int = 300):
    """生成视频脚本"""
    try:
        script = await app.state.llm_service.generate_video_script(
            topic,
            duration
        )
        return {"script": script}
    except Exception as e:
        raise HTTPException(status_code=500, detail=handle_error(e, "脚本生成"))


# TTS相关接口
@app.post("/api/v1/tts/synthesize", response_model=AudioGenerateResponse)
async def synthesize_speech(request: AudioGenerateRequest):
    """语音合成"""
    try:
        tts_request = TTSRequest(
            provider=request.provider,
            text=request.text,
            voice=request.voice,
            speed=request.speed
        )

        response = await app.state.tts_service.synthesize_speech(tts_request)

        return AudioGenerateResponse(
            audio_path=response.audio_path,
            duration=response.duration,
            file_size=response.audio_size,
            generation_time=response.generation_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=handle_error(e, "语音合成"))


# 视频生成相关接口
@app.post("/api/v1/video/generate", response_model=VideoGenerateResponse)
async def generate_video(request: VideoGenerateRequest):
    """生成视频"""
    try:
        video_request = VideoRequest(
            provider=request.provider,
            prompt=request.prompt,
            duration=request.duration,
            quality=request.quality,
            style=request.style,
            width=request.width or 1024,
            height=request.height or 576,
            fps=request.fps or 30
        )

        response = await app.state.video_service.generate_video(video_request)

        return VideoGenerateResponse(
            video_url=response.video_url,
            video_path=response.video_path,
            duration=response.duration,
            file_size=response.file_size,
            generation_time=response.generation_time,
            cost=response.cost
        )
    except Exception as e:
        error_msg = str(e).strip()
        if not error_msg:
            error_msg = "未知错误"
        elif error_msg == "[object Object]" or error_msg.startswith("<"):
            # 处理无法序列化的错误对象
            error_msg = f"视频生成服务错误 ({type(e).__name__})"

        logger.error(f"视频生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"视频生成失败: {error_msg}")


# 社交媒体上传相关接口
@app.post("/api/v1/social/upload")
async def upload_to_platform(request: UploadRequest):
    """上传视频到指定平台"""
    try:
        response = await app.state.social_upload_service.upload_video(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=handle_error(e, "平台上传"))


@app.post("/api/v1/social/batch-upload")
async def batch_upload_to_platforms(request: BatchUploadRequest):
    """批量上传到多个平台"""
    try:
        response = await app.state.social_upload_service.batch_upload(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=handle_error(e, "批量上传"))


@app.get("/api/v1/social/platforms")
async def get_supported_platforms():
    """获取支持的社交媒体平台"""
    try:
        platforms = await app.state.social_upload_service.get_supported_platforms()
        return {"platforms": platforms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=handle_error(e, "获取平台列表"))


@app.post("/api/v1/social/ai-generate-and-upload")
async def ai_generate_and_upload(
    text: str,
    platforms: List[SocialPlatform],
    llm_provider: LLMProvider = LLMProvider.DOUBAO,
    video_provider: VideoProvider = VideoProvider.COMFYUI_WAN,
    tts_provider: TTSProvider = TTSProvider.AZURE
):
    """AI生成内容并上传到社交媒体平台"""
    try:
        # 1. 使用LLM优化文本
        optimized_text = await app.state.llm_service.optimize_text_for_video(
            text,
            llm_provider
        )

        # 2. 生成视频
        video_request = VideoRequest(
            provider=video_provider,
            prompt=optimized_text,
            duration=10
        )
        video_response = await app.state.video_service.generate_video(video_request)

        # 3. 生成音频
        audio_request = TTSRequest(
            provider=tts_provider,
            text=optimized_text
        )
        audio_response = await app.state.tts_service.synthesize_speech(audio_request)

        # 4. 合成最终视频
        final_video_path = f"storage/ai_social_{int(time.time())}.mp4"

        # 使用FFmpeg合成视频和音频
        cmd = [
            "ffmpeg",
            "-i", video_response.video_path,
            "-i", audio_response.audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            "-y",
            final_video_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"视频合成失败: {stderr.decode()}")

        # 5. 批量上传到社交媒体
        batch_request = BatchUploadRequest(
            platforms=platforms,
            video_path=final_video_path,
            title=optimized_text[:50],  # 使用优化后文本的前50个字符作为标题
            description=optimized_text
        )

        upload_response = await app.state.social_upload_service.batch_upload(batch_request)

        return {
            "optimized_text": optimized_text,
            "video_path": final_video_path,
            "upload_results": upload_response.dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=handle_error(e, "AI生成并上传"))


# 完整媒体生成接口
@app.post("/api/v1/media/generate", response_model=MediaGenerateResponse)
async def generate_complete_media(request: MediaGenerateRequest, background_tasks: BackgroundTasks):
    """生成完整媒体内容（视频+音频）"""
    try:
        start_time = asyncio.get_event_loop().time()

        # 1. 使用LLM优化文本
        logger.info("开始优化文本...")
        optimized_text = await app.state.llm_service.optimize_text_for_video(
            request.text,
            request.llm_provider
        )

        # 2. 分割场景
        scenes = []
        lines = optimized_text.strip().split('\n')
        current_scene = ""

        for line in lines:
            if line.startswith('【场景'):
                if current_scene:
                    scenes.append(current_scene.strip())
                current_scene = line
            else:
                current_scene += " " + line if current_scene else line

        if current_scene:
            scenes.append(current_scene.strip())

        logger.info(f"分割出 {len(scenes)} 个场景")

        # 3. 并行生成视频和音频
        logger.info("开始生成视频场景...")
        video_tasks = []
        for scene in scenes[:10]:  # 限制最多10个场景
            # 提取场景描述
            scene_text = scene
            if '】' in scene_text:
                scene_text = scene_text.split('】', 1)[1]

            video_request = VideoRequest(
                provider=request.video_provider,
                prompt=scene_text,
                duration=request.video_duration
            )
            video_tasks.append(app.state.video_service.generate_video(video_request))

        logger.info("开始生成音频...")
        audio_request = TTSRequest(
            provider=request.tts_provider,
            text=optimized_text,
            voice=request.voice
        )
        audio_task = app.state.tts_service.synthesize_speech(audio_request)

        # 等待所有任务完成
        video_responses = await asyncio.gather(*video_tasks, return_exceptions=True)
        audio_response = await audio_task

        # 过滤成功的视频
        successful_videos = []
        for response in video_responses:
            if not isinstance(response, Exception):
                successful_videos.append(response)
            else:
                logger.error(f"视频生成失败: {response}")

        if not successful_videos:
            raise HTTPException(status_code=500, detail="所有视频生成都失败了")

        # 4. 合并视频
        logger.info("合并视频文件...")
        video_paths = [v.video_path for v in successful_videos if v.video_path]
        if len(video_paths) > 1:
            merged_video_path = f"temp/merged_video_{int(start_time)}.mp4"
            await app.state.video_service.merge_videos(video_paths, merged_video_path)
        elif len(video_paths) == 1:
            merged_video_path = video_paths[0]
        else:
            raise HTTPException(status_code=500, detail="没有可用的视频文件")

        # 5. 合并音频到视频
        logger.info("合成最终媒体文件...")
        final_media_path = f"storage/final_media_{int(start_time)}.mp4"

        # 使用FFmpeg合成
        cmd = [
            "ffmpeg",
            "-i", merged_video_path,
            "-i", audio_response.audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            "-y",
            final_media_path
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise HTTPException(status_code=500, detail=f"媒体合成失败: {stderr.decode()}")

        total_time = asyncio.get_event_loop().time() - start_time

        # 计算成本
        total_cost = 0.0
        cost_breakdown = {}

        for video in successful_videos:
            if video.cost:
                total_cost += video.cost
                cost_breakdown[f"video_{video.provider}"] = video.cost

        if audio_response.cost:
            total_cost += audio_response.cost
            cost_breakdown[f"audio_{audio_response.provider}"] = audio_response.cost

        return MediaGenerateResponse(
            video_path=merged_video_path,
            audio_path=audio_response.audio_path,
            final_media_path=final_media_path,
            total_time=total_time,
            scenes_count=len(successful_videos),
            cost_breakdown=cost_breakdown
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=handle_error(e, "完整媒体生成"))


# 文件下载接口
@app.get("/download/{filename}")
async def download_file(filename: str):
    """下载生成的文件"""
    file_path = Path("storage") / filename
    if file_path.exists():
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="文件不存在")


# 系统信息接口
@app.get("/api/v1/system/info")
async def system_info():
    """获取系统信息"""
    return {
        "platform": "AI媒体智能平台",
        "version": "1.0.0",
        "supported_providers": {
            "llm": [provider.value for provider in LLMProvider],
            "tts": [provider.value for provider in TTSProvider],
            "video": [provider.value for provider in VideoProvider]
        },
        "features": [
            "文本优化",
            "视频生成",
            "语音合成",
            "媒体合成",
            "批量处理"
        ]
    }


# 启动脚本
def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="AI媒体智能平台")
    parser.add_argument("--host", default="0.0.0.0", help="绑定地址")
    parser.add_argument("--port", type=int, default=9000, help="端口号")
    parser.add_argument("--reload", action="store_true", help="开发模式")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")

    args = parser.parse_args()

    logger.info(f"启动AI媒体平台服务...")
    logger.info(f"服务地址: http://{args.host}:{args.port}")
    logger.info(f"API文档: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info"
    )


if __name__ == "__main__":
    main()