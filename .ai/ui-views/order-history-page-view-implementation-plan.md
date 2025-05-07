# Plan implementacji widoku OrderHistoryPage (Historia Zamówień)

## 1. Przegląd
Widok "Historia Zamówień" (`OrderHistoryPage`) umożliwia zalogowanemu użytkownikowi (Kupującemu) przeglądanie listy swoich poprzednich zamówień. Wyświetla kluczowe informacje o każdym zamówieniu, takie jak ID, data złożenia, status oraz łączna kwota. Widok zawiera paginację do nawigacji po historii oraz linki do szczegółów poszczególnych zamówień.

## 2. Routing widoku
-   **Ścieżka:** `/orders`
-   **Ochrona:** Wymaga zalogowanego użytkownika z rolą "Kupujący" (Buyer). Przekierowanie na `/login` w przypadku braku autoryzacji lub na stronę główną/błędu w przypadku niepoprawnej roli.

## 3. Struktura komponentów
```
OrderHistoryPage (src/pages/orders/OrderHistoryPage.js)
├── OrdersList (src/components/orders/OrdersList.js)
│   └── OrderItem (src/components/orders/OrderItem.js) (mapowany dla każdego zamówienia)
│       ├── StatusBadge (src/components/shared/StatusBadge.js)
│       └── Link (React Router, do /orders/:orderId)
└── Pagination (src/components/common/Pagination.js)
```

## 4. Szczegóły komponentów

### `OrderHistoryPage`
-   **Opis komponentu:** Główny komponent kontenerowy dla widoku `/orders`. Odpowiedzialny za pobieranie historii zamówień użytkownika, zarządzanie stanem paginacji, ładowania i błędów oraz przekazywanie danych do komponentów podrzędnych.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Nagłówek strony (np. `<h1>Historia Zamówień</h1>`).
    -   Komponent `OrdersList` do wyświetlania listy zamówień.
    -   Komponent `Pagination` do obsługi paginacji.
    -   Elementy do wyświetlania stanu ładowania (np. `Spinner` lub skeleton loader dla listy) i komunikatów o błędach (np. "Nie udało się załadować historii zamówień.").
    -   Komunikat "Nie masz jeszcze żadnych zamówień.", jeśli lista jest pusta.
-   **Obsługiwane interakcje:** Zmiana strony w komponencie `Pagination`.
-   **Obsługiwana walidacja:** Brak bezpośredniej walidacji, przekazuje parametry `page` i `limit` do API.
-   **Typy:** `OrderSummaryVM[]`, `PaginationVM`.
-   **Propsy:** Brak.

### `OrdersList`
-   **Opis komponentu:** Komponent prezentacyjny, który otrzymuje listę zamówień i renderuje komponent `OrderItem` dla każdego z nich. Może wyświetlać nagłówki tabeli, jeśli zamówienia są prezentowane w formie tabelarycznej.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Element `div` lub `ul` jako kontener dla listy, lub struktura `table` (`thead`, `tbody`).
    -   Mapowanie tablicy `orders` na komponenty `OrderItem`.
    -   Nagłówki kolumn (jeśli tabela): "ID Zamówienia", "Data", "Status", "Kwota", "Akcje".
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `OrderSummaryVM[]`.
-   **Propsy:**
    -   `orders: OrderSummaryVM[]` - tablica obiektów zamówień do wyświetlenia.
    -   `isLoading: boolean` (opcjonalnie, do wyświetlania np. skeletonów na poziomie listy).

### `OrderItem`
-   **Opis komponentu:** Komponent prezentacyjny wyświetlający informacje o pojedynczym zamówieniu w liście. Zawiera link do strony szczegółów tego zamówienia.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Elementy `div`, `li` lub `tr` (w zależności od struktury `OrdersList`).
    -   Wyświetlane pola: `order.displayId`, `order.createdAt`, `order.totalAmount`.
    -   Komponent `StatusBadge` do wyświetlenia `order.statusDisplay`.
    -   Komponent `Link` z `react-router-dom` kierujący do `order.detailsLink` (np. `/orders/${order.id}`), z tekstem "Zobacz szczegóły".
-   **Obsługiwane interakcje:** Kliknięcie linku "Zobacz szczegóły".
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `OrderSummaryVM`.
-   **Propsy:**
    -   `order: OrderSummaryVM` - obiekt pojedynczego zamówienia.

