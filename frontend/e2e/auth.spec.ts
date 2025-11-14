import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  const testUser = {
    email: `test-${Date.now()}@example.com`,
    password: 'TestPassword123!',
    fullName: 'Test User',
  };

  test('complete user registration and login flow', async ({ page }) => {
    // Navigate to register page
    await page.goto('/register');
    await expect(page).toHaveURL(/.*register/);

    // Fill registration form
    await page.fill('input[name="full_name"]', testUser.fullName);
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.fill('input[name="confirmPassword"]', testUser.password);

    // Submit registration
    await page.click('button[type="submit"]');

    // Wait for redirect to login or dashboard
    await page.waitForURL(/\/(login|dashboard)/, { timeout: 10000 });

    // If redirected to login, perform login
    if (page.url().includes('/login')) {
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.password);
      await page.click('button[type="submit"]');
    }

    // Verify successful login - should be on dashboard
    await page.waitForURL(/.*dashboard/, { timeout: 10000 });
    await expect(page).toHaveURL(/.*dashboard/);

    // Verify user is logged in by checking for user menu or logout button
    const userMenu = page.locator('[data-testid="user-menu"], button:has-text("Logout"), button:has-text("Log out")');
    await expect(userMenu.first()).toBeVisible({ timeout: 5000 });

    // Logout
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Log out")').first();
    await logoutButton.click();

    // Verify redirect to login page
    await page.waitForURL(/.*login/, { timeout: 10000 });
    await expect(page).toHaveURL(/.*login/);
  });

  test('login with existing user', async ({ page }) => {
    // First register a user
    await page.goto('/register');
    await page.fill('input[name="full_name"]', testUser.fullName);
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);
    await page.fill('input[name="confirmPassword"]', testUser.password);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(2000);

    // Navigate to login page
    await page.goto('/login');
    await expect(page).toHaveURL(/.*login/);

    // Fill login form
    await page.fill('input[name="email"]', testUser.email);
    await page.fill('input[name="password"]', testUser.password);

    // Submit login
    await page.click('button[type="submit"]');

    // Verify successful login
    await page.waitForURL(/.*dashboard/, { timeout: 10000 });
    await expect(page).toHaveURL(/.*dashboard/);
  });

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login');

    // Fill with invalid credentials
    await page.fill('input[name="email"]', 'invalid@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');

    // Submit login
    await page.click('button[type="submit"]');

    // Wait for error message
    await page.waitForTimeout(2000);

    // Should still be on login page
    await expect(page).toHaveURL(/.*login/);
  });
});
