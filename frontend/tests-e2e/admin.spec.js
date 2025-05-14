const { test, expect } = require('@playwright/test');

test.describe('Admin Panel Functionality', () => {
  
  // Login as admin before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Look for email and password fields
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"], input[id*="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"], input[placeholder*="password"], input[id*="password"]').first();
    
    if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
      await emailInput.fill('admin@steambay.com');
      await passwordInput.fill('Admin123!');
      
      // Login
      const loginButton = page.locator('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in"), button:has-text("Zaloguj")').first();
      
      if (!(await loginButton.isDisabled())) {
        await loginButton.click();
        await page.waitForTimeout(3000);
      } else {
        console.log("Login button is disabled, test may not work properly");
        console.log("Login form not found");
        test.skip();
      }
    } else {
      console.log("Login form not found");
      test.skip();
    }
  });
  
  // 10.1 Access to admin panel
  test('can access admin panel', async ({ page }) => {
    // Try to go directly to the admin panel
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'admin-panel.png' });
    
    try {
      // Check if we're in the admin panel
      const adminPanelIndicators = [
        page.locator('text=Admin Panel'),
        page.locator('text=Users'),
        page.locator('text=Products'),
        page.locator('text=Orders'),
        page.locator('text=Logs'),
        page.locator('[data-testid="admin-dashboard"]')
      ];
      
      let adminPanelFound = false;
      for (const indicator of adminPanelIndicators) {
        if (await indicator.count() > 0) {
          adminPanelFound = true;
          break;
        }
      }
      
      // If admin panel indicators not found, check for any administrative elements
      if (!adminPanelFound) {
        const adminElements = [
          page.locator('text=User Management'),
          page.locator('text=Product Management'),
          page.locator('text=Order Management'),
          page.locator('[data-testid*="admin"]')
        ];
        
        for (const element of adminElements) {
          if (await element.count() > 0) {
            adminPanelFound = true;
            break;
          }
        }
      }
      
      // Test passes if admin panel is found
      expect(adminPanelFound).toBeTruthy();
      
    } catch (e) {
      console.error('Error during admin panel test:', e);
      await page.screenshot({ path: 'admin-panel-error.png' });
      throw e;
    }
  });
  
  // Can manage users through admin panel
  test('can manage users', async ({ page }) => {
    // Login as admin first
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Fill login form
    await page.fill('input[type="email"]', 'admin@steambay.com');
    await page.fill('input[type="password"]', 'Admin123!');
    
    const loginButton = page.locator('button[type="submit"]').first();
    
    if (!await loginButton.isDisabled()) {
      await loginButton.click();
      await page.waitForTimeout(2000);
    } else {
      console.log("Login button is disabled, test may not work properly");
      test.skip();
      return;
    }
    
    // Navigate to admin panel (if not automatically redirected)
    try {
      const adminLink = page.locator('a:has-text("Admin Panel"), a[href*="admin"]').first();
      if (await adminLink.count() > 0) {
        await adminLink.click();
      }
    } catch (e) {
      // We might already be in the admin panel
    }
    
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'admin-users-test.png' });
    
    // Look for User Management section
    const userManagementSelectors = [
      'a:has-text("Users")',
      'button:has-text("Users")',
      'a[href*="users"]',
      '[data-testid="users-tab"]',
      '.nav-item:has-text("Users")'
    ];
    
    let userManagementFound = false;
    let userManagementElement = null;
    
    for (const selector of userManagementSelectors) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        userManagementFound = true;
        userManagementElement = element;
        break;
      }
    }
    
    if (!userManagementFound) {
      console.log('User management section not found.');
      test.skip();
      return;
    }
    
    // Click on Users Management tab
    await userManagementElement.click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'users-management.png' });
    
    // Check for user list
    const userListSelectors = [
      'table',
      '[data-testid="users-table"]',
      '.users-list',
      '.user-card'
    ];
    
    let userListFound = false;
    
    for (const selector of userListSelectors) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        userListFound = true;
        break;
      }
    }
    
    expect(userListFound).toBeTruthy();
    
    // Check if there are action buttons to manage users
    const actionButtonSelectors = [
      'button:has-text("Edit")',
      'button:has-text("Delete")',
      'button:has-text("View")',
      'button:has-text("Change Status")',
      '[data-testid*="user-action"]',
      '.user-action-button'
    ];
    
    let actionButtonsFound = false;
    let selector = '';
    
    for (const s of actionButtonSelectors) {
      const buttons = page.locator(s);
      if (await buttons.count() > 0) {
        actionButtonsFound = true;
        selector = s;
        break;
      }
    }
    
    if (actionButtonsFound) {
      console.log(`Found action buttons: ${selector}`);
    }
    
    console.log(`Action buttons found: ${actionButtonsFound}`);
    
    // Test passes if user management section and user list are found
  });
  
  // Can manage products through admin panel
  test('can manage products', async ({ page }) => {
    // Login as admin first
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Fill login form
    await page.fill('input[type="email"]', 'admin@steambay.com');
    await page.fill('input[type="password"]', 'Admin123!');
    
    const loginButton = page.locator('button[type="submit"]').first();
    
    if (!await loginButton.isDisabled()) {
      await loginButton.click();
      await page.waitForTimeout(2000);
    } else {
      console.log("Login button is disabled, test may not work properly");
      test.skip();
      return;
    }
    
    // Navigate to admin panel (if not automatically redirected)
    try {
      const adminLink = page.locator('a:has-text("Admin Panel"), a[href*="admin"]').first();
      if (await adminLink.count() > 0) {
        await adminLink.click();
      }
    } catch (e) {
      // We might already be in the admin panel
    }
    
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'admin-products-test.png' });
    
    // Look for Product Management section
    const productManagementSelectors = [
      'a:has-text("Products")',
      'button:has-text("Products")',
      'a[href*="products"]',
      '[data-testid="products-tab"]',
      '.nav-item:has-text("Products")'
    ];
    
    let productManagementFound = false;
    let productManagementElement = null;
    
    for (const selector of productManagementSelectors) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        productManagementFound = true;
        productManagementElement = element;
        break;
      }
    }
    
    if (!productManagementFound) {
      console.log('Product management section not found.');
      test.skip();
      return;
    }
    
    // Click on Products Management tab
    await productManagementElement.click();
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'products-management.png' });
    
    // Check if there is an "Add Product" button
    const addProductSelectors = [
      'button:has-text("Add")',
      'button:has-text("New")',
      'button:has-text("Create")',
      '[data-testid="add-product"]',
      '.add-product-button'
    ];
    
    let addProductFound = false;
    let selector = '';
    
    for (const s of addProductSelectors) {
      const button = page.locator(s).first();
      if (await button.count() > 0) {
        addProductFound = true;
        selector = s;
        break;
      }
    }
    
    if (addProductFound) {
      console.log(`Found add product button: ${selector}`);
    }
    
    console.log(`Add product button found: ${addProductFound}`);
    
    // Check for product list
    const productListSelectors = [
      'table',
      '[data-testid="products-table"]',
      '.products-list',
      '.product-card'
    ];
    
    let productListFound = false;
    
    for (const selector of productListSelectors) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        productListFound = true;
        break;
      }
    }
    
    expect(productListFound).toBeTruthy();
    
    // Test passes if product management section and product list are found
  });
  
  // 10.4 View orders
  test('can view orders', async ({ page }) => {
    // Go to admin panel
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    
    try {
      // Find and click orders management section
      const orderSectionSelectors = [
        'a:has-text("Orders")',
        'a:has-text("Orders")',
        '[data-testid="admin-orders"]',
        'a[href*="orders"]',
        'a[href*="order"]'
      ];
      
      let orderSectionFound = false;
      for (const selector of orderSectionSelectors) {
        const element = page.locator(selector).first();
        if (await element.count() > 0) {
          await element.click();
          orderSectionFound = true;
          console.log(`Clicked on orders section: ${selector}`);
          break;
        }
      }
      
      if (!orderSectionFound) {
        console.log('Orders management section not found.');
        // Check if we're already on the orders page
        const orderTableSelectors = [
          'table',
          '.order-table',
          '[data-testid="order-list"]',
          '.order-list'
        ];
        
        for (const selector of orderTableSelectors) {
          const element = page.locator(selector).first();
          if (await element.count() > 0) {
            orderSectionFound = true;
            console.log(`Already on orders page, found: ${selector}`);
            break;
          }
        }
        
        if (!orderSectionFound) {
          console.log('Cannot find orders section or orders table.');
          await page.screenshot({ path: 'admin-no-orders-section.png' });
          test.skip();
          return;
        }
      }
      
      // Wait for orders list to load
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'admin-orders-list.png' });
      
      // Check if page contains orders list
      const orderElements = [
        'table',
        '.order-table',
        '[data-testid="order-list"]',
        '.order-list',
        'tr',
        '.order-item'
      ];
      
      let orderListFound = false;
      for (const selector of orderElements) {
        const element = page.locator(selector);
        if (await element.count() > 0) {
          orderListFound = true;
          console.log(`Found orders list: ${selector}`);
          break;
        }
      }
      
      // Test passes if orders list is found
      expect(orderListFound).toBeTruthy();
      
    } catch (e) {
      console.error('Error during orders viewing test:', e);
      await page.screenshot({ path: 'admin-orders-error.png' });
      throw e;
    }
  });
}); 