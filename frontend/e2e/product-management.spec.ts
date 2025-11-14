import { test, expect } from '@playwright/test';

test.describe('Product Management', () => {
  const testUser = {
    email: `test-product-${Date.now()}@example.com`,
    password: 'TestPassword123!',
    fullName: 'Product Test User',
  };

  const testProduct = {
    sku: `SKU-${Date.now()}`,
    name: `Test Product ${Date.now()}`,
    category: 'Electronics',
    currentStock: 100,
    reorderThreshold: 20,
  };

  test.beforeEach(async ({ page }) => {
    // Register and login before each test
    await page.goto('/register');
    await page.fill('input[name="full_name"]', testUser.fullName);
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.fill('input[name="confirmPassword"]', testUser.password);
    await page.click('button[type="submit"]');
    
    // Wait for redirect and ensure we're logged in
    await page.waitForURL(/\/(login|dashboard)/, { timeout: 10000 });
    
    if (page.url().includes('/login')) {
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.password);
      await page.click('button[type="submit"]');
      await page.waitForURL(/.*dashboard/, { timeout: 10000 });
    }
  });

  test('add a product and view it in the table', async ({ page }) => {
    // Navigate to inventory page
    await page.goto('/inventory');
    await expect(page).toHaveURL(/.*inventory/);

    // Click add product button
    const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
    await addButton.click();

    // Wait for modal to appear
    await page.waitForTimeout(1000);

    // Fill product form
    await page.fill('input[name="sku"]', testProduct.sku);
    await page.fill('input[name="name"]', testProduct.name);
    
    // Handle category - could be select or input
    const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
    await categoryInput.fill(testProduct.category);
    
    await page.fill('input[name="current_stock"], input[name="currentStock"]', testProduct.currentStock.toString());
    await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', testProduct.reorderThreshold.toString());

    // Submit form
    const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
    await submitButton.click();

    // Wait for modal to close and table to update
    await page.waitForTimeout(2000);

    // Verify product appears in table
    await expect(page.locator(`text=${testProduct.name}`)).toBeVisible({ timeout: 5000 });
    await expect(page.locator(`text=${testProduct.sku}`)).toBeVisible({ timeout: 5000 });

    // Click on product row to view details
    const productRow = page.locator(`tr:has-text("${testProduct.name}")`).first();
    await productRow.click();

    // Wait for detail modal
    await page.waitForTimeout(1000);

    // Verify product details are displayed
    await expect(page.locator(`text=${testProduct.name}`)).toBeVisible();
    await expect(page.locator(`text=${testProduct.sku}`)).toBeVisible();
  });

  test('edit an existing product', async ({ page }) => {
    // Navigate to inventory page
    await page.goto('/inventory');
    
    // First create a product
    const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
    await addButton.click();
    await page.waitForTimeout(1000);

    await page.fill('input[name="sku"]', testProduct.sku);
    await page.fill('input[name="name"]', testProduct.name);
    const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
    await categoryInput.fill(testProduct.category);
    await page.fill('input[name="current_stock"], input[name="currentStock"]', testProduct.currentStock.toString());
    await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', testProduct.reorderThreshold.toString());

    const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
    await submitButton.click();
    await page.waitForTimeout(2000);

    // Find and click edit button for the product
    const productRow = page.locator(`tr:has-text("${testProduct.name}")`).first();
    const editButton = productRow.locator('button:has-text("Edit"), [aria-label="Edit"]').first();
    await editButton.click();

    // Wait for edit modal
    await page.waitForTimeout(1000);

    // Update product name
    const updatedName = `${testProduct.name} - Updated`;
    await page.fill('input[name="name"]', updatedName);

    // Submit update
    const updateButton = page.locator('button[type="submit"]:has-text("Update"), button[type="submit"]:has-text("Save")').first();
    await updateButton.click();

    // Wait for update to complete
    await page.waitForTimeout(2000);

    // Verify updated name appears in table
    await expect(page.locator(`text=${updatedName}`)).toBeVisible({ timeout: 5000 });
  });

  test('search and filter products', async ({ page }) => {
    // Navigate to inventory page
    await page.goto('/inventory');
    
    // Create a product first
    const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
    await addButton.click();
    await page.waitForTimeout(1000);

    await page.fill('input[name="sku"]', testProduct.sku);
    await page.fill('input[name="name"]', testProduct.name);
    const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
    await categoryInput.fill(testProduct.category);
    await page.fill('input[name="current_stock"], input[name="currentStock"]', testProduct.currentStock.toString());
    await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', testProduct.reorderThreshold.toString());

    const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
    await submitButton.click();
    await page.waitForTimeout(2000);

    // Use search functionality
    const searchInput = page.locator('input[placeholder*="Search"], input[type="search"]').first();
    if (await searchInput.isVisible()) {
      await searchInput.fill(testProduct.name);
      await page.waitForTimeout(1000);

      // Verify filtered results
      await expect(page.locator(`text=${testProduct.name}`)).toBeVisible();
    }
  });
});
