const { chromium } = require('@playwright/test');

async function simpleManualTest() {
  console.log('Starting simple manual test...');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 1000 // Slow down actions
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to the frontend
    await page.goto('http://localhost:5175');
    console.log('✅ Navigated to frontend');

    // Wait for the page to load
    await page.waitForTimeout(3000);

    // Take screenshot of the initial state
    await page.screenshot({ path: '/tmp/manual_step_1_initial.png' });
    console.log('📸 Screenshot: Initial state saved');

    // Look for the "上传视频" (Upload Video) button using multiple selectors
    console.log('🔍 Looking for upload button...');

    const uploadSelectors = [
      'text="上传视频"',
      'button:has-text("上传视频")',
      '.el-button:has-text("上传视频")',
      '*:has-text("上传视频")'
    ];

    let uploadButton = null;
    for (const selector of uploadSelectors) {
      try {
        const element = page.locator(selector).first();
        if (await element.isVisible({ timeout: 2000 })) {
          uploadButton = element;
          console.log(`✅ Found upload button with selector: ${selector}`);
          break;
        }
      } catch (e) {
        continue;
      }
    }

    if (uploadButton) {
      await uploadButton.click();
      console.log('🖱️ Clicked upload button');

      // Wait for dialog to appear
      await page.waitForTimeout(2000);

      // Take screenshot after clicking upload button
      await page.screenshot({ path: '/tmp/manual_step_2_upload_options.png' });
      console.log('📸 Screenshot: Upload options dialog');

      // Check page content for debugging
      const pageContent = await page.content();
      const hasLocalUpload = pageContent.includes('本地上传');
      const hasMaterialLibrary = pageContent.includes('素材库');

      console.log(`🔍 Page content check:`);
      console.log(`  - Contains '本地上传': ${hasLocalUpload}`);
      console.log(`  - Contains '素材库': ${hasMaterialLibrary}`);

      // Try to find any element containing "本地上传"
      try {
        const localUploadElements = await page.locator('*:has-text("本地上传")').all();
        console.log(`🔍 Found ${localUploadElements.length} elements containing '本地上传'`);

        for (let i = 0; i < localUploadElements.length; i++) {
          const isVisible = await localUploadElements[i].isVisible();
          const tagName = await localUploadElements[i].evaluate(el => el.tagName);
          console.log(`  Element ${i}: ${tagName}, visible: ${isVisible}`);

          if (isVisible) {
            console.log(`✅ Clicking on visible element ${i}`);
            await localUploadElements[i].click();
            break;
          }
        }
      } catch (error) {
        console.log('❌ Error finding local upload elements:', error.message);
      }

      // Wait a bit and take another screenshot
      await page.waitForTimeout(2000);
      await page.screenshot({ path: '/tmp/manual_step_3_after_click.png' });
      console.log('📸 Screenshot: After attempting to click local upload');

    } else {
      console.log('❌ Upload button not found');
    }

  } catch (error) {
    console.error('❌ Error during test:', error);
  } finally {
    // Keep browser open for manual inspection for 10 seconds
    console.log('⏸️ Keeping browser open for 10 seconds for manual inspection...');
    await page.waitForTimeout(10000);
    await browser.close();
    console.log('🏁 Test completed');
  }
}

simpleManualTest();