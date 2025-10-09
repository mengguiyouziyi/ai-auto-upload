#!/usr/bin/env python3
"""
截图发布中心界面，用于分析当前UI状态
"""

from playwright.async_api import async_playwright
import asyncio
import time

BASE_URL = "http://localhost:5175"

async def screenshot_publish_center():
    """截图发布中心界面"""
    print("🖼️ 开始截图发布中心界面...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        try:
            page = await context.new_page()
            await page.goto(BASE_URL)
            await page.wait_for_load_state('networkidle')

            # 等待页面完全加载
            await page.wait_for_timeout(3000)

            # 截图首页
            await page.screenshot(path="publish_center_homepage.png", full_page=True)
            print("✅ 首页截图完成: publish_center_homepage.png")

            # 进入发布中心
            try:
                publish_menu = await page.wait_for_selector('text=发布中心', timeout=10000)
                await publish_menu.click()
                await page.wait_for_timeout(2000)

                # 截图发布中心页面
                await page.screenshot(path="publish_center_page.png", full_page=True)
                print("✅ 发布中心页面截图完成: publish_center_page.png")

                # 尝试展开更多UI元素
                # 点击抖音平台
                douyin_elements = await page.query_selector_all('text=抖音')
                if douyin_elements:
                    await douyin_elements[0].click()
                    await page.wait_for_timeout(1000)
                    print("✅ 已选择抖音平台")

                # 再次截图平台选择后的状态
                await page.screenshot(path="publish_center_after_platform_select.png", full_page=True)
                print("✅ 平台选择后截图完成: publish_center_after_platform_select.png")

                # 等待几秒钟观察界面
                print("⏱️ 等待5秒观察界面...")
                await page.wait_for_timeout(5000)

            except Exception as e:
                print(f"❌ 进入发布中心失败: {str(e)}")

        except Exception as e:
            print(f"❌ 截图过程中发生异常: {str(e)}")
            import traceback
            traceback.print_exc()

        finally:
            await browser.close()
            print("🎯 截图任务完成")

if __name__ == "__main__":
    asyncio.run(screenshot_publish_center())