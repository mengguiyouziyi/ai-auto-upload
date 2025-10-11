const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

async function testUploadFunctionality() {
  console.log('🚀 Starting Publish Center upload functionality test...');

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
    slowMo: 1000 // Slow down actions for better visibility
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
      path: path.join(screenshotsDir, '01-homepage.png'),
      fullPage: true
    });
    console.log('✅ Homepage screenshot taken');

    // Step 2: Look for navigation elements
    console.log('🔍 Analyzing page structure...');

    // Get all navigation elements
    const navElements = await page.evaluate(() => {
      const elements = [];
      const allElements = document.querySelectorAll('*');

      allElements.forEach(el => {
        const text = el.textContent?.trim();
        if (text && (text.includes('发布') || text.includes('中心') || text.includes('Publish') || text.includes('Center'))) {
          const rect = el.getBoundingClientRect();
          elements.push({
            tag: el.tagName,
            text: text.substring(0, 50),
            className: el.className,
            id: el.id,
            visible: rect.width > 0 && rect.height > 0,
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

    console.log('📋 Found navigation elements:', JSON.stringify(navElements, null, 2));

    // Try to find and click on publish center
    let publishCenterClicked = false;

    for (const element of navElements) {
      if (element.visible && (element.text.includes('发布中心') || element.text.includes('发布'))) {
        try {
          console.log(`✅ Attempting to click on: ${element.text}`);

          // Try different selectors
          const selectors = [
            `text="${element.text.substring(0, 20)}"`,
            `[class*="${element.className.split(' ').find(c => c.includes('publish') || c.includes('nav'))}"]`,
            `${element.tag.toLowerCase()}:has-text("${element.text.substring(0, 20)}")`
          ];

          for (const selector of selectors) {
            try {
              const el = await page.locator(selector).first();
              if (await el.isVisible()) {
                await el.click();
                publishCenterClicked = true;
                console.log(`✅ Successfully clicked with selector: ${selector}`);
                break;
              }
            } catch (e) {
              // Continue trying
            }
          }

          if (publishCenterClicked) break;
        } catch (error) {
          console.log(`❌ Failed to click on element: ${error.message}`);
        }
      }
    }

    if (!publishCenterClicked) {
      console.log('⚠️ Could not find publish center navigation, taking screenshot of current state...');
      await page.screenshot({
        path: path.join(screenshotsDir, 'publish-center-not-found.png'),
        fullPage: true
      });
    } else {
      await page.waitForTimeout(2000);

      // Take screenshot after navigation
      await page.screenshot({
        path: path.join(screenshotsDir, '02-after-navigation.png'),
        fullPage: true
      });

      // Step 3: Look for tabs and upload buttons
      console.log('🎥 Looking for Video tab and Upload options...');

      const pageElements = await page.evaluate(() => {
        const elements = [];
        const allElements = document.querySelectorAll('*');

        allElements.forEach(el => {
          const text = el.textContent?.trim();
          if (text && (
            text.includes('视频') || text.includes('上传') || text.includes('本地') ||
            text.includes('Video') || text.includes('Upload') || text.includes('Local')
          )) {
            const rect = el.getBoundingClientRect();
            const styles = window.getComputedStyle(el);

            elements.push({
              tag: el.tagName,
              text: text.substring(0, 50),
              className: el.className,
              id: el.id,
              visible: rect.width > 0 && rect.height > 0 && styles.display !== 'none' && styles.visibility !== 'hidden',
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
              }
            });
          }
        });

        return elements;
      });

      console.log('📋 Found relevant elements:', JSON.stringify(pageElements, null, 2));

      // Look specifically for Element Plus upload components
      const uploadComponents = await page.evaluate(() => {
        const components = [];

        // Find el-upload components
        const elUploads = document.querySelectorAll('.el-upload');
        elUploads.forEach((el, index) => {
          const rect = el.getBoundingClientRect();
          const styles = window.getComputedStyle(el);

          components.push({
            type: 'el-upload',
            index: index,
            className: el.className,
            visible: rect.width > 0 && rect.height > 0 && styles.display !== 'none',
            rect: {
              x: rect.x,
              y: rect.y,
              width: rect.width,
              height: rect.height
            },
            innerHTML: el.innerHTML.substring(0, 200),
            buttons: el.querySelectorAll('button').length,
            inputs: el.querySelectorAll('input[type="file"]').length
          });
        });

        // Find drag-drop areas
        const draggers = document.querySelectorAll('.el-upload-dragger, .upload-dragger');
        draggers.forEach((el, index) => {
          const rect = el.getBoundingClientRect();
          const styles = window.getComputedStyle(el);

          components.push({
            type: 'upload-dragger',
            index: index,
            className: el.className,
            visible: rect.width > 0 && rect.height > 0 && styles.display !== 'none',
            rect: {
              x: rect.x,
              y: rect.y,
              width: rect.width,
              height: rect.height
            },
            innerHTML: el.innerHTML.substring(0, 200)
          });
        });

        // Find dialogs
        const dialogs = document.querySelectorAll('.el-dialog, [role="dialog"], .modal');
        dialogs.forEach((el, index) => {
          const rect = el.getBoundingClientRect();
          const styles = window.getComputedStyle(el);

          components.push({
            type: 'dialog',
            index: index,
            className: el.className,
            visible: rect.width > 0 && rect.height > 0 && styles.display !== 'none',
            rect: {
              x: rect.x,
              y: rect.y,
              width: rect.width,
              height: rect.height
            },
            innerHTML: el.innerHTML.substring(0, 300)
          });
        });

        return components;
      });

      console.log('📋 Upload components found:', JSON.stringify(uploadComponents, null, 2));

      // Try to click on Video tab
      let videoTabClicked = false;
      for (const element of pageElements) {
        if (element.visible && element.text.includes('视频')) {
          try {
            const selector = `${element.tag.toLowerCase()}:has-text("${element.text.substring(0, 20)}")`;
            const el = await page.locator(selector).first();
            if (await el.isVisible()) {
              await el.click();
              videoTabClicked = true;
              console.log(`✅ Clicked on Video tab`);
              await page.waitForTimeout(1500);
              break;
            }
          } catch (error) {
            console.log(`❌ Failed to click Video tab: ${error.message}`);
          }
        }
      }

      // Try to click on Local Upload
      let localUploadClicked = false;
      for (const element of pageElements) {
        if (element.visible && element.text.includes('本地上传')) {
          try {
            const selector = `${element.tag.toLowerCase()}:has-text("${element.text.substring(0, 20)}")`;
            const el = await page.locator(selector).first();
            if (await el.isVisible()) {
              await el.click();
              localUploadClicked = true;
              console.log(`✅ Clicked on Local Upload`);
              await page.waitForTimeout(2000);
              break;
            }
          } catch (error) {
            console.log(`❌ Failed to click Local Upload: ${error.message}`);
          }
        }
      }

      // Take final screenshot
      await page.screenshot({
        path: path.join(screenshotsDir, '03-final-state.png'),
        fullPage: true
      });

      // Generate detailed report
      const report = {
        timestamp: new Date().toISOString(),
        baseUrl: baseUrl,
        navElements: navElements,
        pageElements: pageElements,
        uploadComponents: uploadComponents,
        publishCenterClicked: publishCenterClicked,
        videoTabClicked: videoTabClicked,
        localUploadClicked: localUploadClicked
      };

      fs.writeFileSync(
        path.join(testResultsDir, 'upload-test-report.json'),
        JSON.stringify(report, null, 2)
      );

      console.log('✅ Test completed successfully!');
      console.log('📁 Check test-results/ directory for screenshots and report');
      console.log(`📊 Found ${uploadComponents.length} upload components`);
      console.log(`🎯 Publish Center clicked: ${publishCenterClicked}`);
      console.log(`🎥 Video tab clicked: ${videoTabClicked}`);
      console.log(`📁 Local Upload clicked: ${localUploadClicked}`);
    }

  } catch (error) {
    console.error('❌ Test failed:', error);

    // Take error screenshot
    await page.screenshot({
      path: path.join(screenshotsDir, 'error-screenshot.png'),
      fullPage: true
    });

  } finally {
    await browser.close();
  }
}

// Run the test
testUploadFunctionality().catch(console.error);