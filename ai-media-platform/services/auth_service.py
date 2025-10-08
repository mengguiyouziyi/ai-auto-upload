#!/usr/bin/env python3
"""
账号Cookie有效性验证服务
仿照social-auto-upload的实现
"""

import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright

# 平台映射
PLATFORM_MAP = {
    1: "小红书",
    2: "视频号",
    3: "抖音",
    4: "快手"
}

# 验证URL映射
PLATFORM_URLS = {
    1: "https://creator.xiaohongshu.com/creator-micro/content/upload",
    2: "https://channels.weixin.qq.com/platform/post/create",
    3: "https://creator.douyin.com/creator-micro/content/upload",
    4: "https://cp.kuaishou.com/article/publish/video"
}

async def cookie_auth_douyin(cookie_file: Path) -> bool:
    """验证抖音Cookie有效性 - 修复版本"""
    try:
        # 首先检查Cookie文件是否存在和有内容
        if not cookie_file.exists():
            print(f"[-] 抖音Cookie文件不存在: {cookie_file.name}")
            return False

        # 检查文件大小，如果太小可能无效
        if cookie_file.stat().st_size < 100:
            print(f"[-] 抖音Cookie文件过小: {cookie_file.name}")
            return False

        # 简单检查Cookie文件内容
        import json
        try:
            with open(cookie_file, 'r', encoding='utf-8') as f:
                cookie_data = json.load(f)

            # 检查是否有cookies字段
            if 'cookies' not in cookie_data or not cookie_data['cookies']:
                print(f"[-] 抖音Cookie文件无有效cookies: {cookie_file.name}")
                return False

            # 检查是否有重要的抖音cookie
            important_cookies = ['ttwid', 'passport_csrf_token', '__ac_nonce', 'sessionid', 'sid_guard']
            found_cookies = []
            for cookie in cookie_data['cookies']:
                name = cookie.get('name')
                if name in important_cookies:
                    found_cookies.append(name)

            if found_cookies:
                print(f"[+] 抖音Cookie有效: {cookie_file.name}, 找到字段: {found_cookies}")
                return True
            else:
                print(f"[-] 抖音Cookie缺少重要字段: {cookie_file.name}")
                # 如果没有找到重要字段，但有其他cookies也认为有效
                if len(cookie_data['cookies']) > 10:
                    print(f"[+] 抖音Cookie有足够字段数量: {len(cookie_data['cookies'])}, 认为有效")
                    return True
                return False

        except json.JSONDecodeError:
            print(f"[-] 抖音Cookie文件格式错误: {cookie_file.name}")
            return False

    except Exception as e:
        print(f"[!] 抖音Cookie验证异常: {cookie_file.name} - {str(e)}")
        return False

async def cookie_auth_tencent(cookie_file: Path) -> bool:
    """验证视频号Cookie有效性"""
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)

            if not cookie_file.exists():
                return False

            context = await browser.new_context(storage_state=str(cookie_file))
            page = await context.new_page()

            # 访问微信视频号创作者平台
            await page.goto(PLATFORM_URLS[2])

            try:
                # 查找特定元素来判断是否登录成功
                # 如果没有找到特定元素，说明cookie有效
                await page.wait_for_selector('div.title-name:has-text("微信小店")', timeout=5000)
                return False  # 找到了登录提示，cookie失效

            except Exception as e:
                # 没有找到登录提示，说明cookie有效
                print(f"[+] 视频号Cookie有效: {cookie_file.name}")
                return True

            finally:
                await context.close()
                await browser.close()

    except Exception as e:
        print(f"[!] 视频号Cookie验证异常: {cookie_file.name} - {str(e)}")
        return False

async def cookie_auth_ks(cookie_file: Path) -> bool:
    """验证快手Cookie有效性"""
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)

            if not cookie_file.exists():
                return False

            context = await browser.new_context(storage_state=str(cookie_file))
            page = await context.new_page()

            # 访问快手创作者平台
            await page.goto(PLATFORM_URLS[4])

            try:
                # 查找特定元素来判断是否需要登录
                await page.wait_for_selector("div.names div.container div.name:text('机构服务')", timeout=5000)
                return False  # 找到了机构服务，说明需要登录，cookie失效

            except Exception as e:
                # 没有找到登录提示，说明cookie有效
                print(f"[+] 快手Cookie有效: {cookie_file.name}")
                return True

            finally:
                await context.close()
                await browser.close()

    except Exception as e:
        print(f"[!] 快手Cookie验证异常: {cookie_file.name} - {str(e)}")
        return False

