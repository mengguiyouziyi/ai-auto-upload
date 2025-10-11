const { test, expect, devices } = require('@playwright/test');
const path = require('path');

test.describe('Publish Center Upload Functionality Test', () => {
  let page;
  const baseUrl = 'http://localhost:5176';

  test.beforeAll(async ({ browser }) => {
    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      recordVideo: { dir: './test-results/videos' }
    });
    page = await context.newPage();
  });

  test.afterAll(async () => {
    await page.close();
  });

  test('Navigate to Publish Center and analyze upload dialog', async () => {
    console.log('🚀 Starting Publish Center upload functionality test...');

    // Step 1: Navigate to the application
    console.log('📍 Navigating to application...');
    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000); // Wait for page to fully load

    // Take initial screenshot
    await page.screenshot({
      path: './test-results/screenshots/01-homepage.png',
      fullPage: true
    });
    console.log('✅ Homepage screenshot taken');

    // Step 2: Find and navigate to Publish Center
    console.log('🔍 Looking for Publish Center navigation...');

    // Try different selectors for the publish center
    const publishCenterSelectors = [
      'text=发布中心',
      '[data-testid="publish-center"]',
      '.nav-item:has-text("发布中心")',
      'a[href*="publish"]',
      'button:has-text("发布中心")',
      '.menu-item:has-text("发布中心")'
    ];

    let publishCenterFound = false;
    for (const selector of publishCenterSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible()) {
          console.log(`✅ Found Publish Center with selector: ${selector}`);
          await element.click();
          publishCenterFound = true;
          break;
        }
      } catch (error) {
        // Continue to next selector
      }
    }

    if (!publishCenterFound) {
      // Try to find by searching in the entire page
      const allElements = await page.locator('*').all();
      for (const element of allElements) {
        try {
          const text = await element.textContent();
          if (text && text.includes('发布中心')) {
            console.log('✅ Found Publish Center by text content');
            await element.click();
            publishCenterFound = true;
            break;
          }
        } catch (error) {
          // Continue
        }
      }
    }

    if (!publishCenterFound) {
      console.log('❌ Publish Center not found, taking screenshot for debugging...');
      await page.screenshot({
        path: './test-results/screenshots/publish-center-not-found.png',
        fullPage: true
      });
      throw new Error('Could not find Publish Center navigation');
    }

    // Wait for navigation
    await page.waitForTimeout(2000);

    // Take screenshot after navigation
    await page.screenshot({
      path: './test-results/screenshots/02-publish-center-page.png',
      fullPage: true
    });

    // Step 3: Look for Video tab
    console.log('🎥 Looking for Video tab...');

    const videoTabSelectors = [
      'text=视频',
      '[data-testid="video-tab"]',
      '.tab:has-text("视频")',
      'button:has-text("视频")',
      '.nav-tab:has-text("视频")',
      'li:has-text("视频")'
    ];

    let videoTabFound = false;
    for (const selector of videoTabSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible({ timeout: 1000 })) {
          console.log(`✅ Found Video tab with selector: ${selector}`);
          await element.click();
          videoTabFound = true;
          break;
        }
      } catch (error) {
        // Continue to next selector
      }
    }

    if (!videoTabFound) {
      console.log('❌ Video tab not found, taking screenshot for debugging...');
      await page.screenshot({
        path: './test-results/screenshots/video-tab-not-found.png',
        fullPage: true
      });
      throw new Error('Could not find Video tab');
    }

    await page.waitForTimeout(1500);

    // Step 4: Look for Local Upload button
    console.log('📁 Looking for Local Upload button...');

    const localUploadSelectors = [
      'text=本地上传',
      '[data-testid="local-upload"]',
      'button:has-text("本地上传")',
      '.upload-btn:has-text("本地上传")',
      '.local-upload-btn',
      'div:has-text("本地上传")'
    ];

    let localUploadFound = false;
    for (const selector of localUploadSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible({ timeout: 1000 })) {
          console.log(`✅ Found Local Upload with selector: ${selector}`);
          await element.click();
          localUploadFound = true;
          break;
        }
      } catch (error) {
        // Continue to next selector
      }
    }

    if (!localUploadFound) {
      console.log('❌ Local Upload button not found, taking screenshot for debugging...');
      await page.screenshot({
        path: './test-results/screenshots/local-upload-not-found.png',
        fullPage: true
      });
      throw new Error('Could not find Local Upload button');
    }

    await page.waitForTimeout(2000);

    // Step 5: Analyze the upload dialog
    console.log('🔍 Analyzing upload dialog...');

    // Take screenshot of the upload dialog
    await page.screenshot({
      path: './test-results/screenshots/03-upload-dialog.png',
      fullPage: true
    });

    // Look for upload dialog/container
    const dialogSelectors = [
      '.el-dialog',
      '.upload-dialog',
      '.modal',
      '.popup',
      '[role="dialog"]',
      '.upload-container',
      '.upload-modal'
    ];

    let uploadDialog = null;
    for (const selector of dialogSelectors) {
      try {
        const element = await page.locator(selector).first();
        if (await element.isVisible({ timeout: 1000 })) {
          uploadDialog = element;
          console.log(`✅ Found upload dialog with selector: ${selector}`);
          break;
        }
      } catch (error) {
        // Continue
      }
    }

    if (uploadDialog) {
      // Get dialog dimensions
      const dialogBox = await uploadDialog.boundingBox();
      console.log(`📐 Upload dialog dimensions: ${JSON.stringify(dialogBox)}`);

      // Look for upload buttons inside the dialog
      const uploadButtonSelectors = [
        'button:has-text("上传")',
        'button:has-text("选择文件")',
        'button:has-text("Select File")',
        'button:has-text("Upload")',
        '.el-upload',
        '.upload-button',
        '.file-select-btn',
        'input[type="file"]',
        '.el-upload__input'
      ];

      console.log('🔍 Searching for upload buttons...');
      let uploadButtonsFound = [];

      for (const selector of uploadButtonSelectors) {
        try {
          const elements = await uploadDialog.locator(selector).all();
          for (const element of elements) {
            if (await element.isVisible()) {
              const box = await element.boundingBox();
              const text = await element.textContent();
              uploadButtonsFound.push({
                selector,
                text: text || 'No text',
                visible: true,
                dimensions: box
              });
              console.log(`✅ Found upload button: ${selector} - Text: "${text}" - Dimensions: ${JSON.stringify(box)}`);
            } else {
              // Check if element exists but is hidden
              const exists = await element.count() > 0;
              if (exists) {
                uploadButtonsFound.push({
                  selector,
                  text: 'Hidden element',
                  visible: false,
                  dimensions: null
                });
                console.log(`⚠️ Found hidden upload button: ${selector}`);
              }
            }
          }
        } catch (error) {
          // Continue
        }
      }

      // Look for Element Plus el-upload components
      console.log('🔍 Searching for Element Plus el-upload components...');
      const elUploadComponents = await uploadDialog.locator('.el-upload').all();
      console.log(`📊 Found ${elUploadComponents.length} el-upload components`);

      for (let i = 0; i < elUploadComponents.length; i++) {
        const component = elUploadComponents[i];
        const isVisible = await component.isVisible();
        const box = isVisible ? await component.boundingBox() : null;
        const innerHTML = await component.innerHTML();

        console.log(`📋 el-upload component ${i + 1}:`);
        console.log(`   - Visible: ${isVisible}`);
        console.log(`   - Dimensions: ${JSON.stringify(box)}`);
        console.log(`   - Content preview: ${innerHTML.substring(0, 200)}...`);

        // Take screenshot of individual component
        if (isVisible && box) {
          await page.screenshot({
            path: `./test-results/screenshots/el-upload-component-${i + 1}.png`,
            clip: box
          });
        }
      }

      // Look for drag-and-drop areas
      console.log('🔍 Searching for drag-and-drop areas...');
      const dragDropSelectors = [
        '.upload-dragger',
        '.el-upload-dragger',
        '.drop-zone',
        '.upload-area',
        '[data-testid="upload-area"]'
      ];

      for (const selector of dragDropSelectors) {
        try {
          const elements = await uploadDialog.locator(selector).all();
          for (const element of elements) {
            if (await element.isVisible()) {
              const box = await element.boundingBox();
              console.log(`✅ Found drag-drop area: ${selector} - Dimensions: ${JSON.stringify(box)}`);

              // Take screenshot of drag-drop area
              await page.screenshot({
                path: `./test-results/screenshots/drag-drop-${selector.replace(/[^a-zA-Z0-9]/g, '-')}.png`,
                clip: box
              });
            }
          }
        } catch (error) {
          // Continue
        }
      }

      // Check CSS styles that might be hiding buttons
      console.log('🎨 Checking CSS styles...');
      const allButtons = await uploadDialog.locator('button').all();
      for (let i = 0; i < allButtons.length; i++) {
        const button = allButtons[i];
        const isVisible = await button.isVisible();
        const computedStyle = await button.evaluate((el) => {
          const styles = window.getComputedStyle(el);
          return {
            display: styles.display,
            visibility: styles.visibility,
            opacity: styles.opacity,
            width: styles.width,
            height: styles.height,
            zIndex: styles.zIndex,
            position: styles.position
          };
        });

        console.log(`🔘 Button ${i + 1} styles:`, computedStyle);
      }

    } else {
      console.log('❌ No upload dialog found');

      // Take a screenshot of the entire page for debugging
      await page.screenshot({
        path: './test-results/screenshots/no-upload-dialog-found.png',
        fullPage: true
      });
    }

    // Step 6: Generate HTML structure report
    console.log('📄 Generating HTML structure report...');
    const pageHTML = await page.content();
    require('fs').writeFileSync('./test-results/page-structure.html', pageHTML);

    // Get computed styles for the entire page
    const pageStructure = await page.evaluate(() => {
      const getAllElements = (selector) => {
        const elements = Array.from(document.querySelectorAll(selector));
        return elements.map(el => ({
          tagName: el.tagName,
          className: el.className,
          id: el.id,
          textContent: el.textContent?.substring(0, 100),
          isVisible: el.offsetParent !== null,
          computedStyle: {
            display: window.getComputedStyle(el).display,
            visibility: window.getComputedStyle(el).visibility,
            opacity: window.getComputedStyle(el).opacity
          }
        }));
      };

      return {
        uploadButtons: getAllElements('button'),
        uploadInputs: getAllElements('input[type="file"]'),
        elUploadComponents: getAllElements('.el-upload'),
        dialogs: getAllElements('[role="dialog"], .el-dialog, .modal')
      };
    });

    require('fs').writeFileSync(
      './test-results/page-structure.json',
      JSON.stringify(pageStructure, null, 2)
    );

    console.log('✅ Test completed successfully!');
    console.log('📁 Check test-results/ directory for screenshots and reports');

    // Final screenshot
    await page.screenshot({
      path: './test-results/screenshots/final-state.png',
      fullPage: true
    });
  });
});