### `Pagination` (zgodnie z `.ai/ui-plan.md`)
-   **Opis komponentu:** Reużywalny komponent do nawigacji po stronach list.
-   **Główne elementy HTML i komponenty dzieci:** Przyciski "Wstecz", "Dalej", numery stron.
-   **Obsługiwane interakcje:** Kliknięcie na numer strony lub przyciski nawigacyjne.
-   **Typy:** `PaginationVM`.
-   **Propsy:**
    -   `currentPage: number`
    -   `totalPages: number`
    -   `onPageChange: (page: number) => void`

### `StatusBadge` (zgodnie z `.ai/ui-plan.md`)
-   **Opis komponentu:** Reużywalny komponent do wyświetlania statusów z odpowiednim stylem.
-   **Główne elementy HTML i komponenty dzieci:** Element `span` z dynamicznymi klasami Bootstrap.
-   **Typy:** `OrderStatus` (enum backendowy), `string` (mapowana nazwa polska statusu).
-   **Propsy:**
    -   `status: OrderStatus` (lub przetworzona wartość, która pomoże określić styl i tekst).

## 5. Typy

### `OrderSummaryDTO` (z `schemas.OrderSummaryDTO`, odpowiedź API)
```typescript
interface OrderSummaryDTO {
  id: string; // UUID
  status: 'pending_payment' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'failed';
  total_amount: string; // np. "123.45"
  created_at: string; // ISO datetime string
  updated_at?: string | null; // ISO datetime string
}
```

### `OrderListResponseDTO` (z `schemas.OrderListResponse`, odpowiedź API)
```typescript
interface OrderListResponseDTO {
  items: OrderSummaryDTO[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
```

### `OrderSummaryVM` (ViewModel dla `OrderItem`)
```typescript
interface OrderSummaryVM {
  id: string; // Oryginalne UUID do tworzenia linku
  displayId: string; // Skrócone ID do wyświetlania, np. "Zam. #ABC123EF"
  status: 'pending_payment' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'failed'; // Oryginalny status
  statusDisplay: string; // Polska nazwa statusu, np. "Przetwarzane"
  statusClassName: string; // Klasa CSS dla StatusBadge, np. "badge bg-info"
  totalAmount: string; // Sformatowana kwota z walutą, np. "123,45 USD"
  createdAt: string; // Sformatowana data, np. "01.01.2023, 15:30"
  detailsLink: string; // Ścieżka do szczegółów, np. "/orders/uuid-order-id"
}
```
-   **Mapowanie `status` na `statusDisplay` i `statusClassName`**:
    ```javascript
    const orderStatusMap = {
      pending_payment: { text: 'Oczekuje na płatność', className: 'badge bg-warning text-dark' },
      processing: { text: 'Przetwarzane', className: 'badge bg-info' },
      shipped: { text: 'Wysłane', className: 'badge bg-primary' },
      delivered: { text: 'Dostarczone', className: 'badge bg-success' },
      cancelled: { text: 'Anulowane', className: 'badge bg-danger' },
      failed: { text: 'Nieudane', className: 'badge bg-secondary text-white' }, // Dodano text-white dla lepszego kontrastu na ciemnym tle
    };
    ```

### `PaginationVM` (ViewModel dla `Pagination`)
```typescript
interface PaginationVM {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
}
```

## 6. Zarządzanie stanem

Stan będzie zarządzany w komponencie `OrderHistoryPage` przy użyciu hooków `useState` i `useEffect`.

-   `orders: OrderSummaryVM[]`: Przechowuje listę zamówień dla bieżącej strony. Inicjalnie `[]`.
-   `paginationData: PaginationVM | null`: Przechowuje informacje o paginacji (`currentPage`, `totalPages`, `totalItems`, `itemsPerPage`). Inicjalnie `null`.
-   `isLoading: boolean`: Wskazuje, czy trwa pobieranie danych. Domyślnie `true` przy pierwszym ładowaniu.
-   `error: string | null`: Przechowuje komunikat błędu API. Inicjalnie `null`.
-   `currentPageInternal: number`: Stan dla aktualnie żądanej strony. Inicjalnie `1`. Można zintegrować z parametrami URL (`useSearchParams` z React Router).

Opcjonalnie można stworzyć custom hook `useOrderHistory(initialPage: number, itemsPerPage: number)` do enkapsulacji logiki pobierania danych i zarządzania stanem.

