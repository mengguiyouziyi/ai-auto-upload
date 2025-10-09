"""将 social-auto-upload Flask 接口迁移到 FastAPI 的适配层"""

import asyncio
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from queue import Queue
from typing import AsyncGenerator, Dict, List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from loguru import logger

import sys

# -----------------------------
# 初始化依赖路径
# -----------------------------
CURRENT_DIR = Path(__file__).resolve()
PROJECT_ROOT = CURRENT_DIR.parents[3]  # 修正：从backend/routes/向上3级到ai-auto-upload
SOCIAL_ROOT = PROJECT_ROOT / "social-auto-upload"

logger.info(f"legacy_social.py - 当前路径: {CURRENT_DIR}")
logger.info(f"legacy_social.py - 项目根目录: {PROJECT_ROOT}")
logger.info(f"legacy_social.py - social-auto-upload路径: {SOCIAL_ROOT}")
logger.info(f"legacy_social.py - social-auto-upload存在: {SOCIAL_ROOT.exists()}")

# 尝试导入social-auto-upload模块（可选）
try:
    if str(SOCIAL_ROOT) not in sys.path:
        sys.path.insert(0, str(SOCIAL_ROOT))

    from conf import BASE_DIR  # type: ignore
    from myUtils.auth import check_cookie  # type: ignore
    from myUtils.login import (  # type: ignore
        douyin_cookie_gen,
        get_ks_cookie,
        get_tencent_cookie,
        xiaohongshu_cookie_gen,
    )
    from myUtils.postVideo import (  # type: ignore
        post_video_DouYin,
        post_video_ks,
        post_video_tencent,
        post_video_xhs,
    )
    SOCIAL_AUTO_UPLOAD_AVAILABLE = True
    logger.info("social-auto-upload模块导入成功")
except ImportError as exc:  # pragma: no cover - 环境问题
    logger.warning(f"导入 social-auto-upload 模块失败: {exc}")
    logger.warning("将使用独立实现的上传功能")
    SOCIAL_AUTO_UPLOAD_AVAILABLE = False
    BASE_DIR = SOCIAL_ROOT  # 使用备用路径

router = APIRouter()

DATABASE_PATH = BASE_DIR / "db" / "database.db"
VIDEO_STORAGE = BASE_DIR / "videoFile"
COOKIE_STORAGE = BASE_DIR / "cookiesFile"

VIDEO_STORAGE.mkdir(parents=True, exist_ok=True)

# -----------------------------
# 工具函数
# -----------------------------

def _get_db_connection() -> sqlite3.Connection:
    if not DATABASE_PATH.exists():
        raise HTTPException(status_code=500, detail="账号数据库不存在，请先初始化 social-auto-upload 项目")
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


async def _run_in_thread(func, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)


# -----------------------------
# 账号管理相关接口
# -----------------------------


@router.get("/getValidAccounts")
async def get_valid_accounts():
    """获取有效账号列表，兼容原 Flask 返回结构"""
    def fetch_rows() -> List[List]:
        with _get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_info")
            rows = cursor.fetchall()
            return [list(row) for row in rows]

    rows_list = await _run_in_thread(fetch_rows)

    async def check_and_update(row: List) -> List:
        account_type, file_path, status = row[1], row[2], row[4]
        try:
            # 使用我们自己的cookie验证函数
            if SOCIAL_AUTO_UPLOAD_AVAILABLE and 'check_cookie' in globals():
                is_valid = await check_cookie(account_type, file_path)
            else:
                # 使用抖音上传模块中的验证方法
                if account_type == 3:  # 抖音
                    from .douyin_upload import DouYinVideoUploader
                    full_path = SOCIAL_ROOT / "cookiesFile" / file_path
                    uploader = DouYinVideoUploader(str(full_path), headless=True)
                    is_valid = await uploader.cookie_auth()
                else:
                    # 其他平台暂时认为有效
                    is_valid = status == 1
        except Exception as exc:  # Playwright 或浏览器未配置等情况
            logger.warning(f"账号 {row[0]} Cookie 校验失败: {exc}")
            is_valid = status == 1  # 保持原状态，避免误判

        if not is_valid:
            row[4] = 0
            def update_status():
                with _get_db_connection() as conn:
                    conn.execute(
                        "UPDATE user_info SET status = ? WHERE id = ?",
                        (0, row[0]),
                    )
                    conn.commit()
            await _run_in_thread(update_status)
        return row

    updated_rows: List[List] = []
    for row in rows_list:
        updated_rows.append(await check_and_update(row))

    return {"code": 200, "msg": None, "data": updated_rows}


