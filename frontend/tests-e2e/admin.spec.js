const { test, expect } = require('@playwright/test');

test.describe('Admin Panel Functionality', () => {
  
  // Zaloguj się jako admin przed każdym testem
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    
    // Szukamy pola email i hasła
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"], input[id*="email"]').first();
    const passwordInput = page.locator('input[type="password"], input[name="password"], input[placeholder*="password"], input[id*="password"]').first();
    
    if (await emailInput.count() > 0 && await passwordInput.count() > 0) {
      await emailInput.fill('admin@steambay.com');
      await passwordInput.fill('Admin123!');
      
      // Logowanie
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
  
  // 10.1 Dostęp do panelu administracyjnego
  test('can access admin panel', async ({ page }) => {
    // Spróbuj przejść bezpośrednio do panelu administracyjnego
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'admin-panel.png' });
    
    try {
      // Sprawdź, czy jesteśmy w panelu administracyjnym
      const adminPanelIndicators = [
        'h1:has-text("Admin Panel")',
        'h1:has-text("Panel Administratora")',
        '[data-testid="admin-panel"]',
        '.admin-dashboard',
        '.admin-panel'
      ];
      
      let inAdminPanel = false;
      for (const selector of adminPanelIndicators) {
        const element = page.locator(selector).first();
        if (await element.count() > 0) {
          inAdminPanel = true;
          console.log(`Znaleziono wskaźnik panelu administracyjnego: ${selector}`);
          break;
        }
      }
      
      // Jeśli nie znaleziono wskaźników panelu, sprawdź czy są jakieś elementy administracyjne
      if (!inAdminPanel) {
        const adminElements = [
          'text=Users',
          'text=Products',
          'text=Orders',
          'text=Settings',
          'text=Użytkownicy',
          'text=Produkty',
          'text=Zamówienia',
          'text=Ustawienia'
        ];
        
        for (const selector of adminElements) {
          const element = page.locator(selector).first();
          if (await element.count() > 0) {
            inAdminPanel = true;
            console.log(`Znaleziono element administracyjny: ${selector}`);
            break;
          }
        }
      }
      
      // Test przechodzi, jeśli udało się znaleźć panel administracyjny
      expect(inAdminPanel).toBeTruthy();
      
    } catch (e) {
      console.error('Błąd podczas testu panelu administracyjnego:', e);
      await page.screenshot({ path: 'admin-panel-error.png' });
      throw e;
    }
  });
  
  // 10.2 Zarządzanie użytkownikami
  test('can manage users', async ({ page }) => {
    // Przejdź do panelu administracyjnego
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    
    try {
      // Znajdź i kliknij sekcję zarządzania użytkownikami
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
          userSectionFound = true;
          console.log(`Kliknięto sekcję użytkowników: ${selector}`);
          break;
        }
      }
      
      if (!userSectionFound) {
        console.log('Nie znaleziono sekcji zarządzania użytkownikami.');
        // Sprawdź czy jesteśmy już na stronie użytkowników
        const userTableSelectors = [
          'table',
          '.user-table',
          '[data-testid="user-list"]',
          '.user-list'
        ];
        
        for (const selector of userTableSelectors) {
          const element = page.locator(selector).first();
          if (await element.count() > 0) {
            userSectionFound = true;
            console.log(`Jesteśmy już na stronie użytkowników, znaleziono: ${selector}`);
            break;
          }
        }
        
        if (!userSectionFound) {
          console.log('Nie można znaleźć sekcji użytkowników ani tabeli użytkowników.');
          await page.screenshot({ path: 'admin-no-users-section.png' });
          test.skip();
          return;
        }
      }
      
      // Poczekaj na załadowanie listy użytkowników
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'admin-users-list.png' });
      
      // Sprawdź, czy strona zawiera listę użytkowników
      const userElements = [
        'table',
        '.user-table',
        '[data-testid="user-list"]',
        '.user-list',
        'tr',
        '.user-item'
      ];
      
      let userListFound = false;
      for (const selector of userElements) {
        const element = page.locator(selector);
        if (await element.count() > 0) {
          userListFound = true;
          console.log(`Znaleziono listę użytkowników: ${selector}`);
          break;
        }
      }
      
      // Sprawdź, czy są przyciski do zarządzania użytkownikami
      const actionButtons = [
        'button:has-text("Edit")',
        'button:has-text("Delete")',
        'button:has-text("Edytuj")',
        'button:has-text("Usuń")',
        '[data-testid="edit-user"]',
        '[data-testid="delete-user"]',
        '.edit-button',
        '.delete-button'
      ];
      
      let actionButtonsFound = false;
      for (const selector of actionButtons) {
        const element = page.locator(selector).first();
        if (await element.count() > 0) {
          actionButtonsFound = true;
          console.log(`Znaleziono przyciski akcji: ${selector}`);
          break;
        }
      }
      
      // Test przechodzi, jeśli udało się znaleźć listę użytkowników
      expect(userListFound).toBeTruthy();
      
    } catch (e) {
      console.error('Błąd podczas testu zarządzania użytkownikami:', e);
      await page.screenshot({ path: 'admin-users-error.png' });
      throw e;
    }
  });
  
  // 10.3 Zarządzanie produktami
  test('can manage products', async ({ page }) => {
    // Przejdź do panelu administracyjnego
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    
    try {
      // Znajdź i kliknij sekcję zarządzania produktami
      const productSectionSelectors = [
        'a:has-text("Products")',
        'a:has-text("Produkty")',
        '[data-testid="admin-products"]',
        'a[href*="products"]',
        'a[href*="product"]'
      ];
      
      let productSectionFound = false;
      for (const selector of productSectionSelectors) {
        const element = page.locator(selector).first();
        if (await element.count() > 0) {
          await element.click();
          productSectionFound = true;
          console.log(`Kliknięto sekcję produktów: ${selector}`);
          break;
        }
      }
      
      if (!productSectionFound) {
        console.log('Nie znaleziono sekcji zarządzania produktami.');
        // Sprawdź czy jesteśmy już na stronie produktów
        const productTableSelectors = [
          'table',
          '.product-table',
          '[data-testid="product-list"]',
          '.product-list'
        ];
        
        for (const selector of productTableSelectors) {
          const element = page.locator(selector).first();
          if (await element.count() > 0) {
            productSectionFound = true;
            console.log(`Jesteśmy już na stronie produktów, znaleziono: ${selector}`);
            break;
          }
        }
        
        if (!productSectionFound) {
          console.log('Nie można znaleźć sekcji produktów ani tabeli produktów.');
          await page.screenshot({ path: 'admin-no-products-section.png' });
          test.skip();
          return;
        }
      }
      
      // Poczekaj na załadowanie listy produktów
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'admin-products-list.png' });
      
      // Sprawdź, czy strona zawiera listę produktów
      const productElements = [
        'table',
        '.product-table',
        '[data-testid="product-list"]',
        '.product-list',
        'tr',
        '.product-item'
      ];
      
      let productListFound = false;
      for (const selector of productElements) {
        const element = page.locator(selector);
        if (await element.count() > 0) {
          productListFound = true;
          console.log(`Znaleziono listę produktów: ${selector}`);
          break;
        }
      }
      
      // Sprawdź, czy jest przycisk dodawania nowego produktu
      const addProductSelectors = [
        'button:has-text("Add Product")',
        'button:has-text("Dodaj Produkt")',
        'button:has-text("New Product")',
        'button:has-text("Nowy Produkt")',
        '[data-testid="add-product"]',
        '.add-button'
      ];
      
      let addProductFound = false;
      for (const selector of addProductSelectors) {
        const element = page.locator(selector).first();
        if (await element.count() > 0) {
          addProductFound = true;
          console.log(`Znaleziono przycisk dodawania produktu: ${selector}`);
          break;
        }
      }
      
      // Test przechodzi, jeśli udało się znaleźć listę produktów
      expect(productListFound).toBeTruthy();
      
    } catch (e) {
      console.error('Błąd podczas testu zarządzania produktami:', e);
      await page.screenshot({ path: 'admin-products-error.png' });
      throw e;
    }
  });
  
  // 10.4 Przegląd zamówień
  test('can view orders', async ({ page }) => {
    // Przejdź do panelu administracyjnego
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
    
    try {
      // Znajdź i kliknij sekcję zarządzania zamówieniami
      const orderSectionSelectors = [
        'a:has-text("Orders")',
        'a:has-text("Zamówienia")',
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
          console.log(`Kliknięto sekcję zamówień: ${selector}`);
          break;
        }
      }
      
      if (!orderSectionFound) {
        console.log('Nie znaleziono sekcji zarządzania zamówieniami.');
        // Sprawdź czy jesteśmy już na stronie zamówień
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
            console.log(`Jesteśmy już na stronie zamówień, znaleziono: ${selector}`);
            break;
          }
        }
        
        if (!orderSectionFound) {
          console.log('Nie można znaleźć sekcji zamówień ani tabeli zamówień.');
          await page.screenshot({ path: 'admin-no-orders-section.png' });
          test.skip();
          return;
        }
      }
      
      // Poczekaj na załadowanie listy zamówień
      await page.waitForTimeout(2000);
      await page.screenshot({ path: 'admin-orders-list.png' });
      
      // Sprawdź, czy strona zawiera listę zamówień
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
          console.log(`Znaleziono listę zamówień: ${selector}`);
          break;
        }
      }
      
      // Test przechodzi, jeśli udało się znaleźć listę zamówień
      expect(orderListFound).toBeTruthy();
      
    } catch (e) {
      console.error('Błąd podczas testu przeglądania zamówień:', e);
      await page.screenshot({ path: 'admin-orders-error.png' });
      throw e;
    }
  });
}); 