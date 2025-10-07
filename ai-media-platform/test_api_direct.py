#!/usr/bin/env python3
"""
直接测试GLM-4.6 API调用
"""

import asyncio
import json
import time
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_glm_api():
    """直接测试GLM API"""
    print("🚀 直接测试GLM-4.6 API调用...")

    # 导入LLM服务
    from services.llm.llm_service import get_llm_service, LLMProvider

    # 加载配置
    import yaml
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("❌ 配置文件不存在")
        return False

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    print("✅ 配置文件加载成功")

    # 初始化LLM服务
    llm_service = get_llm_service(config)

    # 测试文本
    test_text = """在AI编程工具竞争白热化的当下，OpenAI推出的Codex编程助手凭借"本地安全运行"、"ChatGPT深度集成"、"全工具链覆盖"三大核心优势，迅速在GitHub狂揽4万星标，成为开发者热议的焦点。这款工具搭载GPT-5-Codex模型，能像专业程序员般连续7小时迭代复杂项目、修复Bug、运行测试，彻底改变传统编程的低效流程。"""

    print(f"📝 测试文本长度: {len(test_text)} 字符")

    # 测试1: GLM-4.6
    print("\n🧪 测试1: GLM-4.6")
    try:
        start_time = time.time()
        result = await llm_service.optimize_text_for_video(test_text, LLMProvider.GLM)
        end_time = time.time()

        print(f"✅ GLM-4.6 成功!")
        print(f"📊 响应时间: {end_time - start_time:.2f}秒")
        print(f"📄 结果长度: {len(result)} 字符")
        print(f"🎯 结果预览: {result[:150]}...")

        return True

    except Exception as e:
        print(f"❌ GLM-4.6 失败: {e}")

        # 检查是否包含429错误信息
        if "429" in str(e) or "Too Many Requests" in str(e):
            print("⚠️  确认是429速率限制错误")
            return False
        else:
            print("⚠️  其他类型的错误")
            return False

async def test_multiple_requests():
    """测试多个连续请求"""
    print("\n🧪 测试2: 多个连续请求（触发重试机制）")

    from services.llm.llm_service import get_llm_service, LLMProvider
    import yaml

    config_path = Path("config/config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    llm_service = get_llm_service(config)

    success_count = 0
    fail_count = 0
    fallback_count = 0

    for i in range(3):
        print(f"\n📤 第{i+1}次请求...")

        test_text = f"第{i+1}次测试：GLM-4.6文本优化功能，验证重试和降级机制是否正常工作。"

        try:
            start_time = time.time()
            result = await llm_service.optimize_text_for_video(test_text, LLMProvider.GLM)
            end_time = time.time()

            print(f"✅ 第{i+1}次请求成功")
            print(f"📊 响应时间: {end_time - start_time:.2f}秒")
            print(f"📄 结果长度: {len(result)} 字符")
            success_count += 1

        except Exception as e:
            print(f"❌ 第{i+1}次请求失败: {e}")
            fail_count += 1

    print(f"\n📊 测试结果统计:")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"🔄 总计: {success_count + fail_count}")

    return success_count > 0

async def test_http_api():
    """通过HTTP API测试"""
    print("\n🧪 测试3: HTTP API调用")

    # 检查是否有后端服务器运行
    try:
        import urllib.request
        import urllib.error
        import socket

        # 尝试连接到后端
        try:
            data = json.dumps({'text': 'test', 'provider': 'glm'}).encode('utf-8')
            req = urllib.request.Request(
                'http://localhost:9000/api/v1/llm/optimize-text',
                data=data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    print("✅ 后端API服务器正在运行")
                    # 测试实际请求
                    await test_backend_api()
                    return True
        except Exception as e:
            print(f"❌ 后端API服务器未运行: {e}")
            return False

    except Exception as e:
        print(f"❌ HTTP测试异常: {e}")
        return False

async def test_backend_api():
    """测试后端API"""
    test_data = {
        'text': '测试后端API的GLM-4.6文本优化功能，验证前端到后端的完整流程。',
        'provider': 'glm'
    }

    try:
        print("📤 发送HTTP API请求...")
        start_time = time.time()

        import urllib.request
        import urllib.error

        data = json.dumps(test_data).encode('utf-8')
        req = urllib.request.Request(
            'http://localhost:9000/api/v1/llm/optimize-text',
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            end_time = time.time()

            print(f"📥 HTTP响应状态: {response.status}")
            print(f"📊 响应时间: {end_time - start_time:.2f}秒")

            if response.status == 200:
                response_data = response.read().decode('utf-8')
                data = json.loads(response_data)
                print("✅ HTTP API调用成功")
                print(f"📄 返回数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
                return True
            else:
                print(f"❌ HTTP API调用失败: {response.status}")
                return False

    except Exception as e:
        print(f"🚨 HTTP API请求异常: {e}")
        return False

async def main():
    """主函数"""
    print("🔧 GLM-4.6 API测试")
    print("=" * 50)

    results = []

    # 测试1: 直接LLM服务
    result1 = await test_glm_api()
    results.append(("直接LLM服务测试", result1))

    # 测试2: 多个请求
    result2 = await test_multiple_requests()
    results.append(("多请求重试测试", result2))

    # 测试3: HTTP API
    result3 = await test_http_api()
    results.append(("HTTP API测试", result3))

    print("\n" + "=" * 50)
    print("🎯 测试总结:")

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"\n📊 总体结果: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有测试通过！GLM-4.6修复成功！")
    elif passed > 0:
        print("⚠️  部分测试通过，基本功能可用")
    else:
        print("🚨 所有测试失败，需要进一步修复")

if __name__ == "__main__":
    asyncio.run(main())