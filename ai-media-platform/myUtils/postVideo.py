import asyncio
from datetime import datetime
from pathlib import Path
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from uploader.douyin_uploader.main import DouYinVideo

def post_video_DouYin(title, files, tags, account_list, category=None, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0):
    """
    发布视频到抖音 - 严格按照social-auto-upload官方实现
    """
    print(f"[+] 开始抖音发布流程")
    print(f"    标题: {title}")
    print(f"    文件: {files}")
    print(f"    标签: {tags}")
    print(f"    账号: {account_list}")

    # 生成文件的完整路径
    account_files = []
    for account_file in account_list:
        # 确保cookie文件存在
        cookie_path = Path("cookiesFile") / account_file
        if not cookie_path.exists():
            # 创建cookiesFile目录
            os.makedirs("cookiesFile", exist_ok=True)
            # 创建空的cookie文件
            with open(cookie_path, 'w') as f:
                f.write('{"cookies": [], "origins": []}')
        account_files.append(str(cookie_path))

    # 处理文件路径
    video_files = []
    for file in files:
        # 如果是完整路径，直接使用；否则在uploads目录中查找
        if os.path.isabs(file):
            video_files.append(file)
        else:
            # 在uploads目录中查找文件
            upload_path = Path("uploads") / file
            if upload_path.exists():
                video_files.append(str(upload_path))
            else:
                print(f"[!] 警告: 视频文件不存在: {upload_path}")
                continue

    if not video_files:
        print("[!] 错误: 没有找到有效的视频文件")
        return False

    # 处理定时发布
    if enableTimer:
        # 简单的定时发布逻辑 - 每个视频间隔一定时间
        publish_datetimes = []
        base_time = datetime.now()
        for i, file in enumerate(video_files):
            # 计算发布时间：当前时间 + i * (24小时 / videos_per_day)
            from datetime import timedelta
            publish_time = base_time + timedelta(days=i) + timedelta(hours=12)  # 每天中午12点发布
            publish_datetimes.append(publish_time)
    else:
        publish_datetimes = [0 for _ in range(len(video_files))]  # 立即发布

    # 为每个文件和每个账号组合执行发布
    success_count = 0
    total_count = len(video_files) * len(account_files)

    for file_index, file_path in enumerate(video_files):
        for account_index, cookie_file in enumerate(account_files):
            try:
                print(f"\n[+] 发布进度: {file_index + 1}/{len(video_files)} 文件, {account_index + 1}/{len(account_files)} 账号")
                print(f"    文件: {os.path.basename(file_path)}")
                print(f"    账号: {os.path.basename(cookie_file)}")

                # 创建DouYinVideo实例
                app = DouYinVideo(
                    title=title,
                    file_path=file_path,
                    tags=tags if tags else [],
                    publish_date=publish_datetimes[file_index] if file_index < len(publish_datetimes) else 0,
                    account_file=cookie_file,
                    thumbnail_path=None
                )

                # 执行发布
                asyncio.run(app.main())
                success_count += 1
                print(f"[+] 发布成功: {os.path.basename(file_path)} -> {os.path.basename(cookie_file)}")

            except Exception as e:
                print(f"[!] 发布失败: {os.path.basename(file_path)} -> {os.path.basename(cookie_file)}")
                print(f"    错误: {e}")
                continue

    print(f"\n[+] 抖音发布完成!")
    print(f"    成功: {success_count}/{total_count}")

    return success_count > 0

def post_video_xhs(title, files, tags, account_list, category=None, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0):
    """小红书发布 - 待实现"""
    print(f"[!] 小红书发布功能待实现")
    return False

def post_video_tencent(title, files, tags, account_list, category=None, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0):
    """视频号发布 - 待实现"""
    print(f"[!] 视频号发布功能待实现")
    return False

def post_video_ks(title, files, tags, account_list, category=None, enableTimer=False, videos_per_day=1, daily_times=None, start_days=0):
    """快手发布 - 待实现"""
    print(f"[!] 快手发布功能待实现")
    return False