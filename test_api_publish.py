#!/usr/bin/env python3
"""
测试AI媒体平台的抖音发布API
"""

import asyncio
import json
import requests
import time
from datetime import datetime, timedelta

# API基础URL
BASE_URL = "http://localhost:9000"

async def test_api_publish():
    """测试API发布功能"""
    print("=== 测试AI媒体平台抖音发布API ===")

    # 1. 检查API服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ API服务运行正常: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ API服务未启动，请先启动AI媒体平台服务")
        print("启动命令: cd ai-media-platform/backend && python3 main.py")
        return False

    # 2. 测试发布功能状态
    try:
        response = requests.get(f"{BASE_URL}/publish/test")
        result = response.json()
        print(f"📊 发布功能状态检查:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        if result.get("status") != "success":
            print("❌ 发布功能状态检查失败")
            return False

    except Exception as e:
        print(f"❌ 状态检查失败: {e}")
        return False

    # 3. 创建发布任务
    try:
        publish_data = {
            "title": f"API测试视频-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "video_path": "/Users/sunyouyou/Desktop/projects/bzhi/ai-auto-upload/social-auto-upload/videos/demo.mp4",
            "tags": ["#API测试", "#AI视频", "#自动化发布"],
            "account_file": "douyin_test.json",
            "publish_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }

        print(f"\n📤 创建发布任务:")
        print(json.dumps(publish_data, indent=2, ensure_ascii=False))

        response = requests.post(f"{BASE_URL}/publish/douyin", json=publish_data)

        if response.status_code == 200:
            result = response.json()
            task_id = result.get("task_id")
            print(f"✅ 发布任务创建成功:")
            print(f"   任务ID: {task_id}")
            print(f"   状态: {result.get('status')}")
            print(f"   消息: {result.get('message')}")

            # 4. 监控任务状态
            print(f"\n⏳ 监控任务执行状态...")
            for i in range(60):  # 最多等待60次，每次2秒
                time.sleep(2)

                status_response = requests.get(f"{BASE_URL}/publish/status/{task_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status")
                    message = status_data.get("message")

                    print(f"   [{i+1}/60] 状态: {status} - {message}")

                    if status == "completed":
                        print("🎉 视频发布成功!")
                        return True
                    elif status == "failed":
                        error = status_data.get("error", "未知错误")
                        print(f"❌ 视频发布失败: {error}")
                        return False
                else:
                    print(f"   状态查询失败: {status_response.status_code}")

        else:
            print(f"❌ 创建发布任务失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return False

    except Exception as e:
        print(f"❌ API测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return False


async def main():
    """主测试函数"""
    success = await test_api_publish()

    if success:
        print("\n🎉 API发布功能测试通过!")
    else:
        print("\n⚠️ API发布功能测试失败，请检查错误信息")
        print("\n可能的解决方案:")
        print("1. 确保AI媒体平台服务已启动")
        print("2. 检查cookie文件是否有效")
        print("3. 确认视频文件存在")
        print("4. 检查网络连接")


if __name__ == "__main__":
    asyncio.run(main())