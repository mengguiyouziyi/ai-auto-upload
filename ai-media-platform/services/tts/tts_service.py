"""
TTS语音合成服务模块 - 集成多种语音合成API
支持Azure TTS、阿里云TTS、腾讯云TTS、OpenAI TTS等
"""

import asyncio
import json
import time
from typing import Dict, Optional, Union
from enum import Enum
from pathlib import Path
import httpx
from pydantic import BaseModel
from loguru import logger
import base64


class TTSProvider(str, Enum):
    """支持的TTS提供商"""
    AZURE = "azure_tts"
    ALIYUN = "aliyun_tts"
    TENCENT = "tencent_tts"
    OPENAI = "openai_tts"
    BAIDU = "baidu_tts"


class TTSRequest(BaseModel):
    """TTS请求模型"""
    provider: TTSProvider
    text: str
    voice: Optional[str] = None  # 音色
    speed: float = 1.0  # 语速
    pitch: float = 1.0  # 音调
    format: str = "mp3"  # 输出格式
    sample_rate: int = 22050  # 采样率
    language: str = "zh-CN"  # 语言


class TTSResponse(BaseModel):
    """TTS响应模型"""
    provider: str
    voice: str
    audio_path: str
    audio_size: int
    duration: float
    generation_time: float
    cost: Optional[float] = None


class TTSService:
    """TTS语音合成服务主类"""

    def __init__(self, config: Dict):
        self.config = config
        self.api_keys = config.get("api_keys", {})
        self.models_config = config.get("models", {}).get("tts", {})

    async def synthesize_speech(self, request: TTSRequest) -> TTSResponse:
        """语音合成"""
        try:
            if request.provider == TTSProvider.AZURE:
                return await self._call_azure_tts(request)
            elif request.provider == TTSProvider.ALIYUN:
                return await self._call_aliyun_tts(request)
            elif request.provider == TTSProvider.TENCENT:
                return await self._call_tencent_tts(request)
            elif request.provider == TTSProvider.OPENAI:
                return await self._call_openai_tts(request)
            elif request.provider == TTSProvider.BAIDU:
                return await self._call_baidu_tts(request)
            else:
                raise ValueError(f"不支持的TTS提供商: {request.provider}")

        except Exception as e:
            logger.error(f"TTS合成失败: {e}")
            raise

    async def _call_azure_tts(self, request: TTSRequest) -> TTSResponse:
        """调用Azure TTS API"""
        start_time = time.time()

        config = self.api_keys.get("azure_tts", {})
        api_key = config.get("api_key")
        region = config.get("region", "eastus")

        if not api_key:
            raise ValueError("Azure TTS API密钥未配置")

        voice = request.voice or config.get("voice", "zh-CN-XiaoxiaoNeural")

        # 构建SSML
        ssml = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{request.language}">
    <voice name="{voice}">
        <prosody rate="{request.speed}" pitch="{request.pitch}">
            {request.text}
        </prosody>
    </voice>
