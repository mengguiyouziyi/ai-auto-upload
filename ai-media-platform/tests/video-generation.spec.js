const { test, expect } = require('@playwright/test');

test.describe('视频生成功能测试', () => {
  test.beforeEach(async ({ page }) => {
    // 访问视频生成页面
    await page.goto('http://localhost:5174/#/video-generate');

    // 等待页面加载完成
    await page.waitForSelector('.video-generate', { timeout: 10000 });

    // 监听所有网络请求
    page.on('request', request => {
      console.log('请求:', request.method(), request.url());
    });

    page.on('response', response => {
      console.log('响应:', response.status(), response.url());
    });
  });

  test('基础视频生成测试', async ({ page }) => {
    console.log('开始基础视频生成测试...');

    // 等待并验证页面元素
    await expect(page.locator('text=AI视频生成')).toBeVisible();
    await expect(page.locator('select[name="provider"]')).toBeVisible();
    await expect(page.locator('textarea[placeholder*="视频描述"]')).toBeVisible();
    await expect(page.locator('button:has-text("生成视频")')).toBeVisible();

    // 选择本地GPU提供商
    await page.selectOption('select[name="provider"]', 'local_gpu');

    // 输入测试文本
    const testPrompt = '测试视频生成功能';
    await page.fill('textarea[placeholder*="视频描述"]', testPrompt);

    // 设置视频参数
    await page.locator('input[role="slider"]').first().fill('5'); // 时长5秒

    console.log('准备点击生成按钮...');

    // 点击生成按钮
    await Promise.all([
      page.waitForResponse(response =>
        response.url().includes('/api/v1/video/generate') &&
        response.status() === 200
      ),
      page.click('button:has-text("生成视频")')
    ]);

    console.log('生成按钮已点击，等待响应...');

    // 等待加载完成
    await expect(page.locator('.el-progress')).toBeVisible({ timeout: 5000 });

    // 等待生成完成（最多30秒）
    try {
      await page.waitForFunction(() => {
        const progressText = document.querySelector('.progress-text');
        return progressText && progressText.textContent.includes('生成完成');
      }, { timeout: 30000 });

      console.log('视频生成完成！');

      // 检查是否有视频预览
      const videoElement = page.locator('video');
      if (await videoElement.isVisible()) {
        console.log('视频预览元素可见');

        // 获取视频源
        const videoSrc = await videoElement.getAttribute('src');
        console.log('视频源:', videoSrc);

        // 验证视频URL格式
        expect(videoSrc).toMatch(/http:\/\/192\.168\.1\.246:8002\/download\/.*\.mp4/);
      } else {
        console.log('视频预览元素不可见，检查结果信息...');
      }

      // 检查结果信息
      const resultInfo = page.locator('.el-descriptions');
      if (await resultInfo.isVisible()) {
        console.log('找到结果信息');
        const durationText = await resultInfo.locator('text=视频时长').isVisible();
        console.log('时长信息显示:', durationText);
      }

    } catch (error) {
      console.log('视频生成超时或失败，检查错误信息...');

      // 检查是否有错误消息
      const errorMessage = page.locator('.el-message--error');
      if (await errorMessage.isVisible()) {
        const errorText = await errorMessage.textContent();
        console.error('错误消息:', errorText);
      }

      // 截图保存当前状态
      await page.screenshot({ path: 'video-generation-error.png' });
      throw error;
    }
  });

  test('控制台错误监控测试', async ({ page }) => {
    console.log('开始控制台错误监控测试...');

    // 监听控制台消息
    const consoleMessages = [];
    page.on('console', msg => {
      console.log('控制台消息:', msg.type(), msg.text());
      consoleMessages.push({
        type: msg.type(),
        text: msg.text(),
        location: msg.location()
      });
    });

    // 监听页面错误
    const pageErrors = [];
    page.on('pageerror', error => {
      console.error('页面错误:', error.message);
      pageErrors.push({
        message: error.message,
        stack: error.stack
      });
    });

    // 执行视频生成
    await page.selectOption('select[name="provider"]', 'local_gpu');
    await page.fill('textarea[placeholder*="视频描述"]', '简短测试');
    await page.click('button:has-text("生成视频")');

    // 等待一段时间让错误出现
    await page.waitForTimeout(10000);

    // 检查是否有错误
    if (pageErrors.length > 0) {
      console.error('发现页面错误:', pageErrors);
      throw new Error(`页面错误: ${pageErrors[0].message}`);
    }

    const errorMessages = consoleMessages.filter(msg => msg.type === 'error');
    if (errorMessages.length > 0) {
      console.error('发现控制台错误:', errorMessages);
      throw new Error(`控制台错误: ${errorMessages[0].text}`);
    }

    console.log('没有发现JavaScript错误');
  });

  test('网络请求详细测试', async ({ page }) => {
    console.log('开始网络请求详细测试...');

    // 监听详细网络信息
    const networkRequests = [];
    page.on('request', request => {
      const requestData = {
        url: request.url(),
        method: request.method(),
        headers: request.headers(),
        postData: request.postData()
      };
      console.log('网络请求:', JSON.stringify(requestData, null, 2));
      networkRequests.push(requestData);
    });

    page.on('response', async (response) => {
      const responseData = {
        url: response.url(),
        status: response.status(),
        headers: response.headers()
      };

      try {
        responseData.body = await response.text();
        console.log('网络响应:', JSON.stringify(responseData, null, 2));
      } catch (error) {
        console.log('响应体读取失败:', error.message);
      }
    });

    // 执行视频生成
    await page.selectOption('select[name="provider"]', 'local_gpu');
    await page.fill('textarea[placeholder*="视频描述"]', '网络测试');
    await page.click('button:has-text("生成视频")');

    // 等待请求完成
    await page.waitForTimeout(5000);

    // 验证API请求
    const apiRequests = networkRequests.filter(req =>
      req.url.includes('/api/v1/video/generate')
    );

    expect(apiRequests.length).toBeGreaterThan(0);

    const apiRequest = apiRequests[0];
    console.log('API请求详情:', JSON.stringify(apiRequest, null, 2));

    // 验证请求格式
    expect(apiRequest.method).toBe('POST');
    expect(JSON.parse(apiRequest.postData)).toMatchObject({
      provider: 'local_gpu',
      prompt: '网络测试'
    });
  });
});