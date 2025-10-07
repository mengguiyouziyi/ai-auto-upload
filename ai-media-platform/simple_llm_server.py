#!/usr/bin/env python3
"""
简化的LLM服务器，只包含文本优化功能
"""

import asyncio
import json
import time
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

app = FastAPI(title="简化LLM API服务器")

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175", "http://localhost:5174", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextOptimizeRequest(BaseModel):
    text: str
    provider: str = "glm"

class TextOptimizeResponse(BaseModel):
    optimized_text: str
    provider: str
    response_time: int

@app.get("/")
async def root():
    return {"message": "简化LLM API服务器运行中"}

@app.post("/api/v1/llm/optimize-text", response_model=TextOptimizeResponse)
async def optimize_text(request: TextOptimizeRequest):
    """文本优化API"""
    start_time = time.time()

    print(f"收到文本优化请求: provider={request.provider}, text_length={len(request.text)}")

    try:
        # 导入LLM服务
        from services.llm.llm_service import get_llm_service, LLMProvider
        import yaml

        # 加载配置
        config_path = Path("config/config.yaml")
        if not config_path.exists():
            print("配置文件不存在，使用默认配置")
            config = {}
        else:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

        # 初始化LLM服务
        llm_service = get_llm_service(config)

        # 确定provider
        provider_map = {
            "glm": LLMProvider.GLM,
            "doubao": LLMProvider.DOUBAO,
            "kimi": LLMProvider.KIMI,
            "qwen": LLMProvider.QWEN
        }

        llm_provider = provider_map.get(request.provider, LLMProvider.GLM)

        # 调用LLM服务
        result = await llm_service.optimize_text_for_video(request.text, llm_provider)

        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)

        print(f"优化成功: provider={request.provider}, result_length={len(result)}, response_time={response_time}ms")

        return TextOptimizeResponse(
            optimized_text=result,
            provider=request.provider,
            response_time=response_time
        )

    except Exception as e:
        end_time = time.time()
        response_time = int((end_time - start_time) * 1000)

        error_msg = str(e)
        print(f"优化失败: {error_msg}")

        # 如果是429错误，尝试降级到豆包
        if "429" in error_msg or "Too Many Requests" in error_msg:
            print("GLM API速率限制，尝试降级到豆包...")
            try:
                from services.llm.llm_service import get_llm_service, LLMProvider
                import yaml

                config_path = Path("config/config.yaml")
                if config_path.exists():
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = yaml.safe_load(f)

                llm_service = get_llm_service(config)
                result = await llm_service.optimize_text_for_video(request.text, LLMProvider.DOUBAO)

                print(f"豆包降级成功: result_length={len(result)}")

                return TextOptimizeResponse(
                    optimized_text=result,
                    provider="doubao (fallback)",
                    response_time=response_time
                )
            except Exception as fallback_error:
                print(f"豆包降级也失败: {fallback_error}")

        # 如果所有尝试都失败，返回规则优化结果
        simple_result = f"[优化版本] {request.text[:100]}{'...' if len(request.text) > 100 else ''}"
        print("使用规则优化作为最后备选方案")

        return TextOptimizeResponse(
            optimized_text=simple_result,
            provider="rule-based fallback",
            response_time=response_time
        )

@app.get("/api/v1/llm/providers")
async def get_providers():
    """获取可用的LLM提供商列表"""
    return {
        "providers": [
            {"id": "glm", "name": "GLM-4.6", "status": "available"},
            {"id": "doubao", "name": "豆包", "status": "available"},
            {"id": "kimi", "name": "Kimi", "status": "available"},
            {"id": "qwen", "name": "通义千问", "status": "available"}
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "simple-llm-server"}

if __name__ == "__main__":
    print("启动简化LLM服务器...")
    print("服务器地址: http://localhost:9000")
    print("API文档: http://localhost:9000/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=9000,
        log_level="info"
    )