# Plan implementacji widoku SalesHistoryPage (Historia Sprzedaży)

## 1. Przegląd
Widok "Historia Sprzedaży" (`SalesHistoryPage`) jest przeznaczony dla zalogowanych użytkowników z rolą Sprzedającego (Seller). Umożliwia przeglądanie paginowanej listy zamówień, które zawierają produkty wystawione przez danego sprzedawcę. Widok ma na celu prezentację kluczowych informacji o zamówieniach i, zgodnie z wymaganiami, powinien umożliwiać zmianę statusu zamówienia przez sprzedawcę. Plan ten uwzględnia aktualnie dostępny endpoint `GET /account/sales`, który zwraca ograniczone informacje o zamówieniach.

**Ograniczenie:** Dostępny endpoint `GET /account/sales` zwraca jedynie `OrderSummaryDTO`, które nie zawiera informacji o konkretnych produktach w zamówieniu ani o kupującym. W związku z tym, wyświetlenie tych danych (wymaganych przez opis widoku i US-009) oraz sortowanie po nich **nie jest obecnie możliwe** bez modyfikacji backendu. Plan zakłada tymczasowe pominięcie tych informacji w interfejsie. Funkcjonalność zmiany statusu zamówienia również **nie może zostać w pełni zaimplementowana** bez dedykowanego endpointu API.

## 2. Routing widoku
-   **Ścieżka:** `/seller/sales`
-   **Ochrona:** Wymaga zalogowanego użytkownika z rolą "Seller". Przekierowanie na `/login` lub stronę główną w przypadku braku odpowiedniej roli.

## 3. Struktura komponentów
```
SalesHistoryPage (src/pages/sales/SalesHistoryPage.js)
├── SortControls (src/components/sales/SortControls.js) // Ograniczona funkcjonalność
├── SalesList (src/components/sales/SalesList.js)
│   └── SaleItem (src/components/sales/SaleItem.js) // mapowany
│       ├── StatusBadge (src/components/shared/StatusBadge.js)
│       └── OrderStatusDropdown (src/components/sales/OrderStatusDropdown.js) // Warunkowo renderowany, ograniczona funkcjonalność
└── Pagination (src/components/common/Pagination.js)
```

## 4. Szczegóły komponentów

### `SalesHistoryPage`
-   **Opis komponentu:** Główny komponent kontenerowy dla widoku `/seller/sales`. Odpowiedzialny za pobieranie historii sprzedaży, zarządzanie stanem paginacji, sortowania (w ograniczonym zakresie), ładowania i błędów.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Nagłówek strony (np. `<h1>Historia Sprzedaży</h1>`).
    -   Komponent `SortControls` (umożliwiający sortowanie np. po dacie).
    -   Komponent `SalesList`.
    -   Komponent `Pagination`.
    -   Elementy do wyświetlania stanu ładowania (`Spinner`, skeleton list) i komunikatów o błędach lub braku sprzedaży.
-   **Obsługiwane interakcje:** Zmiana strony (`Pagination`), zmiana sortowania (`SortControls`).
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `SaleItemVM[]`, `PaginationVM`, `SortOptionVM[]`.
-   **Propsy:** Brak.

### `SortControls`
-   **Opis komponentu:** Umożliwia wybór kryterium sortowania. Ze względu na ograniczenia API, dostępne opcje będą ograniczone (np. tylko po dacie).
-   **Główne elementy HTML i komponenty dzieci:**
    -   Etykieta "Sortuj według:".
    -   `SelectInput` (lub przyciski) do wyboru opcji sortowania (np. "Data (Najnowsze)", "Data (Najstarsze)").
-   **Obsługiwane interakcje:** Wybór opcji sortowania.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `SortOptionVM[]`.
-   **Propsy:**
    -   `options: SortOptionVM[]`
    -   `currentSort: string`
    -   `onSortChange: (sortValue: string) => void`

### `SalesList`
-   **Opis komponentu:** Komponent prezentacyjny renderujący listę lub tabelę sprzedanych zamówień.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Struktura `table` (`thead`, `tbody`) z Bootstrap.
    -   Nagłówki kolumn: "ID Zamówienia", "Data", "Status", "Kwota", "Zmień status" (lub "Akcje"). **Uwaga:** Brak kolumn "Produkt" i "Kupujący".
    -   Mapowanie tablicy `sales` na komponenty `SaleItem`.
    -   Komunikat "Brak historii sprzedaży.", jeśli lista jest pusta.
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `SaleItemVM[]`.
-   **Propsy:**
    -   `sales: SaleItemVM[]`
    -   `isLoading: boolean`
    -   `onStatusChange: (orderId: string, newStatus: OrderStatus) => Promise<void>` // Przekazana z SalesHistoryPage