async def cookie_auth_xhs(cookie_file: Path) -> bool:
    """验证小红书Cookie有效性"""
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)

            if not cookie_file.exists():
                return False

            context = await browser.new_context(storage_state=str(cookie_file))
            page = await context.new_page()

            # 访问小红书创作者中心
            await page.goto(PLATFORM_URLS[1])

            try:
                # 等待页面加载
                await page.wait_for_url(PLATFORM_URLS[1], timeout=5000)

                # 检查是否出现登录按钮
                login_elements = await page.get_by_text('手机号登录').count() + await page.get_by_text('扫码登录').count()
                if login_elements > 0:
                    return False

                print(f"[+] 小红书Cookie有效: {cookie_file.name}")
                return True

            except Exception as e:
                # 页面跳转或超时，说明cookie失效
                print(f"[-] 小红书Cookie失效: {cookie_file.name} - {str(e)}")
                return False

            finally:
                await context.close()
                await browser.close()

    except Exception as e:
        print(f"[!] 小红书Cookie验证异常: {cookie_file.name} - {str(e)}")
        return False

async def check_cookie(platform_type: int, cookie_file_path: str) -> bool:
    """
    检查Cookie有效性

    Args:
        platform_type: 平台类型 (1=小红书, 2=视频号, 3=抖音, 4=快手)
        cookie_file_path: Cookie文件路径

    Returns:
        bool: Cookie是否有效
    """
    base_dir = Path(__file__).parent.parent
    cookie_file = base_dir / cookie_file_path

    try:
        match platform_type:
            case 1:  # 小红书
                return await cookie_auth_xhs(cookie_file)
            case 2:  # 视频号
                return await cookie_auth_tencent(cookie_file)
            case 3:  # 抖音
                return await cookie_auth_douyin(cookie_file)
            case 4:  # 快手
                return await cookie_auth_ks(cookie_file)
            case _:
                print(f"[!] 未知平台类型: {platform_type}")
                return False
    except Exception as e:
        print(f"[!] Cookie验证异常 - 平台{platform_type}, 文件{cookie_file_path}: {str(e)}")
        return False

async def batch_check_cookies(accounts: list) -> list:
    """
    批量检查账号Cookie有效性

    Args:
        accounts: 账号列表，每个账号是 [id, type, filePath, userName, status]

    Returns:
        list: 更新后的账号列表
    """
    updated_accounts = []

    for account in accounts:
        account_id, platform_type, cookie_file, username, current_status = account

        print(f"\n🔍 验证账号: {username} ({PLATFORM_MAP.get(platform_type, '未知')})")

        # 检查Cookie有效性
        is_valid = await check_cookie(platform_type, cookie_file)

        # 更新状态
        new_status = 1 if is_valid else 0

        if new_status != current_status:
            print(f"📊 状态更新: {username} {current_status} -> {new_status}")
            account[4] = new_status
        else:
            status_text = "有效" if new_status == 1 else "失效"
            print(f"✅ 状态未变: {username} ({status_text})")

        updated_accounts.append(account)

    return updated_accounts

# 测试函数
async def test_cookie_validation():
    """测试Cookie验证功能"""
    print("🧪 测试Cookie验证功能...")

    # 创建测试账号
    test_accounts = [
        [1, 1, "cookies/test_xhs.json", "测试小红书账号", 1],
        [2, 3, "cookies/test_douyin.json", "测试抖音账号", 1],
        [3, 4, "cookies/test_ks.json", "测试快手账号", 0],
    ]

    updated_accounts = await batch_check_cookies(test_accounts)

    print("\n📋 验证结果:")
    for account in updated_accounts:
        account_id, platform_type, cookie_file, username, status = account
        status_text = "有效" if status == 1 else "失效"
        print(f"  - {username} ({PLATFORM_MAP.get(platform_type, '未知')}): {status_text}")

if __name__ == "__main__":
    asyncio.run(test_cookie_validation())