#!/usr/bin/env python3
"""
社交媒体基础工具
复制自social-auto-upload GitHub版本
"""

import asyncio
import uuid
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def set_init_script(context):
    """设置初始化脚本，用于反检测"""
    stealth_js_path = Path(__file__).parent / "stealth.min.js"
    if stealth_js_path.exists():
        await context.add_init_script(path=stealth_js_path)
    return context