```javascript
// W OrderHistoryPage.js
const [orders, setOrders] = useState<OrderSummaryVM[]>([]);
const [paginationData, setPaginationData] = useState<PaginationVM | null>(null);
const [isLoading, setIsLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [currentPageInternal, setCurrentPageInternal] = useState(1);
const ITEMS_PER_PAGE = 10; // Można ustawić jako stałą lub konfigurowalną
```

## 7. Integracja API

Komunikacja z API będzie realizowana przez dedykowany serwis, np. `src/services/orderService.js`.

### `GET /orders`
-   **Cel:** Pobranie paginowanej listy zamówień dla zalogowanego Kupującego.
-   **Akcja:** Wywoływane przy montowaniu `OrderHistoryPage` oraz przy zmianie `currentPageInternal`.
-   **Parametry Query:** `page` (z `currentPageInternal`), `limit` (np. `ITEMS_PER_PAGE`).
-   **Odpowiedź (sukces 200 OK):** `OrderListResponseDTO`.
    ```json
    // Przykład
    {
      "items": [
        { "id": "uuid1", "status": "delivered", "total_amount": "99.90", "created_at": "2023-01-15T10:00:00Z" }
      ],
      "total": 1,
      "page": 1,
      "limit": 10,
      "pages": 1
    }
    ```
    Frontend mapuje `items` (tablica `OrderSummaryDTO`) na `OrderSummaryVM[]` i aktualizuje stany `orders` oraz `paginationData`.
-   **Błędy:**
    -   `401 Unauthorized (NOT_AUTHENTICATED)`: Obsługa globalna (przekierowanie na `/login`).
    -   `403 Forbidden (INSUFFICIENT_PERMISSIONS)`: Obsługa globalna lub lokalna (przekierowanie / wyświetlenie błędu).
    -   `500 Internal Server Error (FETCH_FAILED)`: Ustawienie stanu `error` i wyświetlenie komunikatu.

## 8. Interakcje użytkownika
1.  **Ładowanie strony:**
    -   Użytkownik przechodzi na `/orders`.
    -   Wyświetlany jest wskaźnik ładowania (np. `Spinner` lub skeleton dla listy).
    -   Wykonywane jest żądanie `GET /orders?page=1&limit=ITEMS_PER_PAGE`.
    -   Po otrzymaniu danych:
        -   Wskaźnik ładowania znika.
        -   `OrdersList` wypełnia się zamówieniami.
        -   `Pagination` wyświetla informacje o stronach.
        -   Jeśli brak zamówień, wyświetlany jest komunikat "Nie masz jeszcze żadnych zamówień."
2.  **Zmiana strony paginacji:**
    -   Użytkownik klika na numer strony lub przycisk "Następna"/"Poprzednia" w komponencie `Pagination`.
    -   `OrderHistoryPage` aktualizuje `currentPageInternal`.
    -   Wyświetlany jest wskaźnik ładowania dla listy.
    -   Wykonywane jest nowe żądanie `GET /orders` z nowym numerem strony.
    -   `OrdersList` aktualizuje się nowymi danymi.
3.  **Kliknięcie "Zobacz szczegóły":**
    -   Użytkownik klika link "Zobacz szczegóły" przy konkretnym zamówieniu w `OrderItem`.
    -   Następuje przekierowanie na stronę szczegółów zamówienia (np. `/orders/uuid-order-id`) obsługiwane przez React Router.

## 9. Warunki i walidacja
-   Na poziomie tego widoku nie ma walidacji formularzy.
-   Parametry `page` i `limit` dla API są kontrolowane przez logikę komponentu `OrderHistoryPage` i `Pagination`. Domyślny `limit` to np. 10.
-   Widok musi być dostępny tylko dla zalogowanych użytkowników z rolą "Buyer".

## 10. Obsługa błędów
-   **Błąd pobierania danych (`GET /orders`):**
    -   `401 Unauthorized`: Globalny `AuthContext` powinien przekierować na `/login`.
    -   `403 Forbidden`: Globalny `AuthContext` lub `ProtectedRoute` powinien przekierować na stronę błędu dostępu lub stronę główną.
    -   `500 Internal Server Error` lub błąd sieciowy:
        -   Ustawić stan `error` w `OrderHistoryPage`.
        -   Wyświetlić komunikat użytkownikowi, np. "Wystąpił błąd podczas ładowania historii zamówień. Spróbuj ponownie później." zamiast listy zamówień.
        -   Ukryć komponent `Pagination` lub wyświetlić go w stanie nieaktywnym.
