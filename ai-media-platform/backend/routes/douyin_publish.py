"""
抖音发布接口 - 严格按照social-auto-upload方式
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

import sys

# 添加social-auto-upload路径
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SOCIAL_ROOT = PROJECT_ROOT / "social-auto-upload"

if str(SOCIAL_ROOT) not in sys.path:
    sys.path.insert(0, str(SOCIAL_ROOT))

try:
    from conf import BASE_DIR
    from uploader.douyin_uploader.main import DouYinVideo
    from utils.files_times import generate_schedule_time_next_day
    SOCIAL_AUTO_UPLOAD_AVAILABLE = True
    logger.info("social-auto-upload模块导入成功")
except ImportError as e:
    logger.error(f"无法导入social-auto-upload模块: {e}")
    SOCIAL_AUTO_UPLOAD_AVAILABLE = False

router = APIRouter()

# 数据库路径
DATABASE_PATH = BASE_DIR / "db" / "database.db"
COOKIE_STORAGE = BASE_DIR / "cookiesFile"

# 发布任务存储
publish_tasks: Dict[str, Dict] = {}


class PublishRequest(BaseModel):
    """发布请求模型"""
    title: str
    video_path: str
    tags: List[str] = []
    account_id: Optional[str] = None
    publish_time: Optional[str] = None  # ISO格式时间字符串
    account_file: Optional[str] = None


class PublishResponse(BaseModel):
    """发布响应模型"""
    task_id: str
    status: str
    message: str


def get_account_file(account_id: Optional[str] = None) -> str:
    """获取账号cookie文件路径"""
    if account_id:
        cookie_file = COOKIE_STORAGE / f"{account_id}.json"
        if cookie_file.exists():
            return str(cookie_file)

    # 如果没有指定账号ID或文件不存在，使用默认的
    default_cookies = list(COOKIE_STORAGE.glob("*.json"))
    if default_cookies:
        return str(default_cookies[0])

    # 如果都没有，尝试使用social-auto-upload的格式
    douyin_cookie = COOKIE_STORAGE / "douyin_uploader" / "account.json"
    if douyin_cookie.exists():
        return str(douyin_cookie)

    raise HTTPException(status_code=404, detail="未找到有效的抖音账号cookie文件")


@router.post("/publish/douyin", response_model=PublishResponse)
async def publish_douyin(request: PublishRequest, background_tasks: BackgroundTasks):
    """
    发布视频到抖音 - 使用social-auto-upload方式
    """
    if not SOCIAL_AUTO_UPLOAD_AVAILABLE:
        raise HTTPException(status_code=500, detail="social-auto-upload模块不可用")

    # 生成任务ID
    task_id = str(uuid.uuid4())

    # 验证视频文件存在
    video_path = Path(request.video_path)
    if not video_path.exists():
        raise HTTPException(status_code=404, detail=f"视频文件不存在: {request.video_path}")

    # 获取账号文件
    try:
        account_file = get_account_file(request.account_id or request.account_file)
    except HTTPException:
        raise HTTPException(status_code=404, detail="未找到有效的抖音账号，请先添加账号")

    # 解析发布时间
    publish_time = None
    if request.publish_time:
        try:
            publish_time = datetime.fromisoformat(request.publish_time.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(status_code=400, detail="发布时间格式错误，请使用ISO格式")

    # 创建任务
    task_info = {
        "task_id": task_id,
        "status": "pending",
        "title": request.title,
        "video_path": str(video_path),
        "tags": request.tags,
        "account_file": account_file,
        "publish_time": publish_time,
        "created_at": datetime.now(),
        "message": "任务已创建，等待执行"
    }

    publish_tasks[task_id] = task_info

    # 添加后台任务
    background_tasks.add_task(execute_douyin_publish, task_id)

    return PublishResponse(
        task_id=task_id,
        status="pending",
        message="发布任务已创建，正在执行中"
    )


@router.get("/publish/status/{task_id}")
async def get_publish_status(task_id: str):
    """获取发布任务状态"""
    if task_id not in publish_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_info = publish_tasks[task_id]
    return {
        "task_id": task_id,
        "status": task_info["status"],
        "message": task_info.get("message", ""),
        "created_at": task_info["created_at"],
        "updated_at": task_info.get("updated_at"),
        "error": task_info.get("error")
    }


@router.get("/publish/tasks")
async def list_publish_tasks():
    """列出所有发布任务"""
    return {
        "tasks": [
            {
                "task_id": task_id,
                "status": task_info["status"],
                "title": task_info["title"],
                "created_at": task_info["created_at"],
                "message": task_info.get("message", "")
            }
            for task_id, task_info in publish_tasks.items()
        ]
    }


async def execute_douyin_publish(task_id: str):
    """
    执行抖音发布任务 - 使用social-auto-upload的DouYinVideo类
    """
    task_info = publish_tasks[task_id]

    try:
        # 更新任务状态
        task_info["status"] = "uploading"
        task_info["message"] = "正在上传视频到抖音..."
        task_info["updated_at"] = datetime.now()

        logger.info(f"开始执行抖音发布任务 {task_id}: {task_info['title']}")

        # 使用social-auto-upload的DouYinVideo类
        video_obj = DouYinVideo(
            title=task_info["title"],
            file_path=task_info["video_path"],
            tags=task_info["tags"],
            publish_date=task_info.get("publish_time") or datetime.now(),
            account_file=task_info["account_file"],
            thumbnail_path=None
        )

        # 执行上传
        await video_obj.main()

        # 任务完成
        task_info["status"] = "completed"
        task_info["message"] = "视频发布成功"
        task_info["updated_at"] = datetime.now()

        logger.info(f"抖音发布任务 {task_id} 执行成功")

    except Exception as e:
        # 任务失败
        task_info["status"] = "failed"
        task_info["message"] = f"发布失败: {str(e)}"
        task_info["error"] = str(e)
        task_info["updated_at"] = datetime.now()

        logger.error(f"抖音发布任务 {task_id} 执行失败: {e}")


@router.post("/publish/test")
async def test_publish():
    """
    测试发布功能 - 查看可用的账号和cookie
    """
    try:
        # 检查social-auto-upload可用性
        if not SOCIAL_AUTO_UPLOAD_AVAILABLE:
            return {
                "status": "error",
                "message": "social-auto-upload模块不可用",
                "social_root": str(SOCIAL_ROOT),
                "social_exists": SOCIAL_ROOT.exists()
            }

        # 检查数据库
        db_exists = DATABASE_PATH.exists()

        # 检查cookie文件
        cookie_files = list(COOKIE_STORAGE.glob("*.json"))
        douyin_cookies = [f for f in cookie_files if "douyin" in f.name.lower()]

        # 检查视频文件
        video_dir = BASE_DIR / "videos"
        video_files = list(video_dir.glob("*.mp4")) if video_dir.exists() else []

        return {
            "status": "success",
            "social_auto_upload_available": True,
            "database_exists": db_exists,
            "cookie_files_count": len(cookie_files),
            "douyin_cookie_files": [f.name for f in douyin_cookies],
            "video_files_count": len(video_files),
            "video_files": [f.name for f in video_files[:5]],  # 只显示前5个
            "paths": {
                "base_dir": str(BASE_DIR),
                "database_path": str(DATABASE_PATH),
                "cookie_storage": str(COOKIE_STORAGE),
                "video_dir": str(video_dir)
            }
        }

    except Exception as e:
        logger.error(f"测试发布功能失败: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# 清理过期任务（可选）
def cleanup_old_tasks():
    """清理超过24小时的任务"""
    current_time = datetime.now()
    expired_tasks = []

    for task_id, task_info in publish_tasks.items():
        if (current_time - task_info["created_at"]).days > 1:
            expired_tasks.append(task_id)

    for task_id in expired_tasks:
        del publish_tasks[task_id]
        logger.info(f"清理过期任务: {task_id}")