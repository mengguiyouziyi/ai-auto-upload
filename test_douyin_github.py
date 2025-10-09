"""
测试抖音发布功能 - GitHub原始实现
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "social-auto-upload"))
sys.path.insert(0, str(PROJECT_ROOT / "ai-media-platform" / "backend"))

from routes.douyin_upload_github import DouYinVideo


async def test_github_implementation():
    """测试GitHub原始实现的抖音发布功能"""
    print("=== 测试GitHub原始实现抖音发布功能 ===")

    # 检查路径
    social_root = PROJECT_ROOT / "social-auto-upload"
    cookie_storage = social_root / "cookiesFile"
    video_dir = social_root / "videos"

    print(f"social-auto-upload路径: {social_root}")
    print(f"social-auto-upload存在: {social_root.exists()}")
    print(f"cookie存储路径: {cookie_storage}")
    print(f"cookie存储存在: {cookie_storage.exists()}")

    # 查找可用的cookie文件
    cookie_files = list(cookie_storage.glob("*.json"))
    print(f"找到 {len(cookie_files)} 个cookie文件:")
    for f in cookie_files:
        print(f"  - {f.name}")

    # 查找可用的视频文件
    if video_dir.exists():
        video_files = list(video_dir.glob("*.mp4"))
        print(f"找到 {len(video_files)} 个视频文件:")
        for f in video_files[:3]:  # 只显示前3个
            print(f"  - {f.name}")
    else:
        print("视频目录不存在")
        return False

    if not cookie_files:
        print("❌ 没有找到可用的cookie文件")
        return False

    if not video_files:
        print("❌ 没有找到可用的视频文件")
        return False

    # 使用第一个cookie文件和第一个视频文件进行测试
    cookie_file = cookie_files[0]
    video_file = video_files[0]

    print(f"\n使用cookie文件: {cookie_file}")
    print(f"使用视频文件: {video_file}")

    try:
        # 创建GitHub原始实现的DouYinVideo对象
        video_obj = DouYinVideo(
            title=f"GitHub测试视频-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            file_path=str(video_file),
            tags=["#GitHub测试", "#AI视频", "#自动化发布"],
            publish_date=datetime.now(),  # 立即发布
            account_file=str(cookie_file),
            thumbnail_path=None
        )

        print("✅ GitHub DouYinVideo对象创建成功")
        print("开始上传测试...")

        # 执行上传
        await video_obj.main()

        print("✅ GitHub原始实现测试完成")
        return True

    except Exception as e:
        print(f"❌ GitHub原始实现测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("开始测试GitHub原始抖音发布功能...")

    # 测试GitHub原始实现
    github_success = await test_github_implementation()

    print(f"\n=== 测试结果 ===")
    print(f"GitHub原始实现测试: {'✅ 通过' if github_success else '❌ 失败'}")

    if github_success:
        print("🎉 GitHub原始实现测试通过！抖音发布功能正常")
    else:
        print("⚠️ GitHub原始实现测试失败，需要进一步调试")


if __name__ == "__main__":
    asyncio.run(main())