-   **Brak zamówień:**
    -   Jeśli API zwróci `total: 0` lub pustą tablicę `items`, `OrderHistoryPage` powinien wyświetlić komunikat "Nie masz jeszcze żadnych zamówień." zamiast `OrdersList` i `Pagination`.

## 11. Kroki implementacji
1.  **Utworzenie struktury plików:**
    -   `src/pages/orders/OrderHistoryPage.js`
    -   `src/components/orders/OrdersList.js`
    -   `src/components/orders/OrderItem.js`
    -   (Zakładamy, że `Pagination.js` i `StatusBadge.js` już istnieją w `src/components/common/` lub `src/components/shared/`).
    -   Rozszerzenie `src/services/orderService.js` o funkcję `fetchOrderHistory(page, limit)`.
2.  **Implementacja `orderService.js`:**
    -   Dodać funkcję `fetchOrderHistory(page, limit)` wysyłającą żądanie `GET /orders` z odpowiednimi parametrami.
3.  **Implementacja `OrderHistoryPage.js`:**
    -   Dodać routing dla `/orders` w głównym konfiguratorze routera (np. `src/routes/index.js`), zabezpieczając go dla roli "Buyer".
    -   Zaimplementować stany: `orders`, `paginationData`, `isLoading`, `error`, `currentPageInternal`.
    -   W `useEffect` (zależnym od `currentPageInternal`):
        -   Wywołać `orderService.fetchOrderHistory`.
        -   Obsłużyć sukces: zmapować DTO na VM, zaktualizować stany.
        -   Obsłużyć błędy: zaktualizować stan `error`.
        -   Zarządzać stanem `isLoading`.
    -   Zaimplementować funkcję `handlePageChange` przekazywaną do `Pagination`.
    -   Renderować `OrdersList`, `Pagination` lub komunikaty o ładowaniu/błędzie/braku danych.
4.  **Implementacja `OrdersList.js`:**
    -   Przyjmować `orders: OrderSummaryVM[]` jako props.
    -   Renderować listę (np. `ul` lub `table > tbody`) mapując `orders` na `OrderItem`.
    -   Opcjonalnie: dodać nagłówki tabeli.
5.  **Implementacja `OrderItem.js`:**
    -   Przyjmować `order: OrderSummaryVM` jako props.
    -   Wyświetlić dane zamówienia: `order.displayId`, `order.createdAt`, `order.totalAmount`.
    -   Użyć komponentu `StatusBadge`, przekazując mu `order.statusDisplay` i/lub `order.statusClassName` (lub `order.status` jeśli `StatusBadge` sam mapuje).
    -   Dodać `Link` z `react-router-dom` do `order.detailsLink`.
6.  **Mapowanie DTO na VM:**
    -   Stworzyć funkcję pomocniczą (np. w `OrderHistoryPage.js` lub w serwisie) do mapowania `OrderSummaryDTO` na `OrderSummaryVM`.
    -   Ta funkcja powinna formatować daty (np. `new Intl.DateTimeFormat('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(dto.created_at))`).
    -   Formatować kwotę (np. `new Intl.NumberFormat('pl-PL', { style: 'currency', currency: 'USD' }).format(parseFloat(dto.total_amount))`).
    -   Tworzyć `displayId` (np. `Zam. #${dto.id.substring(0, 8).toUpperCase()}`).
    -   Mapować status na polską nazwę i klasę CSS używając `orderStatusMap`.
7.  **Stylizacja:**
    -   Użyć klas Bootstrap 5 dla responsywności i wyglądu (np. `table`, `table-hover`, `list-group`, `container`).
    -   Dostosować `StatusBadge` zgodnie z `orderStatusMap`.
8.  **Testowanie:**
    -   Sprawdzić poprawne ładowanie i wyświetlanie listy zamówień.
    -   Przetestować paginację (zmiana stron, działanie przycisków).
    -   Sprawdzić wyświetlanie komunikatów o ładowaniu, błędach i braku zamówień.
    -   Zweryfikować poprawność linków do szczegółów zamówienia.
    -   Przetestować responsywność widoku.
    -   Sprawdzić ochronę trasy (dostęp tylko dla zalogowanych Kupujących). 