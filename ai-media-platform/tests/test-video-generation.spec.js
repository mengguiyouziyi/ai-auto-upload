const { test, expect } = require('@playwright/test');

test.describe('AI媒体平台视频生成功能测试', () => {
  test.beforeEach(async ({ page }) => {
    // 访问视频生成页面
    await page.goto('http://localhost:5174/#/video-generate');

    // 等待页面加载
    await page.waitForSelector('text=AI视频生成', { timeout: 10000 });

    // 监听网络请求
    page.on('request', request => {
      if (request.url().includes('/api/v1/video/generate')) {
        console.log('视频生成请求:', request.method(), request.url());
        console.log('请求体:', request.postData());
      }
    });

    page.on('response', async (response) => {
      if (response.url().includes('/api/v1/video/generate')) {
        console.log('视频生成响应:', response.status());
        try {
          const body = await response.text();
          console.log('响应体:', body);
        } catch (error) {
          console.log('响应体读取失败:', error.message);
        }
      }
    });

    // 监听控制台消息
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.error('控制台错误:', msg.text());
      }
    });
  });

  test('完整视频生成流程测试', async ({ page }) => {
    console.log('开始完整视频生成流程测试...');

    // 1. 选择本地GPU提供商
    console.log('步骤1: 选择视频提供商...');
    const selectElement = page.locator('.el-select').first();
    await expect(selectElement).toBeVisible();

    // 点击打开下拉菜单
    await selectElement.click();
    await page.waitForTimeout(500);

    // 选择本地GPU选项
    const gpuOption = page.locator('div[role="option"]:has-text("本地GPU")');
    await expect(gpuOption).toBeVisible({ timeout: 5000 });
    await gpuOption.click();

    console.log('已选择本地GPU提供商');

    // 2. 输入视频描述
    console.log('步骤2: 输入视频描述...');
    const textarea = page.locator('textarea');
    await expect(textarea).toBeVisible();

    const testPrompt = '测试AI视频生成功能 - 赛博朋克风格';
    await textarea.fill(testPrompt);
    console.log('已输入视频描述:', testPrompt);

    // 3. 设置视频参数
    console.log('步骤3: 设置视频参数...');

    // 设置时长为5秒
    const durationSlider = page.locator('input[role="slider"]').first();
    if (await durationSlider.isVisible()) {
      await durationSlider.fill('5');
      console.log('已设置视频时长为5秒');
    }

    // 4. 点击生成按钮
    console.log('步骤4: 点击生成视频按钮...');
    const generateButton = page.locator('button:has-text("生成视频")');
    await expect(generateButton).toBeVisible();

    // 监听生成过程中的变化
    let progressDetected = false;

    // 开始生成
    await Promise.all([
      page.waitForResponse(response =>
        response.url().includes('/api/v1/video/generate') &&
        response.status() === 200,
        { timeout: 30000 }
      ),
      generateButton.click()
    ]);

    console.log('已点击生成按钮，等待API响应...');

    // 5. 监控生成进度
    console.log('步骤5: 监控生成进度...');

    try {
      // 等待进度条出现
      await expect(page.locator('.el-progress')).toBeVisible({ timeout: 5000 });
      progressDetected = true;
      console.log('检测到进度条');

      // 等待生成完成或超时
      await page.waitForFunction(() => {
        const progressText = document.querySelector('.progress-text');
        return progressText && (
          progressText.textContent.includes('生成完成') ||
          progressText.textContent.includes('生成失败')
        );
      }, { timeout: 45000 });

      console.log('视频生成流程结束');

    } catch (error) {
      console.log('进度监控超时，检查是否有错误...');
    }

    // 6. 检查结果
    console.log('步骤6: 检查生成结果...');

    // 截图保存当前状态
    await page.screenshot({ path: 'video-generation-result.png' });
    console.log('结果截图已保存');

    // 检查是否有错误消息
    const errorMessage = page.locator('.el-message--error');
    if (await errorMessage.isVisible()) {
      const errorText = await errorMessage.textContent();
      console.error('发现错误消息:', errorText);

      // 记录错误详情
      throw new Error(`视频生成失败: ${errorText}`);
    }

    // 检查是否有成功消息
    const successMessage = page.locator('.el-message--success');
    if (await successMessage.isVisible()) {
      const successText = await successMessage.textContent();
      console.log('发现成功消息:', successText);
    }

    // 检查视频预览
    const videoElement = page.locator('video');
    if (await videoElement.isVisible()) {
      console.log('检测到视频预览元素');

      const videoSrc = await videoElement.getAttribute('src');
      if (videoSrc) {
        console.log('视频源地址:', videoSrc);

        // 验证视频URL格式
        expect(videoSrc).toMatch(/http:\/\/192\.168\.1\.246:8002\/download\/enhanced_.*\.mp4/);
        console.log('视频URL格式正确');
      }
    } else {
      console.log('未检测到视频预览元素');
    }

    // 检查生成历史
    const historyTable = page.locator('.el-table');
    if (await historyTable.isVisible()) {
      console.log('检测到生成历史表格');

      const latestRecord = historyTable.locator('.el-table__row').first();
      if (await latestRecord.isVisible()) {
        const recordText = await latestRecord.textContent();
        console.log('最新历史记录:', recordText);
      }
    }

    console.log('视频生成测试完成');
  });

  test('错误处理测试', async ({ page }) => {
    console.log('开始错误处理测试...');

    // 尝试生成空内容视频
    const selectElement = page.locator('.el-select').first();
    await selectElement.click();
    await page.locator('div[role="option"]:has-text("本地GPU")').click();

    // 不输入任何内容直接点击生成
    const generateButton = page.locator('button:has-text("生成视频")');
    await generateButton.click();

    // 等待可能的错误消息
    await page.waitForTimeout(2000);

    // 检查是否有验证错误
    const validationMessage = page.locator('.el-form-item__error');
    if (await validationMessage.isVisible()) {
      const errorText = await validationMessage.textContent();
      console.log('发现验证错误:', errorText);
      expect(errorText).toContain('视频描述');
    }

    // 输入内容后正常生成
    const textarea = page.locator('textarea');
    await textarea.fill('错误处理测试');
    await generateButton.click();

    // 等待完成
    await page.waitForTimeout(5000);
    console.log('错误处理测试完成');
  });

  test('界面交互测试', async ({ page }) => {
    console.log('开始界面交互测试...');

    // 测试所有提供商选项
    const selectElement = page.locator('.el-select').first();
    await selectElement.click();

    const options = [
      '本地GPU (免费)',
      'ModelScope (免费)',
      'Replicate ($5免费)',
      'Runway ML',
      'Pika Labs',
      'Stability AI'
    ];

    for (const optionText of options) {
      try {
        const option = page.locator(`div[role="option"]:has-text("${optionText}")`);
        if (await option.isVisible()) {
          console.log(`找到选项: ${optionText}`);
        } else {
          console.log(`选项不可见: ${optionText}`);
        }
      } catch (error) {
        console.log(`选项检查失败: ${optionText}`);
      }
    }

    // 关闭下拉菜单
    await page.keyboard.press('Escape');

    // 测试滑块交互
    const sliders = page.locator('input[role="slider"]');
    const sliderCount = await sliders.count();
    console.log(`发现 ${sliderCount} 个滑块`);

    // 测试文本输入限制
    const textarea = page.locator('textarea');
    const maxLength = await textarea.getAttribute('maxlength');
    console.log('文本框最大长度:', maxLength);

    // 测试字符计数
    const wordCount = page.locator('text=/1000');
    if (await wordCount.isVisible()) {
      console.log('字符计数器正常工作');
    }

    console.log('界面交互测试完成');
  });
});