"""
社交媒体上传服务模块
"""

from .social_upload_service import (
    get_social_upload_service,
    SocialPlatform,
    UploadRequest,
    UploadResponse,
    BatchUploadRequest,
    BatchUploadResponse
)

__all__ = [
    "get_social_upload_service",
    "SocialPlatform",
    "UploadRequest",
    "UploadResponse",
    "BatchUploadRequest",
    "BatchUploadResponse"
]