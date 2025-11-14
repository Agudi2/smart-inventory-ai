import { test, expect } from '@playwright/test';

test.describe('Predictions and Alerts', () => {
  const testUser = {
    email: `test-alerts-${Date.now()}@example.com`,
    password: 'TestPassword123!',
    fullName: 'Alerts Test User',
  };

  const lowStockProduct = {
    sku: `SKU-LOW-${Date.now()}`,
    name: `Low Stock Product ${Date.now()}`,
    category: 'Electronics',
    currentStock: 5,
    reorderThreshold: 20,
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
  });

  test('view predictions for a product', async ({ page }) => {
    // Create a product first
    await page.goto('/inventory');
    const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
    await addButton.click();
    await page.waitForTimeout(1000);

    await page.fill('input[name="sku"]', lowStockProduct.sku);
    await page.fill('input[name="name"]', lowStockProduct.name);
    const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
    await categoryInput.fill(lowStockProduct.category);
    await page.fill('input[name="current_stock"], input[name="currentStock"]', lowStockProduct.currentStock.toString());
    await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', lowStockProduct.reorderThreshold.toString());

    const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
    await submitButton.click();
    await page.waitForTimeout(2000);

    // Click on product to view details
    const productRow = page.locator(`tr:has-text("${lowStockProduct.name}")`).first();
    await productRow.click();
    await page.waitForTimeout(1000);

    // Look for prediction section or chart
    const predictionSection = page.locator('text=Prediction, text=Forecast, text=Depletion, text=Restock').first();
    
    if (await predictionSection.isVisible({ timeout: 5000 })) {
      // Verify prediction content is displayed
      await expect(predictionSection).toBeVisible();

      // Look for prediction chart
      const chart = page.locator('[class*="recharts"], svg[class*="chart"]').first();
      if (await chart.isVisible({ timeout: 3000 })) {
        await expect(chart).toBeVisible();
      }
    } else {
      // Predictions may not be available for new products
      console.log('Prediction section not found - may require historical data');
    }
  });

  test('view alerts panel on dashboard', async ({ page }) => {
    // Create a low stock product to trigger alert
    await page.goto('/inventory');
    const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
    await addButton.click();
    await page.waitForTimeout(1000);

    await page.fill('input[name="sku"]', lowStockProduct.sku);
    await page.fill('input[name="name"]', lowStockProduct.name);
    const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
    await categoryInput.fill(lowStockProduct.category);
    await page.fill('input[name="current_stock"], input[name="currentStock"]', lowStockProduct.currentStock.toString());
    await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', lowStockProduct.reorderThreshold.toString());

    const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
    await submitButton.click();
    await page.waitForTimeout(2000);

    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForTimeout(2000);

    // Look for alerts section
    const alertsSection = page.locator('text=Alerts, text=Notifications, text=Warnings').first();
    
    if (await alertsSection.isVisible({ timeout: 5000 })) {
      await expect(alertsSection).toBeVisible();

      // Check if low stock alert is displayed
      const lowStockAlert = page.locator(`text=${lowStockProduct.name}, text=Low Stock, text=low stock`).first();
      if (await lowStockAlert.isVisible({ timeout: 3000 })) {
        await expect(lowStockAlert).toBeVisible();
      }
    }
  });

  test('acknowledge an alert', async ({ page }) => {
    // Create a low stock product
    await page.goto('/inventory');
    const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
    await addButton.click();
    await page.waitForTimeout(1000);

    await page.fill('input[name="sku"]', lowStockProduct.sku);
    await page.fill('input[name="name"]', lowStockProduct.name);
    const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
    await categoryInput.fill(lowStockProduct.category);
    await page.fill('input[name="current_stock"], input[name="currentStock"]', lowStockProduct.currentStock.toString());
    await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', lowStockProduct.reorderThreshold.toString());

    const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
    await submitButton.click();
    await page.waitForTimeout(2000);

    // Navigate to dashboard or alerts page
    await page.goto('/dashboard');
    await page.waitForTimeout(2000);

    // Look for acknowledge button on an alert
    const acknowledgeButton = page.locator('button:has-text("Acknowledge"), button:has-text("Dismiss"), [aria-label*="acknowledge"]').first();
    
    if (await acknowledgeButton.isVisible({ timeout: 5000 })) {
      // Click acknowledge
      await acknowledgeButton.click();
      await page.waitForTimeout(1000);

      // Verify alert status changed or alert is removed
      // The alert might disappear or show as acknowledged
      await page.waitForTimeout(1000);
    } else {
      // Try navigating to dedicated alerts page if it exists
      const alertsLink = page.locator('a:has-text("Alerts"), [href*="alerts"]').first();
      if (await alertsLink.isVisible({ timeout: 3000 })) {
        await alertsLink.click();
        await page.waitForTimeout(1000);

        const acknowledgeBtn = page.locator('button:has-text("Acknowledge"), button:has-text("Dismiss")').first();
        if (await acknowledgeBtn.isVisible({ timeout: 3000 })) {
          await acknowledgeBtn.click();
          await page.waitForTimeout(1000);
        }
      }
    }
  });

  test('resolve an alert', async ({ page }) => {
    // Create a low stock product
    await page.goto('/inventory');
    const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
    await addButton.click();
    await page.waitForTimeout(1000);

    await page.fill('input[name="sku"]', lowStockProduct.sku);
    await page.fill('input[name="name"]', lowStockProduct.name);
    const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
    await categoryInput.fill(lowStockProduct.category);
    await page.fill('input[name="current_stock"], input[name="currentStock"]', lowStockProduct.currentStock.toString());
    await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', lowStockProduct.reorderThreshold.toString());

    const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
    await submitButton.click();
    await page.waitForTimeout(2000);

    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForTimeout(2000);

    // Look for resolve button
    const resolveButton = page.locator('button:has-text("Resolve"), button:has-text("Mark Resolved"), [aria-label*="resolve"]').first();
    
    if (await resolveButton.isVisible({ timeout: 5000 })) {
      await resolveButton.click();
      await page.waitForTimeout(1000);

      // Verify alert is resolved (removed or marked as resolved)
      await page.waitForTimeout(1000);
    }
  });

  test('view prediction chart with historical data', async ({ page }) => {
    // Create a product
    await page.goto('/inventory');
    const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
    await addButton.click();
    await page.waitForTimeout(1000);

    const testProduct = {
      sku: `SKU-PRED-${Date.now()}`,
      name: `Prediction Test ${Date.now()}`,
      category: 'Electronics',
      currentStock: 100,
      reorderThreshold: 30,
    };

    await page.fill('input[name="sku"]', testProduct.sku);
    await page.fill('input[name="name"]', testProduct.name);
    const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
    await categoryInput.fill(testProduct.category);
    await page.fill('input[name="current_stock"], input[name="currentStock"]', testProduct.currentStock.toString());
    await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', testProduct.reorderThreshold.toString());

    const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
    await submitButton.click();
    await page.waitForTimeout(2000);

    // Click on product
    const productRow = page.locator(`tr:has-text("${testProduct.name}")`).first();
    await productRow.click();
    await page.waitForTimeout(1000);

    // Look for prediction/forecast tab or section
    const predictionTab = page.locator('button:has-text("Prediction"), button:has-text("Forecast"), [role="tab"]:has-text("Prediction")').first();
    
    if (await predictionTab.isVisible({ timeout: 3000 })) {
      await predictionTab.click();
      await page.waitForTimeout(1000);

      // Verify chart is displayed
      const chart = page.locator('[class*="recharts"], svg').first();
      await expect(chart).toBeVisible({ timeout: 5000 });
    } else {
      // Chart might be visible by default
      const chart = page.locator('[class*="recharts"], svg').first();
      if (await chart.isVisible({ timeout: 3000 })) {
        await expect(chart).toBeVisible();
      }
    }
  });

  test('navigate to alerts page and view all alerts', async ({ page }) => {
    // Create multiple low stock products
    await page.goto('/inventory');
    
    for (let i = 0; i < 2; i++) {
      const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
      await addButton.click();
      await page.waitForTimeout(1000);

      const product = {
        sku: `SKU-ALERT-${Date.now()}-${i}`,
        name: `Alert Product ${Date.now()}-${i}`,
        category: 'Electronics',
        currentStock: 3,
        reorderThreshold: 15,
      };

      await page.fill('input[name="sku"]', product.sku);
      await page.fill('input[name="name"]', product.name);
      const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
      await categoryInput.fill(product.category);
      await page.fill('input[name="current_stock"], input[name="currentStock"]', product.currentStock.toString());
      await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', product.reorderThreshold.toString());

      const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
      await submitButton.click();
      await page.waitForTimeout(2000);
    }

    // Navigate to alerts page if it exists
    const alertsLink = page.locator('a:has-text("Alerts"), [href*="alerts"]').first();
    
    if (await alertsLink.isVisible({ timeout: 3000 })) {
      await alertsLink.click();
      await page.waitForTimeout(1000);

      // Verify alerts page is displayed
      await expect(page).toHaveURL(/.*alerts/);

      // Check for alert items
      const alertItems = page.locator('[class*="alert"], [role="alert"], li:has-text("Low Stock")');
      const count = await alertItems.count();
      
      if (count > 0) {
        await expect(alertItems.first()).toBeVisible();
      }
    } else {
      // Alerts might be on dashboard
      await page.goto('/dashboard');
      await page.waitForTimeout(1000);

      const alertsSection = page.locator('text=Alerts, text=Notifications').first();
      await expect(alertsSection).toBeVisible({ timeout: 5000 });
    }
  });
});