### `SaleItem`
-   **Opis komponentu:** Reprezentuje pojedynczy wiersz w tabeli historii sprzedaży.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Element `tr` z komórkami `td`.
    -   Wyświetlane pola: `sale.displayId`, `sale.createdAt`, `sale.totalAmount`.
    -   Komponent `StatusBadge` dla `sale.statusDisplay`.
    -   Komponent `OrderStatusDropdown` (renderowany warunkowo).
-   **Obsługiwane interakcje:** Wybór nowego statusu w `OrderStatusDropdown`.
-   **Obsługiwana walidacja:** Logika w `OrderStatusDropdown` sprawdza dozwolone zmiany statusu.
-   **Typy:** `SaleItemVM`.
-   **Propsy:**
    -   `sale: SaleItemVM`
    -   `onStatusChange: (orderId: string, newStatus: OrderStatus) => Promise<void>`
    -   `isUpdatingStatus: boolean` // Stan informujący, czy trwa zmiana statusu dla TEGO elementu

### `OrderStatusDropdown`
-   **Opis komponentu:** Dropdown (lub przyciski) umożliwiający Sprzedającemu zmianę statusu zamówienia na dozwolony następny stan.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Komponent `Dropdown` z Bootstrap.
    -   Opcje dropdown renderowane warunkowo: "Oznacz jako wysłane" (jeśli `sale.status === 'processing'`), "Oznacz jako dostarczone" (jeśli `sale.status === 'shipped'`).
-   **Obsługiwane interakcje:** Wybór nowej opcji statusu.
-   **Obsługiwana walidacja:** Upewnia się, że oferuje tylko dozwolone przejścia statusów.
-   **Typy:** `OrderStatus`.
-   **Propsy:**
    -   `orderId: string`
    -   `currentStatus: OrderStatus`
    -   `allowedTransitions: { [key in OrderStatus]?: OrderStatus[] }` // np. { processing: ['shipped'], shipped: ['delivered'] }
    -   `onChange: (orderId: string, newStatus: OrderStatus) => void`
    -   `isLoading: boolean` // Czy trwa zmiana statusu dla tego zamówienia

### `Pagination` i `StatusBadge` (zgodnie z poprzednimi planami)

## 5. Typy

### `OrderSummaryDTO` (z `schemas.OrderSummaryDTO`, odpowiedź API `GET /account/sales`)
```typescript
// Jak w poprzednich planach
interface OrderSummaryDTO {
  id: string; // UUID
  status: 'pending_payment' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'failed';
  total_amount: string;
  created_at: string;
  updated_at?: string | null;
}
```

### `OrderListResponseDTO` (z `schemas.OrderListResponse`, odpowiedź API `GET /account/sales`)
```typescript
// Jak w poprzednich planach
interface OrderListResponseDTO {
  items: OrderSummaryDTO[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
```

### `SaleItemVM` (ViewModel dla `SaleItem`)
```typescript
interface SaleItemVM {
  id: string; // Order UUID
  displayId: string; // Skrócone ID
  status: OrderStatus;
  statusDisplay: string; // Polska nazwa statusu
  statusClassName: string; // Klasa CSS dla StatusBadge
  totalAmount: string; // Sformatowana kwota
  createdAt: string; // Sformatowana data
  // --- Pola logiki zmiany statusu ---
  canChangeStatus: boolean; // Czy status jest taki, że można go zmienić (processing lub shipped)
  nextStatusOptions: { value: OrderStatus; label: string }[]; // Opcje dla dropdown
}
```
-   Mapowanie `status` na `statusDisplay` i `statusClassName` (jak poprzednio, `orderStatusMap`).
-   Logika `canChangeStatus` i `nextStatusOptions`:
    -   Jeśli `status === 'processing'`, `canChangeStatus = true`, `nextStatusOptions = [{ value: 'shipped', label: 'Oznacz jako wysłane' }]`.
    -   Jeśli `status === 'shipped'`, `canChangeStatus = true`, `nextStatusOptions = [{ value: 'delivered', label: 'Oznacz jako dostarczone' }]`.
    -   W przeciwnym razie `canChangeStatus = false`, `nextStatusOptions = []`.

### `PaginationVM` (ViewModel dla `Pagination` - jak w poprzednich planach)

### `SortOptionVM` (ViewModel dla `SortControls`)
```typescript
interface SortOptionVM {
  value: string; // np. 'created_at_desc', 'created_at_asc'
  label: string; // np. 'Data (Najnowsze)'
}
```
**Uwaga:** Opcje sortowania ograniczone do danych dostępnych w `OrderSummaryDTO`, czyli głównie `created_at`. Sortowanie po `total_amount` może wymagać konwersji po stronie klienta lub wsparcia API.

