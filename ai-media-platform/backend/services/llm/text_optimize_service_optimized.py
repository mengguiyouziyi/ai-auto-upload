"""
文本优化服务 - 集成真实LLM API
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import re


class TextOptimizeService:
    """文本优化服务类 - 集成多种LLM API"""

    def __init__(self, config: Dict = None):
        """初始化文本优化服务"""
        self.config = config or {}
        self.api_keys = self.config.get("llm_apis", {})

        # 支持的LLM提供商配置
        self.providers = {
            "openai": {
                "name": "OpenAI GPT-4",
                "available": bool(self.api_keys.get("openai")),
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4-turbo-preview",
                "max_tokens": 4000,
                "temperature": 0.7
            },
            "zhipu": {
                "name": "智谱GLM-4",
                "available": bool(self.api_keys.get("zhipu")),
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
                "model": "glm-4",
                "max_tokens": 4000,
                "temperature": 0.7
            },
            "moonshot": {
                "name": "Moonshot Kimi",
                "available": bool(self.api_keys.get("moonshot")),
                "base_url": "https://api.moonshot.cn/v1",
                "model": "moonshot-v1-8k",
                "max_tokens": 4000,
                "temperature": 0.7
            },
            "doubao": {
                "name": "字节豆包",
                "available": bool(self.api_keys.get("doubao")),
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "model": "doubao-pro-32k",
                "max_tokens": 4000,
                "temperature": 0.7
            },
            "qwen": {
                "name": "通义千问",
                "available": bool(self.api_keys.get("qwen")),
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "model": "qwen-turbo",
                "max_tokens": 4000,
                "temperature": 0.7
            }
        }

        # 文本优化模式
        self.optimization_modes = {
            "creative": {
                "name": "创意优化",
                "description": "增强创意和表现力，适合内容创作",
                "prompt_template": """请对以下文本进行创意优化，使其更加生动有趣，适合内容创作：

原文：{original_text}

要求：
1. 保持原意不变，但增强表现力
2. 使用更生动的词汇和表达方式
3. 适合社交媒体发布
4. 控制在相近的字数范围内
5. 保持语言流畅自然

优化后的文本："""
            },
            "professional": {
                "name": "专业优化",
                "description": "提升专业性和准确性，适合正式场合",
                "prompt_template": """请对以下文本进行专业优化，使其更加准确和专业：

原文：{original_text}

要求：
1. 使用更专业的术语和表达
2. 确保信息的准确性和权威性
3. 逻辑清晰，条理分明
4. 适合专业领域交流
5. 保持客观中性的语调

优化后的文本："""
            },
            "concise": {
                "name": "简洁优化",
                "description": "精简内容，突出重点，提高可读性",
                "prompt_template": """请对以下文本进行简洁优化，使其更加精炼和易读：

原文：{original_text}

要求：
1. 删除冗余信息，保留核心内容
2. 使用简洁明了的语言
3. 突出重点，条理清晰
4. 提高可读性和理解度
5. 控制字数在原文的70%以内

优化后的文本："""
            },
            "seo": {
                "name": "SEO优化",
                "description": "优化搜索引擎排名，增加关键词密度",
                "prompt_template": """请对以下文本进行SEO优化，提升搜索引擎排名：

原文：{original_text}

要求：
1. 合理添加相关关键词
2. 优化标题和描述
3. 提高内容的可读性和价值
4. 保持自然流畅，避免关键词堆砌
5. 适合搜索引擎收录

优化后的文本："""
            },
            "social": {
                "name": "社交优化",
                "description": "优化社交媒体表达，增加互动性",
                "prompt_template": """请对以下文本进行社交媒体优化，增加互动性和传播力：

原文：{original_text}

要求：
1. 使用更贴近社交媒体的表达方式
2. 增加互动元素和话题标签
3. 提高内容的吸引力和分享价值
4. 适合在微博、抖音等平台发布
5. 语言活泼有趣，贴近用户

