"""
文本优化API路由
提供多种LLM文本优化功能
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from loguru import logger
import asyncio
import time
from datetime import datetime

# 导入优化的文本服务
try:
    from services.llm.text_optimize_service_optimized import get_text_optimize_service
    TEXT_SERVICE_AVAILABLE = True
    logger.info("优化文本服务导入成功")
except ImportError as e:
    logger.warning(f"优化文本服务导入失败: {e}，使用模拟服务")
    TEXT_SERVICE_AVAILABLE = False

router = APIRouter(prefix="/api/v1/llm", tags=["文本优化"])

# 全局文本服务实例
_text_service = None

def get_text_service_instance():
    """获取文本服务实例"""
    global _text_service
    if _text_service is None and TEXT_SERVICE_AVAILABLE:
        # 这里可以从app.state.config获取配置
        config = {}
        _text_service = get_text_optimize_service(config)
    return _text_service


class TextOptimizeRequest(BaseModel):
    """文本优化请求模型"""
    text: str
    provider: str = "zhipu"  # zhipu, openai, moonshot, doubao, qwen
    mode: str = "creative"   # creative, professional, concise, seo, social
    custom_prompt: Optional[str] = None


class TextOptimizeResponse(BaseModel):
    """文本优化响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


class BatchTextOptimizeRequest(BaseModel):
    """批量文本优化请求模型"""
    texts: List[str]
    provider: str = "zhipu"
    mode: str = "creative"
    custom_prompt: Optional[str] = None


class ProviderTestRequest(BaseModel):
    """提供商测试请求模型"""
    provider: str


