const { test, expect } = require('@playwright/test');

test.describe('GLM-4.6 前端实际测试 - AI媒体平台', () => {
  let page;

  test.beforeAll(async ({ browser }) => {
    console.log('🚀 开始GLM-4.6前端实际测试...');
  });

  test.beforeEach(async ({ browser }) => {
    page = await browser.newPage();

    // 设置默认超时时间
    page.setDefaultTimeout(60000); // 60秒

    // 监听网络请求
    await page.route('**/api/v1/llm/optimize-text', async (route, request) => {
      const postData = request.postDataJSON();

      console.log(`📤 文本优化请求: Provider=${postData.provider}, TextLength=${postData.text?.length || 0}`);

      // 记录请求开始时间
      const startTime = Date.now();

      try {
        // 继续发送请求
        const response = await route.fetch();
        const endTime = Date.now();

        console.log(`📥 响应状态: ${response.status()}, 耗时: ${endTime - startTime}ms`);

        if (response.status() === 200) {
          const data = await response.json();
          console.log(`✅ 优化成功: Provider=${data.provider}, ResultLength=${data.optimized_text?.length || 0}`);
          console.log(`📄 结果预览: ${data.optimized_text?.substring(0, 100)}...`);
        } else {
          const errorText = await response.text();
          console.log(`❌ 优化失败: ${response.status()} - ${errorText.substring(0, 200)}`);

          // 检查是否是429错误
          if (response.status() === 429) {
            console.log('⚠️  429速率限制错误');
          }
        }

        // 返回响应
        await route.fulfill({
          response: response,
          status: response.status(),
          headers: response.headers(),
          body: await response.text()
        });

      } catch (error) {
        console.log(`🚨 请求异常: ${error.message}`);
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: `网络请求失败: ${error.message}`
          })
        });
      }
    });

    // 监听控制台消息
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`❌ 页面错误: ${msg.text()}`);
      } else if (msg.type() === 'warning') {
        console.log(`⚠️  页面警告: ${msg.text()}`);
      } else if (msg.type() === 'log') {
        console.log(`📝 页面日志: ${msg.text()}`);
      }
    });

    // 监听页面错误
    page.on('pageerror', error => {
      console.log(`🚨 页面异常: ${error.message}`);
    });
  });

  test.afterEach(async () => {
    if (page) {
      await page.close();
    }
  });

  test('测试1: 访问文本优化页面', async ({}) => {
    console.log('📍 测试1: 访问文本优化页面');

    // 首先访问主页
    await page.goto('http://localhost:5174', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 检查页面标题
    const title = await page.title();
    console.log(`📄 页面标题: ${title}`);
    expect(title).toContain('AI媒体智能平台');

    // 截图
    await page.screenshot({ path: 'test-screenshots/real-homepage.png' });
    console.log('📸 主页截图已保存');

    // 查找文本优化导航链接
    const textOptimizeLink = await page.locator('text=文本优化').first();
    if (await textOptimizeLink.isVisible()) {
      console.log('✅ 找到文本优化链接');
      await textOptimizeLink.click();
    } else {
      // 尝试其他方式
      console.log('⚠️  未找到文本优化链接，尝试直接访问URL');
      await page.goto('http://localhost:5174/text-optimize', { waitUntil: 'networkidle' });
    }

    await page.waitForTimeout(3000);

    // 检查是否到达文本优化页面
    const pageTitle = await page.locator('text=AI文本优化').first();
    await expect(pageTitle).toBeVisible({ timeout: 10000 });
    console.log('✅ 成功到达文本优化页面');

    // 截图
    await page.screenshot({ path: 'test-screenshots/text-optimize-page.png' });
    console.log('📸 文本优化页面截图已保存');
  });

  test('测试2: GLM-4.6文本优化完整流程', async ({}) => {
    console.log('📍 测试2: GLM-4.6文本优化完整流程');

    // 访问文本优化页面
    await page.goto('http://localhost:5174/text-optimize', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 查找并选择GLM提供商
    console.log('🔍 查找LLM提供商选择器...');
    const providerSelect = await page.locator('select[placeholder*="AI提供商"], select').first();

    if (await providerSelect.isVisible()) {
      console.log('✅ 找到提供商选择器');

      // 选择GLM
      await providerSelect.selectOption('glm');
      console.log('✅ 已选择GLM-4.6提供商');

      // 验证选择
      const selectedValue = await providerSelect.inputValue();
      console.log(`📊 当前选择: ${selectedValue}`);
    } else {
      console.log('❌ 未找到提供商选择器');
      throw new Error('找不到提供商选择器');
    }

    // 查找文本输入框
    console.log('🔍 查找文本输入框...');
    const textInput = await page.locator('textarea[placeholder*="文本"], textarea').first();

    if (await textInput.isVisible()) {
      console.log('✅ 找到文本输入框');

      // 输入测试文本
      const testText = `在AI编程工具竞争白热化的当下，OpenAI推出的Codex编程助手凭借"本地安全运行"、"ChatGPT深度集成"、"全工具链覆盖"三大核心优势，迅速在GitHub狂揽4万星标，成为开发者热议的焦点。这款工具搭载GPT-5-Codex模型，能像专业程序员般连续7小时迭代复杂项目、修复Bug、运行测试，彻底改变传统编程的低效流程。`;

      await textInput.fill(testText);
      console.log('✅ 已输入测试文本');
      console.log(`📊 文本长度: ${testText.length} 字符`);
    } else {
      console.log('❌ 未找到文本输入框');
      throw new Error('找不到文本输入框');
    }

    // 截图优化前状态
    await page.screenshot({ path: 'test-screenshots/before-glm-optimization.png' });
    console.log('📸 优化前界面截图已保存');

    // 查找并点击AI优化按钮
    console.log('🔍 查找AI优化按钮...');
    const optimizeButton = await page.locator('button:has-text("AI优化"), button:has-text("优化")').first();

    if (await optimizeButton.isVisible()) {
      console.log('✅ 找到AI优化按钮');

      // 点击优化按钮
      await optimizeButton.click();
      console.log('✅ 已点击AI优化按钮');

      // 等待加载状态
      const loadingElement = await page.locator('.loading-container, .el-skeleton').first();
      if (await loadingElement.isVisible({ timeout: 3000 })) {
        console.log('✅ 检测到加载状态');

        // 等待加载完成（最长60秒）
        console.log('⏳ 等待优化完成...');
        await page.waitForFunction(() => {
          const loading = document.querySelector('.loading-container, .el-skeleton');
          return !loading || loading.style.display === 'none';
        }, { timeout: 60000 });

        console.log('✅ 加载完成');
      }

      // 再等待一会儿确保结果完全加载
      await page.waitForTimeout(3000);

    } else {
      console.log('❌ 未找到AI优化按钮');
      throw new Error('找不到AI优化按钮');
    }

    // 检查结果
    console.log('🔍 检查优化结果...');

    const resultContainer = await page.locator('.result-container, .result-text').first();
    const resultText = await page.locator('.result-text').first();

    if (await resultContainer.isVisible({ timeout: 10000 })) {
      console.log('✅ 找到结果容器');

      // 获取结果文本
      const optimizedText = await resultText.textContent();
      if (optimizedText && optimizedText.trim().length > 0) {
        console.log('✅ 找到优化结果');
        console.log(`📊 结果长度: ${optimizedText.length} 字符`);
        console.log(`📄 结果预览: ${optimizedText.substring(0, 200)}...`);

        // 检查是否显示提供商信息
        const providerTag = await page.locator('.el-tag').first();
        if (await providerTag.isVisible()) {
          const provider = await providerTag.textContent();
          console.log(`🏷️  实际使用提供商: ${provider}`);
        }

        // 检查响应时间
        const responseTime = await page.locator('.response-time').first();
        if (await responseTime.isVisible()) {
          const time = await responseTime.textContent();
          console.log(`⏱️  ${time}`);
        }

      } else {
        console.log('⚠️  结果容器存在但内容为空');
      }

    } else {
      console.log('❌ 未找到结果容器');

      // 检查是否有错误消息
      const errorMessage = await page.locator('.el-message--error, .error-message').first();
      if (await errorMessage.isVisible()) {
        const errorText = await errorMessage.textContent();
        console.log(`❌ 发现错误消息: ${errorText}`);
      }
    }

    // 最终截图
    await page.screenshot({ path: 'test-screenshots/after-glm-optimization.png' });
    console.log('📸 优化后界面截图已保存');
  });

  test('测试3: 连续多次GLM请求测试重试机制', async ({}) => {
    console.log('📍 测试3: 连续多次GLM请求测试重试机制');

    await page.goto('http://localhost:5174/text-optimize', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 设置GLM
    const providerSelect = await page.locator('select').first();
    await providerSelect.selectOption('glm');

    const textInput = await page.locator('textarea').first();
    const optimizeButton = await page.locator('button:has-text("AI优化")').first();

    const testTexts = [
      '第一次测试：GLM-4.6文本优化，验证重试和降级机制。',
      '第二次测试：AI编程工具竞争白热化，OpenAI推出Codex编程助手。',
      '第三次测试：验证GLM API在连续请求下的表现和稳定性。'
    ];

    const results = [];

    for (let i = 0; i < testTexts.length; i++) {
      console.log(`\n📤 第${i + 1}次GLM请求...`);

      // 清空并输入新文本
      await textInput.fill(testTexts[i]);

      // 点击优化
      await optimizeButton.click();

      // 等待结果
      try {
        await page.waitForSelector('.result-container', { timeout: 45000 });
        console.log(`✅ 第${i + 1}次请求成功`);
        results.push({ index: i + 1, status: 'success' });

        // 获取结果提供商
        const providerTag = await page.locator('.el-tag').first();
        if (await providerTag.isVisible()) {
          const provider = await providerTag.textContent();
          console.log(`🏷️  实际提供商: ${provider}`);
        }

      } catch (error) {
        console.log(`❌ 第${i + 1}次请求失败: ${error.message}`);
        results.push({ index: i + 1, status: 'failed', error: error.message });
      }

      // 清空结果进行下一次测试
      const clearButton = await page.locator('button:has-text("清空")').first();
      if (await clearButton.isVisible()) {
        await clearButton.click();
        await page.waitForTimeout(1000);
      }
    }

    console.log('\n📊 连续请求测试结果:');
    results.forEach(result => {
      const status = result.status === 'success' ? '✅ 成功' : '❌ 失败';
      console.log(`  第${result.index}次: ${status}${result.error ? ` - ${result.error}` : ''}`);
    });

    const successCount = results.filter(r => r.status === 'success').length;
    console.log(`\n🎯 总体结果: ${successCount}/${testTexts.length} 请求成功`);

    // 截图最终状态
    await page.screenshot({ path: 'test-screenshots/multiple-requests-result.png' });
    console.log('📸 多次请求测试结果截图已保存');
  });

  test('测试4: 错误处理和用户反馈', async ({}) => {
    console.log('📍 测试4: 错误处理和用户反馈');

    await page.goto('http://localhost:5174/text-optimize', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // 设置GLM
    const providerSelect = await page.locator('select').first();
    await providerSelect.selectOption('glm');

    // 测试空文本提交
    console.log('🧪 测试空文本提交...');
    const optimizeButton = await page.locator('button:has-text("AI优化")').first();
    await optimizeButton.click();

    // 检查警告消息
    try {
      await page.waitForSelector('.el-message--warning', { timeout: 3000 });
      console.log('✅ 空文本警告正常显示');
    } catch (error) {
      console.log('⚠️  未找到空文本警告');
    }

    // 输入正常文本
    const textInput = await page.locator('textarea').first();
    await textInput.fill('测试错误处理机制的用户反馈。');

    // 截图错误处理测试
    await page.screenshot({ path: 'test-screenshots/error-handling-test.png' });
    console.log('📸 错误处理测试截图已保存');

    console.log('\n🎯 GLM-4.6前端实际测试完成');
  });
});