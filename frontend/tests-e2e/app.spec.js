const { test, expect } = require('@playwright/test');

test.describe('Basic application functionality', () => {
  test('application loads correctly', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');
    
    // Wait for the page to fully load
    await page.waitForLoadState('networkidle');
    
    // Take a screenshot of the main page for analysis
    await page.screenshot({ path: 'home-page.png' });
    
    // Check if the page has basic HTML structure
    const title = await page.title();
    console.log(`Page title: ${title}`);
    
    // Get body content for diagnostic purposes
    const bodyContent = await page.textContent('body');
    console.log(`Found ${bodyContent.length} characters on the main page`);
    
    // Test passes if the page loaded and has some content
    expect(bodyContent.length).toBeGreaterThan(0);
    
    // Check if any React elements can be found
    const hasReactElements = await page.evaluate(() => {
      return document.querySelectorAll('[data-reactroot], [data-reactid], [class*="react"]').length > 0;
    });
    
    console.log(`Found React elements: ${hasReactElements}`);
    
    // Check if there are any basic navigation elements
    const navElements = await page.locator('nav, header, .navbar, .header, .navigation').count();
    console.log(`Found ${navElements} navigation elements`);
  });
}); 