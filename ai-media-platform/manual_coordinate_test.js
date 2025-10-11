const { chromium } = require('@playwright/test');

async function manualCoordinateTest() {
  console.log('Starting manual coordinate test...');

  const browser = await chromium.launch({
    headless: false,
    slowMo: 500
  });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to the frontend
    await page.goto('http://localhost:5175');
    console.log('✅ Navigated to frontend');

    // Wait for the page to load
    await page.waitForTimeout(3000);

    // Get page dimensions
    const viewport = page.viewportSize();
    console.log(`📐 Page viewport: ${viewport.width}x${viewport.height}`);

    // Take screenshot of the initial state
    await page.screenshot({ path: '/tmp/coord_step_1_initial.png' });
    console.log('📸 Screenshot: Initial state saved');

    // Look for and click the upload button
    const uploadButton = page.locator('*:has-text("上传视频")').first();
    await uploadButton.click();
    console.log('🖱️ Clicked upload button');

    await page.waitForTimeout(2000);

    // Take screenshot of the upload options dialog
    await page.screenshot({ path: '/tmp/coord_step_2_options.png' });
    console.log('📸 Screenshot: Upload options dialog');

    // Try to find the dialog using its class name from the Vue component
    console.log('🔍 Looking for upload options dialog...');

    try {
      // The dialog should have class .upload-options-dialog
      const dialog = page.locator('.upload-options-dialog').first();
      const isDialogVisible = await dialog.isVisible({ timeout: 3000 });
      console.log(`📊 Dialog visibility: ${isDialogVisible}`);

      if (isDialogVisible) {
        // Get dialog position and size
        const dialogBox = await dialog.boundingBox();
        console.log(`📏 Dialog position: x=${dialogBox.x}, y=${dialogBox.y}, width=${dialogBox.width}, height=${dialogBox.height}`);

        // Try to click in the middle of where the "本地上传" button should be
        // Based on the screenshot, it should be in the upper half of the dialog
        const localUploadX = dialogBox.x + dialogBox.width / 2;
        const localUploadY = dialogBox.y + dialogBox.height / 3;

        console.log(`🖱️ Clicking at coordinates: x=${localUploadX}, y=${localUploadY}`);
        await page.mouse.click(localUploadX, localUploadY);
        console.log('🖱️ Clicked on local upload area');

        await page.waitForTimeout(2000);

        // Take screenshot after clicking
        await page.screenshot({ path: '/tmp/coord_step_3_after_click.png' });
        console.log('📸 Screenshot: After clicking local upload');

        // Check if we can find the local upload dialog
        console.log('🔍 Looking for local upload dialog...');
        const localUploadDialog = page.locator('.local-upload-dialog').first();
        const isLocalUploadVisible = await localUploadDialog.isVisible({ timeout: 3000 });
        console.log(`📊 Local upload dialog visibility: ${isLocalUploadVisible}`);

        if (isLocalUploadVisible) {
          console.log('✅ Found local upload dialog!');

          // Take screenshot of the local upload dialog
          await page.screenshot({ path: '/tmp/coord_step_4_local_upload_dialog.png' });
          console.log('📸 Screenshot: Local upload dialog');

          // Check for drag and drop area
          const dragDropArea = page.locator('.el-upload-dragger').first();
          const isDragDropVisible = await dragDropArea.isVisible({ timeout: 3000 });
          console.log(`📊 Drag & drop area visibility: ${isDragDropVisible}`);

          // Check for buttons
          const confirmButton = page.locator('button:has-text("确定")').first();
          const cancelButton = page.locator('button:has-text("取消")').first();

          const isConfirmVisible = await confirmButton.isVisible({ timeout: 3000 });
          const isCancelVisible = await cancelButton.isVisible({ timeout: 3000 });

          console.log(`📊 Confirm button visibility: ${isConfirmVisible}`);
          console.log(`📊 Cancel button visibility: ${isCancelVisible}`);

          if (isConfirmVisible) {
            const confirmText = await confirmButton.textContent();
            console.log(`📊 Confirm button text: "${confirmText}"`);
          }

          console.log('✅ All dialog elements checked successfully!');

        } else {
          console.log('❌ Local upload dialog not found');
        }
      } else {
        console.log('❌ Upload options dialog not found');
      }

    } catch (error) {
      console.error('❌ Error finding dialogs:', error.message);
    }

  } catch (error) {
    console.error('❌ Error during test:', error);
  } finally {
    // Keep browser open for a bit to see the final state
    console.log('⏸️ Keeping browser open for 5 seconds...');
    await page.waitForTimeout(5000);
    await browser.close();
    console.log('🏁 Test completed');
  }
}

manualCoordinateTest();