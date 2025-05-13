/* eslint-disable jest/no-conditional-expect */
const { test, expect } = require('@playwright/test');

test.describe('Admin Panel - User Management', () => {
  
  // Zaloguj się jako admin przed każdym testem
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
        console.log("Przycisk logowania jest wyłączony, test może nie działać poprawnie");
        test.skip();
      }
    } else {
      console.log("Nie znaleziono formularza logowania");
      test.skip();
    }
  });
  
  // Funkcja pomocnicza do navigacji do panelu zarządzania użytkownikami
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
  
  // Scenariusz 1: Przeglądanie listy użytkowników
  test('should display a list of all users with pagination', async ({ page }) => {
    const userSectionFound = await navigateToUserManagement(page);
    expect(userSectionFound).toBeTruthy();
    
    // Sprawdź, czy strona zawiera listę użytkowników
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
    
    // Sprawdź, czy są wyświetlane różne typy użytkowników (Buyers, Sellers, Admins)
    const userRoles = ['Buyer', 'Seller', 'Admin', 'Kupujący', 'Sprzedawca', 'Administrator'];
    let foundRoles = [];
    
    for (const role of userRoles) {
      const roleElement = page.locator(`text=${role}`).first();
      if (await roleElement.count() > 0) {
        foundRoles.push(role);
      }
    }
    
    expect(foundRoles.length).toBeGreaterThan(0);
    
    // Sprawdź, czy działa paginacja (jeśli jest dostępna)
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
        // Kliknij przycisk następnej strony, jeśli jest aktywny
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
    
    // Testujemy paginację tylko jeśli była dostępna
    if (!paginationTested) {
      console.log('Paginacja nie została przetestowana - może nie być dostępna lub aktywna.');
    }
    
    await page.screenshot({ path: 'admin-users-list.png' });
  });
  
  // Scenariusz 2: Przeglądanie szczegółów użytkownika
  test('should display user details when clicking on a user', async ({ page }) => {
    const userSectionFound = await navigateToUserManagement(page);
    expect(userSectionFound).toBeTruthy();
    
    // Znajdź pierwszego użytkownika na liście i kliknij na niego
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
    
    // Zapisz email użytkownika przed kliknięciem
    const userEmail = await userElement.locator('td').nth(1).textContent();
    
    // Kliknij na użytkownika lub przycisk szczegółów
    const detailsButtonSelectors = [
      'button:has-text("Details"), button:has-text("Szczegóły"), a:has-text("Details"), a:has-text("Szczegóły")',
      '[data-testid="view-user-details"]',
      '.details-button'
    ];
    
    let clickedDetails = false;
    
    // Najpierw spróbuj kliknąć przycisk szczegółów, jeśli istnieje
    for (const selector of detailsButtonSelectors) {
      const detailsButton = userElement.locator(selector).first();
      if (await detailsButton.count() > 0) {
        await detailsButton.click();
        clickedDetails = true;
        break;
      }
    }
    
    // Jeśli nie ma przycisku szczegółów, kliknij na cały wiersz
    if (!clickedDetails) {
      await userElement.click();
    }
    
    await page.waitForTimeout(1000);
    
    // Sprawdź, czy wyświetlane są szczegóły użytkownika
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
    
    // Sprawdź, czy wyświetlane są wszystkie wymagane informacje
    const expectedFields = ['ID', 'Email', 'Role', 'Status', 'Created At', 'Data utworzenia', 'Rola', 'Status'];
    let foundFields = 0;
    
    for (const field of expectedFields) {
      const fieldElement = page.locator(`text=${field}`).first();
      if (await fieldElement.count() > 0) {
        foundFields++;
      }
    }
    
    expect(foundFields).toBeGreaterThan(2);
    
    // Sprawdź, czy email użytkownika jest wyświetlany w szczegółach
    const emailInDetails = page.locator(`text=${userEmail}`).first();
    expect(await emailInDetails.count()).toBeGreaterThan(0);
    
    // Sprawdź, czy hasło NIE jest wyświetlane
    const passwordFields = ['Password', 'Hasło', 'password hash', 'hash hasła'];
    let passwordFound = false;
    
    for (const field of passwordFields) {
      const passwordElement = page.locator(`text=${field}`).first();
      if (await passwordElement.count() > 0) {
        // Sprawdź, czy nie ma obok tego pola wartości hasła
        const passwordValue = await passwordElement.locator('..').textContent();
        if (passwordValue.includes('*') || passwordValue.includes('●')) {
          // Jeśli są gwiazdki, to jest OK - hasło jest ukryte
          continue;
        }
        passwordFound = true;
        break;
      }
    }
    
    expect(passwordFound).toBeFalsy();
    
    await page.screenshot({ path: 'admin-user-details.png' });
  });
  
  // Scenariusz 8: Filtrowanie listy użytkowników
  test('should filter users by criteria', async ({ page }) => {
    const userSectionFound = await navigateToUserManagement(page);
    expect(userSectionFound).toBeTruthy();
    
    // Poczekaj na załadowanie listy użytkowników
    await page.waitForTimeout(1000);
    
    // Sprawdź, czy istnieją filtry
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
    
    // Jeśli nie znaleziono filtrów, test jest niejasny
    if (!filterFound) {
      console.log('Nie znaleziono filtrów dla użytkowników.');
      return;
    }
    
    // Zapamiętaj pierwotną liczbę użytkowników
    const userRows = page.locator('table tbody tr, .user-item, [data-testid="user-row"]');
    const initialUserCount = await userRows.count();
    
    // Filtruj według roli (spróbuj różne selekcje)
    const roleFilterSelectors = [
      'select[name="role"], select[id*="role"]',
      '[data-testid="role-filter"]',
      '.role-filter'
    ];
    
    let roleFilterApplied = false;
    
    for (const selector of roleFilterSelectors) {
      const roleFilter = page.locator(selector).first();
      if (await roleFilter.count() > 0) {
        // Spróbuj wybrać rolę "Seller" lub "Sprzedawca"
        try {
          await roleFilter.selectOption({label: 'Seller'});
        } catch (e) {
          try {
            await roleFilter.selectOption({label: 'Sprzedawca'});
          } catch (e2) {
            // Spróbuj inne wartości, jeśli dostępne
            const options = await roleFilter.locator('option').count();
            if (options > 1) {
              await roleFilter.selectOption({index: 1});
            }
          }
        }
        
        // Poczekaj na aktualizację listy
        await page.waitForTimeout(1000);
        
        // Sprawdź, czy lista użytkowników się zmieniła
        const filteredUserCount = await userRows.count();
        const selectedRoleText = await roleFilter.evaluate(el => {
          return el.options[el.selectedIndex].text;
        });
        
        // Sprawdź różne warianty poprawnego filtrowania
        if (filteredUserCount !== initialUserCount) {
          // Jeśli liczba użytkowników się zmieniła, filtr został zastosowany
          roleFilterApplied = true;
        } else {
          // Jeśli liczba się nie zmieniła, sprawdź czy wszyscy użytkownicy mają wybraną rolę
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
        
        // Sprawdź, czy filtr został zastosowany poprawnie
        expect(roleFilterApplied).toBeTruthy();
        break;
      }
    }
    
    await page.screenshot({ path: 'admin-users-filtered.png' });
  });
  
  // Scenariusz 9: Weryfikacja dostępu do panelu admina
  test('should prevent non-admin users from accessing admin panel', async ({ page }) => {
    // Wyloguj się najpierw
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
    
    // Zaloguj się jako kupujący
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
    
    // Próba dostępu do panelu admina jako kupujący
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Sprawdź, czy został przekierowany lub dostał błąd 403
    const currentUrl = page.url();
    
    // Zrób zrzut ekranu, aby zobaczyć co się stało
    await page.screenshot({ path: 'buyer-admin-access.png' });
    
    // Sprawdź czy URL nie kończy się na /admin
    const buyerRedirected = !currentUrl.endsWith('/admin');
    
    // Jeśli nie został przekierowany, sprawdź czy otrzymał komunikat o błędzie dostępu
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
    
    // Sprawdź, czy kupujący nie ma dostępu
    expect(buyerAccessDenied).toBeTruthy();
    
    // Powtórz dla sprzedawcy
    // Wyloguj się najpierw
    await page.goto('/');
    
    for (const selector of logoutSelectors) {
      const logoutButton = page.locator(selector).first();
      if (await logoutButton.count() > 0) {
        await logoutButton.click();
        await page.waitForTimeout(1000);
        break;
      }
    }
    
    // Zaloguj się jako sprzedawca
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
    
    // Próba dostępu do panelu admina jako sprzedawca
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    
    // Sprawdź, czy został przekierowany lub dostał błąd 403
    const currentUrlSeller = page.url();
    
    // Zrób zrzut ekranu, aby zobaczyć co się stało
    await page.screenshot({ path: 'seller-admin-access.png' });
    
    // Sprawdź czy URL nie kończy się na /admin
    const sellerRedirected = !currentUrlSeller.endsWith('/admin');
    
    // Jeśli nie został przekierowany, sprawdź czy otrzymał komunikat o błędzie dostępu
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
    
    // Sprawdź, czy sprzedawca nie ma dostępu
    expect(sellerAccessDenied).toBeTruthy();
  });
}); 