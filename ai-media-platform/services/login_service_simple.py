#!/usr/bin/env python3
"""
简化登录服务 - 基于social-auto-upload原始实现
解决QR码登录"连接服务器失败"问题
"""

import asyncio
import uuid
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright
from queue import Queue

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent

# 抖音登录 - 完全基于social-auto-upload原始实现
async def douyin_cookie_gen(id, status_queue):
    """抖音Cookie生成 - 基于social-auto-upload原始实现"""
    url_changed_event = asyncio.Event()

    async def on_url_change():
        """简单的URL变化检测 - 原始实现方式"""
        try:
            # 检查是否是主框架的变化
            if page.url != original_url:
                print(f"✅ URL变化检测: {original_url} -> {page.url}")
                url_changed_event.set()
        except Exception as e:
            print(f"[!] URL检测异常: {str(e)}")
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()

        # 尝试设置初始化脚本（如果可用）
        try:
            from services.base_social_media import set_init_script
            context = await set_init_script(context)
        except ImportError:
            print("⚠️ 无法导入set_init_script，使用默认设置")

        page = await context.new_page()

        try:
            print(f"🚀 开始抖音登录流程: {id}")

            # 访问抖音创作者中心
            await page.goto("https://creator.douyin.com/")
            original_url = page.url
            print(f"📄 初始URL: {original_url}")

            # 使用原始实现的简单二维码定位方式
            print("🔍 查找二维码元素...")
            try:
                img_locator = page.get_by_role("img", name="二维码")
                src = await img_locator.get_attribute("src")
                print(f"✅ 图片地址: {src[:50] if src else 'None'}...")
                status_queue.put(src if src else "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
            except Exception as e:
                print(f"⚠️ 获取二维码失败: {str(e)}")
                # 如果找不到二维码，发送默认图片
                status_queue.put("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

            # 监听页面的 'framenavigated' 事件，只关注主框架的变化 - 原始实现
            page.on('framenavigated',
                    lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

            print("⏳ 等待用户扫码登录（最多200秒）...")
            print("💡 请在手机抖音App中扫描二维码完成登录")

            # 使用原始实现的简单等待逻辑
            try:
                # 等待 URL 变化或超时
                await asyncio.wait_for(url_changed_event.wait(), timeout=200)
                print("✅ 监听页面跳转成功")
                login_success = True
            except asyncio.TimeoutError:
                print("⏰ 监听页面跳转超时")
                login_success = False

            if login_success:
                print("✅ 登录成功！正在保存Cookie...")

                uuid_v1 = uuid.uuid1()
                print(f"UUID v1: {uuid_v1}")

                # 创建cookies目录 - 使用正确的绝对路径
                cookies_dir = BASE_DIR / "cookies"
                cookies_dir.mkdir(exist_ok=True)

                # 保存Cookie
                cookie_path = cookies_dir / f"{uuid_v1}.json"
                await context.storage_state(path=cookie_path)
                print(f"💾 Cookie已保存: {cookie_path}")

                # 验证Cookie - 尝试验证但即使失败也继续
                print("🔍 验证Cookie有效性...")
                try:
                    from services.auth_service import check_cookie
                    result = await check_cookie(3, f"cookies/{uuid_v1}.json")
                    if result:
                        print("✅ Cookie验证成功")
                    else:
                        print("⚠️ Cookie验证失败，但继续保存账号")
                except Exception as cookie_error:
                    print(f"⚠️ Cookie验证异常，但继续保存账号: {str(cookie_error)}")

                # 更新数据库
                await _update_database(3, id, f"cookies/{uuid_v1}.json")
                status_queue.put("200")
                print(f"🎉 账号 {id} 添加成功！")
            else:
                print("❌ 登录失败")
                status_queue.put("500")

        except Exception as e:
            print(f"[!] 登录流程异常: {str(e)}")
            import traceback
            traceback.print_exc()
            status_queue.put("500")

        finally:
            # 清理资源
            try:
                await page.close()
                await context.close()
                await browser.close()
                print("🧹 浏览器资源已清理")
            except:
                pass

# 快手登录 - 基于原始实现
async def ks_cookie_gen(id, status_queue):
    """快手Cookie生成 - 基于原始实现"""
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()

        # 尝试设置初始化脚本
        try:
            from services.base_social_media import set_init_script
            context = await set_init_script(context)
        except ImportError:
            pass

        page = await context.new_page()
        await page.goto("https://cp.kuaishou.com")

        # 定位并点击"立即登录"按钮（类型为 link）
        await page.get_by_role("link", name="立即登录").click()
        await page.get_by_text("扫码登录").click()
        img_locator = page.get_by_role("img", name="qrcode")
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("✅ 监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("⏰ 监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None

        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 创建cookies目录 - 使用正确的绝对路径
        cookies_dir = BASE_DIR / "cookies"
        cookies_dir.mkdir(exist_ok=True)

        cookie_path = cookies_dir / f"{uuid_v1}.json"
        await context.storage_state(path=cookie_path)

        # 验证Cookie
        try:
            from services.auth_service import check_cookie
            result = await check_cookie(4, f"cookies/{uuid_v1}.json")
            if not result:
                status_queue.put("500")
                await page.close()
                await context.close()
                await browser.close()
                return None
        except Exception:
            print("⚠️ Cookie验证失败，但继续保存")

        await page.close()
        await context.close()
        await browser.close()

        # 更新数据库
        await _update_database(4, id, f"cookies/{uuid_v1}.json")
        status_queue.put("200")

# 小红书登录 - 基于原始实现
async def xiaohongshu_cookie_gen(id, status_queue):
    """小红书Cookie生成 - 基于原始实现"""
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()

        # 尝试设置初始化脚本
        try:
            from services.base_social_media import set_init_script
            context = await set_init_script(context)
        except ImportError:
            pass

        page = await context.new_page()
        await page.goto("https://creator.xiaohongshu.com/")
        await page.locator('img.css-wemwzq').click()

        img_locator = page.get_by_role("img").nth(2)
        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        original_url = page.url
        print("✅ 图片地址:", src)
        status_queue.put(src)
        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("✅ 监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("⏰ 监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None

        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 创建cookies目录 - 使用正确的绝对路径
        cookies_dir = BASE_DIR / "cookies"
        cookies_dir.mkdir(exist_ok=True)

        cookie_path = cookies_dir / f"{uuid_v1}.json"
        await context.storage_state(path=cookie_path)

        # 验证Cookie
        try:
            from services.auth_service import check_cookie
            result = await check_cookie(1, f"cookies/{uuid_v1}.json")
            if not result:
                status_queue.put("500")
                await page.close()
                await context.close()
                await browser.close()
                return None
        except Exception:
            print("⚠️ Cookie验证失败，但继续保存")

        await page.close()
        await context.close()
        await browser.close()

        # 更新数据库
        await _update_database(1, id, f"cookies/{uuid_v1}.json")
        status_queue.put("200")

# 微信视频号登录 - 基于原始实现
async def wechat_cookie_gen(id, status_queue):
    """微信视频号Cookie生成 - 基于原始实现"""
    url_changed_event = asyncio.Event()

    async def on_url_change():
        # 检查是否是主框架的变化
        if page.url != original_url:
            url_changed_event.set()

    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()

        # 尝试设置初始化脚本
        try:
            from services.base_social_media import set_init_script
            context = await set_init_script(context)
        except ImportError:
            pass

        page = await context.new_page()
        await page.goto("https://channels.weixin.qq.com")
        original_url = page.url

        # 监听页面的 'framenavigated' 事件，只关注主框架的变化
        page.on('framenavigated',
                lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

        # 等待 iframe 出现（最多等 60 秒）
        iframe_locator = page.frame_locator("iframe").first

        # 获取 iframe 中的第一个 img 元素
        img_locator = iframe_locator.get_by_role("img").first

        # 获取 src 属性值
        src = await img_locator.get_attribute("src")
        print("✅ 图片地址:", src)
        status_queue.put(src)

        try:
            # 等待 URL 变化或超时
            await asyncio.wait_for(url_changed_event.wait(), timeout=200)  # 最多等待 200 秒
            print("✅ 监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("⏰ 监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None

        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 创建cookies目录 - 使用正确的绝对路径
        cookies_dir = BASE_DIR / "cookies"
        cookies_dir.mkdir(exist_ok=True)

        cookie_path = cookies_dir / f"{uuid_v1}.json"
        await context.storage_state(path=cookie_path)

        # 验证Cookie
        try:
            from services.auth_service import check_cookie
            result = await check_cookie(2, f"cookies/{uuid_v1}.json")
            if not result:
                status_queue.put("500")
                await page.close()
                await context.close()
                await browser.close()
                return None
        except Exception:
            print("⚠️ Cookie验证失败，但继续保存")

        await page.close()
        await context.close()
        await browser.close()

        # 更新数据库
        await _update_database(2, id, f"cookies/{uuid_v1}.json")
        status_queue.put("200")

async def _update_database(platform_type: int, account_id: str, cookie_path: str):
    """更新数据库记录"""
    try:
        import sqlite3
        from pathlib import Path

        # 查找数据库文件
        db_path = Path("accounts.db")
        if not db_path.exists():
            print("⚠️ 数据库文件不存在")
            return

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # 检查账号是否已存在
            cursor.execute("SELECT id FROM user_info WHERE userName = ?", (account_id,))
            existing = cursor.fetchone()

            if existing:
                # 更新现有账号
                cursor.execute('''
                UPDATE user_info
                SET type = ?, filePath = ?, status = 1
                WHERE userName = ?
                ''', (platform_type, cookie_path, account_id))
                print(f"✅ 更新现有账号: {account_id}")
            else:
                # 插入新账号
                cursor.execute('''
                INSERT INTO user_info (type, filePath, userName, status)
                VALUES (?, ?, ?, 1)
                ''', (platform_type, cookie_path, account_id))
                print(f"✅ 添加新账号: {account_id}")

            conn.commit()

    except Exception as e:
        print(f"[!] 更新数据库失败: {str(e)}")

# 平台登录函数映射
PLATFORM_LOGIN_FUNCS = {
    1: xiaohongshu_cookie_gen,  # 小红书
    2: wechat_cookie_gen,       # 微信视频号
    3: douyin_cookie_gen,       # 抖音
    4: ks_cookie_gen            # 快手
}

class LoginService:
    def __init__(self):
        self.active_queues = {}

    async def start_login_process(self, platform_type: str, account_id: str, status_queue: Queue):
        """启动登录流程"""
        platform_type = int(platform_type)
        login_func = PLATFORM_LOGIN_FUNCS.get(platform_type)

        if not login_func:
            print(f"[!] 未知平台类型: {platform_type}")
            status_queue.put("500")
            return

        platform_names = {1: "小红书", 2: "微信视频号", 3: "抖音", 4: "快手"}
        platform_name = platform_names.get(platform_type, f"平台{platform_type}")
        print(f"🚀 开始 {platform_name} 登录流程: {account_id}")

        try:
            await login_func(account_id, status_queue)
            print(f"✅ {platform_name} 登录流程完成")
        except Exception as e:
            print(f"[!] {platform_name} 登录流程异常: {str(e)}")
            status_queue.put("500")

    def get_queue(self, account_id: str):
        """获取指定账号的状态队列"""
        if account_id not in self.active_queues:
            self.active_queues[account_id] = Queue()
        return self.active_queues[account_id]

    def remove_queue(self, account_id: str):
        """移除指定账号的队列"""
        if account_id in self.active_queues:
            del self.active_queues[account_id]

# 全局登录服务实例
login_service = LoginService()

async def run_login_process(platform_type: str, account_id: str, status_queue: Queue):
    """运行登录流程的包装函数"""
    await login_service.start_login_process(platform_type, account_id, status_queue)

# 测试函数 - 测试抖音账号13784855457
async def test_douyin_login():
    """测试抖音登录功能"""
    print("🧪 测试抖音登录功能...")

    # 创建测试队列
    test_queue = Queue()

    # 启动抖音登录流程
    await login_service.start_login_process("3", "13784855457", test_queue)

    print("✅ 抖音登录测试完成")

if __name__ == "__main__":
    asyncio.run(test_douyin_login())