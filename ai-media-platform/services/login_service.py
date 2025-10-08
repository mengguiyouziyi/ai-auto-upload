#!/usr/bin/env python3
"""
实际登录服务 - 完全复制social-auto-upload的Playwright登录实现
"""

import asyncio
import uuid
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright
from queue import Queue
from services.base_social_media import set_init_script
from services.auth_service import check_cookie

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent

# 抖音登录 - 修复版本的实现
async def douyin_cookie_gen(id, status_queue):
    """抖音Cookie生成 - 修复URL检测问题"""
    url_changed_event = asyncio.Event()
    login_success = False

    async def on_url_change():
        """修复URL变化检测逻辑"""
        try:
            current_url = page.url
            if current_url != original_url:
                print(f"🔗 URL变化检测: {original_url} -> {current_url}")
                url_changed_event.set()
        except Exception as e:
            print(f"[!] URL检测异常: {str(e)}")

    async def check_login_success():
        """检查登录成功的多种方法 - 更严格的版本"""
        try:
            current_url = page.url
            print(f"🔍 检查登录状态, 当前URL: {current_url}")

            # 方法1: 检查URL变化到明确的成功页面
            if current_url != original_url:
                # 检查是否跳转到创作者中心或其他成功页面
                success_patterns = [
                    "creator-micro",
                    "content/upload",
                    "/publish",
                    "/studio"
                ]
                if any(pattern in current_url for pattern in success_patterns):
                    print("✅ 方法1: URL跳转到成功页面")
                    return True
                else:
                    print(f"⚠️ URL已变化但不是成功页面: {current_url}")

            # 方法2: 检查是否有明确的用户登录元素
            try:
                # 检查是否有用户头像、用户名等明确的登录标识
                user_elements = await page.query_selector_all(
                    '[class*="avatar"], [class*="user-name"], [class*="nickname"], '
                    '[class*="user-info"], [data-testid*="user"], img[alt*="头像"]'
                )
                if user_elements:
                    # 进一步验证元素是否真的可见
                    visible_elements = []
                    for element in user_elements:
                        try:
                            if await element.is_visible():
                                visible_elements.append(element)
                        except:
                            pass

                    if visible_elements:
                        print(f"✅ 方法2: 找到 {len(visible_elements)} 个可见的用户元素")
                        return True
            except Exception as e:
                print(f"[!] 方法2异常: {str(e)}")

            # 方法3: 检查二维码是否真的消失且页面发生变化
            try:
                qr_elements = await page.query_selector_all('img[alt*="二维码"], img[src*="qr"], .qrcode')

                # 检查页面标题是否改变
                current_title = await page.title()

                # 如果二维码消失且页面标题不是登录页标题，可能登录成功
                if not qr_elements and "登录" not in current_title:
                    print("✅ 方法3: 二维码消失且页面标题无'登录'")
                    return True
                elif qr_elements:
                    print(f"⚠️ 仍存在 {len(qr_elements)} 个二维码元素")

            except Exception as e:
                print(f"[!] 方法3异常: {str(e)}")

            # 方法4: 检查是否有登录按钮消失
            try:
                login_buttons = await page.query_selector_all(
                    'button:has-text("登录"), .login-btn, [class*="login"]'
                )
                if not login_buttons:
                    print("✅ 方法4: 登录按钮消失")
                    return True
                else:
                    print(f"⚠️ 仍存在 {len(login_buttons)} 个登录按钮")
            except:
                pass

            print(f"❌ 所有登录检测方法均未通过")
            return False

        except Exception as e:
            print(f"[!] 登录检查异常: {str(e)}")
            return False

    async with async_playwright() as playwright:
        options = {
            'headless': False
        }
        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()
        context = await set_init_script(context)
        page = await context.new_page()

        try:
            print(f"🚀 开始抖音登录流程: {id}")

            # 访问抖音创作者中心
            await page.goto("https://creator.douyin.com/")
            await page.wait_for_load_state('networkidle')
            original_url = page.url
            print(f"📄 初始URL: {original_url}")

            # 查找二维码元素 - 使用当前抖音页面的正确选择器
            print("🔍 查找二维码元素...")

            # 尝试多种选择器来找到二维码
            qr_selectors = [
                'img[class*="qrcode_img"]',
                '[class*="qr"] img',
                'img[src*="qr"]'
            ]

            img_locator = None
            src = None

            for selector in qr_selectors:
                try:
                    print(f"   尝试选择器: {selector}")
                    img_locator = page.locator(selector).first
                    if await img_locator.count() > 0:
                        src = await img_locator.get_attribute("src")
                        if src and (src.startswith('data:') or 'qr' in src.lower()):
                            print(f"   ✅ 找到二维码，使用选择器: {selector}")
                            break
                except Exception as e:
                    print(f"   ❌ 选择器失败 {selector}: {str(e)}")
                    continue

            # 尝试获取二维码
            try:
                if not src and img_locator:
                    src = await img_locator.get_attribute("src")
                if src:
                    print(f"✅ 图片地址: {src[:50]}...")
                    status_queue.put(src)
                else:
                    print("⚠️ 二维码src属性为空")
                    status_queue.put("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")
            except Exception as e:
                print(f"⚠️ 获取二维码失败: {str(e)}")
                status_queue.put("data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

            # 监听页面导航事件
            page.on('framenavigated', lambda frame: asyncio.create_task(on_url_change()) if frame == page.main_frame else None)

            print("⏳ 等待用户扫码登录（最多200秒）...")
            print("💡 请在手机抖音App中扫描二维码完成登录")

            # 使用轮询检查登录状态
            start_time = asyncio.get_event_loop().time()
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time

                if elapsed > 200:  # 200秒超时
                    print("⏰ 登录超时")
                    break

                # 检查登录是否成功
                if await check_login_success():
                    login_success = True
                    break

                await asyncio.sleep(2)  # 每2秒检查一次

            if login_success:
                print("✅ 登录成功！正在保存Cookie...")

                uuid_v1 = uuid.uuid1()
                print(f"UUID v1: {uuid_v1}")

                # 创建cookies目录
                cookies_dir = Path("cookies")
                cookies_dir.mkdir(exist_ok=True)

                # 保存Cookie
                await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
                print(f"💾 Cookie已保存: cookies/{uuid_v1}.json")

                # 验证Cookie
                print("🔍 验证Cookie有效性...")
                result = await check_cookie(3, f"cookies/{uuid_v1}.json")
                if result:
                    print("✅ Cookie验证成功")

                    # 更新数据库
                    await _update_database(3, id, f"cookies/{uuid_v1}.json")
                    status_queue.put("200")
                    print(f"🎉 账号 {id} 添加成功！")
                else:
                    print("❌ Cookie验证失败")
                    status_queue.put("500")
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

# 快手登录 - 复制GitHub版本实现
async def ks_cookie_gen(id, status_queue):
    """快手Cookie生成 - 复制自social-auto-upload GitHub版本"""
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
        context = await set_init_script(context)
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
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 创建cookies目录
        cookies_dir = Path("cookies")
        cookies_dir.mkdir(exist_ok=True)

        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(4, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        # 更新数据库
        await _update_database(4, id, f"cookies/{uuid_v1}.json")
        status_queue.put("200")

# 小红书登录 - 复制GitHub版本实现
async def xiaohongshu_cookie_gen(id, status_queue):
    """小红书Cookie生成 - 复制自social-auto-upload GitHub版本"""
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
        context = await set_init_script(context)
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
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 创建cookies目录
        cookies_dir = Path("cookies")
        cookies_dir.mkdir(exist_ok=True)

        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(1, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
        await page.close()
        await context.close()
        await browser.close()

        # 更新数据库
        await _update_database(1, id, f"cookies/{uuid_v1}.json")
        status_queue.put("200")

# 微信视频号登录 - 复制GitHub版本实现
async def wechat_cookie_gen(id, status_queue):
    """微信视频号Cookie生成 - 复制自social-auto-upload GitHub版本"""
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
        context = await set_init_script(context)
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
            print("监听页面跳转成功")
        except asyncio.TimeoutError:
            status_queue.put("500")
            print("监听页面跳转超时")
            await page.close()
            await context.close()
            await browser.close()
            return None
        uuid_v1 = uuid.uuid1()
        print(f"UUID v1: {uuid_v1}")

        # 创建cookies目录
        cookies_dir = Path("cookies")
        cookies_dir.mkdir(exist_ok=True)

        await context.storage_state(path=cookies_dir / f"{uuid_v1}.json")
        result = await check_cookie(2, f"{uuid_v1}.json")
        if not result:
            status_queue.put("500")
            await page.close()
            await context.close()
            await browser.close()
            return None
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