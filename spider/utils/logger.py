"""
日志配置工具
"""
import sys
from pathlib import Path
from loguru import logger
from config.settings import LOGS_DIR

def setup_logger():
    """配置日志系统"""
    # 移除默认控制台输出
    logger.remove()

    # 控制台输出格式
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 文件输出格式
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )

    # 添加控制台输出
    logger.add(
        sys.stdout,
        format=console_format,
        level="INFO",
        colorize=True
    )

    # 添加一般日志文件
    logger.add(
        LOGS_DIR / "spider.log",
        format=file_format,
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8"
    )

    # 添加错误日志文件
    logger.add(
        LOGS_DIR / "error.log",
        format=file_format,
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8"
    )

    return logger

# 初始化日志
setup_logger()