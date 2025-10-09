"""
独立的抖音上传模块，不依赖social-auto-upload的复杂依赖
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


class DouYinVideoUploader:
    """抖音视频上传器"""

    def __init__(self, account_file: str, headless: bool = False):
        self.account_file = account_file
        self.headless = headless
        self.local_executable_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    async def cookie_auth(self) -> bool:
        """验证cookie是否有效"""
        if not PLAYWRIGHT_AVAILABLE:
            return False

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(storage_state=self.account_file)

            try:
                page = await context.new_page()
                await page.goto("https://creator.douyin.com/creator-micro/content/upload")
                await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=5000)

                # 检查是否需要登录
                if await page.get_by_text('手机号登录').count() or await page.get_by_text('扫码登录').count():
                    logger.warning("Cookie已失效，需要重新登录")
                    return False
                else:
                    logger.info("Cookie验证通过")
                    return True

            except Exception as e:
                logger.warning(f"Cookie验证失败: {e}")
                return False
            finally:
                await context.close()
                await browser.close()

  
    async def set_schedule_time(self, page: Page, publish_date: datetime):
        """设置定时发布时间"""
        try:
            # 选择定时发布选项
            label_element = page.locator("[class^='radio']:has-text('定时发布')")
            await label_element.click()
            await asyncio.sleep(1)

            publish_date_hour = publish_date.strftime("%Y-%m-%d %H:%M")
            await page.locator('.semi-input[placeholder="日期和时间"]').click()
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.type(str(publish_date_hour))
            await page.keyboard.press("Enter")

            await asyncio.sleep(1)
            logger.info(f"定时发布时间设置成功: {publish_date_hour}")
        except Exception as e:
            logger.warning(f"设置定时发布时间失败: {e}")

    async def handle_upload_error(self, page: Page):
        """处理上传错误"""
        logger.info('视频上传出错，正在重新上传...')
        try:
            await page.locator('div.progress-div [class^="upload-btn-input"]').set_input_files(self.file_path)
        except Exception as e:
            logger.error(f"重新上传失败: {e}")

    async def upload_video(self, title: str, file_path: str, tags: List[str],
                         publish_date: Optional[datetime] = None,
                         thumbnail_path: Optional[str] = None) -> bool:
        """上传视频到抖音"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright不可用，无法上传视频")
            return False

        self.file_path = file_path

        async with async_playwright() as playwright:
            # 启动浏览器
            if self.local_executable_path and Path(self.local_executable_path).exists():
                browser = await playwright.chromium.launch(
                    headless=self.headless,
                    executable_path=self.local_executable_path
                )
            else:
                browser = await playwright.chromium.launch(headless=self.headless)

            try:
                # 创建上下文
                context = await browser.new_context(storage_state=self.account_file)
                await set_init_script(context)

                page = await context.new_page()

                # 访问上传页面
                await page.goto("https://creator.douyin.com/creator-micro/content/upload")
                logger.info(f'正在上传视频: {title}')

                # 等待页面加载
                await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload")
                await asyncio.sleep(5)

                # 检查登录状态
                if await page.locator("text=扫码登录").count() > 0:
                    logger.error("检测到登录页面，cookie可能已失效")
                    return False

                # 上传视频文件 - 添加调试和更新的选择器
                logger.info("开始查找上传元素...")

                # 先打印页面内容用于调试
                try:
                    page_content = await page.content()
                    logger.info(f"当前页面URL: {page.url}")
                    # 查找所有包含"上传"的文本
                    upload_texts = await page.locator("text=上传").count()
                    logger.info(f"找到 {upload_texts} 个包含'上传'的元素")

                    # 查找所有file input
                    file_inputs = await page.locator("input[type='file']").count()
                    logger.info(f"找到 {file_inputs} 个file input元素")
                except Exception as e:
                    logger.warning(f"调试信息获取失败: {e}")

                upload_selectors = [
                    # 新的抖音创作者中心选择器
                    "input[type='file'][accept*='video']",
                    "input[type='file'][accept*='mp4']",
                    "input[type='file'][accept*='video/*']",
                    "input[type='file'][accept='.mp4,.mov,.avi']",
                    # 基于class的选择器
                    ".upload-input input[type='file']",
                    ".upload-zone input[type='file']",
                    ".upload-area input[type='file']",
                    ".upload-container input[type='file']",
                    "div[class*='upload'] input[type='file']",
                    "div[class*='Upload'] input[type='file']",
                    # 更通用的选择器
                    "input[type='file']",
                    # 尝试通过按钮文本查找
                    "text=上传视频 >> .. >> input[type='file']",
                    "text=点击上传 >> .. >> input[type='file']",
                    "text=选择视频 >> .. >> input[type='file']",
                    # 通过特定区域查找
                    "[class*='content'] input[type='file']",
                    "[class*='creator'] input[type='file']",
                    # 新的尝试 - 通过可见性
                    "input[type='file']:visible",
                    "input[type='file']:not([style*='display: none'])",
                    "input[type='file']:not([hidden])"
                ]

                upload_success = False
                for i, selector in enumerate(upload_selectors):
                    try:
                        logger.info(f"尝试选择器 {i+1}: {selector}")
                        element_count = await page.locator(selector).count()
                        logger.info(f"找到 {element_count} 个匹配元素")

                        if element_count > 0:
                            # 尝试设置文件
                            await page.locator(selector).first.set_input_files(file_path)
                            logger.info(f"使用选择器 '{selector}' 成功上传文件")
                            upload_success = True
                            break
                    except Exception as e:
                        logger.debug(f"选择器 '{selector}' 失败: {e}")
                        continue

                if not upload_success:
                    logger.error("所有上传选择器都失败")
                    # 尝试等待页面完全加载
                    logger.info("等待页面完全加载...")
                    await asyncio.sleep(3)

                    # 再次尝试最基本的选择器
                    try:
                        await page.locator("input[type='file']").first.set_input_files(file_path)
                        logger.info("使用基本选择器成功上传文件")
                        upload_success = True
                    except Exception as e:
                        logger.error(f"基本选择器也失败: {e}")
                        return False

                # 等待进入发布页面
                while True:
                    try:
                        await page.wait_for_url(
                            "https://creator.douyin.com/creator-micro/content/publish?enter_from=publish_page",
                            timeout=3000
                        )
                        logger.info("成功进入version_1发布页面")
                        break
                    except:
                        try:
                            await page.wait_for_url(
                                "https://creator.douyin.com/creator-micro/content/post/video?enter_from=publish_page",
                                timeout=3000
                            )
                            logger.info("成功进入version_2发布页面")
                            break
                        except:
                            await asyncio.sleep(0.5)

                # 填充标题和话题
                await asyncio.sleep(1)
                logger.info('正在填充标题和话题...')

                try:
                    title_container = page.get_by_text('作品标题').locator("..").locator("xpath=following-sibling::div[1]").locator("input")
                    if await title_container.count():
                        await title_container.fill(title[:30])
                    else:
                        titlecontainer = page.locator(".notranslate")
                        await titlecontainer.click()
                        await page.keyboard.press("Backspace")
                        await page.keyboard.press("Control+KeyA")
                        await page.keyboard.press("Delete")
                        await page.keyboard.type(title)
                        await page.keyboard.press("Enter")
                except Exception as e:
                    logger.warning(f"填充标题失败: {e}")

                # 添加话题标签
                css_selector = ".zone-container"
                for index, tag in enumerate(tags, start=1):
                    try:
                        await page.type(css_selector, "#" + tag)
                        await page.press(css_selector, "Space")
                    except Exception as e:
                        logger.warning(f"添加话题 {tag} 失败: {e}")

                logger.info(f'总共添加{len(tags)}个话题')

                # 等待视频上传完成
                while True:
                    try:
                        number = await page.locator('[class^="long-card"] div:has-text("重新上传")').count()
                        if number > 0:
                            logger.info("视频上传完毕")
                            break
                        else:
                            logger.info("正在上传视频中...")
                            await asyncio.sleep(2)

                            if await page.locator('div.progress-div > div:has-text("上传失败")').count():
                                logger.warning("发现上传出错，准备重试")
                                await self.handle_upload_error(page)
                    except:
                        logger.info("正在上传视频中...")
                        await asyncio.sleep(2)

                # 设置定时发布
                if publish_date and publish_date != 0:
                    await self.set_schedule_time(page, publish_date)

                # 发布视频
                while True:
                    try:
                        publish_button = page.get_by_role('button', name="发布", exact=True)
                        if await publish_button.count():
                            await publish_button.click()

                        await page.wait_for_url(
                            "https://creator.douyin.com/creator-micro/content/manage**",
                            timeout=3000
                        )
                        logger.success("视频发布成功")
                        return True

                    except Exception as e:
                        logger.info("视频正在发布中...")
                        await asyncio.sleep(0.5)

                # 保存cookie
                await context.storage_state(path=self.account_file)
                logger.info('Cookie更新完毕')

            except Exception as e:
                logger.error(f"上传视频失败: {e}")
                import traceback
                traceback.print_exc()
                return False
            finally:
                await browser.close()


