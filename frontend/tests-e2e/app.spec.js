const { test, expect } = require('@playwright/test');

test.describe('Basic application functionality', () => {
  test('application loads correctly', async ({ page }) => {
    // Przejdź do aplikacji
    await page.goto('/');
    
    // Poczekaj na pełne załadowanie strony
    await page.waitForLoadState('networkidle');
    
    // Zrób zrzut ekranu głównej strony do analizy
    await page.screenshot({ path: 'home-page.png' });
    
    // Sprawdź czy strona ma podstawową strukturę HTML
    const title = await page.title();
    console.log(`Tytuł strony: ${title}`);
    
    // Pobierz zawartość body dla celów diagnostycznych
    const bodyContent = await page.textContent('body');
    console.log(`Znaleziono ${bodyContent.length} znaków na stronie głównej`);
    
    // Test przechodzi, jeśli strona się załadowała i ma jakąś zawartość
    expect(bodyContent.length).toBeGreaterThan(0);
    
    // Sprawdź, czy można znaleźć jakikolwiek element wskazujący na React
    const hasReactElements = await page.evaluate(() => {
      return document.querySelectorAll('[data-reactroot], [data-reactid], [class*="react"]').length > 0;
    });
    
    console.log(`Znaleziono elementy React: ${hasReactElements}`);
    
    // Sprawdź czy istnieją jakieś podstawowe elementy nawigacyjne
    const navElements = await page.locator('nav, header, .navbar, .header, .navigation').count();
    console.log(`Znaleziono ${navElements} elementów nawigacyjnych`);
  });
}); 