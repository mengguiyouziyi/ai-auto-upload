const { chromium } = require('@playwright/test');

async function testUploadDialog() {
  console.log('Starting upload dialog test...');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to the frontend
    await page.goto('http://localhost:5175');
    console.log('✅ Navigated to frontend');

    // Wait for the page to load
    await page.waitForTimeout(2000);

    // Take a screenshot of the initial state
    await page.screenshot({ path: '/tmp/test_step_1_initial.png' });
    console.log('📸 Screenshot: Initial state saved');

    // Look for the "上传视频" (Upload Video) button
    const uploadButton = await page.locator('text=上传视频').first();
    if (await uploadButton.isVisible()) {
      console.log('✅ Found upload button');
      await uploadButton.click();
      console.log('🖱️ Clicked upload button');

      // Wait for dialog to appear
      await page.waitForTimeout(2000);

      // Take screenshot after clicking upload button
      await page.screenshot({ path: '/tmp/test_step_2_upload_options.png' });
      console.log('📸 Screenshot: Upload options dialog');

      // Debug: check what elements are present
      console.log('🔍 Looking for elements with text "本地上传"...');

      // Try different selectors for the local upload button
      const selectors = [
        'text="本地上传"',
        '.el-button:has-text("本地上传")',
        '[role="button"]:has-text("本地上传")',
        '*:has-text("本地上传")'
      ];

      let localUploadButton = null;
      for (const selector of selectors) {
        const element = page.locator(selector).first();
        if (await element.isVisible()) {
          localUploadButton = element;
          console.log(`✅ Found local upload button with selector: ${selector}`);
          break;
        }
      }

      if (localUploadButton) {
        console.log('✅ Found local upload button');
        await localUploadButton.click();
        console.log('🖱️ Clicked local upload button');

        // Wait for upload dialog to appear
        await page.waitForTimeout(1000);

        // Take screenshot of the upload dialog
        await page.screenshot({ path: '/tmp/test_step_3_upload_dialog.png' });
        console.log('📸 Screenshot: Upload dialog');

        // Check for dialog elements
        const dragDropArea = await page.locator('.el-upload-dragger').first();
        const confirmButton = await page.locator('text=确定').first();
        const cancelButton = await page.locator('text=取消').first();

        console.log('🔍 Checking dialog elements:');
        console.log(`  - Drag & drop area visible: ${await dragDropArea.isVisible()}`);
        console.log(`  - Confirm button visible: ${await confirmButton.isVisible()}`);
        console.log(`  - Cancel button visible: ${await cancelButton.isVisible()}`);

        // Check confirm button text (should show count)
        const confirmButtonText = await confirmButton.textContent();
        console.log(`  - Confirm button text: "${confirmButtonText}"`);

        if (await dragDropArea.isVisible()) {
          console.log('✅ Drag and drop area is visible');

          // Try to simulate file selection by creating a test file
          const fileInput = await page.locator('input[type="file"]').first();
          if (await fileInput.isVisible()) {
            console.log('✅ File input found');

            // Check if we have any test video files available
            const testFiles = [
              '/Users/sunyouyou/Desktop/projects/bzhi/ai-auto-upload/ai-media-platform/test_video.mp4'
            ];

            let testFile = null;
            for (const file of testFiles) {
              try {
                const fs = require('fs');
                if (fs.existsSync(file)) {
                  testFile = file;
                  break;
                }
              } catch (e) {
                continue;
              }
            }

            if (testFile) {
              console.log(`📁 Using test file: ${testFile}`);
              await fileInput.setInputFiles(testFile);
              console.log('📁 File selected');

              // Wait for file to be processed
              await page.waitForTimeout(2000);

              // Take screenshot after file selection
              await page.screenshot({ path: '/tmp/test_step_4_file_selected.png' });
              console.log('📸 Screenshot: File selected');

              // Check confirm button text again (should show count)
              const confirmButtonTextAfter = await confirmButton.textContent();
              console.log(`  - Confirm button text after file selection: "${confirmButtonTextAfter}"`);

              // Try to click confirm button
              if (await confirmButton.isEnabled()) {
                console.log('✅ Confirm button is enabled');
                await confirmButton.click();
                console.log('🖱️ Clicked confirm button');

                // Wait for upload to complete
                await page.waitForTimeout(3000);

                // Take screenshot after upload
                await page.screenshot({ path: '/tmp/test_step_5_after_upload.png' });
                console.log('📸 Screenshot: After upload');

                // Check if dialog closed and files appear in main interface
                const uploadedFiles = await page.locator('.uploaded-files').first();
                if (await uploadedFiles.isVisible()) {
                  console.log('✅ Uploaded files section is visible in main interface');
                } else {
                  console.log('❌ Uploaded files section not found');
                }
              } else {
                console.log('❌ Confirm button is not enabled');
              }
            } else {
              console.log('❌ No test video file found');
            }
          } else {
            console.log('❌ File input not found');
          }
        } else {
          console.log('❌ Drag and drop area not visible');
        }
      } else {
        console.log('❌ Local upload button not found');
      }
    } else {
      console.log('❌ Upload button not found');
    }

  } catch (error) {
    console.error('❌ Error during test:', error);
  } finally {
    await browser.close();
    console.log('🏁 Test completed');
  }
}

testUploadDialog();