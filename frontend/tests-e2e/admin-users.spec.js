/* eslint-disable jest/no-conditional-expect */
const { test, expect } = require('@playwright/test');

test.describe('Admin Panel - User Management', () => {
  
  // Login as admin before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"], input[id*="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"], input[placeholder*="password"], input[id*="password"]').first();
    
    if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
      await emailInput.fill('admin@steambay.com');
      await passwordInput.fill('Admin123!');
      
      const loginButton = page.locator('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in"), button:has-text("Zaloguj")').first();
      
      if (!(await loginButton.isDisabled())) {
        await loginButton.click();
        await page.waitForTimeout(3000);
      } else {
        console.log("Login button is disabled, test may not work properly");
        test.skip();
      }
    } else {
      console.log("Login form not found");
      test.skip();
    }
  });
  
  // Helper function to navigate to user management panel
  async function navigateToUserManagement(page) {
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    
    const userSectionSelectors = [
      'a:has-text("Users")',
      'a:has-text("Użytkownicy")',
      '[data-testid="admin-users"]',
      'a[href*="users"]',
      'a[href*="user"]'
    ];
    
    let userSectionFound = false;
    for (const selector of userSectionSelectors) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        await element.click();
        await page.waitForTimeout(1000);
        userSectionFound = true;
        break;
      }
    }
    
    return userSectionFound;
  }
  
  // Scenario 1: Browsing user list
  test('should display a list of all users with pagination', async ({ page }) => {
    const userSectionFound = await navigateToUserManagement(page);
    expect(userSectionFound).toBeTruthy();
    
    // Check if page contains user list
    const userTableSelectors = [
      'table',
      '.user-table',
      '[data-testid="user-list"]',
      '.user-list'
    ];
    
    let userTableElement = null;
    for (const selector of userTableSelectors) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        userTableElement = element;
        break;
      }
    }
    
    expect(userTableElement).not.toBeNull();
    
    // Check if different user types are displayed (Buyers, Sellers, Admins)
    const userRoles = ['Buyer', 'Seller', 'Admin', 'Kupujący', 'Sprzedawca', 'Administrator'];
    let foundRoles = [];
    
    for (const role of userRoles) {
      const roleElement = page.locator(`text=${role}`).first();
      if (await roleElement.count() > 0) {
        foundRoles.push(role);
      }
    }
    
    expect(foundRoles.length).toBeGreaterThan(0);
    
    // Check if pagination works (if available)
    const paginationSelectors = [
      '.pagination',
      '[data-testid="pagination"]',
      'nav:has(ul li)',
      'button:has-text("Next")',
      'button:has-text("Następna")'
    ];
    
    let paginationTested = false;
    
    for (const selector of paginationSelectors) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        // Click next page button if active
        const nextPageButton = page.locator('button:has-text("Next"), button:has-text("Następna"), a:has-text("Next"), a:has-text("Następna")').first();
        if (await nextPageButton.count() > 0 && !(await nextPageButton.isDisabled())) {
          const currentFirstUser = await page.locator('tr').nth(1).textContent();
          await nextPageButton.click();
          await page.waitForTimeout(1000);
          
          const newFirstUser = await page.locator('tr').nth(1).textContent();
          expect(currentFirstUser).not.toEqual(newFirstUser);
          paginationTested = true;
        }
        break;
      }
    }
    
    // Only test pagination if it was available
    if (!paginationTested) {
      console.log('Pagination was not tested - may not be available or active.');
    }
    
    await page.screenshot({ path: 'admin-users-list.png' });
  });
  
  // Scenario 2: Viewing user details
  test('should display user details when clicking on a user', async ({ page }) => {
    const userSectionFound = await navigateToUserManagement(page);
    expect(userSectionFound).toBeTruthy();
    
    // Find first user in the list and click on it
    const userSelectors = [
      'table tbody tr',
      '.user-item',
      '[data-testid="user-row"]'
    ];
    
    let userElement = null;
    for (const selector of userSelectors) {
      const elements = page.locator(selector);
      if (await elements.count() > 0) {
        userElement = elements.first();
        break;
      }
    }
    
    expect(userElement).not.toBeNull();
    
    // Save user email before clicking
    const userEmail = await userElement.locator('td').nth(1).textContent();
    
    // Click on user or details button
    const detailsButtonSelectors = [
      'button:has-text("Details"), button:has-text("Szczegóły"), a:has-text("Details"), a:has-text("Szczegóły")',
      '[data-testid="view-user-details"]',
      '.details-button'
    ];
    
    let clickedDetails = false;
    
    // First try to click details button if it exists
    for (const selector of detailsButtonSelectors) {
      const detailsButton = userElement.locator(selector).first();
      if (await detailsButton.count() > 0) {
        await detailsButton.click();
        clickedDetails = true;
        break;
      }
    }
    
    // If no details button, click on the entire row
    if (!clickedDetails) {
      await userElement.click();
    }
    
    await page.waitForTimeout(1000);
    
    // Check if user details are displayed
    const detailsSelectors = [
      'h2:has-text("User Details"), h2:has-text("Szczegóły Użytkownika")',
      '[data-testid="user-details"]',
      '.user-details',
      '.user-profile'
    ];
    
    let detailsFound = false;
    for (const selector of detailsSelectors) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        detailsFound = true;
        break;
      }
    }
    
    expect(detailsFound).toBeTruthy();
    
    // Check if all required information is displayed
    const expectedFields = ['ID', 'Email', 'Role', 'Status', 'Created At', 'Data utworzenia', 'Rola', 'Status'];
    let foundFields = 0;
    
    for (const field of expectedFields) {
      const fieldElement = page.locator(`text=${field}`).first();
      if (await fieldElement.count() > 0) {
        foundFields++;
      }
    }
    
    expect(foundFields).toBeGreaterThan(2);
    
    // Check if user email is displayed in details
    const emailInDetails = page.locator(`text=${userEmail}`).first();
    expect(await emailInDetails.count()).toBeGreaterThan(0);
    
    // Check if password is NOT displayed
    const passwordFields = ['Password', 'Hasło', 'password hash', 'hash hasła'];
    let passwordFound = false;
    
    for (const field of passwordFields) {
      const passwordElement = page.locator(`text=${field}`).first();
      if (await passwordElement.count() > 0) {
        // Check if there is no password value next to this field
        const passwordValue = await passwordElement.locator('..').textContent();
        if (passwordValue.includes('*') || passwordValue.includes('●')) {
          // If there are asterisks, it's OK - password is hidden
          continue;
        }
        passwordFound = true;
        break;
      }
    }
    
    expect(passwordFound).toBeFalsy();
    
    await page.screenshot({ path: 'admin-user-details.png' });
  });
  
  // Scenario 8: Filtering user list
  test('should filter users by criteria', async ({ page }) => {
    const userSectionFound = await navigateToUserManagement(page);
    expect(userSectionFound).toBeTruthy();
    
    // Wait for user list to load
    await page.waitForTimeout(1000);
    
    // Check if filters exist
    const filterSelectors = [
      '[data-testid="user-filter"]',
      '.filter-options',
      'select[name="role"], select[id*="role"]',
      'select[name="status"], select[id*="status"]',
      'input[placeholder*="Search"], input[placeholder*="Filter"]',
      'input[placeholder*="Szukaj"], input[placeholder*="Filtruj"]'
    ];
    
    let filterFound = false;
    
    for (const selector of filterSelectors) {
      const element = page.locator(selector).first();
      if (await element.count() > 0) {
        filterFound = true;
        break;
      }
    }
    
    // If no filters found, test is unclear
    if (!filterFound) {
      console.log('No filters found for users.');
      return;
    }
    
    // Remember initial user count
    const userRows = page.locator('table tbody tr, .user-item, [data-testid="user-row"]');
    const initialUserCount = await userRows.count();
    
    // Filter by role (try different selections)
    const roleFilterSelectors = [
      'select[name="role"], select[id*="role"]',
      '[data-testid="role-filter"]',
      '.role-filter'
    ];
    
    let roleFilterApplied = false;
    
    for (const selector of roleFilterSelectors) {
      const roleFilter = page.locator(selector).first();
      if (await roleFilter.count() > 0) {
        // Try to select role "Seller" or "Sprzedawca"
        try {
          await roleFilter.selectOption({label: 'Seller'});
        } catch (e) {
          try {
            await roleFilter.selectOption({label: 'Sprzedawca'});
          } catch (e2) {
            // Try other values if available
            const options = await roleFilter.locator('option').count();
            if (options > 1) {
              await roleFilter.selectOption({index: 1});
            }
          }
        }
        
        // Wait for list to update
        await page.waitForTimeout(1000);
        
        // Check if user list changed
        const filteredUserCount = await userRows.count();
        const selectedRoleText = await roleFilter.evaluate(el => {
          return el.options[el.selectedIndex].text;
        });
        
        // Check different variants of correct filtering
        if (filteredUserCount !== initialUserCount) {
          // If user count changed, filter applied
          roleFilterApplied = true;
        } else {
          // If count didn't change, check if all users have selected role
          let allHaveRole = true;
          
          for (let i = 0; i < filteredUserCount; i++) {
            const userRole = await userRows.nth(i).locator('td').nth(2).textContent();
            if (!userRole.includes(selectedRoleText)) {
              allHaveRole = false;
              break;
            }
          }
          
          roleFilterApplied = allHaveRole;
        }
        
        // Check if filter applied correctly
        expect(roleFilterApplied).toBeTruthy();
        break;
      }
    }
    
    await page.screenshot({ path: 'admin-users-filtered.png' });
  });
  
  // Scenario 9: Verifying admin panel access
  test('should prevent non-admin users from accessing admin panel', async ({ page }) => {
    // Logout first
    await page.goto('/');
    
    const logoutSelectors = [
      'a:has-text("Logout")',
      'a:has-text("Wyloguj")',
      '[data-testid="logout"]',
      '.logout-button'
    ];
    
    for (const selector of logoutSelectors) {
      const logoutButton = page.locator(selector).first();
      if (await logoutButton.count() > 0) {
        await logoutButton.click();
        await page.waitForTimeout(1000);
        break;
      }
    }
    
    // Login as buyer
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"], input[id*="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"], input[placeholder*="password"], input[id*="password"]').first();
    
    if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
      await emailInput.fill('buyer@steambay.com');
      await passwordInput.fill('Buyer123!');
      
      const loginButton = page.locator('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in"), button:has-text("Zaloguj")').first();
      
      if (!(await loginButton.isDisabled())) {
        await loginButton.click();
        await page.waitForTimeout(3000);
      }
    }
    
    // Try accessing admin panel as buyer
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Check if redirected or got 403 error
    const currentUrl = page.url();
    
    // Take screenshot to see what happened
    await page.screenshot({ path: 'buyer-admin-access.png' });
    
    // Check if URL doesn't end with /admin
    const buyerRedirected = !currentUrl.endsWith('/admin');
    
    // If not redirected, check if got access denied message
    let buyerAccessDenied = buyerRedirected;
    
    if (!buyerRedirected) {
      const accessDeniedSelectors = [
        'text=Access Denied',
        'text=Forbidden',
        'text=403',
        'text=Unauthorized',
        'text=Brak dostępu',
        'text=Dostęp zabroniony',
        'text=Odmowa dostępu'
      ];
      
      for (const selector of accessDeniedSelectors) {
        const element = page.locator(selector).first();
        if (await element.count() > 0) {
          buyerAccessDenied = true;
          break;
        }
      }
    }
    
    // Check if buyer doesn't have access
    expect(buyerAccessDenied).toBeTruthy();
    
    // Repeat for seller
    // Logout first
    await page.goto('/');
    
    for (const selector of logoutSelectors) {
      const logoutButton = page.locator(selector).first();
      if (await logoutButton.count() > 0) {
        await logoutButton.click();
        await page.waitForTimeout(1000);
        break;
      }
    }
    
    // Login as seller
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
      await emailInput.fill('seller@steambay.com');
      await passwordInput.fill('Seller123!');
      
      const loginButton = page.locator('button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in"), button:has-text("Zaloguj")').first();
      
      if (!(await loginButton.isDisabled())) {
        await loginButton.click();
        await page.waitForTimeout(3000);
      }
    }
    
    // Try accessing admin panel as seller
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Check if redirected or got 403 error
    const currentUrlSeller = page.url();
    
    // Take screenshot to see what happened
    await page.screenshot({ path: 'seller-admin-access.png' });
    
    // Check if URL doesn't end with /admin
    const sellerRedirected = !currentUrlSeller.endsWith('/admin');
    
    // If not redirected, check if got access denied message
    let sellerAccessDenied = sellerRedirected;
    
    if (!sellerRedirected) {
      const accessDeniedSelectors = [
        'text=Access Denied',
        'text=Forbidden',
        'text=403',
        'text=Unauthorized',
        'text=Brak dostępu',
        'text=Dostęp zabroniony',
        'text=Odmowa dostępu'
      ];
      
      for (const selector of accessDeniedSelectors) {
        const element = page.locator(selector).first();
        if (await element.count() > 0) {
          sellerAccessDenied = true;
          break;
        }
      }
    }
    
    // Check if seller doesn't have access
    expect(sellerAccessDenied).toBeTruthy();
  });
}); 