### `UpdateOrderStatusRequestDTO` (Hipotetyczny DTO dla brakującego endpointu)
```typescript
interface UpdateOrderStatusRequestDTO {
  status: 'shipped' | 'delivered';
}
```

## 6. Zarządzanie stanem

Stan zarządzany w `SalesHistoryPage` (`useState`, `useEffect`, `useSearchParams`).

-   `sales: SaleItemVM[]`: Lista zamówień (sprzedaży) do wyświetlenia.
-   `paginationData: PaginationVM | null`: Dane paginacji.
-   `isLoading: boolean`: Stan ładowania listy.
-   `error: string | null`: Komunikat błędu API.
-   `currentSort: string`: Aktualne kryterium sortowania (np. 'created_at_desc', synchronizowane z URL).
-   `updatingStatusMap: { [orderId: string]: boolean }`: Mapa przechowująca stan ładowania dla operacji zmiany statusu poszczególnych zamówień.

```javascript
// W SalesHistoryPage.js
const [searchParams, setSearchParams] = useSearchParams();
const [sales, setSales] = useState<SaleItemVM[]>([]);
const [paginationData, setPaginationData] = useState<PaginationVM | null>(null);
const [isLoading, setIsLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
const [currentSort, setCurrentSort] = useState(searchParams.get('sort') || 'created_at_desc');
const [updatingStatusMap, setUpdatingStatusMap] = useState<{ [orderId: string]: boolean }>({});

// useEffect do pobierania danych w zależności od searchParams (page, sort)

const handleSortChange = (sortValue: string) => {
  setCurrentSort(sortValue);
  const newParams = new URLSearchParams(searchParams);
  newParams.set('sort', sortValue);
  newParams.set('page', '1'); // Reset do strony 1 przy zmianie sortowania
  setSearchParams(newParams);
};

const handleStatusChange = async (orderId: string, newStatus: OrderStatus) => {
  setUpdatingStatusMap(prev => ({ ...prev, [orderId]: true }));
  try {
    // await salesService.updateOrderStatus(orderId, { status: newStatus }); // Wywołanie brakującego API
    // Po sukcesie API:
    // Odśwież listę lub zaktualizuj stan lokalnie
    // Pokaż ToastNotification sukcesu
    console.warn("API do zmiany statusu zamówienia nie jest zdefiniowane."); // Tymczasowe ostrzeżenie
    alert("Funkcjonalność zmiany statusu niezaimplementowana (brak API).");
  } catch (err) {
    // Pokaż ToastNotification błędu
    console.error("Błąd zmiany statusu zamówienia:", err);
  } finally {
    setUpdatingStatusMap(prev => ({ ...prev, [orderId]: false }));
  }
};
```
Custom hook `useSalesHistory` jest dobrym kandydatem.

## 7. Integracja API

Serwis `src/services/salesService.js` (lub rozszerzenie `orderService.js`).

### `GET /account/sales`
-   **Cel:** Pobranie paginowanej listy zamówień sprzedawcy.
-   **Akcja:** Wywoływane przy montowaniu `SalesHistoryPage` i zmianie strony/sortowania.
-   **Parametry Query:** `page`, `limit`, `sort` (ograniczony do np. `created_at_desc`, `created_at_asc`).
-   **Odpowiedź (sukces 200 OK):** `OrderListResponseDTO`. Mapowane na `SaleItemVM[]`.
-   **Błędy:** `401`, `403`, `500`.

### **(Brakujący Endpoint)** `PATCH /orders/{order_id}/status` (lub podobny)
-   **Cel:** Zmiana statusu zamówienia przez sprzedawcę.
-   **Akcja:** Wywoływana przez `handleStatusChange` w `SalesHistoryPage` po interakcji z `OrderStatusDropdown`.
-   **Parametry Ścieżki:** `order_id`.
-   **Request Body:** `UpdateOrderStatusRequestDTO` (hipotetyczny).
-   **Odpowiedź:** Prawdopodobnie zaktualizowany obiekt zamówienia lub status 200 OK.
-   **Błędy:** 401, 403 (np. próba nieprawidłowej zmiany statusu), 404, 500.

## 8. Interakcje użytkownika
1.  **Ładowanie strony:** Pobranie pierwszej strony sprzedaży z domyślnym sortowaniem.
2.  **Sortowanie:** Wybór opcji sortowania -> aktualizacja URL -> pobranie danych z nowym sortowaniem (strona 1).
3.  **Paginacja:** Kliknięcie strony -> aktualizacja URL -> pobranie danych dla nowej strony.
4.  **Zmiana statusu:**
    -   Kliknięcie na `OrderStatusDropdown` (widoczne dla statusów `processing` i `shipped`).
    -   Wybór nowej, dozwolonej opcji (np. "Oznacz jako wysłane").
    -   **(Hipotetycznie)** Wywołanie API zmiany statusu. Wyświetlenie stanu ładowania dla tego wiersza.
    -   Po odpowiedzi API: aktualizacja UI (zmiana statusu w wierszu, deaktywacja dropdowna) lub wyświetlenie błędu (Toast).

