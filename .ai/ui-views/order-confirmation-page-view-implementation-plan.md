# Plan implementacji widoku OrderConfirmationPage (Potwierdzenie Zamówienia)

## 1. Przegląd
Widok "Potwierdzenie Zamówienia" (`OrderConfirmationPage`) jest wyświetlany użytkownikowi po pomyślnym przetworzeniu płatności za zamówienie (co jest sygnalizowane przez status zamówienia `processing` po obsłużeniu callbacku przez backend). Informuje użytkownika o sukcesie, wyświetla numer zamówienia, podstawowe podsumowanie zakupionych przedmiotów i dostarcza link do pełnej historii zamówień. Kluczowym elementem tego widoku jest również wyczyszczenie koszyka użytkownika.

## 2. Routing widoku
-   **Ścieżka:** `/order/confirmation` (lub `/payment/success` - ścieżka docelowa po powrocie z mocka płatności, może nie zawierać `:orderId` bezpośrednio w URL, jeśli ID jest pobierane inaczej).
    *   **Uwaga:** Mechanizm przekazania `orderId` do tego widoku musi zostać zaimplementowany. Zakładamy, że `orderId` ostatniego zamówienia jest zapisywany w `sessionStorage` *przed* przekierowaniem do mocka płatności i odczytywany przez ten komponent po powrocie.
-   **Ochrona:** Wymaga zalogowanego użytkownika (Kupującego). Powinien być dostępny tylko bezpośrednio po udanej transakcji.

## 3. Struktura komponentów
```
OrderConfirmationPage (src/pages/orders/OrderConfirmationPage.js)
├── SuccessMessage (src/components/orders/SuccessMessage.js)
├── ConfirmationOrderSummary (src/components/orders/ConfirmationOrderSummary.js)
│   └── ConfirmationOrderItem (src/components/orders/ConfirmationOrderItem.js) // mapowany
└── Link (React Router, to="/orders")
```

## 4. Szczegóły komponentów

### `OrderConfirmationPage`
-   **Opis komponentu:** Główny komponent kontenerowy. Odpowiedzialny za:
    -   Pobranie `orderId` ostatniego zamówienia (np. z `sessionStorage`).
    -   Pobranie szczegółów zamówienia (`GET /orders/:orderId`) w celu weryfikacji statusu i wyświetlenia podsumowania.
    -   Weryfikację, czy status zamówienia to `processing`.
    -   Wywołanie funkcji czyszczącej koszyk z `CartContext` (jeśli status to `processing`).
    -   Zarządzanie stanami ładowania i błędów.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Komponent `SuccessMessage`.
    -   Komponent `ConfirmationOrderSummary` (renderowany warunkowo po sukcesie i załadowaniu danych).
    -   Link do historii zamówień (`<Link to="/orders">`).
    -   Elementy do wyświetlania stanu ładowania (`Spinner`) i komunikatów o błędach (np. "Weryfikacja statusu płatności...", "Nie udało się potwierdzić zamówienia.").
-   **Obsługiwane interakcje:** Brak bezpośrednich, reaguje na załadowanie strony.
-   **Obsługiwana walidacja:** Sprawdzenie statusu zamówienia (`=== 'processing'`).
-   **Typy:** `ConfirmationOrderDetailVM | null`.
-   **Propsy:** Brak.

### `SuccessMessage`
-   **Opis komponentu:** Wyświetla komunikat o sukcesie, ikonę i numer potwierdzonego zamówienia.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Ikona sukcesu (np. SVG lub FontAwesome).
    -   Nagłówek `<h2>` lub `<p>` z tekstem "Zamówienie złożone pomyślnie!".
    -   Paragraf `<p>` z tekstem "Numer Twojego zamówienia: **{displayOrderId}**".
    -   Stylizacja Bootstrap (np. `alert alert-success`).
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** Brak specyficznych.
-   **Propsy:**
    -   `displayOrderId: string` - Sformatowany numer zamówienia do wyświetlenia.

### `ConfirmationOrderSummary`
-   **Opis komponentu:** Wyświetla uproszczone podsumowanie zamówienia (lista produktów).
-   **Główne elementy HTML i komponenty dzieci:**
    -   Nagłówek (np. `<h4>Podsumowanie zamówienia:</h4>`).
    -   Lista `ul` lub tabela `table` (Bootstrap) do wyświetlenia pozycji.
    -   Mapowanie `items` na komponenty `ConfirmationOrderItem`.
    -   Wyświetlenie łącznej kwoty zamówienia (`order.totalAmount`).
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `ConfirmationOrderItemVM[]`, `string` (dla totalAmount).
-   **Propsy:**
    -   `items: ConfirmationOrderItemVM[]`
    -   `totalAmount: string`

