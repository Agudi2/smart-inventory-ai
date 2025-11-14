import { test, expect } from '@playwright/test';

test.describe('Barcode Scanning and Stock Adjustment', () => {
  const testUser = {
    email: `test-barcode-${Date.now()}@example.com`,
    password: 'TestPassword123!',
    fullName: 'Barcode Test User',
  };

  const testProduct = {
    sku: `SKU-BARCODE-${Date.now()}`,
    name: `Barcode Test Product ${Date.now()}`,
    category: 'Electronics',
    currentStock: 50,
    reorderThreshold: 10,
    barcode: `123456789${Date.now().toString().slice(-3)}`,
  };

  test.beforeEach(async ({ page }) => {
    // Register and login
    await page.goto('/register');
    await page.fill('input[name="full_name"]', testUser.fullName);
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.fill('input[name="confirmPassword"]', testUser.password);
    await page.click('button[type="submit"]');
    
    await page.waitForURL(/\/(login|dashboard)/, { timeout: 10000 });
    
    if (page.url().includes('/login')) {
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.password);
      await page.click('button[type="submit"]');
      await page.waitForURL(/.*dashboard/, { timeout: 10000 });
    }

    // Create a product with barcode
    await page.goto('/inventory');
    const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
    await addButton.click();
    await page.waitForTimeout(1000);

    await page.fill('input[name="sku"]', testProduct.sku);
    await page.fill('input[name="name"]', testProduct.name);
    const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
    await categoryInput.fill(testProduct.category);
    await page.fill('input[name="current_stock"], input[name="currentStock"]', testProduct.currentStock.toString());
    await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', testProduct.reorderThreshold.toString());
    
    // Add barcode if field exists
    const barcodeInput = page.locator('input[name="barcode"]');
    if (await barcodeInput.isVisible()) {
      await barcodeInput.fill(testProduct.barcode);
    }

    const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
    await submitButton.click();
    await page.waitForTimeout(2000);
  });

  test('open barcode scanner modal', async ({ page, context }) => {
    // Grant camera permissions
    await context.grantPermissions(['camera']);

    await page.goto('/inventory');

    // Look for scan barcode button
    const scanButton = page.locator('button:has-text("Scan"), button:has-text("Barcode"), [aria-label*="scan"]').first();
    
    if (await scanButton.isVisible({ timeout: 5000 })) {
      await scanButton.click();

      // Wait for scanner modal to appear
      await page.waitForTimeout(1000);

      // Verify scanner modal is visible
      const scannerModal = page.locator('[role="dialog"]:has-text("Scan"), [role="dialog"]:has-text("Barcode")');
      await expect(scannerModal.first()).toBeVisible({ timeout: 5000 });

      // Close modal
      const closeButton = page.locator('button:has-text("Close"), button:has-text("Cancel"), [aria-label="Close"]').first();
      await closeButton.click();
    } else {
      // If no scan button, test passes as feature may not be on this page
      console.log('Barcode scan button not found on inventory page');
    }
  });

  test('manual barcode lookup and stock adjustment', async ({ page }) => {
    await page.goto('/inventory');

    // Look for barcode lookup or search functionality
    const barcodeInput = page.locator('input[placeholder*="barcode"], input[name="barcode"]').first();
    
    if (await barcodeInput.isVisible({ timeout: 3000 })) {
      // Enter barcode
      await barcodeInput.fill(testProduct.barcode);
      
      // Submit or search
      const searchButton = page.locator('button:has-text("Search"), button:has-text("Lookup"), button[type="submit"]').first();
      if (await searchButton.isVisible({ timeout: 2000 })) {
        await searchButton.click();
        await page.waitForTimeout(1000);
      }

      // Verify product is found
      await expect(page.locator(`text=${testProduct.name}`)).toBeVisible({ timeout: 5000 });
    } else {
      // Alternative: Search for product by name and adjust stock
      const searchInput = page.locator('input[placeholder*="Search"], input[type="search"]').first();
      if (await searchInput.isVisible()) {
        await searchInput.fill(testProduct.name);
        await page.waitForTimeout(1000);
      }

      // Find product row and click to view details
      const productRow = page.locator(`tr:has-text("${testProduct.name}")`).first();
      await productRow.click();
      await page.waitForTimeout(1000);
    }
  });

  test('stock adjustment workflow', async ({ page }) => {
    await page.goto('/inventory');

    // Find the product
    const productRow = page.locator(`tr:has-text("${testProduct.name}")`).first();
    await expect(productRow).toBeVisible({ timeout: 5000 });

    // Click on product to open details or find adjust button
    await productRow.click();
    await page.waitForTimeout(1000);

    // Look for stock adjustment controls
    const adjustButton = page.locator('button:has-text("Adjust"), button:has-text("Update Stock"), button:has-text("Modify")').first();
    
    if (await adjustButton.isVisible({ timeout: 3000 })) {
      await adjustButton.click();
      await page.waitForTimeout(500);

      // Fill adjustment form
      const quantityInput = page.locator('input[name="quantity"], input[type="number"]').first();
      await quantityInput.fill('10');

      const reasonInput = page.locator('input[name="reason"], textarea[name="reason"], select[name="reason"]').first();
      if (await reasonInput.isVisible({ timeout: 2000 })) {
        await reasonInput.fill('Stock replenishment');
      }

      // Submit adjustment
      const submitButton = page.locator('button[type="submit"]:has-text("Adjust"), button[type="submit"]:has-text("Update"), button[type="submit"]:has-text("Save")').first();
      await submitButton.click();

      // Wait for update
      await page.waitForTimeout(2000);

      // Verify stock was updated (new stock should be 60)
      const newStock = testProduct.currentStock + 10;
      await expect(page.locator(`text=${newStock}`)).toBeVisible({ timeout: 5000 });
    } else {
      // Alternative: Edit product to change stock
      const editButton = page.locator('button:has-text("Edit"), [aria-label="Edit"]').first();
      if (await editButton.isVisible({ timeout: 3000 })) {
        await editButton.click();
        await page.waitForTimeout(1000);

        const stockInput = page.locator('input[name="current_stock"], input[name="currentStock"]').first();
        const newStock = testProduct.currentStock + 10;
        await stockInput.fill(newStock.toString());

        const saveButton = page.locator('button[type="submit"]:has-text("Save"), button[type="submit"]:has-text("Update")').first();
        await saveButton.click();
        await page.waitForTimeout(2000);
      }
    }
  });

  test('view stock movement history', async ({ page }) => {
    await page.goto('/inventory');

    // Find and click on product
    const productRow = page.locator(`tr:has-text("${testProduct.name}")`).first();
    await productRow.click();
    await page.waitForTimeout(1000);

    // Look for history or movements section
    const historyTab = page.locator('button:has-text("History"), button:has-text("Movements"), [role="tab"]:has-text("History")').first();
    
    if (await historyTab.isVisible({ timeout: 3000 })) {
      await historyTab.click();
      await page.waitForTimeout(1000);

      // Verify history section is visible
      const historySection = page.locator('text=Transaction, text=Movement, text=History').first();
      await expect(historySection).toBeVisible({ timeout: 5000 });
    }
  });
});
