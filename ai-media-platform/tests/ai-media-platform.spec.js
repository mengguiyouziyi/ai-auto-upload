const { test, expect } = require('@playwright/test');

test.describe('AI媒体智能平台测试', () => {

  test.beforeEach(async ({ page }) => {
    // 设置超时时间
    test.setTimeout(30000);
  });

  test('前端页面加载测试', async ({ page }) => {
    console.log('🧪 测试前端页面加载...');

    // 访问前端页面
    await page.goto('http://localhost:5174');

    // 等待页面加载
    await page.waitForLoadState('networkidle');

    // 检查页面标题
    await expect(page).toHaveTitle(/AI媒体智能平台/);

    // 检查主要元素是否存在
    await expect(page.locator('.logo h2')).toContainText('AI媒体智能平台');

    // 检查导航菜单 - 使用更具体的选择器避免重复元素
    await expect(page.locator('.el-menu .el-menu-item:has-text("首页")')).toBeVisible();
    await expect(page.locator('.el-menu .el-menu-item:has-text("账号管理")')).toBeVisible();
    await expect(page.locator('.el-menu .el-menu-item:has-text("素材管理")')).toBeVisible();
    await expect(page.locator('.el-menu .el-menu-item:has-text("发布中心")')).toBeVisible();
    await expect(page.locator('.el-menu .el-menu-item:has-text("网站")')).toBeVisible();
    await expect(page.locator('.el-menu .el-menu-item:has-text("数据")')).toBeVisible();

    console.log('✅ 前端页面加载测试通过');
  });

  test('侧边栏功能测试', async ({ page }) => {
    console.log('🧪 测试侧边栏功能...');

    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // 检查侧边栏是否展开状态
    const sidebar = page.locator('.el-aside');
    await expect(sidebar).toBeVisible();

    // 点击折叠按钮
    await page.click('.toggle-sidebar');

    // 等待动画完成
    await page.waitForTimeout(300);

    // 检查是否折叠
    const collapsedSidebar = page.locator('.el-aside[style*="64px"]');
    await expect(collapsedSidebar).toBeVisible();

    console.log('✅ 侧边栏功能测试通过');
  });

  test('后端API连接测试', async ({ page }) => {
    console.log('🧪 测试前后端API连接...');

    await page.goto('http://localhost:5174');
    await page.waitForLoadState('networkidle');

    // 监听网络请求
    let apiCallSuccess = false;

    page.on('response', async (response) => {
      if (response.url().includes('localhost:9000')) {
        const status = response.status();
        if (status === 200) {
          apiCallSuccess = true;
          console.log(`✅ API调用成功: ${response.url()} - 状态码: ${status}`);
        }
      }
    });

    // 等待一会儿让前端尝试连接后端
    await page.waitForTimeout(2000);

    // 直接测试API连接
    try {
      const response = await page.evaluate(async () => {
        const res = await fetch('http://localhost:9000/health');
        return { status: res.status, data: await res.json() };
      });

      expect(response.status).toBe(200);
      expect(response.data.status).toBe('healthy');
      console.log('✅ 后端API连接测试通过');
    } catch (error) {
      console.log('❌ 后端API连接失败:', error.message);
      throw error;
    }
  });
});