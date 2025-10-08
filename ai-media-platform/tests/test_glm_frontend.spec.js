const { test, expect } = require('@playwright/test');

test.describe('AI媒体平台 - GLM-4.6文本优化功能测试', () => {
  let page;

  test.beforeAll(async ({ browser }) => {
    console.log('🚀 开始GLM-4.6前端测试...');
  });

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();
    // 监听网络请求
    await page.route('**/api/v1/llm/optimize-text', async route => {
      const request = route.request();
      const postData = request.postDataJSON();

      console.log(`📤 文本优化请求: ${postData.provider}`);
      console.log(`📝 原始文本长度: ${postData.text?.length || 0}`);

      // 继续发送请求
      const response = await route.fetch({
        postData: JSON.stringify(postData)
      });

      // 检查响应状态
      console.log(`📥 响应状态: ${response.status()}`);

      if (response.status() === 429) {
        console.log('⚠️  429速率限制错误');
      } else if (response.status() === 200) {
        const data = await response.json();
        console.log(`✅ 优化成功，结果长度: ${data.optimized_text?.length || 0}`);
      }

      // 返回响应
      await route.fulfill({
        response: response,
        status: response.status(),
        headers: response.headers(),
        body: await response.text()
      });
    });

    // 监听控制台错误
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`❌ 控制台错误: ${msg.text()}`);
      } else if (msg.type() === 'warning') {
        console.log(`⚠️  控制台警告: ${msg.text()}`);
      }
    });

    // 监听页面错误
    page.on('pageerror', error => {
      console.log(`🚨 页面错误: ${error.message}`);
    });
  });

  test.afterEach(async () => {
    if (page) {
      await page.close();
    }
  });

  test('基础功能 - 访问文本优化页面', async ({}) => {
    console.log('📍 测试: 访问AI媒体平台首页');

    // 访问前端页面
    await page.goto('http://localhost:5174');

    // 等待页面加载
    await page.waitForTimeout(2000);

    // 检查页面标题
    const title = await page.title();
    console.log(`📄 页面标题: ${title}`);

    // 截图
    await page.screenshot({ path: 'test-screenshots/homepage.png' });
    console.log('📸 首页截图已保存');

    // 检查是否包含关键元素
    const content = await page.content();
    expect(content).toContain('AI媒体智能平台');
  });

  test('文本优化 - GLM-4.6提供商', async ({}) => {
    console.log('📍 测试: GLM-4.6文本优化');

    // 访问页面
    await page.goto('http://localhost:5174');
    await page.waitForTimeout(3000);

    // 查找文本优化相关元素
    const optimizeButton = await page.locator('text=AI优化').first();
    if (await optimizeButton.isVisible()) {
      console.log('✅ 找到AI优化按钮');
      await optimizeButton.click();
      await page.waitForTimeout(1000);
    }

    // 查找LLM提供商选择器
    const providerSelect = await page.locator('select').first();
    if (await providerSelect.isVisible()) {
      console.log('✅ 找到提供商选择器');

      // 选择GLM
      await providerSelect.selectOption('glm');
      console.log('✅ 已选择GLM提供商');
    }

    // 查找文本输入框
    const textInput = await page.locator('textarea, input[type="text"]').first();
    if (await textInput.isVisible()) {
      console.log('✅ 找到文本输入框');

      // 输入测试文本
      const testText = `在AI编程工具竞争白热化的当下，OpenAI推出的Codex编程助手凭借三大核心优势，迅速在GitHub狂揽4万星标，成为开发者热议的焦点。`;
      await textInput.fill(testText);
      console.log('✅ 已输入测试文本');
    }

    // 截图当前状态
    await page.screenshot({ path: 'test-screenshots/before-optimization.png' });
    console.log('📸 优化前界面截图已保存');

    // 查找并点击优化按钮
    const buttons = await page.locator('button').all();
    let optimizeButtonFound = false;

    for (const button of buttons) {
      const buttonText = await button.textContent();
      if (buttonText && (buttonText.includes('优化') || buttonText.includes('生成'))) {
        console.log(`✅ 找到优化按钮: ${buttonText}`);
        await button.click();
        optimizeButtonFound = true;
        break;
      }
    }

    if (!optimizeButtonFound) {
      console.log('⚠️  未找到优化按钮，尝试其他方式...');
      // 尝试通过其他方式触发优化
      const anyButton = await page.locator('button').first();
      if (await anyButton.isVisible()) {
        await anyButton.click();
      }
    }

    // 等待优化结果
    console.log('⏳ 等待优化结果...');
    await page.waitForTimeout(10000);

    // 检查是否有结果或错误信息
    const resultSelectors = [
      'text=优化结果',
      'text=优化失败',
      'text=Network Error',
      'text=错误',
      'text=成功',
      '[class*="result"]',
      '[class*="output"]'
    ];

    let foundResult = false;
    for (const selector of resultSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible({ timeout: 2000 })) {
          const text = await element.textContent();
          console.log(`✅ 找到结果: ${text?.substring(0, 100)}...`);
          foundResult = true;
          break;
        }
      } catch (e) {
        // 继续尝试下一个选择器
      }
    }

    if (!foundResult) {
      console.log('⚠️  未找到明显的优化结果，检查页面内容...');
      const pageContent = await page.content();
      if (pageContent.includes('429') || pageContent.includes('Too Many Requests')) {
        console.log('❌ 发现429错误');
      } else if (pageContent.includes('Network Error')) {
        console.log('❌ 发现网络错误');
      }
    }

    // 最终截图
    await page.screenshot({ path: 'test-screenshots/after-optimization.png' });
    console.log('📸 优化后界面截图已保存');
  });

  test('测试备用方案 - 豆包提供商', async ({}) => {
    console.log('📍 测试: 豆包文本优化（备用方案）');

    // 访问页面
    await page.goto('http://localhost:5174');
    await page.waitForTimeout(3000);

    // 查找LLM提供商选择器并选择豆包
    const providerSelect = await page.locator('select').first();
    if (await providerSelect.isVisible()) {
      await providerSelect.selectOption('doubao');
      console.log('✅ 已选择豆包提供商');
    }

    // 输入测试文本
    const textInput = await page.locator('textarea, input[type="text"]').first();
    if (await textInput.isVisible()) {
      await textInput.fill('测试豆包API的文本优化功能，确保备用方案正常工作。');
      console.log('✅ 已输入测试文本');
    }

    // 点击优化按钮
    const buttons = await page.locator('button').all();
    for (const button of buttons) {
      const buttonText = await button.textContent();
      if (buttonText && (buttonText.includes('优化') || buttonText.includes('生成'))) {
        await button.click();
        console.log('✅ 已点击优化按钮');
        break;
      }
    }

    // 等待结果
    await page.waitForTimeout(8000);

    // 检查结果
    await page.screenshot({ path: 'test-screenshots/doubao-result.png' });
    console.log('📸 豆包测试结果截图已保存');
  });

  test('网络请求监控', async ({}) => {
    console.log('📍 测试: 监控网络请求和错误');

    const apiCalls = [];
    const errors = [];

    // 监控所有网络请求
    page.on('request', request => {
      if (request.url().includes('/api/v1/llm/')) {
        apiCalls.push({
          url: request.url(),
          method: request.method(),
          postData: request.postData()
        });
        console.log(`🌐 API请求: ${request.method()} ${request.url()}`);
      }
    });

    page.on('response', response => {
      if (response.url().includes('/api/v1/llm/')) {
        console.log(`📥 API响应: ${response.status()} ${response.url()}`);
        if (response.status() >= 400) {
          errors.push({
            status: response.status(),
            url: response.url(),
            statusText: response.statusText()
          });
        }
      }
    });

    // 访问页面并进行操作
    await page.goto('http://localhost:5174');
    await page.waitForTimeout(2000);

    // 尝试文本优化
    const textInput = await page.locator('textarea, input[type="text"]').first();
    if (await textInput.isVisible()) {
      await textInput.fill('监控网络请求的测试文本');

      const button = await page.locator('button').first();
      if (await button.isVisible()) {
        await button.click();
        await page.waitForTimeout(5000);
      }
    }

    console.log(`📊 总API调用数: ${apiCalls.length}`);
    console.log(`❌ 错误数: ${errors.length}`);

    for (const error of errors) {
      console.log(`   - ${error.status} ${error.statusText} for ${error.url}`);
    }

    expect(errors.length).toBeLessThan(3); // 允许少量重试错误
  });
});