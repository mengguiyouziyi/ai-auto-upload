"""
抖音上传模块 - 严格按照social-auto-upload方式
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

try:
    from playwright.async_api import async_playwright, Playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    logger.warning("Playwright未安装，将无法执行抖音上传")
    PLAYWRIGHT_AVAILABLE = False

# 设置路径以便导入social-auto-upload的模块
sys.path.append(str(Path(__file__).parent.parent.parent.parent / "social-auto-upload"))

try:
    from utils.base_social_media import set_init_script
    from utils.log import douyin_logger
    from conf import LOCAL_CHROME_PATH
    SOCIAL_AUTO_UPLOAD_AVAILABLE = True
except ImportError as e:
    logger.warning(f"无法导入social-auto-upload模块: {e}")
    SOCIAL_AUTO_UPLOAD_AVAILABLE = False


async def set_init_script(context):
    """设置初始化脚本，模拟真实浏览器环境"""
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });

        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });

        window.chrome = {
            runtime: {},
        };

        Object.defineProperty(navigator, 'languages', {
            get: () => ['zh-CN', 'zh', 'en'],
        });
    """)


async def cookie_auth(account_file):
    """验证cookie是否有效 - 按照social-auto-upload方式"""
    if not PLAYWRIGHT_AVAILABLE:
        return False

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=account_file)
        context = await set_init_script(context)
        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        try:
            await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)
        except:
            print("[+] 等待5秒 cookie 失效")
            await context.close()
            await browser.close()
            return False
        # 2024.06.17 抖音创作者中心改版
        if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
            print("[+] 等待5秒 cookie 失效")
            return False
        else:
            print("[+] cookie 有效")
            return True


async def douyin_setup(account_file, handle=False):
    """设置抖音账号 - 按照social-auto-upload方式"""
    if not os.path.exists(account_file) or not await cookie_auth(account_file):
        if not handle:
            # Todo alert message
            return False
        logger.info('[+] cookie文件不存在或已失效，即将自动打开浏览器，请扫码登录，登陆后会自动生成cookie文件')
        await douyin_cookie_gen(account_file)
    return True


async def douyin_cookie_gen(account_file):
    """生成抖音cookie - 按照social-auto-upload方式"""
    async with async_playwright() as playwright:
        options = {
            'headless': False,
        }

        # 检查本地Chrome路径
        local_chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        if os.path.exists(local_chrome_path):
            options['executable_path'] = local_chrome_path

        browser = await playwright.chromium.launch(**options)
        context = await browser.new_context()
        context = await set_init_script(context)

        page = await context.new_page()
        await page.goto("https://creator.douyin.com/")
        await page.pause()
        # 点击调试器的继续，保存cookie
        await context.storage_state(path=account_file)


