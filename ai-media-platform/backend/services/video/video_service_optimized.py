"""
文生视频服务模块 - 4步LoRA优化版本
基于769759d66fe2111e917befbee6ac9ffc11a2b9ab提交的修复
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Union
from enum import Enum
from pathlib import Path
import aiohttp

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # 简单的BaseModel替代
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


class VideoProvider(str, Enum):
    """支持的视频生成提供商"""
    COMFYUI_WAN = "comfyui_wan"
    LOCAL_GPU = "local_gpu"
    SIMPLE_OPEN = "simple_open"


class VideoRequest(BaseModel):
    """视频生成请求模型"""
    provider: VideoProvider
    prompt: str
    duration: int = 10
    width: int = 640  # 提升默认分辨率
    height: int = 640  # 提升默认分辨率
    fps: int = 16
    quality: str = "high"
    style: Optional[str] = None
    seed: Optional[int] = None
    aspect_ratio: Optional[str] = None
    use_standard_workflow: bool = True


class VideoResponse(BaseModel):
    """视频生成响应模型"""
    provider: str
    model: str
    video_url: str
    video_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: str = "completed"
    duration: float
    fps: int
    resolution: str
    file_size: Optional[int] = None
    generation_time: float
    cost: Optional[float] = None
    prompt: str
    request_id: str


class OptimizedVideoService:
    """4步LoRA优化视频生成服务类"""

    def __init__(self, config: Dict):
        """初始化视频服务"""
        self.config = config
        self.api_keys = config.get("video_apis", {})

        # ComfyUI配置
        self.comfyui_api_url = "http://192.168.1.246:5001"  # API包装器地址
        self.comfyui_direct_url = "http://192.168.1.246:8188"  # 直接ComfyUI地址
        self.comfyui_url = self.comfyui_direct_url  # 用于视频下载的URL

        print("🚀 4步LoRA优化视频服务初始化完成")

    async def generate_video(self, request: VideoRequest) -> VideoResponse:
        """生成视频 - 强制使用4步LoRA优化工作流"""
        print(f"收到视频生成请求: provider={request.provider}, prompt={request.prompt[:50]}...")

        try:
            # 强制使用4步LoRA优化工作流（跳过API包装器默认参数）
            print("🚀 强制使用4步LoRA优化工作流（跳过API包装器默认参数）")
            return await self._generate_via_direct_comfyui(request)

        except Exception as e:
            print(f"视频生成失败: {str(e)}")
            raise Exception(f"视频生成失败: {str(e)}")

    async def _generate_via_direct_comfyui(self, request: VideoRequest):
        """直接调用ComfyUI - 4步LoRA优化版本"""
        start_time = time.time()

        try:
            print(f"🎯 直接调用ComfyUI: {self.comfyui_direct_url}")

            # 创建4步LoRA优化的工作流
            workflow = self._create_4step_lora_workflow(request)

            # 提交到ComfyUI
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30.0)) as session:
                async with session.post(f"{self.comfyui_direct_url}/prompt", json={
                    "prompt": workflow
                }) as response:
                    response.raise_for_status()
                    result = await response.json()
                    task_id = result.get("prompt_id")

            if not task_id:
                raise Exception("提交ComfyUI任务失败")

            print(f"ComfyUI任务已创建: {task_id}")
            print(f"开始监控任务 {task_id}...")

            # 监控任务进度并获取结果
            video_info = await self._monitor_direct_task(task_id, request, start_time)

            if not video_info:
                raise Exception("ComfyUI视频生成失败")

            return VideoResponse(
                provider="comfyui_wan",
                model="wan-2.2-t2v-4step-lora",
                video_url=video_info["video_url"],
                video_path=video_info["video_path"],
                thumbnail_url=None,
                status="completed",
                duration=request.duration,
                fps=min(request.fps, 16),
                resolution=f"{request.width}x{request.height}",
                file_size=video_info.get("file_size"),
                generation_time=video_info["generation_time"],
                prompt=request.prompt,
                request_id=str(uuid.uuid4())
            )

        except Exception as e:
            print(f"直接ComfyUI调用失败: {str(e)}")
            raise Exception(f"ComfyUI视频生成失败: {str(e)}")

    def _create_4step_lora_workflow(self, request: VideoRequest):
        """创建4步LoRA优化的工作流"""
        # 优化prompt
        optimized_prompt = self._optimize_prompt(request.prompt)

        # 生成唯一文件名
        filename_prefix = f"wan_video_{uuid.uuid4().hex[:8]}"

        # 使用640x640作为默认分辨率（更高的质量）
        width = min(max(640, min(request.width, 1024)), 1024)
        height = min(max(640, min(request.height, 1024)), 1024)

        # 81帧（5秒@16fps）- 优化的帧数
        num_frames = min(max(48, request.duration * 16), 160)

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
            "77": {  # LoRALoader
                "inputs": {
                    "lora_name": "wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors",
                    "strength_model": 1.0,
                    "strength_clip": 1.0
                },
                "class_type": "LoRALoader"
            },
            "79": {  # WanVideoT2V - 4步优化
                "inputs": {
                    "prompt": optimized_prompt,
                    "negative_prompt": "static, still, frozen, motionless, blurry, low quality, distorted, watermark, text, error, ugly, deformed",
                    "width": width,
                    "height": height,
                    "num_frames": num_frames,
                    "steps": steps,  # 4步LoRA
                    "cfg": cfg,    # 降低CFG到1.0
                    "shift": shift,  # LoRA优化参数
                    "seed": request.seed or -1,
                    "denoising_strength": 1.0,
                    "context_frames": 16,
                    "context_overlap": 4
                },
                "class_type": "WanVideoT2V"
            },
            "81": {  # VAE编码
                "inputs": {
                    "samples": ["79", 0],
                    "vae": ["73", 0]
                },
                "class_type": "VAEEncode"
            },
            "83": {  # 创建视频
                "inputs": {
                    "fps": min(request.fps, 16),
                    "images": ["81", 0],
                    "loop_count": 0
                },
                "class_type": "CreateVideo"
            },
            "85": {  # 保存MP4
                "inputs": {
                    "filename_prefix": filename_prefix,
                    "format": "mp4",
                    "codec": "h264",
                    "fps": min(request.fps, 16),
                    "crf": 23,
                    "video": ["83", 0]
                },
                "class_type": "SaveVideo"
            }
        }

        print(f"🎬 创建4步LoRA优化工作流:")
        print(f"   文件名: {filename_prefix}")
        print(f"   分辨率: {width}x{height}")
        print(f"   帧数: {num_frames}帧 (时长{request.duration}秒)")
        print(f"   步数: {steps}步 (LoRA优化)")
        print(f"   CFG: {cfg}")
        print(f"   原始prompt: {request.prompt[:50]}...")
        print(f"   优化prompt: {optimized_prompt[:50]}...")

        return workflow

    def _optimize_prompt(self, prompt: str) -> str:
        """优化prompt，适合4步LoRA快速生成"""
        # 定义场景首尾相接的模板
        scene_templates = [
            "科技代码流动，数字网格背景，逐渐构建出动态界面",
            "自然风光转场，山水相连，云雾缭绕过渡",
            "城市天际线，建筑群相连，灯光渐变展示",
            "抽象形状变换，色彩流动，几何图形自然过渡",
            "人物动作连贯，姿态流畅，场景无缝切换"
        ]

        # 检查用户prompt是否包含场景关键词
        if "【场景" in prompt and "】" in prompt:
            # 已经是场景格式，保持原样
            return prompt
        elif len(prompt) > 100:
            # prompt过长，选择合适的场景模板
            for template in scene_templates:
                if any(keyword in prompt.lower() for keyword in ["科技", "代码", "数字"]):
                    return f"高科技视频：{template}，{prompt[:30]}，流畅动画，电影级画质"
                elif any(keyword in prompt.lower() for keyword in ["山", "水", "自然", "风景"]):
                    return f"自然风光：{template}，{prompt[:30]}，唯美意境，4K画质"
                elif any(keyword in prompt.lower() for keyword in ["城市", "建筑", "灯光"]):
                    return f"城市景观：{template}，{prompt[:30]}，现代都市，高清画质"

        # 默认优化：添加场景连接词
        if "，" in prompt:
            parts = prompt.split("，", 2)
            if len(parts) >= 2:
                return f"{parts[0]}，自然过渡到{parts[1]}，{'，'.join(parts[2:]) if len(parts) > 2 else ''}"

        # 简单prompt，添加场景连接
        return f"{prompt}，场景自然过渡，动画流畅，高清画质"

    async def _monitor_direct_task(self, task_id: str, request: VideoRequest, start_time: float):
        """监控直接ComfyUI任务进度"""
        max_wait_time = 600  # 10分钟超时
        check_interval = 3   # 3秒检查一次

        print(f"⏱️ 开始监控任务 {task_id[:8]}...")

        while time.time() - start_time < max_wait_time:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15.0)) as session:
                    async with session.get(f"{self.comfyui_direct_url}/history/{task_id}") as response:
                        response.raise_for_status()
                        history = await response.json()

                        if task_id in history:
                            task_data = history[task_id]
                            status_info = task_data.get("status", {})
                            queue_info = status_info.get("queue", {})

                            # 显示详细进度信息
                            elapsed = time.time() - start_time
                            if queue_info:
                                queue_remaining = queue_info.get("remaining", 0)
                                queue_total = queue_info.get("total", 0)
                                print(f"⏳ 任务进行中... ({elapsed:.1f}秒) 队列进度: {queue_remaining}/{queue_total}")
                            else:
                                print(f"⏳ 任务进行中... ({elapsed:.1f}秒)")

                            # 检查任务是否完成
                            if status_info.get("status_str") == "success" or task_data.get("status") == "completed":
                                outputs = task_data.get("outputs", {})

                                # 查找输出文件
                                filename = None
                                file_size = 0

                                for node_id, node_output in outputs.items():
                                    print(f"🔍 检查节点 {node_id} 输出: {list(node_output.keys())}")

                                    # 优先查找视频输出
                                    if "videos" in node_output:
                                        videos = node_output["videos"]
                                        if videos and len(videos) > 0:
                                            video = videos[0]
                                            filename = video.get("filename", "")
                                            file_info = video.get("subfolder", "")
                                            print(f"🎬 找到视频输出: {filename} (子文件夹: {file_info})")

                                    # 然后查找图像输出
                                    elif "images" in node_output:
                                        images = node_output["images"]
                                        if images and len(images) > 0 and filename is None:
                                            filename = images[0].get("filename")
                                            file_info = images[0].get("subfolder", "")
                                            print(f"📸 找到图像输出: {filename} (子文件夹: {file_info})")

                                if filename:
                                    generation_time = time.time() - start_time

                                    # 尝试获取文件大小
                                    try:
                                        file_url = f"{self.comfyui_direct_url}/view?filename={filename}"
                                        async with session.head(file_url, timeout=5.0) as file_response:
                                            if file_response.status_code == 200:
                                                size_header = file_response.headers.get("content-length", "0")
                                                file_size = int(size_header)
                                    except:
                                        pass

                                    print(f"✅ 视频生成完成！")
                                    print(f"   文件: {filename}")
                                    print(f"   耗时: {generation_time:.1f}秒")
                                    print(f"   文件大小: {file_size:,} bytes")

                                    # 返回视频信息
                                    return {
                                        "video_url": f"{self.comfyui_direct_url}/view?filename={filename}",
                                        "video_path": filename,
                                        "file_size": file_size,
                                        "generation_time": generation_time
                                    }
                                else:
                                    print("⚠️ 任务完成但未找到输出文件")
                                    return None

                            elif status_info.get("status_str") == "error" or task_data.get("status") == "failed":
                                error_msg = task_data.get("error", "未知错误")
                                print(f"❌ 任务失败: {error_msg}")
                                raise Exception(f"ComfyUI任务失败: {error_msg}")

                await asyncio.sleep(check_interval)

            except Exception as e:
                print(f"监控任务异常: {e}")
                await asyncio.sleep(check_interval)
                continue

        elapsed = time.time() - start_time
        print(f"⏰ 任务超时 ({elapsed:.1f}秒)")
        raise Exception(f"ComfyUI任务超时: {elapsed:.1f}秒")

    def get_available_models(self, provider: VideoProvider) -> List[str]:
        """获取指定提供商的可用模型列表"""
        if provider == VideoProvider.COMFYUI_WAN:
            return ["wan-2.2-t2v-4step-lora"]
        elif provider == VideoProvider.LOCAL_GPU:
            return ["basic_video_generator"]
        elif provider == VideoProvider.SIMPLE_OPEN:
            return ["ai_style_generator"]
        else:
            return []

    def get_supported_providers(self) -> List[Dict[str, any]]:
        """获取支持的视频提供商列表"""
        return [
            {
                "value": "comfyui_wan",
                "label": "ComfyUI Wan 2.2 (4步LoRA优化)",
                "description": "使用4步LoRA优化工作流，8倍速度提升",
                "models": ["wan-2.2-t2v-4step-lora"],
                "recommended": True,
                "max_duration": 30,
                "max_resolution": "1024x1024",
                "supports_style": False,
                "supports_aspect_ratio": False,
                "default_fps": 16,
                "quality_levels": ["standard", "high", "ultra"],
                "optimization": "4步LoRA，8倍速度提升，2.5倍清晰度"
            },
            {
                "value": "local_gpu",
                "label": "本地GPU服务器",
                "description": "使用本地GPU服务器生成视频",
                "models": ["basic_video_generator"],
                "recommended": False,
                "max_duration": 60,
                "max_resolution": "1920x1080",
                "supports_style": True,
                "supports_aspect_ratio": True
            },
            {
                "value": "simple_open",
                "label": "免费开源API",
                "description": "使用免费的第三方API生成视频",
                "models": ["ai_style_generator"],
                "recommended": False,
                "max_duration": 15,
                "max_resolution": "1024x576",
                "supports_style": True,
                "supports_aspect_ratio": False
            }
        ]


def get_optimized_video_service(config: Dict) -> OptimizedVideoService:
    """获取优化视频服务实例"""
    return OptimizedVideoService(config)