@router.get("/deleteAccount")
async def delete_account(id: int):
    def delete() -> Optional[int]:
        with _get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, filePath FROM user_info WHERE id = ?", (id,))
            record = cursor.fetchone()
            if record is None:
                return None
            conn.execute("DELETE FROM user_info WHERE id = ?", (id,))
            conn.commit()
            return record["id"]

    result = await _run_in_thread(delete)
    if result is None:
        raise HTTPException(status_code=404, detail="账号不存在")
    return {"code": 200, "msg": "account deleted successfully", "data": None}


@router.post("/updateUserinfo")
async def update_userinfo(payload: Dict[str, int | str]):
    user_id = payload.get("id")
    type_ = payload.get("type")
    user_name = payload.get("userName")

    if user_id is None or type_ is None or not user_name:
        raise HTTPException(status_code=400, detail="缺少必要参数")

    def update() -> int:
        with _get_db_connection() as conn:
            conn.execute(
                "UPDATE user_info SET type = ?, userName = ? WHERE id = ?",
                (type_, user_name, user_id),
            )
            conn.commit()
            return conn.total_changes

    changes = await _run_in_thread(update)
    if changes == 0:
        raise HTTPException(status_code=404, detail="账号不存在")

    return {"code": 200, "msg": "account update successfully", "data": None}


# -----------------------------
# 素材管理接口
# -----------------------------


@router.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")

    uuid_name = f"{uuid.uuid1()}_{file.filename}"
    target_path = VIDEO_STORAGE / uuid_name

    content = await file.read()
    await _run_in_thread(target_path.write_bytes, content)

    return {"code": 200, "msg": "File uploaded successfully", "data": uuid_name}


@router.post("/uploadSave")
async def upload_save(file: UploadFile = File(...), filename: Optional[str] = None):
    if not file.filename:
        raise HTTPException(status_code=400, detail="未选择文件")

    suffix = Path(file.filename).suffix
    base_name = filename or Path(file.filename).stem
    final_name = f"{uuid.uuid1()}_{base_name}{suffix}"
    target_path = VIDEO_STORAGE / final_name

    content = await file.read()
    await _run_in_thread(target_path.write_bytes, content)

    file_size_mb = round(target_path.stat().st_size / (1024 * 1024), 2)

    def insert_record():
        with _get_db_connection() as conn:
            conn.execute(
                "INSERT INTO file_records (filename, filesize, file_path) VALUES (?, ?, ?)",
                (f"{base_name}{suffix}", file_size_mb, final_name),
            )
            conn.commit()

    await _run_in_thread(insert_record)

    return {
        "code": 200,
        "msg": "File uploaded and saved successfully",
        "data": {"filename": f"{base_name}{suffix}", "filepath": final_name},
    }


@router.get("/getFiles")
async def get_files():
    def fetch() -> List[Dict[str, str | int]]:
        with _get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM file_records")
            return [dict(row) for row in cursor.fetchall()]

    records = await _run_in_thread(fetch)
    return {"code": 200, "msg": "success", "data": records}


@router.get("/deleteFile")
async def delete_file(id: int):
    def remove() -> Optional[Dict[str, str]]:
        with _get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, filename, file_path FROM file_records WHERE id = ?", (id,))
            record = cursor.fetchone()
            if record is None:
                return None
            conn.execute("DELETE FROM file_records WHERE id = ?", (id,))
            conn.commit()
            return dict(record)

    record = await _run_in_thread(remove)
    if record is None:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 文件留在磁盘以便留存，与原逻辑一致
    return {"code": 200, "msg": "File deleted successfully", "data": {"id": record["id"], "filename": record["filename"]}}


@router.get("/getFile")
async def get_file(filename: str):
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="非法文件名")
    file_path = VIDEO_STORAGE / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(file_path)


# -----------------------------
# 发布中心接口
# -----------------------------


@router.post("/generateDouyinCookie")
async def generate_douyin_cookie_endpoint(account_file: str):
    """生成抖音Cookie，打开浏览器让用户登录"""
    try:
        from .douyin_upload import generate_douyin_cookie

        # 构建完整的Cookie文件路径
        full_path = SOCIAL_ROOT / "cookiesFile" / account_file

        logger.info(f"开始生成抖音Cookie: {account_file}")
        success = await generate_douyin_cookie(str(full_path))

        if success:
            return {"code": 200, "msg": "抖音Cookie生成成功，请检查浏览器并完成登录", "data": None}
        else:
            return {"code": 500, "msg": "抖音Cookie生成失败", "data": None}

    except Exception as e:
        logger.error(f"生成抖音Cookie失败: {e}")
        return {"code": 500, "msg": f"生成Cookie失败: {str(e)}", "data": None}