class DouYinVideo(object):
    """抖音视频上传器 - 完全按照social-auto-upload模式"""

    def __init__(self, title, file_path, tags, publish_date: datetime, account_file, thumbnail_path=None):
        self.title = title  # 视频标题
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.date_format = '%Y年%m月%d日 %H:%M'
        self.local_executable_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        self.thumbnail_path = thumbnail_path

    async def set_schedule_time(self, page, publish_date):
        """设置定时发布时间 - 按照social-auto-upload方式"""
        # 选择包含特定文本内容的 label 元素
        label_element = page.locator("[class^='radio']:has-text('定时发布')")
        # 在选中的 label 元素下点击 checkbox
        await label_element.click()
        await asyncio.sleep(1)
        publish_date_hour = publish_date.strftime("%Y-%m-%d %H:%M")

        await asyncio.sleep(1)
        await page.locator('.semi-input[placeholder="日期和时间"]').click()
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.type(str(publish_date_hour))
        await page.keyboard.press("Enter")

        await asyncio.sleep(1)

    async def handle_upload_error(self, page):
        """处理上传错误 - 按照social-auto-upload方式"""
        logger.info('视频出错了，重新上传中')
        await page.locator('div.progress-div [class^="upload-btn-input"]').set_input_files(self.file_path)

    async def main(self) -> None:
        """主上传方法 - 完全按照social-auto-upload方式"""
        # 使用 Chromium 浏览器启动一个浏览器实例
        if self.local_executable_path:
            browser = await playwright.chromium.launch(headless=False, executable_path=self.local_executable_path)
        else:
            browser = await playwright.chromium.launch(headless=False)
        # 创建一个浏览器上下文，使用指定的 cookie 文件
        context = await browser.new_context(storage_state=f"{self.account_file}")
        context = await set_init_script(context)

        # 创建一个新的页面
        page = await context.new_page()
        # 访问指定的 URL
        await page.goto("https://creator.douyin.com/creator-micro/content/upload")
        logger.info(f'[+]正在上传-------{self.title}.mp4')
        # 等待页面跳转到指定的 URL，没进入，则自动等待到超时
        logger.info(f'[-] 正在打开主页...')
        await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload")

        # 等待页面完全加载 (React应用需要更多时间)
        logger.info("[-] 等待页面完全加载...")
        await asyncio.sleep(5)

        # 检查页面是否需要登录或显示其他内容
        try:
            # 检查是否在登录页面
            if await page.locator("text=扫码登录").count() > 0:
                logger.error("[!] 检测到登录页面，cookie可能已失效")
                raise Exception("Cookie已失效，需要重新登录")

            # 检查页面标题
            title = await page.title()
            logger.info(f"[-] 当前页面标题: {title}")

            # 尝试等待上传区域出现
            await page.wait_for_selector("body", timeout=10000)
            logger.info("[-] 页面基础加载完成")

        except Exception as e:
            logger.error(f"[-] 页面检查失败: {str(e)}")

        # 点击 "上传视频" 按钮
        # 尝试多种可能的上传输入框选择器 (2025年10月更新)
        upload_selectors = [
            # 优先尝试现代上传组件选择器
            "input[type='file'][accept*='video']",
            "input[type='file'][accept*='mp4']",
            "input[type='file'][accept*='video/*']",
            # React组件常见的class命名
            ".upload-input input[type='file']",
            ".upload-zone input[type='file']",
            ".upload-area input[type='file']",
            ".upload-container input[type='file']",
            ".video-upload input[type='file']",
            # 通用容器选择器
            "div[class*='upload'] input[type='file']",
            "div[class*='Upload'] input[type='file']",
            "div[class*='container'] input[type='file']",
            "div[class*='zone'] input[type='file']",
            # 抖音特定组件
            "div[class*='creator'] input[type='file']",
            "div[class*='content'] input[type='file']",
            # 最通用的选择器
            "input[type='file']",
            # 通过文本找到上传区域然后查找内部input
            "text=上传视频 >> .. >> input[type='file']",
            "text=选择视频 >> .. >> input[type='file']",
            "text=发布视频 >> .. >> input[type='file']"
        ]

        upload_success = False
        for selector in upload_selectors:
            try:
                await page.wait_for_selector(selector, timeout=2000)
                await page.locator(selector).set_input_files(self.file_path)
                logger.info(f"[+] 使用选择器 '{selector}' 成功上传文件")
                upload_success = True
                break
            except Exception as e:
                logger.info(f"[-] 选择器 '{selector}' 失败: {str(e)}")
                continue

        if not upload_success:
            # 最后尝试原始选择器，但添加更具体的条件
            try:
                file_inputs = await page.locator("div[class^='container'] input[type='file']").count()
                if file_inputs > 0:
                    await page.locator("div[class^='container'] input[type='file']").first.set_input_files(self.file_path)
                    logger.info("[+] 使用备选选择器成功上传文件")
                    upload_success = True
                else:
                    raise Exception("未找到文件上传输入框")
            except Exception as e:
                logger.error(f"[!] 所有上传选择器都失败: {str(e)}")
                raise Exception(f"无法找到上传输入框: {str(e)}")

        # 等待页面跳转到指定的 URL 2025.01.08修改在原有基础上兼容两种页面
        while True:
            try:
                # 尝试等待第一个 URL
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/publish?enter_from=publish_page", timeout=3000)
                logger.info("[+] 成功进入version_1发布页面!")
                break  # 成功进入页面后跳出循环
            except Exception:
                try:
                    # 如果第一个 URL 超时，再尝试等待第二个 URL
                    await page.wait_for_url(
                        "https://creator.douyin.com/creator-micro/content/post/video?enter_from=publish_page",
                        timeout=3000)
                    logger.info("[+] 成功进入version_2发布页面!")

                    break  # 成功进入页面后跳出循环
                except Exception:
                    # 如果两个 URL 都超时，继续等待
                    logger.info("[-] 等待页面跳转中...")
                    await asyncio.sleep(2)
                    continue

        # 等待页面加载
        await asyncio.sleep(5)

        # 填写标题
        try:
            title_selectors = [
                "input[placeholder*='标题']",
                "textarea[placeholder*='标题']",
                "input[placeholder*='作品标题']",
                ".title-input input",
                ".video-title input"
            ]

            title_filled = False
            for selector in title_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    await page.locator(selector).fill(self.title)
                    logger.info(f"[+] 使用选择器 '{selector}' 成功填写标题")
                    title_filled = True
                    break
                except Exception as e:
                    logger.info(f"[-] 标题选择器 '{selector}' 失败: {str(e)}")
                    continue

            if not title_filled:
                logger.warning("[!] 无法找到标题输入框")
        except Exception as e:
            logger.warning(f"[!] 填写标题失败: {str(e)}")

        # 填写描述
        try:
            desc_selectors = [
                "textarea[placeholder*='描述']",
                "textarea[placeholder*='简介']",
                "textarea[placeholder*='作品简介']",
                ".desc-input textarea",
                ".video-desc textarea"
            ]

            desc_filled = False
            description = f"{self.title}\n{' '.join(self.tags)}"
            for selector in desc_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    await page.locator(selector).fill(description)
                    logger.info(f"[+] 使用选择器 '{selector}' 成功填写描述")
                    desc_filled = True
                    break
                except Exception as e:
                    logger.info(f"[-] 描述选择器 '{selector}' 失败: {str(e)}")
                    continue

            if not desc_filled:
                logger.warning("[!] 无法找到描述输入框")
        except Exception as e:
            logger.warning(f"[!] 填写描述失败: {str(e)}")

        # 设置定时发布
        if self.publish_date:
            await self.set_schedule_time(page, self.publish_date)

        # 发布视频
        try:
            publish_selectors = [
                "button:has-text('发布')",
                "button:has-text('立即发布')",
                "button:has-text('提交')",
                ".publish-button button",
                ".submit-button button"
            ]

            for selector in publish_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    await page.locator(selector).click()
                    logger.info(f"[+] 使用选择器 '{selector}' 成功点击发布")
                    break
                except Exception as e:
                    logger.info(f"[-] 发布按钮选择器 '{selector}' 失败: {str(e)}")
                    continue

            logger.info("[+] 视频发布成功")
            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"[!] 发布失败: {str(e)}")
            raise

        # 关闭浏览器
        await context.close()
        await browser.close()


# 兼容性接口
class DouYinVideoUploader:
    """兼容性包装器"""

    def __init__(self, account_file: str, headless: bool = False):
        self.account_file = account_file
        self.headless = headless
        self.local_executable_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    async def upload_video(self, title: str, file_path: str, tags: List[str],
                         publish_date: Optional[datetime] = None,
                         thumbnail_path: Optional[str] = None) -> bool:
        """兼容性上传方法"""
        try:
            # 创建social-auto-upload格式的对象
            video_obj = DouYinVideo(
                title=title,
                file_path=file_path,
                tags=tags,
                publish_date=publish_date or datetime.now(),
                account_file=self.account_file,
                thumbnail_path=thumbnail_path
            )

            # 使用playwright包装
            async with async_playwright() as playwright:
                # 修改main方法以接受playwright参数
                video_obj.playwright = playwright
                await video_obj.main()

            return True
        except Exception as e:
            logger.error(f"上传失败: {e}")
            return False