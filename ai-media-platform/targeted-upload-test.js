const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

async function testTargetedUploadFunctionality() {
  console.log('🚀 Starting Targeted Upload Functionality Test...');

  // Create test results directory
  const testResultsDir = './test-results';
  const screenshotsDir = path.join(testResultsDir, 'screenshots');

  if (!fs.existsSync(testResultsDir)) {
    fs.mkdirSync(testResultsDir, { recursive: true });
  }
  if (!fs.existsSync(screenshotsDir)) {
    fs.mkdirSync(screenshotsDir, { recursive: true });
  }

  const browser = await chromium.launch({
    headless: false, // Show the browser
    slowMo: 500 // Slow down actions for better visibility
  });

  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });

  const page = await context.newPage();
  const baseUrl = 'http://localhost:5176';

  try {
    // Step 1: Navigate to the application
    console.log('📍 Navigating to application...');
    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Take initial screenshot
    await page.screenshot({
      path: path.join(screenshotsDir, 'targeted-01-homepage.png'),
      fullPage: true
    });
    console.log('✅ Homepage screenshot taken');

    // Step 2: Click on the "内容上传" (Content Upload) card
    console.log('📁 Looking for Content Upload card...');

    const contentUploadCard = await page.locator('div:has-text("内容上传")').first();
    if (await contentUploadCard.isVisible()) {
      console.log('✅ Found Content Upload card');
      await contentUploadCard.click();
      await page.waitForTimeout(2000);

      // Take screenshot after clicking content upload
      await page.screenshot({
        path: path.join(screenshotsDir, 'targeted-02-after-content-upload-click.png'),
        fullPage: true
      });

      // Check if any dialog/modal appeared
      const dialogAppeared = await page.locator('.el-dialog, [role="dialog"], .modal').isVisible();
      console.log(`🔍 Dialog appeared after click: ${dialogAppeared}`);

      if (dialogAppeared) {
        // Take screenshot of dialog
        const dialogBox = await page.locator('.el-dialog, [role="dialog"], .modal').boundingBox();
        await page.screenshot({
          path: path.join(screenshotsDir, 'targeted-03-upload-dialog.png'),
          clip: dialogBox
        });
        console.log('✅ Dialog screenshot taken');
      }
    }

    // Step 3: Try to find hidden or collapsed upload functionality
    console.log('🔍 Searching for hidden upload elements...');

    const allUploadElements = await page.evaluate(() => {
      const elements = [];
      const allElements = document.querySelectorAll('*');

      allElements.forEach(el => {
        const text = el.textContent?.trim();
        const className = el.className;

        // Look for upload-related elements
        if (text && (
          text.includes('本地上传') || text.includes('本地') || text.includes('上传') ||
          text.includes('Local') || text.includes('Upload') ||
          className.includes('upload') ||
          el.tagName === 'INPUT' && el.type === 'file'
        )) {
          const rect = el.getBoundingClientRect();
          const styles = window.getComputedStyle(el);
          const isVisible = rect.width > 0 && rect.height > 0 &&
                           styles.display !== 'none' &&
                           styles.visibility !== 'hidden' &&
                           styles.opacity !== '0';

          elements.push({
            tag: el.tagName,
            text: text?.substring(0, 50) || 'No text',
            className: className,
            id: el.id,
            visible: isVisible,
            rect: {
              x: rect.x,
              y: rect.y,
              width: rect.width,
              height: rect.height
            },
            styles: {
              display: styles.display,
              visibility: styles.visibility,
              opacity: styles.opacity,
              zIndex: styles.zIndex
            },
            isFileInput: el.tagName === 'INPUT' && el.type === 'file',
            isElUpload: className.includes('el-upload'),
            isDialog: className.includes('dialog') || el.role === 'dialog'
          });
        }
      });

      return elements;
    });

    console.log(`📋 Found ${allUploadElements.length} upload-related elements:`);
    allUploadElements.forEach((el, index) => {
      console.log(`   ${index + 1}. ${el.tag} - "${el.text}" - Visible: ${el.visible} - Class: ${el.className}`);
    });

    // Step 4: Try to click on any visible upload elements
    for (let i = 0; i < allUploadElements.length; i++) {
      const element = allUploadElements[i];
      if (element.visible && (element.text.includes('上传') || element.text.includes('本地'))) {
        try {
          console.log(`🎯 Attempting to click on: ${element.text}`);

          let selector;
          if (element.isFileInput) {
            selector = 'input[type="file"]';
          } else if (element.isElUpload) {
            selector = '.el-upload';
          } else {
            selector = `${element.tag.toLowerCase()}:has-text("${element.text.substring(0, 20)}")`;
          }

          const el = await page.locator(selector).first();
          if (await el.isVisible()) {
            await el.click();
            await page.waitForTimeout(2000);

            // Take screenshot after click
            await page.screenshot({
              path: path.join(screenshotsDir, `targeted-04-after-upload-click-${i}.png`),
              fullPage: true
            });

            // Check for file dialog
            const fileDialogAppeared = await page.locator('.el-dialog, [role="dialog"], .modal').isVisible();
            console.log(`   Dialog appeared: ${fileDialogAppeared}`);

            if (fileDialogAppeared) {
              const dialogBox = await page.locator('.el-dialog, [role="dialog"], .modal').boundingBox();
              await page.screenshot({
                path: path.join(screenshotsDir, `targeted-05-upload-dialog-${i}.png`),
                clip: dialogBox
              });
            }
          }
        } catch (error) {
          console.log(`   ❌ Failed to click: ${error.message}`);
        }
      }
    }

    // Step 5: Try to expand AI创作 menu to access 视频生成
    console.log('🎥 Trying to expand AI Creation menu...');

    const aiCreationMenu = await page.locator('.el-sub-menu:has-text("AI创作")').first();
    if (await aiCreationMenu.isVisible()) {
      console.log('✅ Found AI Creation menu, attempting to expand...');
      await aiCreationMenu.click();
      await page.waitForTimeout(1000);

      // Look for video generation option
      const videoGeneration = await page.locator('.el-menu-item:has-text("视频生成")').first();
      if (await videoGeneration.isVisible()) {
        console.log('✅ Found Video Generation option');
        await videoGeneration.click();
        await page.waitForTimeout(2000);

        // Take screenshot
        await page.screenshot({
          path: path.join(screenshotsDir, 'targeted-06-video-generation-page.png'),
          fullPage: true
        });

        // Check for upload functionality on video generation page
        const videoPageUploadElements = await page.evaluate(() => {
          const elements = [];
          const allElements = document.querySelectorAll('*');

          allElements.forEach(el => {
            const text = el.textContent?.trim();
            const className = el.className;

            if (text && (
              text.includes('本地上传') || text.includes('上传文件') || text.includes('选择文件') ||
              text.includes('Local Upload') || text.includes('Select File') ||
              className.includes('upload') ||
              el.tagName === 'INPUT' && el.type === 'file'
            )) {
              const rect = el.getBoundingClientRect();
              const styles = window.getComputedStyle(el);
              const isVisible = rect.width > 0 && rect.height > 0 &&
                               styles.display !== 'none' &&
                               styles.visibility !== 'hidden';

              elements.push({
                tag: el.tagName,
                text: text?.substring(0, 50) || 'No text',
                className: className,
                id: el.id,
                visible: isVisible,
                rect: {
                  x: rect.x,
                  y: rect.y,
                  width: rect.width,
                  height: rect.height
                }
              });
            }
          });

          return elements;
        });

        console.log(`📋 Found ${videoPageUploadElements.length} upload elements on video generation page`);
        videoPageUploadElements.forEach((el, index) => {
          console.log(`   ${index + 1}. ${el.tag} - "${el.text}" - Visible: ${el.visible}`);
        });
      }
    }

    // Step 6: Generate final comprehensive report
    const finalReport = {
      timestamp: new Date().toISOString(),
      baseUrl: baseUrl,
      uploadElementsFound: allUploadElements.length,
      visibleUploadElements: allUploadElements.filter(el => el.visible).length,
      hiddenUploadElements: allUploadElements.filter(el => !el.visible).length,
      fileInputsFound: allUploadElements.filter(el => el.isFileInput).length,
      elUploadComponentsFound: allUploadElements.filter(el => el.isElUpload).length,
      uploadElements: allUploadElements
    };

    fs.writeFileSync(
      path.join(testResultsDir, 'targeted-upload-test-report.json'),
      JSON.stringify(finalReport, null, 2)
    );

    console.log('✅ Targeted test completed successfully!');
    console.log('📁 Check test-results/ directory for screenshots and detailed report');
    console.log(`📊 Total upload-related elements found: ${allUploadElements.length}`);
    console.log(`👁️ Visible upload elements: ${allUploadElements.filter(el => el.visible).length}`);
    console.log(`🙈 Hidden upload elements: ${allUploadElements.filter(el => !el.visible).length}`);

    // Take final screenshot
    await page.screenshot({
      path: path.join(screenshotsDir, 'targeted-07-final-state.png'),
      fullPage: true
    });

  } catch (error) {
    console.error('❌ Test failed:', error);

    // Take error screenshot
    await page.screenshot({
      path: path.join(screenshotsDir, 'targeted-error-screenshot.png'),
      fullPage: true
    });

  } finally {
    await browser.close();
  }
}

// Run the test
testTargetedUploadFunctionality().catch(console.error);