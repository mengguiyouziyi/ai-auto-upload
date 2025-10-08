"""
TTS语音合成服务模块
"""

from .tts_service import get_tts_service, TTSProvider, TTSRequest, TTSResponse

__all__ = [
    "get_tts_service",
    "TTSProvider",
    "TTSRequest",
    "TTSResponse"
]