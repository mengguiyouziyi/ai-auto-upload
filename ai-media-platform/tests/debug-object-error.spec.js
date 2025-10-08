const { test, expect } = require('@playwright/test');

test('深入调试 [object Object] 错误', async ({ page }) => {
  console.log('开始深入调试 [object Object] 错误...');

  // 访问页面
  await page.goto('http://localhost:5174/#/video-generate');
  await page.waitForTimeout(3000);

  // 设置详细的错误监控
  const errors = [];
  const consoleMessages = [];
  const networkErrors = [];

  // 监听所有控制台消息
  page.on('console', msg => {
    const message = {
      type: msg.type(),
      text: msg.text(),
      location: msg.location(),
      args: [],
      timestamp: new Date().toISOString()
    };

    // 尝试获取参数详情
    try {
      message.args = msg.args().map(arg => {
        try {
          return JSON.stringify(arg);
        } catch {
          return String(arg);
        }
      });
    } catch (error) {
      message.args = ['无法获取参数'];
    }

    consoleMessages.push(message);

    if (msg.type() === 'error') {
      console.error('🔴 控制台错误:', msg.text());
      console.error('   位置:', msg.location());
      console.error('   参数:', message.args);
      errors.push(message);
    } else if (msg.type() === 'warn') {
      console.warn('🟡 控制台警告:', msg.text());
    } else if (msg.type() === 'log') {
      console.log('🔵 控制台日志:', msg.text());
      if (msg.text().includes('[object Object]')) {
        console.log('   发现 [object Object] 消息!');
        errors.push({ ...message, type: 'object_error' });
      }
    }
  });

  // 监听页面错误
  page.on('pageerror', error => {
    const errorInfo = {
      message: error.message,
      stack: error.stack,
      name: error.name,
      timestamp: new Date().toISOString()
    };
    console.error('🚨 页面错误:', errorInfo);
    errors.push({ type: 'pageerror', ...errorInfo });
  });

  // 监听请求失败
  page.on('requestfailed', request => {
    const failure = {
      url: request.url(),
      failure: request.failure(),
      timestamp: new Date().toISOString()
    };
    console.error('❌ 请求失败:', failure);
    networkErrors.push(failure);
    errors.push({ type: 'network_error', ...failure });
  });

  // 监听网络响应
  page.on('response', async (response) => {
    if (response.url().includes('/api/v1/video/generate')) {
      try {
        const body = await response.text();
        console.log('📡 API响应:', response.status(), body);

        // 检查响应内容是否有问题
        if (body.includes('[object Object]')) {
          console.log('⚠️ API响应包含 [object Object]!');
          errors.push({
            type: 'api_object_error',
            url: response.url(),
            status: response.status(),
            body: body,
            timestamp: new Date().toISOString()
          });
        }
      } catch (error) {
        console.log('响应解析失败:', error.message);
      }
    }
  });

  // 注入错误捕获脚本
  await page.addInitScript(() => {
    // 重写 console.error 来捕获更多错误
    const originalConsoleError = console.error;
    console.error = function(...args) {
      // 检查是否有 [object Object]
      const hasObjectError = args.some(arg =>
        typeof arg === 'object' && arg !== null && String(arg) === '[object Object]'
      );

      if (hasObjectError) {
        originalConsoleError('🔍 发现 [object Object] 错误:', ...args);
        // 保存到 window 对象供后续检查
        if (!window.playwrightErrors) window.playwrightErrors = [];
        window.playwrightErrors.push({
          type: 'console_object_error',
          args: args.map(arg => {
            if (typeof arg === 'object' && arg !== null) {
              try {
                return JSON.stringify(arg, null, 2);
              } catch {
                return String(arg) + ' (类型: ' + arg.constructor.name + ')';
              }
            }
            return String(arg);
          }),
          timestamp: new Date().toISOString(),
          stack: new Error().stack
        });
      }

      originalConsoleError.apply(console, args);
    };

    // 监听 Promise 拒绝
    window.addEventListener('unhandledrejection', event => {
      console.error('🔥 未处理的Promise拒绝:', event.reason);
      if (!window.playwrightErrors) window.playwrightErrors = [];
      window.playwrightErrors.push({
        type: 'unhandled_rejection',
        reason: event.reason,
        timestamp: new Date().toISOString()
      });
    });

    // 监听错误事件
    window.addEventListener('error', event => {
      console.error('💥 全局错误事件:', event.error);
      if (!window.playwrightErrors) window.playwrightErrors = [];
      window.playwrightErrors.push({
        type: 'global_error',
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: new Date().toISOString()
      });
    });

    // 重写 fetch 来监控所有网络请求
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
      try {
        const response = await originalFetch.apply(this, args);

        // 克隆响应以避免消费问题
        const clonedResponse = response.clone();

        // 检查响应内容
        clonedResponse.text().then(body => {
          if (body.includes('[object Object]')) {
            console.error('🌐 Fetch响应包含 [object Object]:', args[0], body);
          }
        }).catch(() => {
          // 忽略解析错误
        });

        return response;
      } catch (error) {
        console.error('🌐 Fetch错误:', args[0], error);
        throw error;
      }
    };

    // 监听 Vue 错误（如果页面使用Vue）
    if (window.Vue) {
      window.Vue.config.errorHandler = function(err, vm, info) {
        console.error('🟢 Vue错误:', err, info);
        if (!window.playwrightErrors) window.playwrightErrors = [];
        window.playwrightErrors.push({
          type: 'vue_error',
          error: err.message,
          component: info,
          stack: err.stack,
          timestamp: new Date().toISOString()
        });
      };
    }

    // 监听 Element Plus 错误
    if (window.ElementPlus) {
      console.log('检测到 Element Plus');
    }
  });

  console.log('开始执行用户操作...');

  // 等待页面完全加载
  await page.waitForSelector('text=AI视频生成', { timeout: 10000 });

  // 执行视频生成操作
  console.log('步骤1: 选择本地GPU...');
  const selectElement = page.locator('.el-select').first();
  await selectElement.click();
  await page.waitForTimeout(500);
  const gpuOption = page.locator('div[role="option"]:has-text("本地GPU")');
  await gpuOption.click();

  console.log('步骤2: 输入测试文本...');
  const textarea = page.locator('textarea');
  await textarea.fill('调试 [object Object] 错误测试');

  console.log('步骤3: 点击生成按钮...');
  const generateButton = page.locator('button:has-text("生成视频")');

  // 在点击前截图
  await page.screenshot({ path: 'before-click-debug.png' });

  await generateButton.click();

  console.log('步骤4: 等待和处理结果...');

  // 等待一段时间让所有错误出现
  await page.waitForTimeout(10000);

  // 检查页面上的错误消息
  console.log('检查页面错误消息...');
  const errorElements = await page.$$('.el-message--error');
  for (let i = 0; i < errorElements.length; i++) {
    const errorText = await errorElements[i].textContent();
    console.log(`页面错误消息 ${i}:`, errorText);

    if (errorText.includes('[object Object]')) {
      console.log('🎯 找到 [object Object] 错误消息!');
      errors.push({
        type: 'page_error_message',
        text: errorText,
        element: await errorElements[i].innerHTML(),
        timestamp: new Date().toISOString()
      });
    }
  }

  // 获取页面注入的错误信息
  const injectedErrors = await page.evaluate(() => {
    return window.playwrightErrors || [];
  });

  console.log('注入的错误信息:', injectedErrors);
  errors.push(...injectedErrors);

  // 最终截图
  await page.screenshot({ path: 'final-debug-state.png' });

  // 输出详细的错误分析
  console.log('\n' + '='.repeat(50));
  console.log('🔍 错误分析报告');
  console.log('='.repeat(50));

  if (errors.length === 0) {
    console.log('✅ 没有发现任何错误');
  } else {
    console.log(`❌ 发现 ${errors.length} 个错误:`);

    errors.forEach((error, index) => {
      console.log(`\n错误 ${index + 1}:`);
      console.log(`  类型: ${error.type}`);
      console.log(`  时间: ${error.timestamp}`);

      if (error.message) {
        console.log(`  消息: ${error.message}`);
      }

      if (error.text) {
        console.log(`  文本: ${error.text}`);
      }

      if (error.args) {
        console.log(`  参数: ${error.args.join(', ')}`);
      }

      if (error.stack) {
        console.log(`  堆栈: ${error.stack}`);
      }

      if (error.body) {
        console.log(`  响应体: ${error.body}`);
      }
    });
  }

  console.log('\n🔵 控制台消息统计:');
  const logTypes = {};
  consoleMessages.forEach(msg => {
    logTypes[msg.type] = (logTypes[msg.type] || 0) + 1;
  });

  Object.entries(logTypes).forEach(([type, count]) => {
    console.log(`  ${type}: ${count} 条`);
  });

  // 断言检查
  expect(errors.length).toBe(0);
});