优化后的文本："""
            }
        }

        print("🤖 文本优化服务初始化完成")
        print(f"   可用LLM: {[p['name'] for p in self.providers.values() if p['available']]}")

    async def optimize_text(self, text: str, provider: str = "zhipu", mode: str = "creative",
                          custom_prompt: str = None) -> Dict[str, Any]:
        """优化文本"""
        print(f"🎯 开始文本优化:")
        print(f"   提供商: {provider}")
        print(f"   优化模式: {mode}")
        print(f"   原文长度: {len(text)}字")
        print(f"   原文内容: {text[:50]}...")

        # 验证参数
        if not text.strip():
            return self._create_error_response("文本内容不能为空")

        if provider not in self.providers:
            return self._create_error_response(f"不支持的LLM提供商: {provider}")

        if not self.providers[provider]["available"]:
            return self._create_error_response(f"LLM提供商 {provider} 不可用，请检查API密钥配置")

        if mode not in self.optimization_modes and custom_prompt is None:
            return self._create_error_response(f"不支持的优化模式: {mode}")

        try:
            # 构建提示词
            if custom_prompt:
                prompt = custom_prompt.replace("{original_text}", text)
            else:
                mode_config = self.optimization_modes[mode]
                prompt = mode_config["prompt_template"].replace("{original_text}", text)

            # 调用LLM API
            start_time = time.time()
            optimized_text = await self._call_llm_api(provider, prompt)
            generation_time = time.time() - start_time

            if optimized_text:
                print(f"✅ 文本优化完成:")
                print(f"   优化后长度: {len(optimized_text)}字")
                print(f"   耗时: {generation_time:.2f}秒")
                print(f"   优化后内容: {optimized_text[:50]}...")

                return {
                    "original_text": text,
                    "optimized_text": optimized_text,
                    "provider": provider,
                    "provider_name": self.providers[provider]["name"],
                    "mode": mode,
                    "mode_name": self.optimization_modes.get(mode, {}).get("name", mode),
                    "generation_time": generation_time,
                    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "text_length": {
                        "original": len(text),
                        "optimized": len(optimized_text),
                        "ratio": len(optimized_text) / len(text) if text else 0
                    }
                }
            else:
                return self._create_error_response("LLM API调用失败")

        except Exception as e:
            print(f"❌ 文本优化失败: {str(e)}")
            return self._create_error_response(f"优化失败: {str(e)}")

    async def _call_llm_api(self, provider: str, prompt: str) -> Optional[str]:
        """调用LLM API"""
        provider_config = self.providers[provider]
        api_key = self.api_keys.get(provider)

        if not api_key:
            print(f"❌ 缺少 {provider} 的API密钥")
            return None

        try:
            if provider == "openai":
                return await self._call_openai_api(prompt, provider_config, api_key)
            elif provider == "zhipu":
                return await self._call_zhipu_api(prompt, provider_config, api_key)
            elif provider == "moonshot":
                return await self._call_moonshot_api(prompt, provider_config, api_key)
            elif provider == "doubao":
                return await self._call_doubao_api(prompt, provider_config, api_key)
            elif provider == "qwen":
                return await self._call_qwen_api(prompt, provider_config, api_key)
            else:
                print(f"❌ 不支持的LLM提供商: {provider}")
                return None

        except Exception as e:
            print(f"❌ LLM API调用异常: {str(e)}")
            return None

    async def _call_openai_api(self, prompt: str, config: Dict, api_key: str) -> Optional[str]:
        """调用OpenAI API"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": "你是一个专业的文本优化专家，擅长提升文本质量和表现力。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"]
        }

        return await self._make_http_request(config["base_url"] + "/chat/completions", headers, data)

    async def _call_zhipu_api(self, prompt: str, config: Dict, api_key: str) -> Optional[str]:
        """调用智谱AI API"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": "你是一个专业的文本优化专家，擅长提升文本质量和表现力。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"]
        }

        return await self._make_http_request(config["base_url"] + "/chat/completions", headers, data)

    async def _call_moonshot_api(self, prompt: str, config: Dict, api_key: str) -> Optional[str]:
        """调用Moonshot API"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": "你是一个专业的文本优化专家，擅长提升文本质量和表现力。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"]
        }

        return await self._make_http_request(config["base_url"] + "/chat/completions", headers, data)

    async def _call_doubao_api(self, prompt: str, config: Dict, api_key: str) -> Optional[str]:
        """调用豆包API"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": config["model"],
            "messages": [
                {"role": "system", "content": "你是一个专业的文本优化专家，擅长提升文本质量和表现力。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": config["max_tokens"],
            "temperature": config["temperature"]
        }

        return await self._make_http_request(config["base_url"] + "/chat/completions", headers, data)

    async def _call_qwen_api(self, prompt: str, config: Dict, api_key: str) -> Optional[str]:
        """调用通义千问API"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": config["model"],
            "input": {
                "messages": [
                    {"role": "system", "content": "你是一个专业的文本优化专家，擅长提升文本质量和表现力。"},
                    {"role": "user", "content": prompt}
                ]
            },
            "parameters": {
                "max_tokens": config["max_tokens"],
                "temperature": config["temperature"]
            }
        }

        return await self._make_http_request(config["base_url"] + "/services/aigc/text-generation/generation", headers, data)

    async def _make_http_request(self, url: str, headers: Dict, data: Dict, timeout: int = 30) -> Optional[str]:
        """发送HTTP请求"""
        try:
            timeout_obj = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_obj) as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._extract_text_from_response(result)
                    else:
                        error_text = await response.text()
                        print(f"❌ API请求失败: {response.status} - {error_text}")
                        return None

        except asyncio.TimeoutError:
            print(f"❌ API请求超时")
            return None
        except Exception as e:
            print(f"❌ API请求异常: {str(e)}")
            return None

    def _extract_text_from_response(self, response: Dict) -> Optional[str]:
        """从API响应中提取文本"""
        try:
            # OpenAI格式
            if "choices" in response:
                return response["choices"][0]["message"]["content"]
            # 通义千问格式
            elif "output" in response and "text" in response["output"]:
                return response["output"]["text"]
            # 其他格式
            elif "text" in response:
                return response["text"]
            elif "content" in response:
                return response["content"]
            else:
                print(f"❌ 无法解析API响应格式: {response}")
                return None

        except Exception as e:
            print(f"❌ 提取响应文本失败: {str(e)}")
            return None

    def _create_error_response(self, error_msg: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "error": error_msg,
            "original_text": "",
            "optimized_text": "",
            "provider": "",
            "mode": "",
            "generation_time": 0,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    async def batch_optimize(self, texts: List[str], **kwargs) -> List[Dict[str, Any]]:
        """批量优化文本"""
        results = []

        for i, text in enumerate(texts):
            print(f"🔄 批量优化进度: {i+1}/{len(texts)}")

            try:
                result = await self.optimize_text(text, **kwargs)
                results.append({
                    "index": i + 1,
                    "status": "success" if not result.get("error") else "error",
                    "data": result
                })
            except Exception as e:
                results.append({
                    "index": i + 1,
                    "status": "error",
                    "error": str(e)
                })

        return results

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """获取可用的LLM提供商"""
        return [
            {
                "id": provider_id,
                "name": config["name"],
                "available": config["available"],
                "model": config["model"]
            }
            for provider_id, config in self.providers.items()
        ]

    def get_optimization_modes(self) -> List[Dict[str, Any]]:
        """获取优化模式"""
        return [
            {
                "id": mode_id,
                "name": config["name"],
                "description": config["description"]
            }
            for mode_id, config in self.optimization_modes.items()
        ]

    async def test_provider(self, provider: str) -> Dict[str, Any]:
        """测试LLM提供商连接"""
        if provider not in self.providers:
            return {
                "success": False,
                "message": f"不支持的提供商: {provider}"
            }

        if not self.providers[provider]["available"]:
            return {
                "success": False,
                "message": f"提供商 {provider} 不可用，请检查API密钥"
            }

        try:
            test_text = "这是一个测试文本。"
            result = await self.optimize_text(test_text, provider=provider, mode="creative")

            if result and not result.get("error"):
                return {
                    "success": True,
                    "message": f"{provider} 连接测试成功",
                    "provider": provider,
                    "provider_name": self.providers[provider]["name"],
                    "test_result": result
                }
            else:
                return {
                    "success": False,
                    "message": f"{provider} 连接测试失败",
                    "error": result.get("error", "未知错误")
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"{provider} 连接测试异常",
                "error": str(e)
            }


def get_text_optimize_service(config: Dict = None) -> TextOptimizeService:
    """获取文本优化服务实例"""
    return TextOptimizeService(config)