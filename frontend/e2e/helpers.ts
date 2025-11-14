import { Page } from '@playwright/test';

/**
 * Helper functions for E2E tests
 */

export interface TestUser {
  email: string;
  password: string;
  fullName: string;
}

export interface TestProduct {
  sku: string;
  name: string;
  category: string;
  currentStock: number;
  reorderThreshold: number;
  barcode?: string;
}

/**
 * Register and login a test user
 */
export async function registerAndLogin(page: Page, user: TestUser): Promise<void> {
  await page.goto('/register');
  await page.fill('input[name="full_name"]', user.fullName);
  await page.fill('input[name="email"]', user.email);
  await page.fill('input[name="password"]', user.password);
  await page.fill('input[name="confirmPassword"]', user.password);
  await page.click('button[type="submit"]');
  
  await page.waitForURL(/\/(login|dashboard)/, { timeout: 10000 });
  
  if (page.url().includes('/login')) {
    await page.fill('input[name="email"]', user.email);
    await page.fill('input[name="password"]', user.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/.*dashboard/, { timeout: 10000 });
  }
}

/**
 * Create a test product
 */
export async function createProduct(page: Page, product: TestProduct): Promise<void> {
  await page.goto('/inventory');
  
  const addButton = page.locator('button:has-text("Add Product"), button:has-text("New Product"), button:has-text("Create Product")').first();
  await addButton.click();
  await page.waitForTimeout(1000);

  await page.fill('input[name="sku"]', product.sku);
  await page.fill('input[name="name"]', product.name);
  
  const categoryInput = page.locator('input[name="category"], select[name="category"]').first();
  await categoryInput.fill(product.category);
  
  await page.fill('input[name="current_stock"], input[name="currentStock"]', product.currentStock.toString());
  await page.fill('input[name="reorder_threshold"], input[name="reorderThreshold"]', product.reorderThreshold.toString());

  if (product.barcode) {
    const barcodeInput = page.locator('input[name="barcode"]');
    if (await barcodeInput.isVisible()) {
      await barcodeInput.fill(product.barcode);
    }
  }

  const submitButton = page.locator('button[type="submit"]:has-text("Create"), button[type="submit"]:has-text("Add"), button[type="submit"]:has-text("Save")').first();
  await submitButton.click();
  await page.waitForTimeout(2000);
}

/**
 * Generate unique test user credentials
 */
export function generateTestUser(prefix: string = 'test'): TestUser {
  return {
    email: `${prefix}-${Date.now()}@example.com`,
    password: 'TestPassword123!',
    fullName: `${prefix} User ${Date.now()}`,
  };
}

/**
 * Generate unique test product data
 */
export function generateTestProduct(prefix: string = 'TEST'): TestProduct {
  return {
    sku: `SKU-${prefix}-${Date.now()}`,
    name: `${prefix} Product ${Date.now()}`,
    category: 'Electronics',
    currentStock: 100,
    reorderThreshold: 20,
  };
}

/**
 * Wait for API response
 */
export async function waitForApiResponse(page: Page, urlPattern: string | RegExp, timeout: number = 5000): Promise<void> {
  await page.waitForResponse(
    response => {
      const url = response.url();
      if (typeof urlPattern === 'string') {
        return url.includes(urlPattern);
      }
      return urlPattern.test(url);
    },
    { timeout }
  );
}

/**
 * Clear local storage and cookies
 */
export async function clearAuth(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });
  await page.context().clearCookies();
}