@router.post("/optimize-text", response_model=TextOptimizeResponse)
async def optimize_text(request: TextOptimizeRequest):
    """优化文本"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="文本内容不能为空")

        # 优先使用优化服务
        text_service = get_text_service_instance()
        if text_service:
            logger.info(f"使用优化文本服务: provider={request.provider}, mode={request.mode}")
            result = await text_service.optimize_text(
                text=request.text,
                provider=request.provider,
                mode=request.mode,
                custom_prompt=request.custom_prompt
            )

            if result and not result.get("error"):
                return TextOptimizeResponse(
                    success=True,
                    message="文本优化成功",
                    data=result
                )
            else:
                error_msg = result.get("error", "未知错误") if result else "服务不可用"
                return TextOptimizeResponse(
                    success=False,
                    message=f"文本优化失败: {error_msg}",
                    data=result
                )
        else:
            # 回退到模拟服务
            logger.info("使用模拟文本优化服务")
            await asyncio.sleep(1)  # 模拟处理时间

            optimized_text = f"[{request.provider.upper()}优化] {request.text}，增强表现力，更加生动有趣。"

            result = {
                "original_text": request.text,
                "optimized_text": optimized_text,
                "provider": request.provider,
                "provider_name": request.provider.upper(),
                "mode": request.mode,
                "mode_name": f"{request.mode}优化",
                "generation_time": 1.0,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "text_length": {
                    "original": len(request.text),
                    "optimized": len(optimized_text),
                    "ratio": len(optimized_text) / len(request.text) if request.text else 0
                }
            }

            return TextOptimizeResponse(
                success=True,
                message="文本优化完成（模拟）",
                data=result
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文本优化API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-optimize")
async def batch_optimize_text(request: BatchTextOptimizeRequest):
    """批量优化文本"""
    try:
        if not request.texts:
            raise HTTPException(status_code=400, detail="文本列表不能为空")

        if len(request.texts) > 10:
            raise HTTPException(status_code=400, detail="一次最多批量处理10个文本")

        text_service = get_text_service_instance()
        results = []

        for i, text in enumerate(request.texts):
            logger.info(f"批量优化进度: {i+1}/{len(request.texts)}")

            try:
                if text_service:
                    result = await text_service.optimize_text(
                        text=text,
                        provider=request.provider,
                        mode=request.mode,
                        custom_prompt=request.custom_prompt
                    )
                else:
                    # 模拟服务
                    await asyncio.sleep(0.5)
                    result = {
                        "original_text": text,
                        "optimized_text": f"[批量优化] {text}，增强表现力。",
                        "provider": request.provider,
                        "mode": request.mode,
                        "generation_time": 0.5,
                        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }

                results.append({
                    "index": i + 1,
                    "status": "success" if not result.get("error") else "error",
                    "data": result
                })

            except Exception as e:
                logger.error(f"批量优化失败 {i+1}: {e}")
                results.append({
                    "index": i + 1,
                    "status": "error",
                    "error": str(e)
                })

        success_count = sum(1 for r in results if r.get("status") == "success")

        return {
            "success": True,
            "message": f"批量优化完成，成功 {success_count}/{len(request.texts)} 个",
            "data": {
                "results": results,
                "summary": {
                    "total": len(request.texts),
                    "success": success_count,
                    "failed": len(request.texts) - success_count
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量文本优化API错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_llm_providers():
    """获取可用的LLM提供商列表"""
    try:
        text_service = get_text_service_instance()

        if text_service:
            providers = text_service.get_available_providers()
        else:
            # 模拟提供商列表
            providers = [
                {"id": "zhipu", "name": "智谱GLM-4", "available": True, "model": "glm-4"},
                {"id": "openai", "name": "OpenAI GPT-4", "available": False, "model": "gpt-4"},
                {"id": "moonshot", "name": "Moonshot Kimi", "available": True, "model": "moonshot-v1-8k"},
                {"id": "doubao", "name": "字节豆包", "available": True, "model": "doubao-pro-32k"},
                {"id": "qwen", "name": "通义千问", "available": True, "model": "qwen-turbo"}
            ]

        return {
            "success": True,
            "data": {
                "providers": providers
            }
        }

    except Exception as e:
        logger.error(f"获取LLM提供商列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimization-modes")
async def get_optimization_modes():
    """获取文本优化模式列表"""
    try:
        text_service = get_text_service_instance()

        if text_service:
            modes = text_service.get_optimization_modes()
        else:
            # 模拟优化模式列表
            modes = [
                {"id": "creative", "name": "创意优化", "description": "增强创意和表现力，适合内容创作"},
                {"id": "professional", "name": "专业优化", "description": "提升专业性和准确性，适合正式场合"},
                {"id": "concise", "name": "简洁优化", "description": "精简内容，突出重点，提高可读性"},
                {"id": "seo", "name": "SEO优化", "description": "优化搜索引擎排名，增加关键词密度"},
                {"id": "social", "name": "社交优化", "description": "优化社交媒体表达，增加互动性"}
            ]

        return {
            "success": True,
            "data": {
                "modes": modes
            }
        }

    except Exception as e:
        logger.error(f"获取优化模式列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-provider")
async def test_provider(request: ProviderTestRequest):
    """测试LLM提供商连接"""
    try:
        text_service = get_text_service_instance()

        if text_service:
            result = await text_service.test_provider(request.provider)
            return result
        else:
            # 模拟测试结果
            await asyncio.sleep(1)
            return {
                "success": request.provider in ["zhipu", "moonshot", "doubao", "qwen"],
                "message": f"{request.provider} 连接测试完成（模拟）",
                "provider": request.provider,
                "provider_name": request.provider.upper()
            }

    except Exception as e:
        logger.error(f"测试LLM提供商失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def text_optimize_health():
    """文本优化服务健康检查"""
    try:
        text_service = get_text_service_instance()

        service_status = {
            "status": "healthy",
            "service": "text_optimize",
            "timestamp": datetime.now().isoformat(),
            "optimized_service_available": TEXT_SERVICE_AVAILABLE,
            "supported_providers": ["zhipu", "openai", "moonshot", "doubao", "qwen"],
            "supported_modes": ["creative", "professional", "concise", "seo", "social"],
            "features": ["single_optimize", "batch_optimize", "provider_test", "multiple_modes"]
        }

        if text_service:
            providers = text_service.get_available_providers()
            service_status["available_providers"] = [p for p in providers if p["available"]]
        else:
            service_status["available_providers"] = []

        return service_status

    except Exception as e:
        logger.error(f"文本优化健康检查失败: {e}")
        return {
            "status": "unhealthy",
            "service": "text_optimize",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }