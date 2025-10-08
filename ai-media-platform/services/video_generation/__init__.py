"""
视频生成服务模块
"""

from .video_service import get_video_service, VideoProvider, VideoRequest, VideoResponse

__all__ = [
    "get_video_service",
    "VideoProvider",
    "VideoRequest",
    "VideoResponse"
]