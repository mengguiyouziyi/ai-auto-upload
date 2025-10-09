# -*- coding: utf-8 -*-
from datetime import datetime
from playwright.async_api import Playwright, async_playwright, Page
import os
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent.parent))

class DouYinVideo(object):
    def __init__(self, title, file_path, tags, publish_date: datetime, account_file, thumbnail_path=None):
        self.title = title  # 视频标题
        self.file_path = file_path
        self.tags = tags
        self.publish_date = publish_date
        self.account_file = account_file
        self.date_format = '%Y年%m月%d日 %H:%M'
        self.thumbnail_path = thumbnail_path

    async def set_schedule_time_douyin(self, page, publish_date):
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
        print('[+] 视频出错了，重新上传中')
        await page.locator('div.progress-div [class^="upload-btn-input"]').set_input_files(self.file_path)

    async def upload(self, playwright: Playwright) -> None:
        print(f"[+] 开始上传视频到抖音: {self.title}")

        # 使用 Chromium 浏览器启动一个浏览器实例
        browser = await playwright.chromium.launch(headless=False)

        # 检查账号文件是否存在
        if not os.path.exists(self.account_file):
            print(f"[!] 错误: 账号文件不存在: {self.account_file}")
            # 创建一个空的cookie文件结构
            os.makedirs(os.path.dirname(self.account_file), exist_ok=True)
            with open(self.account_file, 'w') as f:
                f.write('{"cookies": [], "origins": []}')

        # 创建一个浏览器上下文，使用指定的 cookie 文件
        try:
            context = await browser.new_context(storage_state=self.account_file)
        except Exception as e:
            print(f"[!] Cookie文件格式错误，使用新上下文: {e}")
            context = await browser.new_context()

        # 创建一个新的页面
        page = await context.new_page()

        try:
            # 访问指定的 URL
            await page.goto("https://creator.douyin.com/creator-micro/content/upload")
            print(f"[-] 正在打开抖音创作者中心...")

            # 等待页面跳转到指定的 URL，没进入，则自动等待到超时
            try:
                await page.wait_for_url("https://creator.douyin.com/creator-micro/content/upload", timeout=10000)
            except:
                print("[-] 页面跳转超时，继续尝试...")

            # 等待页面完全加载 (React应用需要更多时间)
            print("[-] 等待页面完全加载...")
            await asyncio.sleep(5)

            # 检查页面是否需要登录
            try:
                # 检查是否在登录页面
                if await page.locator("text=扫码登录").count() > 0 or await page.locator("text=手机号登录").count() > 0:
                    print("[!] 检测到登录页面，需要手动登录")
                    print("[+] 请手动登录抖音，登录完成后按Enter继续...")
                    input("按Enter键继续...")

                    # 重新访问页面
                    await page.goto("https://creator.douyin.com/creator-micro/content/upload")
                    await asyncio.sleep(5)

                # 保存登录状态
                await context.storage_state(path=self.account_file)
                print("[-] 登录状态已保存")

            except Exception as e:
                print(f"[-] 页面检查失败: {str(e)}")

            # 点击 "上传视频" 按钮
            # 尝试多种可能的上传输入框选择器
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
            print(f"[-] 尝试上传文件: {self.file_path}")

            for selector in upload_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    await page.locator(selector).set_input_files(self.file_path)
                    print(f"[+] 使用选择器 '{selector}' 成功上传文件")
                    upload_success = True
                    break
                except Exception as e:
                    print(f"[-] 选择器 '{selector}' 失败: {str(e)}")
                    continue

            if not upload_success:
                # 最后尝试原始选择器
                try:
                    file_inputs = await page.locator("div[class^='container'] input[type='file']").count()
                    if file_inputs > 0:
                        await page.locator("div[class^='container'] input[type='file']").first.set_input_files(self.file_path)
                        print("[+] 使用备选选择器成功上传文件")
                        upload_success = True
                    else:
                        raise Exception("未找到文件上传输入框")
                except Exception as e:
                    print(f"[!] 所有上传选择器都失败: {str(e)}")
                    # 不抛出异常，继续执行后续步骤

            # 等待页面跳转到发布页面
            print("[-] 等待进入发布页面...")
            max_attempts = 20  # 最大尝试次数
            attempt = 0

            while attempt < max_attempts:
                try:
                    # 尝试等待第一个 URL
                    await page.wait_for_url(
                        "https://creator.douyin.com/creator-micro/content/publish?enter_from=publish_page", timeout=3000)
                    print("[+] 成功进入version_1发布页面!")
                    break  # 成功进入页面后跳出循环
                except Exception:
                    try:
                        # 如果第一个 URL 超时，再尝试等待第二个 URL
                        await page.wait_for_url(
                            "https://creator.douyin.com/creator-micro/content/post/video?enter_from=publish_page",
                            timeout=3000)
                        print("[+] 成功进入version_2发布页面!")
                        break  # 成功进入页面后跳出循环
                    except:
                        if attempt < max_attempts - 1:
                            print(f"  [-] 超时未进入视频发布页面，重新尝试... ({attempt + 1}/{max_attempts})")
                            await asyncio.sleep(1)  # 等待 1 秒后重新尝试
                        attempt += 1

            if attempt >= max_attempts:
                print("[!] 未能进入发布页面，但继续尝试填写表单")

            # 填充标题和话题
            await asyncio.sleep(2)
            print(f'[-] 正在填充标题和话题...')

            try:
                title_container = page.get_by_text('作品标题').locator("..").locator("xpath=following-sibling::div[1]").locator("input")
                if await title_container.count():
                    await title_container.fill(self.title[:30])
                    print(f"[+] 标题填写成功: {self.title[:30]}")
                else:
                    # 尝试其他方式填写标题
                    titlecontainer = page.locator(".notranslate")
                    if await titlecontainer.count():
                        await titlecontainer.click()
                        await page.keyboard.press("Backspace")
                        await page.keyboard.press("Control+KeyA")
                        await page.keyboard.press("Delete")
                        await page.keyboard.type(self.title)
                        await page.keyboard.press("Enter")
                        print(f"[+] 标题填写成功(备选方式): {self.title}")
            except Exception as e:
                print(f"[-] 标题填写失败: {e}")

            # 添加话题标签
            if self.tags:
                css_selector = ".zone-container"
                for index, tag in enumerate(self.tags, start=1):
                    try:
                        await page.type(css_selector, "#" + tag)
                        await page.press(css_selector, "Space")
                        print(f"[+] 添加话题 #{tag}")
                    except Exception as e:
                        print(f"[-] 添加话题失败 #{tag}: {e}")

            print(f'[-] 总共添加{len(self.tags) if self.tags else 0}个话题')

            # 等待视频上传完成
            print("[-] 等待视频上传完成...")
            upload_attempts = 0
            max_upload_attempts = 60  # 最大等待60次，每次2秒，总共2分钟

            while upload_attempts < max_upload_attempts:
                try:
                    # 判断重新上传按钮是否存在，如果不存在，代表视频正在上传，则等待
                    number = await page.locator('[class^="long-card"] div:has-text("重新上传")').count()
                    if number > 0:
                        print("[+] 视频上传完毕")
                        break
                    else:
                        if upload_attempts % 10 == 0:  # 每20秒打印一次
                            print("  [-] 正在上传视频中...")

                        # 检查是否有上传错误
                        if await page.locator('div.progress-div > div:has-text("上传失败")').count():
                            print("  [-] 发现上传出错了... 准备重试")
                            await self.handle_upload_error(page)

                    await asyncio.sleep(2)
                    upload_attempts += 1

                except Exception as e:
                    print(f"  [-] 上传检查异常: {e}")
                    await asyncio.sleep(2)
                    upload_attempts += 1

            if upload_attempts >= max_upload_attempts:
                print("[!] 视频上传超时，但继续尝试发布")

            # 设置定时发布
            if self.publish_date != 0:
                print("[-] 设置定时发布...")
                await self.set_schedule_time_douyin(page, self.publish_date)

            # 尝试发布视频
            print("[-] 尝试发布视频...")
            publish_attempts = 0
            max_publish_attempts = 30  # 最大尝试30次，每次1秒

            while publish_attempts < max_publish_attempts:
                try:
                    # 判断视频是否发布成功
                    publish_button = page.get_by_role('button', name="发布", exact=True)
                    if await publish_button.count():
                        await publish_button.click()
                        print("[+] 点击发布按钮")

                        # 等待跳转到管理页面
                        try:
                            await page.wait_for_url("https://creator.douyin.com/creator-micro/content/manage**", timeout=10000)
                            print("[+] 视频发布成功")
                            break
                        except:
                            print("[-] 等待跳转超时，继续尝试...")
                    else:
                        if publish_attempts % 10 == 0:  # 每10秒打印一次
                            print("  [-] 寻找发布按钮中...")
                except Exception as e:
                    if publish_attempts % 10 == 0:
                        print(f"  [-] 发布尝试异常: {e}")

                await asyncio.sleep(1)
                publish_attempts += 1

            if publish_attempts >= max_publish_attempts:
                print("[!] 发布超时或失败")

            # 保存cookie
            try:
                await context.storage_state(path=self.account_file)
                print("[-] Cookie更新完毕！")
            except Exception as e:
                print(f"[-] Cookie保存失败: {e}")

            await asyncio.sleep(2)  # 延迟便于观察

        except Exception as e:
            print(f"[!] 发布过程中出现错误: {e}")
            # 尝试截图保存错误状态
            try:
                await page.screenshot(full_page=True, path='error_douyin_upload.png')
                print("[-] 错误截图已保存: error_douyin_upload.png")
            except:
                pass

        finally:
            # 关闭浏览器上下文和浏览器实例
            try:
                await context.close()
                await browser.close()
                print("[-] 浏览器已关闭")
            except:
                pass

    async def main(self):
        async with async_playwright() as playwright:
            await self.upload(playwright)