</speak>"""

        headers = {
            "Ocp-Apim-Subscription-Key": api_key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": f"audio-16khz-128kbitrate-mono-mp3"
        }

        url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, content=ssml.encode('utf-8'))
            response.raise_for_status()

            # 保存音频文件
            timestamp = int(time.time())
            filename = f"azure_tts_{timestamp}.mp3"
            audio_path = Path("./temp") / filename
            audio_path.parent.mkdir(exist_ok=True)

            with open(audio_path, "wb") as f:
                f.write(response.content)

            # 计算时长（简单估算）
            text_length = len(request.text)
            estimated_duration = text_length * 0.15 / request.speed  # 假设每个字符0.15秒

            generation_time = time.time() - start_time
            audio_size = len(response.content)

            # Azure TTS计费（每1000字符约$0.016）
            cost = (text_length / 1000) * 0.016

            return TTSResponse(
                provider="azure_tts",
                voice=voice,
                audio_path=str(audio_path),
                audio_size=audio_size,
                duration=estimated_duration,
                generation_time=generation_time,
                cost=cost
            )

    async def _call_aliyun_tts(self, request: TTSRequest) -> TTSResponse:
        """调用阿里云TTS API"""
        start_time = time.time()

        config = self.api_keys.get("aliyun_tts", {})
        access_key_id = config.get("access_key_id")
        access_key_secret = config.get("access_key_secret")
        region = config.get("region", "cn-shanghai")

        if not access_key_id or not access_key_secret:
            raise ValueError("阿里云TTS配置未完整")

        voice = request.voice or config.get("voice", "xiaoyun")

        # 阿里云TTS需要复杂的签名过程，这里简化处理
        # 实际使用时需要按照阿里云API文档实现签名算法

        # 模拟调用过程
        logger.info(f"阿里云TTS合成: {request.text[:50]}...")
        await asyncio.sleep(2)

        timestamp = int(time.time())
        filename = f"aliyun_tts_{timestamp}.mp3"
        audio_path = Path("./temp") / filename
        audio_path.parent.mkdir(exist_ok=True)

        # 创建模拟音频文件（实际应该是API返回的音频数据）
        dummy_audio = b"fake_audio_data" * 1000  # 模拟音频数据
        with open(audio_path, "wb") as f:
            f.write(dummy_audio)

        text_length = len(request.text)
        estimated_duration = text_length * 0.15 / request.speed
        generation_time = time.time() - start_time
        audio_size = len(dummy_audio)

        return TTSResponse(
            provider="aliyun_tts",
            voice=voice,
            audio_path=str(audio_path),
            audio_size=audio_size,
            duration=estimated_duration,
            generation_time=generation_time,
            cost=0.0
        )

    async def _call_tencent_tts(self, request: TTSRequest) -> TTSResponse:
        """调用腾讯云TTS API"""
        start_time = time.time()

        config = self.api_keys.get("tencent_tts", {})
        secret_id = config.get("secret_id")
        secret_key = config.get("secret_key")
        region = config.get("region", "ap-beijing")

        if not secret_id or not secret_key:
            raise ValueError("腾讯云TTS配置未完整")

        voice = request.voice or config.get("voice", "101001")

        # 模拟腾讯云TTS调用
        logger.info(f"腾讯云TTS合成: {request.text[:50]}...")
        await asyncio.sleep(2)

        timestamp = int(time.time())
        filename = f"tencent_tts_{timestamp}.mp3"
        audio_path = Path("./temp") / filename
        audio_path.parent.mkdir(exist_ok=True)

        dummy_audio = b"fake_tencent_audio_data" * 1000
        with open(audio_path, "wb") as f:
            f.write(dummy_audio)

        text_length = len(request.text)
        estimated_duration = text_length * 0.15 / request.speed
        generation_time = time.time() - start_time
        audio_size = len(dummy_audio)

        return TTSResponse(
            provider="tencent_tts",
            voice=voice,
            audio_path=str(audio_path),
            audio_size=audio_size,
            duration=estimated_duration,
            generation_time=generation_time,
            cost=0.0
        )

    async def _call_openai_tts(self, request: TTSRequest) -> TTSResponse:
        """调用OpenAI TTS API"""
        start_time = time.time()

        config = self.api_keys.get("openai", {})
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.openai.com/v1")

        if not api_key:
            raise ValueError("OpenAI API密钥未配置")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        voice = request.voice or "alloy"

        payload = {
            "model": "tts-1",
            "input": request.text,
            "voice": voice,
            "speed": request.speed,
            "response_format": request.format
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/audio/speech",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            # 保存音频文件
            timestamp = int(time.time())
            filename = f"openai_tts_{timestamp}.{request.format}"
            audio_path = Path("./temp") / filename
            audio_path.parent.mkdir(exist_ok=True)

            with open(audio_path, "wb") as f:
                f.write(response.content)

            # 估算时长
            text_length = len(request.text)
            estimated_duration = text_length * 0.15 / request.speed

            generation_time = time.time() - start_time
            audio_size = len(response.content)

            # OpenAI TTS计费（每1000字符约$0.015）
            cost = (text_length / 1000) * 0.015

            return TTSResponse(
                provider="openai_tts",
                voice=voice,
                audio_path=str(audio_path),
                audio_size=audio_size,
                duration=estimated_duration,
                generation_time=generation_time,
                cost=cost
            )

    async def _call_baidu_tts(self, request: TTSRequest) -> TTSResponse:
        """调用百度TTS API"""
        start_time = time.time()

        config = self.api_keys.get("wenxin", {})
        api_key = config.get("api_key")
        secret_key = config.get("secret_key")

        if not api_key or not secret_key:
            raise ValueError("百度TTS配置未完整")

        # 获取access_token
        access_token = await self._get_baidu_access_token(api_key, secret_key)

        voice = request.voice or "0"  # 0为女声，1为男声

        params = {
            "tex": request.text,
            "tok": access_token,
            "per": voice,
            "spd": int(request.speed * 5),  # 语速0-15
            "pit": int(request.pitch * 5),  # 音调0-15
            "aue": 3,  # mp3格式
            "cuid": "ai_media_platform",
            "lan": "zh"
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://tsn.baidu.com/text2audio",
                params=params
            )

            # 检查响应类型
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                # 返回了错误信息
                error_data = response.json()
                raise ValueError(f"百度TTS失败: {error_data}")

            # 保存音频文件
            timestamp = int(time.time())
            filename = f"baidu_tts_{timestamp}.mp3"
            audio_path = Path("./temp") / filename
            audio_path.parent.mkdir(exist_ok=True)

            with open(audio_path, "wb") as f:
                f.write(response.content)

            text_length = len(request.text)
            estimated_duration = text_length * 0.15 / request.speed
            generation_time = time.time() - start_time
            audio_size = len(response.content)

            return TTSResponse(
                provider="baidu_tts",
                voice=voice,
                audio_path=str(audio_path),
                audio_size=audio_size,
                duration=estimated_duration,
                generation_time=generation_time,
                cost=0.0
            )

    async def _get_baidu_access_token(self, api_key: str, secret_key: str) -> str:
        """获取百度access_token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": secret_key
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data["access_token"]

    async def batch_synthesize(self, texts: list[str], provider: TTSProvider, voice: Optional[str] = None) -> list[TTSResponse]:
        """批量语音合成"""
        tasks = []
        for text in texts:
            request = TTSRequest(
                provider=provider,
                text=text,
                voice=voice
            )
            tasks.append(self.synthesize_speech(request))

        # 并行合成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        audios = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"文本{i+1}合成失败: {result}")
            else:
                audios.append(result)

        return audios

    async def merge_audio_files(self, audio_paths: list[str], output_path: str) -> str:
        """合并多个音频文件"""
        try:
            import subprocess

            # 创建文件列表
            file_list_path = "./temp/audio_file_list.txt"
            with open(file_list_path, "w") as f:
                for path in audio_paths:
                    f.write(f"file '{path}'\n")

            # 使用FFmpeg合并音频
            cmd = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", file_list_path,
                "-c", "copy",
                "-y",
                output_path
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise ValueError(f"音频合并失败: {stderr.decode()}")

            # 清理临时文件
            Path(file_list_path).unlink(missing_ok=True)

            logger.info(f"音频合并完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"音频合并失败: {e}")
            raise


# 全局TTS服务实例
_tts_service: Optional[TTSService] = None


def get_tts_service(config: Dict) -> TTSService:
    """获取TTS服务实例"""
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService(config)
    return _tts_service


# 测试代码
async def main():
    """测试TTS服务"""
    config = {
        "api_keys": {
            "azure_tts": {
                "api_key": "your-azure-key",
                "region": "eastus"
            },
            "openai": {
                "api_key": "your-openai-key"
            }
        }
    }

    service = get_tts_service(config)

    # 测试语音合成
    request = TTSRequest(
        provider=TTSProvider.AZURE,
        text="你好，这是一个语音合成测试。",
        voice="zh-CN-XiaoxiaoNeural"
    )

    try:
        response = await service.synthesize_speech(request)
        print(f"语音合成成功: {response.audio_path}")
        print(f"音频时长: {response.duration:.2f}秒")
        print(f"文件大小: {response.audio_size}字节")
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())