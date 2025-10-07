const { chromium } = require('playwright');

async function testGLMFrontend() {
  console.log('🚀 开始GLM-4.6前端直接测试...');

  let browser;
  let page;

  try {
    // 启动浏览器
    browser = await chromium.launch({
      headless: false, // 显示浏览器窗口
      slowMo: 1000     // 减慢操作速度
    });
    page = await browser.newPage();

    // 设置默认超时
    page.setDefaultTimeout(60000);

    // 监听网络请求
    const apiCalls = [];
    await page.route('**/api/v1/llm/optimize-text', async (route, request) => {
      const postData = request.postDataJSON();
      const callId = apiCalls.length + 1;

      console.log(`📤 API请求 #${callId}: Provider=${postData.provider}, TextLength=${postData.text?.length || 0}`);

      const startTime = Date.now();
      let success = false;
      let providerUsed = 'unknown';

      try {
        const response = await route.fetch();
        const status = response.status();
        const endTime = Date.now();

        if (status === 200) {
          const data = await response.json();
          success = true;
          providerUsed = data.provider || 'unknown';

          console.log(`✅ 请求成功 #${callId}: Status=${status}, Provider=${providerUsed}, Duration=${endTime - startTime}ms`);
          console.log(`📄 结果长度: ${data.optimized_text?.length || 0}`);
          console.log(`📄 结果预览: ${data.optimized_text?.substring(0, 100)}...`);
        } else {
          const errorText = await response.text();
          console.log(`❌ 请求失败 #${callId}: Status=${status}, Error=${errorText.substring(0, 150)}`);
        }

        apiCalls.push({
          id: callId,
          provider: postData.provider,
          providerUsed: providerUsed,
          success: success,
          duration: endTime - startTime,
          status: status
        });

        // 返回响应
        await route.fulfill({
          response: response,
          status: status,
          headers: response.headers(),
          body: await response.text()
        });

      } catch (error) {
        const endTime = Date.now();
        console.log(`🚨 请求异常 #${callId}: ${error.message}`);

        apiCalls.push({
          id: callId,
          provider: postData.provider,
          providerUsed: 'error',
          success: false,
          duration: endTime - startTime,
          error: error.message
        });

        await route.fulfill({
          status: 500,
          body: JSON.stringify({ detail: `网络错误: ${error.message}` })
        });
      }
    });

    // 监听控制台消息
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log(`❌ 页面错误: ${msg.text()}`);
      } else if (msg.type() === 'warning') {
        console.log(`⚠️  页面警告: ${msg.text()}`);
      }
    });

    page.on('pageerror', error => {
      console.log(`🚨 页面异常: ${error.message}`);
    });

    // 1. 访问文本优化页面
    console.log('\n📍 步骤1: 访问文本优化页面');
    await page.goto('http://localhost:5175/text-optimize', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // 截图
    await page.screenshot({ path: 'test-screenshots/direct-test-step1.png' });
    console.log('📸 步骤1完成截图');

    // 检查页面是否加载成功
    const pageTitle = await page.locator('text=AI文本优化').first();
    if (await pageTitle.isVisible({ timeout: 10000 })) {
      console.log('✅ 页面加载成功');
    } else {
      throw new Error('页面加载失败');
    }

    // 2. 选择GLM提供商
    console.log('\n📍 步骤2: 选择GLM-4.6提供商');
    const providerSelect = await page.locator('select').first();
    await providerSelect.waitFor({ state: 'visible', timeout: 10000 });
    await providerSelect.selectOption('glm');
    await page.waitForTimeout(1000);
    console.log('✅ 已选择GLM-4.6');

    // 3. 输入测试文本
    console.log('\n📍 步骤3: 输入测试文本');
    const textInput = await page.locator('textarea').first();
    await textInput.waitFor({ state: 'visible', timeout: 10000 });

    const testText = `在AI编程工具竞争白热化的当下，OpenAI推出的Codex编程助手凭借"本地安全运行"、"ChatGPT深度集成"、"全工具链覆盖"三大核心优势，迅速在GitHub狂揽4万星标，成为开发者热议的焦点。这款工具搭载GPT-5-Codex模型，能像专业程序员般连续7小时迭代复杂项目、修复Bug、运行测试，彻底改变传统编程的低效流程。`;

    await textInput.fill(testText);
    await page.waitForTimeout(1000);
    console.log(`✅ 已输入测试文本 (长度: ${testText.length})`);

    // 截图
    await page.screenshot({ path: 'test-screenshots/direct-test-step2.png' });
    console.log('📸 步骤2-3完成截图');

    // 4. 点击优化按钮
    console.log('\n📍 步骤4: 点击AI优化按钮');
    const optimizeButton = await page.locator('button:has-text("AI优化")').first();
    await optimizeButton.waitFor({ state: 'visible', timeout: 10000 });

    const startTime = Date.now();
    await optimizeButton.click();
    console.log('✅ 已点击优化按钮');

    // 5. 等待结果
    console.log('\n📍 步骤5: 等待优化结果...');
    console.log('⏳ 等待中... (最长90秒)');

    let resultFound = false;
    let actualProvider = '';

    try {
      // 等待结果容器出现
      await page.waitForSelector('.result-container', { timeout: 90000 });
      const endTime = Date.now();
      console.log(`✅ 收到结果! 总耗时: ${endTime - startTime}ms`);
      resultFound = true;

      // 获取结果文本
      const resultText = await page.locator('.result-text').first();
      await resultText.waitFor({ state: 'visible', timeout: 5000 });

      const optimizedText = await resultText.textContent();
      console.log(`📄 优化结果长度: ${optimizedText.length} 字符`);
      console.log(`📄 结果预览: ${optimizedText.substring(0, 200)}...`);

      // 检查提供商标签
      const providerTag = await page.locator('.el-tag').first();
      if (await providerTag.isVisible()) {
        actualProvider = await providerTag.textContent();
        console.log(`🏷️  页面显示提供商: ${actualProvider}`);
      }

      // 检查响应时间
      const responseTimeElement = await page.locator('.response-time').first();
      if (await responseTimeElement.isVisible()) {
        const responseTime = await responseTimeElement.textContent();
        console.log(`⏱️  页面显示响应时间: ${responseTime}`);
      }

    } catch (error) {
      console.log(`❌ 等待结果超时: ${error.message}`);
    }

    // 6. 最终检查和截图
    console.log('\n📍 步骤6: 最终检查');
    await page.screenshot({ path: 'test-screenshots/direct-test-final.png' });
    console.log('📸 最终状态截图');

    // 7. 分析结果
    console.log('\n📊 测试结果分析:');
    console.log(`总API调用次数: ${apiCalls.length}`);

    for (const call of apiCalls) {
      const status = call.success ? '✅ 成功' : '❌ 失败';
      console.log(`  请求 #${call.id}: ${status}, Provider: ${call.provider} → ${call.providerUsed}, Duration: ${call.duration}ms`);

      if (call.error) {
        console.log(`    错误: ${call.error}`);
      }
    }

    if (resultFound) {
      console.log('\n🎉 GLM-4.6前端测试成功！');

      if (actualProvider.includes('glm') || actualProvider.includes('GLM')) {
        console.log('✅ 使用了GLM-4.6提供商');
      } else {
        console.log('🔄 自动降级到备用提供商');
      }
    } else {
      console.log('\n❌ GLM-4.6前端测试失败');
      console.log('原因: 未收到优化结果');
    }

    // 8. 等待用户查看结果
    console.log('\n⏳ 测试完成，浏览器将保持打开状态10秒供查看...');
    await page.waitForTimeout(10000);

  } catch (error) {
    console.log(`\n🚨 测试过程中发生错误: ${error.message}`);

    if (page) {
      await page.screenshot({ path: 'test-screenshots/direct-test-error.png' });
      console.log('📸 错误状态截图已保存');
    }
  } finally {
    if (browser) {
      await browser.close();
      console.log('\n🔚 浏览器已关闭');
    }
  }
}

// 运行测试
testGLMFrontend().catch(console.error);