### `ConfirmationOrderItem`
-   **Opis komponentu:** Wyświetla pojedynczą pozycję w podsumowaniu zamówienia na stronie potwierdzenia.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Element `li` lub `tr`.
    -   Wyświetlane pola: `item.offerTitle`, `item.quantity`, `item.priceAtPurchaseFormatted`, `item.itemSumFormatted`.
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `ConfirmationOrderItemVM`.
-   **Propsy:**
    -   `item: ConfirmationOrderItemVM`

## 5. Typy

### `OrderDetailDTO` (z `schemas.OrderDetailDTO`, odpowiedź API `GET /orders/{order_id}`)
```typescript
// Jak w planie dla OrderDetailPage
interface OrderDetailDTO {
  id: string; // UUID zamówienia
  buyer_id: string; // UUID kupującego
  status: 'pending_payment' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'failed';
  created_at: string;
  updated_at?: string | null;
  items: OrderItemDTO[];
  total_amount: string;
}
```

### `OrderItemDTO` (z `schemas.OrderItemDTO`, część `OrderDetailDTO`)
```typescript
// Jak w planie dla OrderDetailPage
interface OrderItemDTO {
  id: number;
  offer_id: string;
  quantity: number;
  price_at_purchase: string;
  offer_title: string;
}
```

### `ConfirmationOrderItemVM` (ViewModel dla `ConfirmationOrderItem`)
```typescript
interface ConfirmationOrderItemVM {
  offerTitle: string;
  quantity: number;
  priceAtPurchaseFormatted: string; // Sformatowana cena jednostkowa z walutą
  itemSumFormatted: string; // Sformatowana suma pozycji z walutą
}
```

### `ConfirmationOrderDetailVM` (ViewModel dla `OrderConfirmationPage`)
```typescript
interface ConfirmationOrderDetailVM {
  id: string; // UUID zamówienia
  displayId: string; // Skrócone ID zamówienia do wyświetlania
  items: ConfirmationOrderItemVM[];
  totalAmount: string; // Sformatowana łączna kwota
  // Status nie jest bezpośrednio potrzebny w VM, bo komponent jest renderowany tylko dla 'processing'
}
```

## 6. Zarządzanie stanem

Stan zarządzany w `OrderConfirmationPage` (`useState`, `useEffect`).

-   `orderId: string | null`: ID zamówienia odczytane z `sessionStorage`. Inicjalnie `null`.
-   `orderDetails: ConfirmationOrderDetailVM | null`: Dane zamówienia po pomyślnym pobraniu i weryfikacji statusu. Inicjalnie `null`.
-   `isLoading: boolean`: Wskazuje na proces pobierania i weryfikacji. Inicjalnie `true`.
-   `error: string | null`: Komunikat błędu (problem z pobraniem ID, błąd API, nieprawidłowy status zamówienia). Inicjalnie `null`.
-   `verificationComplete: boolean`: Flaga wskazująca, czy proces weryfikacji został zakończony (sukcesem lub błędem).

