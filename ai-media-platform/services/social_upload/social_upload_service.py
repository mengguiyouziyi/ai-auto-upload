"""
社交媒体上传服务模块 - 集成多平台内容发布功能
支持抖音、快手、小红书、B站、视频号、百家号等平台
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Union
from enum import Enum
from pathlib import Path
import sys

import httpx
from pydantic import BaseModel
from loguru import logger

CURRENT_DIR = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_DIR.parents[3]
LEGACY_SOCIAL_DIR = PROJECT_ROOT / 'social-auto-upload'
if LEGACY_SOCIAL_DIR.exists() and str(LEGACY_SOCIAL_DIR) not in sys.path:
    sys.path.insert(0, str(LEGACY_SOCIAL_DIR))

# 导入各平台上传模块
try:
    from uploader.douyin_uploader.main import post_video_DouYin
    from uploader.ks_uploader.main import post_video_ks
    from uploader.xiaohongshu_uploader.main import post_video_xhs
    from uploader.bilibili_uploader.main import post_video_bilibili
    from uploader.tencent_uploader.main import post_video_tencent
    from uploader.baijiahao_uploader.main import post_video_baijiahao
except ImportError as e:
    logger.warning(f"部分上传模块导入失败: {e}")


class SocialPlatform(str, Enum):
    """支持的社交媒体平台"""
    DOUYIN = "douyin"          # 抖音
    KUAISHOU = "kuaishou"       # 快手
    XIAOHONGSHU = "xiaohongshu" # 小红书
    BILIBILI = "bilibili"       # B站
    WECHAT_VIDEO = "wechat"     # 微信视频号
    BAIJIAHAO = "baijiahao"     # 百家号


class UploadRequest(BaseModel):
    """上传请求模型"""
    platform: SocialPlatform
    video_path: str
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    cover_image: Optional[str] = None
    # 平台特定参数
    cookies: Optional[Dict] = None
    account_info: Optional[Dict] = None


class UploadResponse(BaseModel):
    """上传响应模型"""
    platform: str
    success: bool
    video_url: Optional[str] = None
    post_id: Optional[str] = None
    error_message: Optional[str] = None
    upload_time: float


class BatchUploadRequest(BaseModel):
    """批量上传请求模型"""
    platforms: List[SocialPlatform]
    video_path: str
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    cover_image: Optional[str] = None
    platform_configs: Optional[Dict[str, Dict]] = None


class BatchUploadResponse(BaseModel):
    """批量上传响应模型"""
    total_platforms: int
    success_count: int
    failed_count: int
    results: List[UploadResponse]
    total_time: float


class SocialUploadService:
    """社交媒体上传服务主类"""

    def __init__(self, config: Dict):
        self.config = config
        self.storage_config = config.get("storage", {})

    async def upload_video(self, request: UploadRequest) -> UploadResponse:
        """上传视频到指定平台"""
        start_time = time.time()

        try:
            if request.platform == SocialPlatform.DOUYIN:
                result = await self._upload_to_douyin(request)
            elif request.platform == SocialPlatform.KUAISHOU:
                result = await self._upload_to_kuaishou(request)
            elif request.platform == SocialPlatform.XIAOHONGSHU:
                result = await self._upload_to_xiaohongshu(request)
            elif request.platform == SocialPlatform.BILIBILI:
                result = await self._upload_to_bilibili(request)
            elif request.platform == SocialPlatform.WECHAT_VIDEO:
                result = await self._upload_to_wechat_video(request)
            elif request.platform == SocialPlatform.BAIJIAHAO:
                result = await self._upload_to_baijiahao(request)
            else:
                raise ValueError(f"不支持的平台: {request.platform}")

            upload_time = time.time() - start_time

            return UploadResponse(
                platform=request.platform,
                success=result.get("success", False),
                video_url=result.get("video_url"),
                post_id=result.get("post_id"),
                error_message=result.get("error_message"),
                upload_time=upload_time
            )

        except Exception as e:
            logger.error(f"视频上传失败: {e}")
            return UploadResponse(
                platform=request.platform,
                success=False,
                error_message=str(e),
                upload_time=time.time() - start_time
            )

    async def _upload_to_douyin(self, request: UploadRequest) -> Dict:
        """上传到抖音"""
        try:
            # 使用原有的抖音上传逻辑
            cookies = request.cookies or {}
            account_info = request.account_info or {}

            # 构建上传参数
            upload_params = {
                "video_path": request.video_path,
                "title": request.title,
                "description": request.description or "",
                "tags": request.tags or [],
                "cookies": cookies,
                "account_info": account_info
            }

            # 调用原有上传函数
            result = await asyncio.to_thread(post_video_DouYin, upload_params)

            return {
                "success": True,
                "video_url": result.get("video_url"),
                "post_id": result.get("post_id")
            }

        except Exception as e:
            logger.error(f"抖音上传失败: {e}")
            return {
                "success": False,
                "error_message": str(e)
            }

    async def _upload_to_kuaishou(self, request: UploadRequest) -> Dict:
        """上传到快手"""
        try:
            cookies = request.cookies or {}
            account_info = request.account_info or {}

            upload_params = {
                "video_path": request.video_path,
                "title": request.title,
                "description": request.description or "",
                "tags": request.tags or [],
                "cookies": cookies,
                "account_info": account_info
            }

            result = await asyncio.to_thread(post_video_ks, upload_params)

            return {
                "success": True,
                "video_url": result.get("video_url"),
                "post_id": result.get("post_id")
            }

        except Exception as e:
            logger.error(f"快手上传失败: {e}")
            return {
                "success": False,
                "error_message": str(e)
            }

    async def _upload_to_xiaohongshu(self, request: UploadRequest) -> Dict:
        """上传到小红书"""
        try:
            cookies = request.cookies or {}
            account_info = request.account_info or {}

            upload_params = {
                "video_path": request.video_path,
                "title": request.title,
                "description": request.description or "",
                "tags": request.tags or [],
                "cookies": cookies,
                "account_info": account_info
            }

            result = await asyncio.to_thread(post_video_xhs, upload_params)

            return {
                "success": True,
                "video_url": result.get("video_url"),
                "post_id": result.get("post_id")
            }

        except Exception as e:
            logger.error(f"小红书上传失败: {e}")
            return {
                "success": False,
                "error_message": str(e)
            }

    async def _upload_to_bilibili(self, request: UploadRequest) -> Dict:
        """上传到B站"""
        try:
            # B站上传逻辑
            upload_params = {
                "video_path": request.video_path,
                "title": request.title,
                "description": request.description or "",
                "tags": request.tags or [],
                "account_info": request.account_info or {}
            }

            result = await asyncio.to_thread(post_video_bilibili, upload_params)

            return {
                "success": True,
                "video_url": result.get("video_url"),
                "post_id": result.get("post_id")
            }

        except Exception as e:
            logger.error(f"B站上传失败: {e}")
            return {
                "success": False,
                "error_message": str(e)
            }

    async def _upload_to_wechat_video(self, request: UploadRequest) -> Dict:
        """上传到微信视频号"""
        try:
            upload_params = {
                "video_path": request.video_path,
                "title": request.title,
                "description": request.description or "",
                "tags": request.tags or [],
                "cookies": request.cookies or {},
                "account_info": request.account_info or {}
            }

            result = await asyncio.to_thread(post_video_tencent, upload_params)

            return {
                "success": True,
                "video_url": result.get("video_url"),
                "post_id": result.get("post_id")
            }

        except Exception as e:
            logger.error(f"微信视频号上传失败: {e}")
            return {
                "success": False,
                "error_message": str(e)
            }

    async def _upload_to_baijiahao(self, request: UploadRequest) -> Dict:
        """上传到百家号"""
        try:
            upload_params = {
                "video_path": request.video_path,
                "title": request.title,
                "description": request.description or "",
                "tags": request.tags or [],
                "account_info": request.account_info or {}
            }

            result = await asyncio.to_thread(post_video_baijiahao, upload_params)

            return {
                "success": True,
                "video_url": result.get("video_url"),
                "post_id": result.get("post_id")
            }

        except Exception as e:
            logger.error(f"百家号上传失败: {e}")
            return {
                "success": False,
                "error_message": str(e)
            }

    async def batch_upload(self, request: BatchUploadRequest) -> BatchUploadResponse:
        """批量上传到多个平台"""
        start_time = time.time()

        tasks = []
        for platform in request.platforms:
            # 获取平台特定配置
            platform_config = {}
            if request.platform_configs and platform.value in request.platform_configs:
                platform_config = request.platform_configs[platform.value]

            upload_request = UploadRequest(
                platform=platform,
                video_path=request.video_path,
                title=request.title,
                description=request.description,
                tags=request.tags,
                cover_image=request.cover_image,
                **platform_config
            )

            tasks.append(self.upload_video(upload_request))

        # 并行上传
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 统计结果
        success_count = 0
        failed_count = 0
        processed_results = []

        for result in results:
            if isinstance(result, Exception):
                failed_count += 1
                processed_results.append(UploadResponse(
                    platform="unknown",
                    success=False,
                    error_message=str(result),
                    upload_time=0
                ))
            else:
                processed_results.append(result)
                if result.success:
                    success_count += 1
                else:
                    failed_count += 1

        total_time = time.time() - start_time

        return BatchUploadResponse(
            total_platforms=len(request.platforms),
            success_count=success_count,
            failed_count=failed_count,
            results=processed_results,
            total_time=total_time
        )

    async def get_upload_status(self, task_id: str) -> Dict:
        """获取上传任务状态"""
        # 这里可以实现任务状态查询逻辑
        return {
            "task_id": task_id,
            "status": "completed",  # pending, uploading, completed, failed
            "progress": 100,
            "message": "上传完成"
        }

    async def cancel_upload(self, task_id: str) -> bool:
        """取消上传任务"""
        # 这里可以实现任务取消逻辑
        logger.info(f"取消上传任务: {task_id}")
        return True

    async def get_supported_platforms(self) -> List[Dict]:
        """获取支持的平台列表"""
        return [
            {
                "platform": SocialPlatform.DOUYIN,
                "name": "抖音",
                "description": "短视频平台，适合娱乐内容",
                "max_video_size": "2GB",
                "max_video_duration": "15分钟",
                "supported_formats": ["mp4", "mov"]
            },
            {
                "platform": SocialPlatform.KUAISHOU,
                "name": "快手",
                "description": "短视频平台，适合生活记录",
                "max_video_size": "2GB",
                "max_video_duration": "10分钟",
                "supported_formats": ["mp4", "mov"]
            },
            {
                "platform": SocialPlatform.XIAOHONGSHU,
                "name": "小红书",
                "description": "生活方式分享平台",
                "max_video_size": "500MB",
                "max_video_duration": "5分钟",
                "supported_formats": ["mp4", "mov"]
            },
            {
                "platform": SocialPlatform.BILIBILI,
                "name": "B站",
                "description": "弹幕视频网站，适合年轻用户",
                "max_video_size": "8GB",
                "max_video_duration": "12小时",
                "supported_formats": ["mp4", "flv", "avi"]
            },
            {
                "platform": SocialPlatform.WECHAT_VIDEO,
                "name": "微信视频号",
                "description": "微信生态短视频平台",
                "max_video_size": "1GB",
                "max_video_duration": "30分钟",
                "supported_formats": ["mp4", "mov"]
            },
            {
                "platform": SocialPlatform.BAIJIAHAO,
                "name": "百家号",
                "description": "百度内容创作平台",
                "max_video_size": "2GB",
                "max_video_duration": "60分钟",
                "supported_formats": ["mp4", "mov"]
            }
        ]


# 全局社交媒体上传服务实例
_social_upload_service: Optional[SocialUploadService] = None


def get_social_upload_service(config: Dict) -> SocialUploadService:
    """获取社交媒体上传服务实例"""
    global _social_upload_service
    if _social_upload_service is None:
        _social_upload_service = SocialUploadService(config)
    return _social_upload_service


# 测试代码
async def main():
    """测试社交媒体上传服务"""
    config = {
        "storage": {
            "base_path": "./storage"
        }
    }

    service = get_social_upload_service(config)

    # 测试获取支持的平台
    platforms = await service.get_supported_platforms()
    print("支持的社交媒体平台:")
    for platform in platforms:
        print(f"- {platform['name']}: {platform['description']}")

    # 测试批量上传
    request = BatchUploadRequest(
        platforms=[SocialPlatform.DOUYIN, SocialPlatform.KUAISHOU],
        video_path="./test_video.mp4",
        title="测试视频标题",
        description="这是一个测试视频",
        tags=["测试", "AI", "视频"]
    )

    try:
        result = await service.batch_upload(request)
        print(f"批量上传结果: 成功{result.success_count}个，失败{result.failed_count}个")
    except Exception as e:
        print(f"批量上传测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())