## 9. Warunki i walidacja
-   **Dostęp:** Tylko dla roli `Seller`.
-   **Sortowanie:** Ograniczone do pól dostępnych w API (`created_at`).
-   **Zmiana statusu:** `OrderStatusDropdown` powinien oferować tylko dozwolone przejścia (`processing` -> `shipped`, `shipped` -> `delivered`).

## 10. Obsługa błędów
-   **Błędy API (`GET /account/sales`):**
    -   `401`, `403`: Obsługa globalna/przekierowanie.
    -   `500`: Wyświetlenie komunikatu "Nie udało się załadować historii sprzedaży."
-   **Błędy API (zmiana statusu - hipotetyczne):**
    -   Wyświetlenie `ToastNotification` z błędem, np. "Nie udało się zmienić statusu zamówienia."
-   **Brak sprzedaży:** Wyświetlenie komunikatu "Brak historii sprzedaży." zamiast tabeli.

## 11. Kroki implementacji
1.  **Utworzenie struktury plików:**
    -   `src/pages/sales/SalesHistoryPage.js`
    -   `src/components/sales/SortControls.js`
    -   `src/components/sales/SalesList.js`
    -   `src/components/sales/SaleItem.js`
    -   `src/components/sales/OrderStatusDropdown.js`
    -   Rozszerzenie `src/services/salesService.js` (lub `orderService.js`).
2.  **Implementacja `salesService.js`:**
    -   Dodać funkcję `fetchSalesHistory(params: { page, limit, sort })`.
    -   **(Placeholder)** Dodać funkcję `updateOrderStatus(orderId, data)` - **implementacja będzie niepełna bez API.**
3.  **Implementacja `SalesHistoryPage.js`:**
    -   Routing `/seller/sales` (zabezpieczony dla `Seller`).
    -   Stany (`sales`, `paginationData`, `isLoading`, `error`, `currentSort`, `updatingStatusMap`).
    -   Integracja z `useSearchParams`.
    -   `useEffect` do pobierania danych.
    -   Implementacja `handleSortChange`, `handlePageChange`, `handleStatusChange` (z zaznaczeniem braku API dla zmiany statusu).
    -   Renderowanie komponentów podrzędnych.
4.  **Implementacja `SortControls.js`:**
    -   Przyjmowanie `options`, `currentSort`, `onSortChange`.
    -   Renderowanie selecta/przycisków.
5.  **Implementacja `SalesList.js`:**
    -   Przyjmowanie `sales`, `isLoading`, `onStatusChange`.
    -   Renderowanie tabeli z nagłówkami (bez produktu/kupującego).
    -   Mapowanie `sales` na `SaleItem`.
6.  **Implementacja `SaleItem.js`:**
    -   Przyjmowanie `sale`, `onStatusChange`, `isUpdatingStatus`.
    -   Wyświetlanie danych (`displayId`, `createdAt`, `totalAmount`, `StatusBadge`).
    -   Warunkowe renderowanie `OrderStatusDropdown` na podstawie `sale.canChangeStatus`.
7.  **Implementacja `OrderStatusDropdown.js`:**
    -   Przyjmowanie `orderId`, `currentStatus`, `allowedTransitions`, `onChange`, `isLoading`.
    -   Logika renderowania dostępnych opcji na podstawie `currentStatus` i `allowedTransitions`.
    -   Wywołanie `onChange` przy wyborze.
    -   Wyświetlanie stanu ładowania (`isLoading`).
8.  **Implementacja `Pagination.js` i `StatusBadge.js`** (jeśli nie istnieją).
9.  **Mapowanie DTO na VM:**
    -   Funkcja `mapOrderSummaryToSaleItemVM(dto: OrderSummaryDTO): SaleItemVM` (formatowanie daty, kwoty, ID, mapowanie statusu, określanie logiki zmiany statusu).
10. **Stylizacja:** Bootstrap 5.
11. **Testowanie:**
    -   Ładowanie i wyświetlanie listy (z ograniczonymi danymi).
    -   Paginacja.
    -   Sortowanie (po dacie).
    -   Wyświetlanie stanów ładowania/błędów/braku danych.
    -   **(Manualne/Częściowe)** Wyświetlanie `OrderStatusDropdown` dla odpowiednich statusów i jego deaktywacja podczas "zmiany" (brak realnej zmiany bez API).
    -   Ochrona trasy dla roli `Seller`.

</rewritten_file> 