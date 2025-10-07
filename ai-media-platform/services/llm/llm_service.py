"""
LLM服务模块 - 集成多种大语言模型API
支持豆包、文心一言、OpenAI、通义千问等
"""

import asyncio
import json
from typing import Dict, List, Optional, Union
from enum import Enum
import httpx
from pydantic import BaseModel
from loguru import logger


class LLMProvider(str, Enum):
    """支持的LLM提供商"""
    OPENAI = "openai"
    DOUBAO = "doubao"
    WENXIN = "wenxin"
    QWEN = "qwen"
    GLM = "glm"
    KIMI = "kimi"


class Message(BaseModel):
    """聊天消息模型"""
    role: str  # system, user, assistant
    content: str


class LLMRequest(BaseModel):
    """LLM请求模型"""
    provider: LLMProvider
    messages: List[Message]
    model: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    stream: bool = False


class LLMResponse(BaseModel):
    """LLM响应模型"""
    provider: str
    model: str
    content: str
    usage: Optional[Dict] = None
    response_time: float


class LLMService:
    """LLM服务主类"""

    def __init__(self, config: Dict):
        self.config = config
        self.api_keys = config.get("api_keys", {})
        self.models_config = config.get("models", {}).get("llm", {})

    async def generate_text(self, request: LLMRequest) -> LLMResponse:
        """生成文本"""
        try:
            if request.provider == LLMProvider.OPENAI:
                return await self._call_openai(request)
            elif request.provider == LLMProvider.DOUBAO:
                return await self._call_doubao(request)
            elif request.provider == LLMProvider.WENXIN:
                return await self._call_wenxin(request)
            elif request.provider == LLMProvider.QWEN:
                return await self._call_qwen(request)
            elif request.provider == LLMProvider.GLM:
                return await self._call_glm(request)
            elif request.provider == LLMProvider.KIMI:
                return await self._call_kimi(request)
            else:
                raise ValueError(f"不支持的LLM提供商: {request.provider}")

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            raise

    async def _call_openai(self, request: LLMRequest) -> LLMResponse:
        """调用OpenAI API"""
        import time
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

        model = request.model or "gpt-3.5-turbo"

        payload = {
            "model": model,
            "messages": [msg.dict() for msg in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")

            response_time = time.time() - start_time

            return LLMResponse(
                provider="openai",
                model=model,
                content=content,
                usage=usage,
                response_time=response_time
            )

    async def _call_doubao(self, request: LLMRequest) -> LLMResponse:
        """调用豆包API"""
        import time
        start_time = time.time()

        config = self.api_keys.get("doubao", {})
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")

        if not api_key:
            raise ValueError("豆包API密钥未配置")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        model = request.model or config.get("model", "doubao-pro-32k")

        payload = {
            "model": model,
            "messages": [msg.dict() for msg in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")

            response_time = time.time() - start_time

            return LLMResponse(
                provider="doubao",
                model=model,
                content=content,
                usage=usage,
                response_time=response_time
            )

    async def _call_wenxin(self, request: LLMRequest) -> LLMResponse:
        """调用文心一言API"""
        import time
        import hashlib
        import urllib.parse
        start_time = time.time()

        config = self.api_keys.get("wenxin", {})
        api_key = config.get("api_key")
        secret_key = config.get("secret_key")
        base_url = config.get("base_url", "https://aip.baidubce.com")

        if not api_key or not secret_key:
            raise ValueError("文心一言API密钥未配置")

        # 获取access_token
        access_token = await self._get_wenxin_access_token(api_key, secret_key)

        model = request.model or "ERNIE-4.0-8K"

        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "messages": [msg.dict() for msg in request.messages],
            "max_output_tokens": request.max_tokens,
            "temperature": request.temperature,
            "disable_search": False,
            "enable_citation": False
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions?access_token={access_token}",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            content = data.get("result", "")
            usage = data.get("usage")

            response_time = time.time() - start_time

            return LLMResponse(
                provider="wenxin",
                model=model,
                content=content,
                usage=usage,
                response_time=response_time
            )

    async def _get_wenxin_access_token(self, api_key: str, secret_key: str) -> str:
        """获取文心一言access_token"""
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

    async def _call_qwen(self, request: LLMRequest) -> LLMResponse:
        """调用通义千问API"""
        import time
        start_time = time.time()

        config = self.api_keys.get("qwen", {})
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://dashscope.aliyuncs.com/api/v1")

        if not api_key:
            raise ValueError("通义千问API密钥未配置")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        model = request.model or config.get("model", "qwen-turbo")

        payload = {
            "model": model,
            "input": {
                "messages": [msg.dict() for msg in request.messages]
            },
            "parameters": {
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            }
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/services/aigc/text-generation/generation",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            content = data["output"]["text"]
            usage = data.get("usage")

            response_time = time.time() - start_time

            return LLMResponse(
                provider="qwen",
                model=model,
                content=content,
                usage=usage,
                response_time=response_time
            )

    async def _call_glm(self, request: LLMRequest) -> LLMResponse:
        """调用GLM API (支持Anthropic兼容格式)"""
        import time
        start_time = time.time()

        config = self.api_keys.get("glm", {})
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://open.bigmodel.cn/api/anthropic")
        api_format = config.get("api_format", "anthropic")  # 默认使用Anthropic格式

        if not api_key:
            raise ValueError("GLM API密钥未配置")

        if api_format == "anthropic":
            return await self._call_glm_anthropic(request, config, start_time)
        else:
            return await self._call_glm_legacy(request, config, start_time)

    async def _call_glm_anthropic(self, request: LLMRequest, config: dict, start_time: float) -> LLMResponse:
        """调用GLM Anthropic兼容格式API"""
        import time
        import asyncio

        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://open.bigmodel.cn/api/anthropic")

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        model = request.model or config.get("model", "glm-4.6")

        # 转换消息格式为Anthropic格式
        messages = []
        for msg in request.messages:
            if msg.role == "system":
                # Anthropic API中system消息需要单独处理
                continue
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 添加system消息（如果有）
        system_message = None
        for msg in request.messages:
            if msg.role == "system":
                system_message = msg.content
                break

        payload = {
            "model": model,
            "max_tokens": request.max_tokens,
            "messages": messages,
            "temperature": request.temperature
        }

        if system_message:
            payload["system"] = system_message

        # 实现重试机制，解决429错误
        max_retries = 3
        retry_delays = [2, 4, 8]  # 指数退避

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.post(
                        f"{base_url}/v1/messages",
                        headers=headers,
                        json=payload
                    )

                    # 如果成功，返回结果
                    if response.status_code == 200:
                        data = response.json()
                        content = data["content"][0]["text"]
                        usage = data.get("usage", {})
                        response_time = time.time() - start_time

                        return LLMResponse(
                            provider="glm",
                            model=data.get("model", model),
                            content=content,
                            usage=usage,
                            response_time=response_time
                        )

                    # 处理429错误（速率限制）
                    elif response.status_code == 429:
                        if attempt < max_retries - 1:
                            logger.warning(f"GLM API速率限制，等待{retry_delays[attempt]}秒后重试 (尝试 {attempt + 1}/{max_retries})")
                            await asyncio.sleep(retry_delays[attempt])
                            continue
                        else:
                            raise Exception(f"GLM API速率限制，已重试{max_retries}次，请稍后再试")

                    # 其他HTTP错误
                    else:
                        error_text = response.text
                        raise Exception(f"GLM API请求失败: HTTP {response.status_code} - {error_text}")

            except httpx.RequestError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"GLM API网络错误，等待{retry_delays[attempt]}秒后重试: {e}")
                    await asyncio.sleep(retry_delays[attempt])
                    continue
                else:
                    raise Exception(f"GLM API网络错误，已重试{max_retries}次: {e}")

        # 这里不应该到达，但为了安全起见
        raise Exception("GLM API调用失败")

    async def _call_glm_legacy(self, request: LLMRequest, config: dict, start_time: float) -> LLMResponse:
        """调用GLM传统格式API (备用)"""
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://open.bigmodel.cn/api/paas/v4")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        model = request.model or config.get("model", "glm-4v-plus")
        payload = {
            "model": model,
            "messages": [msg.dict() for msg in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")
            response_time = time.time() - start_time

            return LLMResponse(
                provider="glm",
                model=model,
                content=content,
                usage=usage,
                response_time=response_time
            )

    async def _call_kimi(self, request: LLMRequest) -> LLMResponse:
        """调用Kimi API"""
        import time
        start_time = time.time()

        config = self.api_keys.get("kimi", {})
        api_key = config.get("api_key")
        base_url = config.get("base_url", "https://api.moonshot.cn/v1")

        if not api_key:
            raise ValueError("Kimi API密钥未配置")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        model = request.model or config.get("model", "moonshot-v1-8k")

        payload = {
            "model": model,
            "messages": [msg.dict() for msg in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": request.stream
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage")

            response_time = time.time() - start_time

            return LLMResponse(
                provider="kimi",
                model=model,
                content=content,
                usage=usage,
                response_time=response_time
            )

    async def optimize_text_for_video(self, text: str, provider: LLMProvider = LLMProvider.GLM) -> str:
        """优化文本以适合视频生成（专门为文生视频模型优化）"""
        system_prompt = """你是一个专业的视频脚本优化师，专门为AI文生视频模型优化文案。请将用户提供的文本内容改写为最适合AI视频生成的描述性prompt。

核心要求：
1. 转换为视觉导向的描述：重点描述画面内容、场景、动作、色彩、构图等视觉元素
2. 使用电影化的语言：包含镜头运动、画面转场、视觉特效等描述
3. 添加情感和氛围描述：如温馨、科技感、神秘、活力等
4. 保持简洁但信息丰富：每个场景描述控制在100字以内
5. 使用视频生成模型友好的关键词：如"高清"、"细节丰富"、"电影级光效"等

格式要求：
- 每个场景用【场景X：视觉风格】开头
- 然后是具体的画面描述
- 包含主体、环境、动作、色彩、光影、镜头等元素

示例格式：
【场景1：赛博朋克风格】雨夜的街道，霓虹灯反射在湿漉漉的地面上，全息广告牌闪烁着蓝紫光芒，身穿黑色风衣的主角走向镜头，特写镜头展现坚定的眼神，电影级光效，细节丰富，4K高清

【场景2：温馨室内】阳光透过落地窗洒进客厅，木质地板上斑驳的光影，猫咪在沙发上打盹，温暖的色调，柔焦效果，宁静舒适的氛围"""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"请将以下文本优化为AI视频生成的视觉描述脚本：\n\n{text}")
        ]

        request = LLMRequest(
            provider=provider,
            messages=messages,
            temperature=0.7,
            max_tokens=4000
        )

        # 尝试使用指定的provider，失败时自动切换到备用选项
        try:
            response = await self.generate_text(request)
            logger.info(f"使用 {provider.value} 成功优化文本")
            return response.content
        except Exception as e:
            logger.warning(f"使用 {provider.value} 优化文本失败: {e}")

            # 定义备用provider列表（优先使用可用的免费服务）
            fallback_providers = []

            # 如果当前是GLM，优先尝试豆包（通常比较稳定）
            if provider == LLMProvider.GLM:
                if self.api_keys.get("doubao", {}).get("api_key"):
                    fallback_providers.append(LLMProvider.DOUBAO)
                if self.api_keys.get("kimi", {}).get("api_key"):
                    fallback_providers.append(LLMProvider.KIMI)
                if self.api_keys.get("qwen", {}).get("api_key"):
                    fallback_providers.append(LLMProvider.QWEN)
            # 如果当前是其他provider，尝试GLM
            elif provider != LLMProvider.GLM and self.api_keys.get("glm", {}).get("api_key"):
                fallback_providers.append(LLMProvider.GLM)
                if self.api_keys.get("doubao", {}).get("api_key"):
                    fallback_providers.append(LLMProvider.DOUBAO)

            # 尝试所有备用providers
            for fallback_provider in fallback_providers:
                try:
                    logger.info(f"尝试使用备用provider: {fallback_provider.value}")
                    fallback_request = LLMRequest(
                        provider=fallback_provider,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=4000
                    )
                    response = await self.generate_text(fallback_request)
                    logger.info(f"使用备用provider {fallback_provider.value} 成功优化文本")
                    return response.content
                except Exception as fallback_error:
                    logger.warning(f"备用provider {fallback_provider.value} 也失败了: {fallback_error}")
                    continue

            # 所有provider都失败了，返回一个简化的优化版本
            logger.error("所有LLM provider都失败了，返回简化版本文本优化")
            return self._simple_text_optimization(text)

    def _simple_text_optimization(self, text: str) -> str:
        """简单的文本优化（当所有LLM provider都失败时的备用方案）"""
        # 提取关键信息并格式化为视频脚本
        sentences = text.split('。')
        script_parts = []

        for i, sentence in enumerate(sentences[:5], 1):  # 最多处理5句话
            sentence = sentence.strip()
            if not sentence:
                continue

            # 简单的场景描述生成
            if i == 1:
                script_parts.append(f"【场景1：开场介绍】{sentence}，清晰明了的表达，专业的视觉效果")
            elif i == 2:
                script_parts.append(f"【场景2：详细说明】{sentence}，配合图示和动画效果")
            elif i == 3:
                script_parts.append(f"【场景3：实例展示】{sentence}，实际应用场景演示")
            elif i == 4:
                script_parts.append(f"【场景4：总结归纳】{sentence}，重点突出，条理清晰")
            else:
                script_parts.append(f"【场景{i}：补充说明】{sentence}，简洁明了的结尾")

        return '\n\n'.join(script_parts) if script_parts else text

    async def generate_video_script(self, topic: str, duration: int = 300, provider: LLMProvider = LLMProvider.DOUBAO) -> str:
        """生成视频脚本"""
        system_prompt = f"""你是一个专业的视频脚本编剧。请为指定主题生成一个{duration}秒的视频脚本。

要求：
1. 脚本时长约{duration}秒（按每分钟150-180字计算）
2. 包含开场、主体、结尾三个部分
3. 每个场景都要有明确的画面描述和配音内容
4. 语言要生动有趣，适合视频呈现
5. 输出格式：使用【场景X：画面描述】配音内容的格式

示例：
【场景1：展示科技感的开场动画】人工智能，这个曾经只存在于科幻电影中的概念...
【场景2：展示AI在工作中的应用场景】如今，它已经深入到我们工作的方方面面..."""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"请为以下主题生成视频脚本：{topic}")
        ]

        request = LLMRequest(
            provider=provider,
            messages=messages,
            temperature=0.8,
            max_tokens=4000
        )

        response = await self.generate_text(request)
        return response.content


# 全局LLM服务实例
_llm_service: Optional[LLMService] = None


def get_llm_service(config: Dict) -> LLMService:
    """获取LLM服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(config)
    return _llm_service


# 测试代码
async def main():
    """测试LLM服务"""
    config = {
        "api_keys": {
            "openai": {
                "api_key": "your-openai-key"
            },
            "doubao": {
                "api_key": "your-doubao-key"
            }
        }
    }

    service = get_llm_service(config)

    # 测试文本优化
    text = """
    人工智能（AI）是计算机科学的一个分支，它致力于创建能够执行通常需要人类智能的任务的系统。
    这些任务包括学习、推理、问题解决、感知和语言理解。AI技术在近年来发展迅速，
    已经在医疗、金融、交通、教育等多个领域得到广泛应用。
    """

    try:
        optimized = await service.optimize_text_for_video(text, LLMProvider.OPENAI)
        print("优化后的视频文案：")
        print(optimized)
    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())