@router.post("/postVideo")
async def post_video(payload: Dict):
    file_list = payload.get("fileList", [])
    account_list = payload.get("accountList", [])
    type_ = payload.get("type")
    title = payload.get("title")
    tags = payload.get("tags")
    category = payload.get("category") or None
    enable_timer = payload.get("enableTimer")
    videos_per_day = payload.get("videosPerDay")
    daily_times = payload.get("dailyTimes")
    start_days = payload.get("startDays")

    logger.info(
        "发布任务: type={} files={} accounts={}", type_, file_list, account_list
    )

    # 对于抖音上传，使用我们独立实现的模块
    if type_ == 3:
        try:
            from .douyin_upload import upload_douyin_video
            # 自动登录功能，默认关闭避免意外打开浏览器
            auto_login = payload.get("autoLogin", False)

            success = await upload_douyin_video(
                title=title,
                file_list=file_list,
                tags=tags or [],
                account_list=account_list,
                category=category or 0,
                enable_timer=bool(enable_timer),
                videos_per_day=videos_per_day or 1,
                daily_times=daily_times or ["10:00"],
                start_days=start_days or 0,
                auto_login=auto_login
            )

            if success:
                return {"code": 200, "msg": "抖音视频上传成功", "data": None}
            else:
                return {"code": 500, "msg": "抖音视频上传失败", "data": None}

        except Exception as e:
            logger.error(f"抖音上传失败: {e}")
            return {"code": 500, "msg": f"抖音上传出错: {str(e)}", "data": None}

    # 对于其他平台，尝试使用原始social-auto-upload实现
    if SOCIAL_AUTO_UPLOAD_AVAILABLE:
        try:
            async def run_post():
                match type_:
                    case 1:
                        await _run_in_thread(
                            post_video_xhs,
                            title,
                            file_list,
                            tags,
                            account_list,
                            category,
                            enable_timer,
                            videos_per_day,
                            daily_times,
                            start_days,
                        )
                    case 2:
                        await _run_in_thread(
                            post_video_tencent,
                            title,
                            file_list,
                            tags,
                            account_list,
                            category,
                            enable_timer,
                            videos_per_day,
                            daily_times,
                            start_days,
                        )
                    case 4:
                        await _run_in_thread(
                            post_video_ks,
                            title,
                            file_list,
                            tags,
                            account_list,
                            category,
                            enable_timer,
                            videos_per_day,
                            daily_times,
                            start_days,
                        )
                    case _:
                        raise HTTPException(status_code=400, detail="不支持的平台类型")

            await run_post()
            return {"code": 200, "msg": None, "data": None}

        except Exception as e:
            logger.error(f"发布失败: {e}")
            return {"code": 500, "msg": f"发布失败: {str(e)}", "data": None}
    else:
        logger.error(f"不支持的平台类型 {type_}，social-auto-upload模块不可用")
        return {"code": 400, "msg": f"不支持的平台类型或模块缺失: {type_}", "data": None}


@router.post("/postVideoBatch")
async def post_video_batch(batch_payload: List[Dict]):
    if not isinstance(batch_payload, list):
        raise HTTPException(status_code=400, detail="请求体需要为数组")

    for payload in batch_payload:
        await post_video(payload)

    return {"code": 200, "msg": None, "data": None}


# -----------------------------
# 登录扫码 SSE 接口
# -----------------------------

active_queues: Dict[str, Queue] = {}


def run_async_login(type_: str, account_name: str, status_queue: Queue):
    if type_ == "1":
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(xiaohongshu_cookie_gen(account_name, status_queue))
        loop.close()
    elif type_ == "2":
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(get_tencent_cookie(account_name, status_queue))
        loop.close()
    elif type_ == "3":
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(douyin_cookie_gen(account_name, status_queue))
        loop.close()
    elif type_ == "4":
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(get_ks_cookie(account_name, status_queue))
        loop.close()
    else:
        status_queue.put("500")


@router.get("/login")
async def login(type: str, id: str):
    status_queue: Queue = Queue()
    active_queues[id] = status_queue

    thread = threading.Thread(
        target=run_async_login,
        args=(type, id, status_queue),
        daemon=True,
    )
    thread.start()

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            while True:
                message = await _run_in_thread(status_queue.get)
                yield f"data: {message}\n\n"
        except asyncio.CancelledError:
            raise
        finally:
            active_queues.pop(id, None)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


__all__ = ["router"]
