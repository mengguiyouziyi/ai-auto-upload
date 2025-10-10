const { test, expect } = require('@playwright/test');

test('直接测试视频生成API', async ({ page }) => {
  console.log('开始直接API测试...');

  // 访问页面
  await page.goto('http://localhost:5174/#/video-generate');
  await page.waitForTimeout(3000);

  // 监听所有网络请求和响应
  const apiCalls = [];
  page.on('request', request => {
    if (request.url().includes('/api/v1/video/generate')) {
      const callData = {
        url: request.url(),
        method: request.method(),
        headers: request.headers(),
        body: request.postData(),
        timestamp: new Date().toISOString()
      };
      apiCalls.push({ type: 'request', ...callData });
      console.log('API请求:', JSON.stringify(callData, null, 2));
    }
  });

  page.on('response', async (response) => {
    if (response.url().includes('/api/v1/video/generate')) {
      try {
        const body = await response.text();
        const callData = {
          url: response.url(),
          status: response.status(),
          headers: response.headers(),
          body: body,
          timestamp: new Date().toISOString()
        };
        apiCalls.push({ type: 'response', ...callData });
        console.log('API响应:', JSON.stringify(callData, null, 2));
      } catch (error) {
        console.log('响应解析失败:', error.message);
      }
    }
  });

  // 监听控制台消息
  const consoleMessages = [];
  page.on('console', msg => {
    const message = {
      type: msg.type(),
      text: msg.text(),
      location: msg.location(),
      timestamp: new Date().toISOString()
    };
    consoleMessages.push(message);

    if (msg.type() === 'error') {
      console.error('控制台错误:', msg.text());
    } else if (msg.type() === 'log') {
      console.log('控制台日志:', msg.text());
    }
  });

  // 监听未处理的Promise拒绝
  page.on('pageerror', error => {
    console.error('页面错误:', error.message);
    consoleMessages.push({
      type: 'pageerror',
      text: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
  });

  // 尝试手动执行JavaScript来触发API调用
  console.log('尝试直接调用API...');

  await page.evaluate(() => {
    return fetch('http://localhost:9000/api/v1/video/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        provider: 'local_gpu',
        prompt: 'Playwright直接测试',
        duration: 5,
        quality: 'high',
        width: 512,
        height: 320,
        fps: 16
      })
    }).then(response => response.text())
      .then(data => {
        console.log('直接API调用结果:', data);
        return data;
      })
      .catch(error => {
        console.error('直接API调用失败:', error);
        throw error;
      });
  });

  await page.waitForTimeout(5000);

  // 尝试通过页面表单触发
  console.log('尝试通过表单触发...');

  // 查找并操作元素
  const selectElements = await page.$$('.el-select');
  console.log(`找到 ${selectElements.length} 个选择元素`);

  if (selectElements.length > 0) {
    try {
      // 尝试点击第一个选择元素
      await selectElements[0].click();
      await page.waitForTimeout(1000);

      // 查找所有可点击的选项
      const options = await page.$$('div[role="option"], .el-select-dropdown__item');
      console.log(`找到 ${options.length} 个选项`);

      for (let i = 0; i < options.length; i++) {
        const text = await options[i].textContent();
        console.log(`选项 ${i}: ${text}`);

        if (text && text.includes('本地GPU')) {
          await options[i].click();
          console.log('已选择本地GPU');
          break;
        }
      }
    } catch (error) {
      console.log('选择元素操作失败:', error.message);
    }
  }

  // 查找文本框
  const textareas = await page.$$('textarea');
  console.log(`找到 ${textareas.length} 个文本框`);

  if (textareas.length > 0) {
    try {
      await textareas[0].fill('Playwright表单测试');
      console.log('已输入测试文本');
    } catch (error) {
      console.log('文本框操作失败:', error.message);
    }
  }

  // 查找生成按钮
  const buttons = await page.$$('button');
  console.log(`找到 ${buttons.length} 个按钮`);

  for (let i = 0; i < buttons.length; i++) {
    const text = await buttons[i].textContent();
    console.log(`按钮 ${i}: ${text}`);

    if (text && text.includes('生成视频')) {
      try {
        console.log('找到生成按钮，准备点击...');
        await buttons[i].click();
        console.log('已点击生成按钮');
        break;
      } catch (error) {
        console.log('按钮点击失败:', error.message);
      }
    }
  }

  // 等待响应
  await page.waitForTimeout(10000);

  // 检查最终状态
  console.log('检查最终状态...');

  // 查找错误消息
  const errorElements = await page.$$('.el-message--error');
  if (errorElements.length > 0) {
    for (let i = 0; i < errorElements.length; i++) {
      const errorText = await errorElements[i].textContent();
      console.log(`错误消息 ${i}: ${errorText}`);
    }
  }

  // 查找成功消息
  const successElements = await page.$$('.el-message--success');
  if (successElements.length > 0) {
    for (let i = 0; i < successElements.length; i++) {
      const successText = await successElements[i].textContent();
      console.log(`成功消息 ${i}: ${successText}`);
    }
  }

  // 截图
  await page.screenshot({ path: 'simple-test-final.png' });
  console.log('最终截图已保存');

  // 输出总结
  console.log('\n=== 测试总结 ===');
  console.log(`API调用次数: ${apiCalls.length}`);
  console.log(`控制台消息数: ${consoleMessages.length}`);

  const errors = consoleMessages.filter(msg => msg.type === 'error' || msg.type === 'pageerror');
  if (errors.length > 0) {
    console.log(`发现 ${errors.length} 个错误:`);
    errors.forEach((error, index) => {
      console.log(`  错误 ${index + 1}: ${error.text}`);
    });
  }

  const logs = consoleMessages.filter(msg => msg.type === 'log');
  console.log(`发现 ${logs.length} 个日志消息`);

  // 验证API调用
  const requests = apiCalls.filter(call => call.type === 'request');
  const responses = apiCalls.filter(call => call.type === 'response');

  console.log(`API请求数: ${requests.length}`);
  console.log(`API响应数: ${responses.length}`);

  if (responses.length > 0) {
    responses.forEach((response, index) => {
      console.log(`响应 ${index + 1}: 状态码 ${response.status}`);

      try {
        const data = JSON.parse(response.body);
        console.log(`  响应数据:`, data);

        if (data.success === false) {
          console.log(`  ❌ API返回失败: ${data.message || '未知错误'}`);
        } else {
          console.log(`  ✅ API调用成功`);
        }
      } catch (error) {
        console.log(`  响应解析失败: ${error.message}`);
      }
    });
  }

  // 断言验证
  expect(requests.length).toBeGreaterThan(0);
  expect(responses.length).toBeGreaterThan(0);
});