async def generate_douyin_cookie(account_file: str) -> bool:
    """
    生成抖音Cookie，打开浏览器让用户登录

    Args:
        account_file: Cookie文件路径

    Returns:
        bool: 是否成功生成Cookie
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright不可用，无法生成Cookie")
        return False

    logger.info(f"开始生成抖音Cookie: {account_file}")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        try:
            context = await browser.new_context()
            await set_init_script(context)

            page = await context.new_page()
            await page.goto("https://creator.douyin.com/")

            logger.info("浏览器已打开，请扫码登录抖音创作者中心")
            logger.info("登录完成后，Cookie将自动保存")

            # 等待用户登录 - 这里简化处理，实际应该等待登录成功
            await page.wait_for_timeout(60000)  # 等待60秒

            # 保存Cookie
            await context.storage_state(path=account_file)
            logger.success(f"Cookie已保存到: {account_file}")
            return True

        except Exception as e:
            logger.error(f"生成Cookie失败: {e}")
            return False
        finally:
            await browser.close()


async def upload_douyin_video(title: str, file_list: List[str], tags: List[str],
                            account_list: List[str], category: int = 0,
                            enable_timer: bool = False, videos_per_day: int = 1,
                            daily_times: List[str] = None, start_days: int = 0,
                            auto_login: bool = False) -> bool:
    """
    抖音视频上传函数，兼容social-auto-upload的postVideo接口格式

    Args:
        title: 视频标题
        file_list: 视频文件路径列表
        tags: 话题标签列表
        account_list: 账号cookie文件列表
        category: 分类（暂未使用）
        enable_timer: 是否启用定时发布
        videos_per_day: 每天发布视频数量
        daily_times: 每天发布时间
        start_days: 开始天数
        auto_login: 是否自动处理登录（打开浏览器让用户登录）

    Returns:
        bool: 上传是否成功
    """
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright不可用，无法上传视频")
        return False

    # 获取基础路径
    base_dir = Path(__file__).resolve().parents[3] / "social-auto-upload"
    video_dir = base_dir / "videoFile"
    cookie_dir = base_dir / "cookiesFile"

    logger.info(f"开始抖音视频上传任务:")
    logger.info(f"  标题: {title}")
    logger.info(f"  视频文件: {file_list}")
    logger.info(f"  话题标签: {tags}")
    logger.info(f"  账号文件: {account_list}")
    logger.info(f"  定时发布: {enable_timer}")

    # 处理定时发布时间
    publish_dates = []
    if enable_timer:
        # 简单的定时发布逻辑
        from datetime import datetime, timedelta
        base_time = datetime.now() + timedelta(days=start_days)

        for i, file_path in enumerate(file_list):
            for time_str in daily_times[:videos_per_day]:
                hour, minute = map(int, time_str.split(':'))
                publish_time = base_time + timedelta(days=i, hours=hour, minutes=minute)
                publish_dates.append(publish_time)
    else:
        publish_dates = [None] * len(file_list)

    # 对每个视频和账号组合进行上传
    success_count = 0
    total_tasks = len(file_list) * len(account_list)

    for file_index, file_path in enumerate(file_list):
        full_file_path = video_dir / file_path
        if not full_file_path.exists():
            logger.error(f"视频文件不存在: {full_file_path}")
            continue

        publish_date = publish_dates[file_index] if file_index < len(publish_dates) else None

        for account_file in account_list:
            full_account_path = cookie_dir / account_file
            if not full_account_path.exists():
                logger.error(f"账号Cookie文件不存在: {full_account_path}")
                continue

            logger.info(f"正在上传: {file_path} -> {account_file}")

            uploader = DouYinVideoUploader(str(full_account_path), headless=False)

            # 验证cookie有效性
            cookie_valid = await uploader.cookie_auth()
            if not cookie_valid:
                if auto_login:
                    logger.info(f"账号 {account_file} 的Cookie已失效，尝试自动登录...")
                    # 尝试重新生成Cookie
                    if await generate_douyin_cookie(str(full_account_path)):
                        logger.info(f"账号 {account_file} 重新登录成功")
                        # 重新创建uploader对象
                        uploader = DouYinVideoUploader(str(full_account_path), headless=False)
                    else:
                        logger.error(f"账号 {account_file} 重新登录失败，跳过")
                        continue
                else:
                    logger.warning(f"账号 {account_file} 的Cookie已失效，跳过")
                    continue

            # 执行上传
            try:
                success = await uploader.upload_video(
                    title=title,
                    file_path=str(full_file_path),
                    tags=tags,
                    publish_date=publish_date
                )

                if success:
                    success_count += 1
                    logger.info(f"上传成功: {file_path} -> {account_file}")
                else:
                    logger.error(f"上传失败: {file_path} -> {account_file}")

            except Exception as e:
                logger.error(f"上传过程出错: {file_path} -> {account_file}, 错误: {e}")

            # 等待一段时间避免频繁操作
            await asyncio.sleep(2)

    logger.info(f"抖音上传任务完成: {success_count}/{total_tasks} 成功")
    return success_count > 0