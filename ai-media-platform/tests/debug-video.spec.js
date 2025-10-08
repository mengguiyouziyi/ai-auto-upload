const { test, expect } = require('@playwright/test');

test('调试视频生成页面', async ({ page }) => {
  console.log('开始调试视频生成页面...');

  // 访问页面
  await page.goto('http://localhost:5174/#/video-generate');
  await page.waitForTimeout(3000);

  // 截图查看页面状态
  await page.screenshot({ path: 'debug-page-1.png' });
  console.log('截图1: 页面加载状态');

  // 尝试查找页面元素
  try {
    const videoGenTitle = await page.locator('text=AI视频生成').isVisible();
    console.log('AI视频生成标题可见:', videoGenTitle);
  } catch (error) {
    console.log('找不到AI视频生成标题');
  }

  // 尝试不同的选择器
  const selectors = [
    'select',
    'el-select',
    '.el-select',
    '[data-testid*="provider"]',
    'select:has-text("本地GPU")',
    'select:has-text("提供商")'
  ];

  for (const selector of selectors) {
    try {
      const element = await page.locator(selector).first();
      if (await element.isVisible()) {
        console.log(`找到选择器: ${selector}`);

        // 尝试选择选项
        try {
          await element.selectOption({ label: '本地GPU (免费)' });
          console.log('成功选择本地GPU选项');
          break;
        } catch (error) {
          console.log(`选择器 ${selector} 无法选择选项:`, error.message);
        }
      }
    } catch (error) {
      console.log(`选择器 ${selector} 不可见`);
    }
  }

  // 查找文本输入框
  const textSelectors = [
    'textarea',
    'input[type="text"]',
    '.el-textarea',
    'textarea:has-text("视频描述")',
    '[placeholder*="视频描述"]',
    '[placeholder*="描述"]'
  ];

  for (const selector of textSelectors) {
    try {
      const element = await page.locator(selector).first();
      if (await element.isVisible()) {
        console.log(`找到文本输入框: ${selector}`);

        try {
          await element.fill('测试视频生成');
          console.log('成功输入测试文本');
          break;
        } catch (error) {
          console.log(`文本框 ${selector} 无法输入:`, error.message);
        }
      }
    } catch (error) {
      console.log(`文本框 ${selector} 不可见`);
    }
  }

  // 查找生成按钮
  const buttonSelectors = [
    'button:has-text("生成视频")',
    'button[type="submit"]',
    '.el-button--primary',
    'button:has-text("生成")'
  ];

  for (const selector of buttonSelectors) {
    try {
      const element = await page.locator(selector).first();
      if (await element.isVisible()) {
        console.log(`找到生成按钮: ${selector}`);

        // 尝试点击按钮
        try {
          await element.click();
          console.log('成功点击生成按钮');

          // 等待一下看是否有响应
          await page.waitForTimeout(5000);

          // 截图
          await page.screenshot({ path: 'debug-after-click.png' });
          console.log('截图2: 点击按钮后状态');

          break;
        } catch (error) {
          console.log(`按钮 ${selector} 无法点击:`, error.message);
        }
      }
    } catch (error) {
      console.log(`按钮 ${selector} 不可见`);
    }
  }

  // 检查页面控制台错误
  const consoleMessages = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('控制台错误:', msg.text());
      consoleMessages.push(msg.text());
    }
  });

  await page.waitForTimeout(3000);

  if (consoleMessages.length > 0) {
    console.log('发现控制台错误:', consoleMessages);
  } else {
    console.log('没有发现控制台错误');
  }

  // 最终截图
  await page.screenshot({ path: 'debug-final.png' });
  console.log('最终截图已保存');
});