```javascript
// W OrderConfirmationPage.js
import { useState, useEffect, useContext } from 'react';
import { CartContext } from '../../contexts/CartContext'; // Przykład

const [orderId, setOrderId] = useState<string | null>(null);
const [orderDetails, setOrderDetails] = useState<ConfirmationOrderDetailVM | null>(null);
const [isLoading, setIsLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [verificationComplete, setVerificationComplete] = useState(false);
const { clearCart } = useContext(CartContext);

useEffect(() => {
  // 1. Pobierz orderId z sessionStorage
  const storedOrderId = sessionStorage.getItem('lastOrderId');
  if (!storedOrderId) {
    setError('Nie można zidentyfikować zamówienia.');
    setIsLoading(false);
    setVerificationComplete(true);
    return;
  }
  setOrderId(storedOrderId);

  // 2. Wywołaj funkcję weryfikującą
  verifyOrder(storedOrderId);

}, []); // Uruchom tylko raz

const verifyOrder = async (id: string) => {
  try {
    const fetchedOrderDTO = await orderService.fetchOrderDetails(id); // Wywołanie API

    if (fetchedOrderDTO.status === 'processing') {
      // 3. Sukces - mapuj DTO na VM
      const vm = mapOrderToConfirmationVM(fetchedOrderDTO);
      setOrderDetails(vm);
      // 4. Wyczyść koszyk
      clearCart();
      // Opcjonalnie: usuń ID z sessionStorage
      sessionStorage.removeItem('lastOrderId');
    } else {
      // 5. Błąd - niepoprawny status
      setError(`Nieprawidłowy status zamówienia: ${fetchedOrderDTO.status}. Płatność mogła się nie powiesć.`);
      // Opcjonalnie: usuń ID z sessionStorage
      sessionStorage.removeItem('lastOrderId');
    }
  } catch (apiError) {
    // 6. Błąd API
    setError('Nie udało się zweryfikować statusu zamówienia. Skontaktuj się z obsługą.');
    // Log apiError
  } finally {
    setIsLoading(false);
    setVerificationComplete(true);
  }
};
```

## 7. Integracja API

Serwis `src/services/orderService.js`.

### `GET /orders/{order_id}`
-   **Cel:** Pobranie szczegółów zamówienia w celu weryfikacji statusu (`processing`) i uzyskania danych do podsumowania.
-   **Akcja:** Wywoływane raz przez `OrderConfirmationPage` po odczytaniu `orderId` z `sessionStorage`.
-   **Odpowiedź (sukces 200 OK):** `OrderDetailDTO`. Frontend sprawdza pole `status`. Jeśli `processing`, mapuje na `ConfirmationOrderDetailVM` i czyści koszyk. Jeśli inny, traktuje jako błąd dla tej strony.
-   **Błędy:**
    -   `401 Unauthorized (NOT_AUTHENTICATED)`: Globalna obsługa.
    -   `403 Forbidden (ACCESS_DENIED)`: Ustawienie `error` ("Brak dostępu do zamówienia.").
    -   `404 Not Found (ORDER_NOT_FOUND)`: Ustawienie `error` ("Zamówienie nie znalezione.").
    -   `500 Internal Server Error (FETCH_FAILED)`: Ustawienie `error` ("Błąd serwera.").

## 8. Interakcje użytkownika
1.  **Automatyczne działania po wejściu na stronę:**
    -   Pobranie `orderId` z `sessionStorage`.
    -   Wyświetlenie stanu ładowania/weryfikacji.
    -   Wywołanie `GET /orders/:orderId`.
    -   Weryfikacja statusu (`processing`).
    -   Wyczyszczenie koszyka (`CartContext`).
    -   Aktualizacja stanu (wyświetlenie sukcesu lub błędu).
2.  **Kliknięcie linku "Zobacz historię zamówień":**
    -   Przekierowanie na `/orders` (React Router).

## 9. Warunki i walidacja
-   **Istnienie `orderId`:** Komponent musi znaleźć `orderId` w `sessionStorage`.
-   **Status zamówienia:** Musi być `processing`, aby strona potwierdzenia została poprawnie wyświetlona. Inne statusy są traktowane jako błąd w kontekście tej strony.
-   Użytkownik musi być zalogowany (`AuthContext`).

## 10. Obsługa błędów
-   **Brak `orderId` w `sessionStorage`:** Wyświetlić błąd "Nie można zidentyfikować zamówienia do potwierdzenia."
-   **Błędy API (`GET /orders/:orderId`):**
    -   `401`: Globalna obsługa.
    -   `403`: Wyświetlić błąd "Brak dostępu do podglądu tego zamówienia."
    -   `404`: Wyświetlić błąd "Nie znaleziono zamówienia powiązanego z tą transakcją."
    -   `500`: Wyświetlić błąd "Wystąpił błąd serwera podczas weryfikacji zamówienia."
-   **Nieprawidłowy status zamówienia (inny niż `processing`):** Wyświetlić błąd "Status zamówienia nie został poprawnie zaktualizowany. Skontaktuj się z pomocą techniczną." lub podobny.
-   **Wszystkie błędy:** Stan `isLoading` na `false`, `verificationComplete` na `true`, `error` ustawiony, nie renderować `SuccessMessage` ani `ConfirmationOrderSummary`, tylko komunikat błędu.

