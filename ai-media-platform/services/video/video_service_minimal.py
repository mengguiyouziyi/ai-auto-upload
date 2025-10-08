"""
文生视频服务模块 - 简化版本，专注于ComfyUI集成
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Union
from enum import Enum
from pathlib import Path

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
    duration: int = 10  # 增加默认视频时长（秒）
    width: int = 720
    height: int = 720
    fps: int = 16
    quality: str = "high"  # low, medium, high
    style: Optional[str] = None  # 视频风格
    seed: Optional[int] = None
    aspect_ratio: Optional[str] = None
    use_standard_workflow: bool = True  # 使用标准工作流


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


class VideoService:
    """视频生成服务类"""

    def __init__(self, config: Dict):
        """初始化视频服务"""
        self.config = config
        self.api_keys = config.get("video_apis", {})
        print("视频服务初始化完成")

    async def generate_video(self, request: VideoRequest) -> VideoResponse:
        """生成视频的主入口"""
        try:
            if request.provider == VideoProvider.COMFYUI_WAN:
                return await self._call_comfyui_wan(request)
            elif request.provider == VideoProvider.LOCAL_GPU:
                return await self._call_local_gpu(request)
            elif request.provider == VideoProvider.SIMPLE_OPEN:
                return await self._call_simple_open(request)
            else:
                raise ValueError(f"不支持的视频提供商: {request.provider}")
        except Exception as e:
            raise Exception(f"视频生成失败: {str(e)}")

    async def _call_comfyui_wan(self, request: VideoRequest) -> VideoResponse:
        """调用ComfyUI本地部署的Wan 2.2模型生成视频 - 使用标准工作流文件"""
        start_time = time.time()

        # ComfyUI API配置
        comfyui_url = "http://192.168.1.246:8188"

        print(f"使用ComfyUI Wan 2.2标准工作流: {comfyui_url}")
        print(f"提示词: {request.prompt[:50]}...")

        try:
            # 使用标准工作流文件
            workflow = await self._load_standard_workflow(comfyui_url, request)

            # 提交任务到ComfyUI
            prompt_id = await self._submit_comfyui_prompt(comfyui_url, workflow)

            if not prompt_id:
                raise Exception("提交ComfyUI任务失败")

            print(f"ComfyUI任务已创建: {prompt_id}")

            # 监控任务进度并获取结果
            video_filename, generation_time, file_size = await self._monitor_comfyui_task(
                comfyui_url, prompt_id, start_time
            )

            if not video_filename:
                raise Exception("ComfyUI视频生成失败")

            # 构建视频URL
            video_url = f"{comfyui_url}/view?filename={video_filename}"

            generation_time = time.time() - start_time

            return VideoResponse(
                provider="comfyui_wan",
                model="wan-2.2-t2v",
                video_url=video_url,
                video_path=video_url,  # 对于远程API，path和url相同
                thumbnail_url=None,
                status="completed",
                duration=request.duration,
                fps=min(request.fps, 16),  # Wan 2.2 默认16fps
                resolution=f"{request.width}x{request.height}",
                file_size=file_size if file_size > 0 else None,
                generation_time=generation_time,
                prompt=request.prompt,
                request_id=str(uuid.uuid4())
            )

        except Exception as e:
            raise Exception(f"ComfyUI视频生成失败: {str(e)}")

    async def _load_standard_workflow(self, comfyui_url: str, request: VideoRequest) -> Dict[str, any]:
        """加载ComfyUI工作流文件 - 优先使用双GPU工作流"""
        if not HTTPX_AVAILABLE:
            raise Exception("httpx库未安装，无法进行HTTP请求")

        # 1️⃣ 首先尝试加载优化的工作流文件
        try:
            workflow_file = Path(__file__).parent.parent.parent / "optimized_video_workflow.json"
            if workflow_file.exists():
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_data = json.load(f)

                # 处理工作流格式
                if "workflow" in workflow_data:
                    workflow = workflow_data["workflow"]
                else:
                    workflow = workflow_data

                # 优化prompt并更新参数
                optimized_prompt = self._optimize_prompt_scenes(request.prompt)
                workflow = self._update_workflow_parameters(workflow, optimized_prompt, request)

                print("✅ 成功加载双GPU工作流文件")
                print(f"   优化prompt: {optimized_prompt[:50]}...")
                return workflow
            else:
                print(f"⚠️ 优化工作流文件不存在: {workflow_file}")

        except Exception as e:
            print(f"⚠️ 加载双GPU工作流失败: {str(e)}")

        # 2️⃣ 尝试加载标准工作流文件
        # 尝试加载优化工作流文件
        workflow_filenames = [
            "user/default/workflows/optimized_video_workflow.json",  # 优化工作流
            "user/default/workflows/corrected_video_workflow.json",  # 修正工作流
            "user/default/workflows/video_wan2_2_14B_t2v.json"  # 标准工作流（回退）
        ]

        for workflow_filename in workflow_filenames:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(f"{comfyui_url}/view", params={
                        "filename": workflow_filename
                    })
                    response.raise_for_status()
                    workflow = response.json()

                print(f"✅ 成功加载工作流文件: {workflow_filename}")
                return self._update_workflow_parameters(workflow, request.prompt, request)

            except Exception as e:
                print(f"⚠️ 无法加载工作流文件 {workflow_filename}: {str(e)}")
                continue

        # 所有工作流都加载失败，使用默认工作流
        print("⚠️ 所有工作流文件加载失败，使用默认工作流")
        return self._create_fallback_workflow(request)

    def _update_workflow_parameters(self, workflow: Dict, prompt: str, request: VideoRequest) -> Dict:
        """更新工作流参数"""
        # 处理工作流格式
        if workflow and "workflow" in workflow:
            actual_workflow = workflow["workflow"]
        else:
            actual_workflow = workflow

        # 查找并修改WanVideoT2V节点
        for node_id, node in actual_workflow.items():
            if node.get("class_type") == "WanVideoT2V":
                inputs = node["inputs"]
                inputs["prompt"] = prompt
                inputs["width"] = min(max(512, min(request.width, 1024)), 1024)  # 提升最小分辨率为512
                inputs["height"] = min(max(512, min(request.height, 1024)), 1024)  # 提升最小分辨率为512
                inputs["num_frames"] = max(48, min(request.duration * 16, 160))  # 增加帧数：48-160帧
                inputs["steps"] = max(25, min(40, 35 - request.duration // 6))  # 增加步数，提升质量
                inputs["cfg"] = 7.5  # 提升CFG值，获得更好的生成质量
                inputs["seed"] = request.seed or -1
                print(f"✅ 修改WanVideoT2V节点参数: {node_id}")
                break

        # 查找并修改保存节点 - 优先查找MP4保存节点
        mp4_node_found = False
        for node_id, node in actual_workflow.items():
            if node.get("class_type") == "SaveVideo":
                inputs = node["inputs"]
                inputs["filename_prefix"] = f"wan_video_{uuid.uuid4().hex[:8]}"
                inputs["format"] = "mp4"  # 确保MP4格式
                inputs["codec"] = "h264"  # H.264编码
                inputs["fps"] = min(max(request.fps, 12), 24)  # 确保fps在12-24之间
                inputs["crf"] = 23  # 控制视频质量和文件大小的平衡点
                print(f"✅ 修改MP4保存节点参数: {node_id}")
                mp4_node_found = True
                break

        # 如果没有找到MP4保存节点，查找其他保存节点
        if not mp4_node_found:
            for node_id, node in actual_workflow.items():
                if node.get("class_type") in ["SaveAnimatedWEBP", "SaveAnimatedPNG"]:
                    inputs = node["inputs"]
                    inputs["filename_prefix"] = f"wan_video_{uuid.uuid4().hex[:8]}"
                    inputs["fps"] = min(request.fps, 16)
                    inputs["quality"] = 90
                    print(f"✅ 修改动画保存节点参数: {node_id}")
                    break

        return actual_workflow

    def _create_fallback_workflow(self, request: VideoRequest) -> Dict[str, any]:
        """创建高性能双GPU视频工作流 - 优化场景首尾相接，生成MP4"""
        # 计算合适的帧数 - 优化版本
        num_frames = max(48, min(request.duration * 16, 160))  # 增加帧数：48-160帧，提升流畅度

        # 根据时长调整采样步数 - 优化版本
        steps = max(25, min(40, 35 - request.duration // 6))  # 增加步数：25-40步，提升质量

        # 生成唯一文件名
        filename_prefix = f"wan_video_{uuid.uuid4().hex[:8]}"

        # 优化prompt，使其更短且场景首尾相接
        optimized_prompt = self._optimize_prompt_scenes(request.prompt)

        workflow = {
            "1": {
                "inputs": {
                    "prompt": optimized_prompt,
                    "negative_prompt": "static, still, frozen, motionless, blurry, low quality, distorted, watermark, text, error, ugly, deformed",
                    "width": min(max(512, min(request.width, 1024)), 1024),  # 提升最小分辨率为512
                    "height": min(max(512, min(request.height, 1024)), 1024),  # 提升最小分辨率为512
                    "num_frames": num_frames,
                    "steps": steps,
                    "cfg": 7.5,  # 提升CFG值，获得更好的生成质量
                    "seed": request.seed or -1
                },
                "class_type": "WanVideoT2V"
            },
            "2": {
                "inputs": {
                    "samples": ["1", 0],
                    "vae_name": "Wan2_1_VAE.safetensors"  # 使用正确的VAE名称
                },
                "class_type": "WanVideoVAE"
            },
            "3": {
                "inputs": {
                    "fps": min(request.fps, 16),
                    "images": ["2", 0]
                },
                "class_type": "CreateVideo"
            },
            "4": {
                "inputs": {
                    "filename_prefix": filename_prefix,
                    "format": "mp4",  # 确保MP4格式
                    "codec": "h264",  # H.264编码
                    "video": ["3", 0]
                },
                "class_type": "SaveVideo"
            }
        }

        print(f"🎬 创建优化工作流:")
        print(f"   文件名: {filename_prefix}")
        print(f"   帧数: {num_frames}帧 (时长{request.duration}秒)")
        print(f"   分辨率: {request.width}x{request.height}")
        print(f"   步数: {steps}步")
        print(f"   原始prompt: {request.prompt[:50]}...")
        print(f"   优化prompt: {optimized_prompt[:50]}...")

        return workflow

    def _optimize_prompt_scenes(self, prompt: str) -> str:
        """优化prompt，使其更短且场景首尾相接"""
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
            parts = prompt.split("，", 2)  # 最多分成3部分
            if len(parts) >= 2:
                return f"{parts[0]}，自然过渡到{parts[1]}，{'，'.join(parts[2:]) if len(parts) > 2 else ''}"

        # 简单prompt，添加场景连接
        return f"{prompt}，场景自然过渡，动画流畅，高清画质"

    async def _submit_comfyui_prompt(self, comfyui_url: str, workflow: Dict[str, any]) -> str:
        """提交任务到ComfyUI"""
        if not HTTPX_AVAILABLE:
            raise Exception("httpx库未安装，无法进行HTTP请求")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{comfyui_url}/prompt",
                json={"prompt": workflow}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("prompt_id")

    async def _monitor_comfyui_task(self, comfyui_url: str, prompt_id: str, start_time: float) -> tuple:
        """监控ComfyUI任务进度 - 高性能版本"""
        if not HTTPX_AVAILABLE:
            raise Exception("httpx库未安装，无法进行HTTP请求")

        check_interval = 3  # 更频繁的检查
        max_wait_time = 600  # 10分钟超时，视频生成需要更长时间

        print(f"⏱️ 开始监控任务 {prompt_id[:8]}...")

        while time.time() - start_time < max_wait_time:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(f"{comfyui_url}/history/{prompt_id}")
                    response.raise_for_status()

                    history = response.json()
                    if prompt_id in history:
                        task_data = history[prompt_id]
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

                            # 详细查找输出 - 优先查找MP4视频
                            filename = None
                            file_size = 0
                            mp4_filename = None

                            for node_id, node_output in outputs.items():
                                print(f"🔍 检查节点 {node_id} 输出: {list(node_output.keys())}")

                                # 首先查找视频输出
                                if "videos" in node_output:
                                    videos = node_output["videos"]
                                    if videos and len(videos) > 0:
                                        for video in videos:
                                            video_filename = video.get("filename", "")
                                            file_info = video.get("subfolder", "")

                                            # 优先选择MP4文件
                                            if video_filename.endswith(".mp4"):
                                                mp4_filename = video_filename
                                                print(f"🎬 找到MP4视频: {video_filename} (子文件夹: {file_info})")
                                            elif filename is None:
                                                filename = video_filename
                                                print(f"🎬 找到视频输出: {video_filename} (子文件夹: {file_info})")

                                # 然后查找图像输出（动图等）
                                if "images" in node_output:
                                    images = node_output["images"]
                                    if images and len(images) > 0 and filename is None:
                                        filename = images[0].get("filename")
                                        file_info = images[0].get("subfolder", "")
                                        print(f"📸 找到图像输出: {filename} (子文件夹: {file_info})")

                            # 使用MP4文件（如果找到）
                            if mp4_filename:
                                filename = mp4_filename
                                print(f"✅ 优先使用MP4格式: {filename}")

                            if filename:
                                generation_time = time.time() - start_time

                                # 尝试获取文件大小和类型验证
                                try:
                                    file_url = f"{comfyui_url}/view?filename={filename}"
                                    file_response = await client.head(file_url, timeout=5.0)
                                    if file_response.status_code == 200:
                                        size_header = file_response.headers.get("content-length", "0")
                                        file_size = int(size_header)
                                        content_type = file_response.headers.get("content-type", "")

                                        print(f"📊 文件大小: {file_size:,} bytes")
                                        print(f"📁 文件类型: {content_type}")

                                        # 根据文件扩展名和大小进行验证
                                        if filename.endswith(".mp4"):
                                            if file_size < 10000:  # MP4文件通常大于10KB
                                                print("⚠️ 警告: MP4文件过小，可能生成不完整")
                                            else:
                                                print("✅ MP4文件大小正常")
                                        elif filename.endswith((".webp", ".gif", ".png")):
                                            if file_size < 1000:
                                                print("⚠️ 警告: 图像文件过小")
                                            else:
                                                print("✅ 动图文件大小正常")
                                        else:
                                            # 未知格式，根据大小判断
                                            if file_size < 1000:
                                                print("⚠️ 警告: 文件过小，可能是静态图片")
                                            else:
                                                print("✅ 文件大小正常，应该是视频文件")

                                except Exception as size_e:
                                    print(f"⚠️ 无法获取文件大小: {size_e}")

                                print(f"✅ 视频生成完成！")
                                print(f"   文件: {filename}")
                                print(f"   耗时: {generation_time:.1f}秒")
                                print(f"   文件大小: {file_size:,} bytes")

                                return filename, generation_time, file_size
                            else:
                                print("⚠️ 任务完成但未找到输出文件")
                                # 尝试构造可能的文件名
                                import time as time_module
                                timestamp = int(time_module.time())
                                filename = f"wan_video_{timestamp}.webp"
                                generation_time = time.time() - start_time
                                file_size = 0
                                return filename, generation_time, file_size

                        elif status_info.get("status_str") == "error" or task_data.get("status") == "failed":
                            error_msg = task_data.get("error", "未知错误")
                            print(f"❌ 任务失败: {error_msg}")

                            # 显示详细错误信息
                            if "node_errors" in task_data:
                                node_errors = task_data["node_errors"]
                                for node_id, error_info in node_errors.items():
                                    print(f"   节点 {node_id} 错误: {error_info}")

                            raise Exception(f"ComfyUI任务失败: {error_msg}")

                await asyncio.sleep(check_interval)

            except Exception as e:
                print(f"监控任务异常: {e}")
                await asyncio.sleep(check_interval)

        elapsed = time.time() - start_time
        print(f"⏰ 任务超时 ({elapsed:.1f}秒)")
        raise Exception(f"ComfyUI任务超时: {elapsed:.1f}秒")

    async def _call_local_gpu(self, request: VideoRequest) -> VideoResponse:
        """调用本地GPU服务器生成视频"""
        raise NotImplementedError("本地GPU服务暂未实现")

    async def _call_simple_open(self, request: VideoRequest) -> VideoResponse:
        """调用免费开源API生成视频"""
        raise NotImplementedError("免费开源API服务暂未实现")

    def get_available_models(self, provider: VideoProvider) -> List[str]:
        """获取指定提供商的可用模型列表"""
        if provider == VideoProvider.COMFYUI_WAN:
            return ["wan-2.2-t2v"]
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
                "label": "ComfyUI Wan 2.2 (标准工作流)",
                "description": "使用标准ComfyUI工作流，支持更长视频生成",
                "models": ["wan-2.2-t2v"],
                "recommended": True,
                "max_duration": 30,  # 增加最大支持时长
                "max_resolution": "1280x720",  # 提高分辨率
                "supports_style": False,
                "supports_aspect_ratio": False,
                "default_fps": 16,
                "quality_levels": ["standard", "high", "ultra"]
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


def get_video_service(config: Dict) -> VideoService:
    """获取视频服务实例"""
    return VideoService(config)