## 11. Kroki implementacji
1.  **Zapewnienie zapisywania `orderId`:** Upewnić się, że w procesie *przed* przekierowaniem do mocka płatności (np. po otrzymaniu odpowiedzi z `POST /orders`), `orderId` jest zapisywany do `sessionStorage` (np. `sessionStorage.setItem('lastOrderId', orderId)`).
2.  **Utworzenie struktury plików:**
    -   `src/pages/orders/OrderConfirmationPage.js`
    -   `src/components/orders/SuccessMessage.js`
    -   `src/components/orders/ConfirmationOrderSummary.js`
    -   `src/components/orders/ConfirmationOrderItem.js`
    -   Upewnić się, że `src/services/orderService.js` ma funkcję `fetchOrderDetails(orderId)`.
    -   Upewnić się, że `CartContext` (`src/contexts/CartContext.js`) eksportuje funkcję `clearCart()`.
3.  **Implementacja `OrderConfirmationPage.js`:**
    -   Dodać routing (np. `/order/confirmation` lub `/payment/success`).
    -   Zaimplementować stany (`orderId`, `orderDetails`, `isLoading`, `error`, `verificationComplete`).
    -   W `useEffect`:
        -   Odczytać `orderId` z `sessionStorage`.
        -   Obsłużyć błąd braku `orderId`.
        -   Wywołać asynchroniczną funkcję weryfikującą (jak w przykładzie w sekcji 6).
    -   Funkcja weryfikująca:
        -   Wywołuje `orderService.fetchOrderDetails`.
        -   Sprawdza status odpowiedzi.
        -   Jeśli `processing`, mapuje DTO na VM, ustawia `orderDetails`, wywołuje `clearCart()`, usuwa `orderId` z sessionStorage.
        -   Jeśli inny status lub błąd API, ustawia `error`, usuwa `orderId` z sessionStorage.
        -   Ustawia `isLoading` na `false` i `verificationComplete` na `true` w bloku `finally`.
    -   Renderowanie warunkowe:
        -   Gdy `isLoading`, pokazać `Spinner`.
        -   Gdy `verificationComplete` i `error`, pokazać komunikat błędu.
        -   Gdy `verificationComplete` i `orderDetails`, pokazać `SuccessMessage`, `ConfirmationOrderSummary` i link do `/orders`.
4.  **Implementacja `SuccessMessage.js`:**
    -   Prosty komponent wyświetlający ikonę, tekst sukcesu i przekazany `displayOrderId`.
5.  **Implementacja `ConfirmationOrderSummary.js`:**
    -   Przyjmować `items` i `totalAmount` jako props.
    -   Renderować listę/tabelę, mapując `items` na `ConfirmationOrderItem`.
    -   Wyświetlić `totalAmount`.
6.  **Implementacja `ConfirmationOrderItem.js`:**
    -   Przyjmować `item` jako props.
    -   Wyświetlić dane pozycji (`offerTitle`, `quantity`, `priceAtPurchaseFormatted`, `itemSumFormatted`).
7.  **Mapowanie DTO na VM:**
    -   Funkcja pomocnicza `mapOrderToConfirmationVM(dto: OrderDetailDTO): ConfirmationOrderDetailVM`.
    -   Mapowanie `OrderItemDTO` na `ConfirmationOrderItemVM` (formatowanie cen).
    -   Tworzenie `displayId`, formatowanie `totalAmount`.
8.  **Integracja z `CartContext`:**
    -   Użyć `useContext(CartContext)` w `OrderConfirmationPage` do pobrania `clearCart`.
9.  **Stylizacja:**
    -   Użycie Bootstrap 5 (`Container`, `Alert`, `Table`, `ListGroup`).
10. **Testowanie:**
    -   Symulacja pomyślnego powrotu: zapisać `orderId` do `sessionStorage`, upewnić się, że API zwróci status `processing` -> sprawdzić wyświetlenie potwierdzenia, podsumowania, linku i wyczyszczenie koszyka.
    -   Symulacja powrotu bez `orderId` w `sessionStorage` -> sprawdzić komunikat błędu.
    -   Symulacja powrotu, gdy API zwraca błąd (403, 404, 500) -> sprawdzić komunikaty błędów.
    -   Symulacja powrotu, gdy API zwraca inny status niż `processing` -> sprawdzić komunikat błędu.
    -   Sprawdzić działanie linku do historii zamówień.

</rewritten_file> 