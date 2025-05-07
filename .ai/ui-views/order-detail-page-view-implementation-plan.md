# Plan implementacji widoku OrderDetailPage (Szczegóły Zamówienia - dla Kupującego)

## 1. Przegląd
Widok "Szczegóły Zamówienia" (`OrderDetailPage`) ma na celu dostarczenie zalogowanemu Kupującemu pełnych informacji o konkretnym, wybranym przez niego zamówieniu. Wyświetla ogólne dane zamówienia, takie jak jego ID, data złożenia, status, oraz szczegółową listę zakupionych produktów wraz z ich ilością, ceną jednostkową w momencie zakupu i sumą dla pozycji. Dodatkowo prezentowana jest łączna kwota zamówienia.

## 2. Routing widoku
-   **Ścieżka:** `/orders/:orderId` (gdzie `:orderId` to UUID zamówienia)
-   **Ochrona:** Wymaga zalogowanego użytkownika z rolą "Kupujący" (Buyer). Użytkownik powinien mieć dostęp tylko do swoich zamówień. Przekierowanie na `/login` w przypadku braku autoryzacji lub na stronę historii zamówień/błędu w przypadku próby dostępu do nie swojego zamówienia.

## 3. Struktura komponentów
```
OrderDetailPage (src/pages/orders/OrderDetailPage.js)
├── OrderDetailsPanel (src/components/orders/OrderDetailsPanel.js)
│   └── StatusBadge (src/components/shared/StatusBadge.js)
└── ItemsListInOrder (src/components/orders/ItemsListInOrder.js)
    └── OrderItemDetailRow (src/components/orders/OrderItemDetailRow.js) // mapowany
```

## 4. Szczegóły komponentów

### `OrderDetailPage`
-   **Opis komponentu:** Główny komponent kontenerowy dla widoku `/orders/:orderId`. Odpowiedzialny za pobranie szczegółów konkretnego zamówienia na podstawie `orderId` z parametrów URL, zarządzanie stanem ładowania i błędów oraz przekazywanie danych do komponentów podrzędnych.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Nagłówek strony (np. `<h1>Szczegóły zamówienia nr {displayOrderId}</h1>`).
    -   Link "Wróć do historii zamówień" (`<Link to="/orders">`).
    -   Komponent `OrderDetailsPanel` do wyświetlania ogólnych informacji o zamówieniu.
    -   Komponent `ItemsListInOrder` do wyświetlania listy produktów w zamówieniu.
    -   Elementy do wyświetlania stanu ładowania (np. `Spinner`) i komunikatów o błędach (np. "Nie udało się załadować szczegółów zamówienia." lub "Zamówienie nie znalezione.").
-   **Obsługiwane interakcje:** Brak bezpośrednich interakcji, pobiera dane na podstawie parametru z URL.
-   **Obsługiwana walidacja:** Sprawdzenie, czy `orderId` jest poprawnym UUID (opcjonalnie po stronie klienta, głównie po stronie serwera).
-   **Typy:** `OrderDetailVM`.
-   **Propsy:** Brak (pobiera `orderId` z `useParams` z React Router).

### `OrderDetailsPanel`
-   **Opis komponentu:** Komponent prezentacyjny wyświetlający ogólne informacje o zamówieniu: ID, data złożenia, status (z użyciem `StatusBadge`) oraz łączną kwotę zamówienia.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Elementy `div` lub `dl` do prezentacji danych (np. "ID Zamówienia:", "Data złożenia:", "Status:", "Łączna kwota:").
    -   Komponent `StatusBadge` do wyświetlenia `order.statusDisplay`.
    -   Stylowanie za pomocą Bootstrap 5 (np. `card`, `card-body`).
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `OrderDetailVM` (część dotycząca ogólnych informacji).
-   **Propsy:**
    -   `order: Pick<OrderDetailVM, 'displayId' | 'createdAt' | 'statusDisplay' | 'statusClassName' | 'totalAmount'> | null` - obiekt zawierający wybrane dane zamówienia.

### `ItemsListInOrder`
-   **Opis komponentu:** Komponent prezentacyjny, który otrzymuje listę pozycji z zamówienia i renderuje `OrderItemDetailRow` dla każdej z nich. Zazwyczaj będzie to tabela.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Struktura `table` (`thead`, `tbody`) z Bootstrap.
    -   Nagłówki tabeli: "Produkt", "Ilość", "Cena jednostkowa", "Suma pozycji".
    -   Mapowanie tablicy `items` na komponenty `OrderItemDetailRow` w `tbody`.
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `OrderItemVM[]`.
-   **Propsy:**
    -   `items: OrderItemVM[]` - tablica obiektów pozycji zamówienia.

### `OrderItemDetailRow`
-   **Opis komponentu:** Komponent prezentacyjny wyświetlający informacje o pojedynczej pozycji (produkcie) w zamówieniu, jako wiersz tabeli.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Element `tr` z komórkami `td`.
    -   Wyświetlane pola: `item.offerTitle`, `item.quantity`, `item.priceAtPurchaseFormatted`, `item.itemSumFormatted`.
    -   Opcjonalnie: link do produktu `item.offerId` (jeśli oferta nadal istnieje i jest dostępna - poza zakresem MVP, ale można przygotować `item.offerLink`).
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `OrderItemVM`.
-   **Propsy:**
    -   `item: OrderItemVM` - obiekt pojedynczej pozycji zamówienia.

### `StatusBadge` (zgodnie z `.ai/ui-plan.md` i poprzednim planem)
-   Propsy: `statusDisplay: string`, `statusClassName: string`.

## 5. Typy

### `OrderItemDTO` (z `schemas.OrderItemDTO`, część odpowiedzi API)
```typescript
interface OrderItemDTO {
  id: number; // order_items.id
  offer_id: string; // UUID
  quantity: number;
  price_at_purchase: string; // np. "50.00"
  offer_title: string;
}
```

### `OrderDetailDTO` (z `schemas.OrderDetailDTO`, odpowiedź API)
```typescript
interface OrderDetailDTO {
  id: string; // UUID zamówienia
  buyer_id: string; // UUID kupującego
  status: 'pending_payment' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'failed';
  created_at: string; // ISO datetime string
  updated_at?: string | null; // ISO datetime string
  items: OrderItemDTO[];
  total_amount: string; // np. "123.45"
}
```

### `OrderItemVM` (ViewModel dla `OrderItemDetailRow`)
```typescript
interface OrderItemVM {
  id: number; // order_items.id
  offerId: string; // UUID oferty
  offerTitle: string;
  quantity: number;
  priceAtPurchase: number; // Jako liczba dla obliczeń
  priceAtPurchaseFormatted: string; // Sformatowana cena jednostkowa z walutą, np. "50,00 USD"
  itemSum: number; // quantity * priceAtPurchase
  itemSumFormatted: string; // Sformatowana suma pozycji z walutą, np. "50,00 USD"
  // offerLink?: string; // Opcjonalny link do oferty
}
```

### `OrderDetailVM` (ViewModel dla `OrderDetailPage`)
```typescript
interface OrderDetailVM {
  id: string; // UUID zamówienia
  displayId: string; // Skrócone ID zamówienia do wyświetlania, np. "Zam. #ABC123EF"
  buyerId: string;
  status: 'pending_payment' | 'processing' | 'shipped' | 'delivered' | 'cancelled' | 'failed';
  statusDisplay: string; // Polska nazwa statusu
  statusClassName: string; // Klasa CSS dla StatusBadge
  createdAt: string; // Sformatowana data złożenia zamówienia, np. "01.01.2023, 15:30"
  updatedAt?: string | null; // Sformatowana data ostatniej aktualizacji
  items: OrderItemVM[];
  totalAmount: string; // Sformatowana łączna kwota zamówienia z walutą, np. "123,45 USD"
}
```
-   Mapowanie `status` na `statusDisplay` i `statusClassName` jak w poprzednim planie (`orderStatusMap`).

## 6. Zarządzanie stanem

Stan będzie zarządzany w komponencie `OrderDetailPage` przy użyciu hooków `useState`, `useEffect` i `useParams`.

-   `order: OrderDetailVM | null`: Przechowuje szczegóły pobranego zamówienia. Inicjalnie `null`.
-   `isLoading: boolean`: Wskazuje, czy trwa pobieranie danych. Domyślnie `true`.
-   `error: string | null`: Przechowuje komunikat błędu API (np. "Zamówienie nie znalezione", "Brak dostępu"). Inicjalnie `null`.
-   `orderId: string | undefined`: Pobierane z `useParams()`.

```javascript
// W OrderDetailPage.js
import { useParams } from 'react-router-dom';

const { orderId } = useParams<{ orderId: string }>();
const [order, setOrder] = useState<OrderDetailVM | null>(null);
const [isLoading, setIsLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
```

Niestandardowy hook `useOrderDetail(orderId: string | undefined)` mógłby enkapsulować logikę pobierania danych i zarządzania stanem `order`, `isLoading`, `error`.

## 7. Integracja API

Komunikacja z API będzie realizowana poprzez dedykowany serwis, np. `src/services/orderService.js`.

### `GET /orders/{order_id}`
-   **Cel:** Pobranie szczegółowych informacji o konkretnym zamówieniu.
-   **Akcja:** Wywoływane przy montowaniu `OrderDetailPage`, jeśli `orderId` jest dostępne.
-   **Parametry Ścieżki:** `order_id` (UUID zamówienia).
-   **Odpowiedź (sukces 200 OK):** `OrderDetailDTO`.
    ```json
    // Przykład
    {
      "id": "uuid-order-id",
      "buyer_id": "uuid-buyer-id",
      "status": "processing",
      "created_at": "2023-01-15T10:00:00Z",
      "updated_at": null,
      "items": [
        { "id": 123, "offer_id": "uuid-offer-1", "quantity": 1, "price_at_purchase": "50.00", "offer_title": "Produkt A" }
      ],
      "total_amount": "50.00"
    }
    ```
    Frontend mapuje `OrderDetailDTO` na `OrderDetailVM`, w tym mapuje każdą pozycję z `items` (tablica `OrderItemDTO`) na `OrderItemVM`.
-   **Błędy:**
    -   `401 Unauthorized (NOT_AUTHENTICATED)`: Obsługa globalna (przekierowanie na `/login`).
    -   `403 Forbidden (ACCESS_DENIED)`: Ustawienie stanu `error` na "Brak uprawnień do wyświetlenia tego zamówienia." i wyświetlenie komunikatu.
    -   `404 Not Found (ORDER_NOT_FOUND)`: Ustawienie stanu `error` na "Zamówienie o podanym ID nie zostało znalezione." i wyświetlenie komunikatu.
    -   `500 Internal Server Error (FETCH_FAILED)`: Ustawienie stanu `error` na "Wystąpił błąd serwera." i wyświetlenie komunikatu.

## 8. Interakcje użytkownika
1.  **Ładowanie strony:**
    -   Użytkownik przechodzi na `/orders/:orderId` (np. z linku w `OrderHistoryPage`).
    -   Komponent pobiera `orderId` z parametrów URL.
    -   Wyświetlany jest wskaźnik ładowania (np. `Spinner`).
    -   Wykonywane jest żądanie `GET /orders/{orderId}`.
    -   Po otrzymaniu danych:
        -   Wskaźnik ładowania znika.
        -   `OrderDetailsPanel` i `ItemsListInOrder` wypełniają się danymi zamówienia.
    -   W przypadku błędu (403, 404, 500), wyświetlany jest odpowiedni komunikat błędu zamiast danych zamówienia.
2.  **Nawigacja powrotna:**
    -   Użytkownik klika link "Wróć do historii zamówień".
    -   Następuje przekierowanie na `/orders` obsługiwane przez React Router.

## 9. Warunki i walidacja
-   Brak walidacji formularzy w tym widoku.
-   Kluczowe jest sprawdzenie, czy zalogowany użytkownik jest właścicielem zamówienia (`buyer_id` z odpowiedzi API powinno zgadzać się z ID zalogowanego użytkownika, jeśli API tego nie weryfikuje w pełni w kontekście roli Buyer - chociaż endpoint wskazuje, że Buyer widzi tylko swoje zamówienia).
-   `orderId` z URL powinno być poprawnym UUID (choć walidacja tego po stronie klienta jest mniej krytyczna niż serwerowa).

## 10. Obsługa błędów
-   **Błąd pobierania danych (`GET /orders/{orderId}`):**
    -   `401 Unauthorized`: Globalny `AuthContext` powinien przekierować na `/login`.
    -   `403 Forbidden (ACCESS_DENIED)`: Wyświetlić komunikat: "Nie masz uprawnień do wyświetlenia tego zamówienia." Użytkownik powinien być przekierowany np. do `/orders`.
    -   `404 Not Found (ORDER_NOT_FOUND)`: Wyświetlić komunikat: "Zamówienie nie zostało znalezione."
    -   `500 Internal Server Error` lub błąd sieciowy: Wyświetlić komunikat: "Wystąpił błąd podczas ładowania szczegółów zamówienia. Spróbuj ponownie później."
-   **Niepoprawny `orderId` w URL (np. nie UUID):**
    -   Jeśli serwis API odrzuci żądanie z powodu niepoprawnego formatu ID (np. błąd 400 lub 404), obsłużyć jak standardowy błąd API.
    -   Można dodać prostą walidację formatu UUID po stronie klienta przed wysłaniem żądania, aby uniknąć niepotrzebnych wywołań API, i od razu wyświetlić błąd "Nieprawidłowy format ID zamówienia".

## 11. Kroki implementacji
1.  **Utworzenie struktury plików:**
    -   `src/pages/orders/OrderDetailPage.js`
    -   `src/components/orders/OrderDetailsPanel.js`
    -   `src/components/orders/ItemsListInOrder.js`
    -   `src/components/orders/OrderItemDetailRow.js`
    -   Rozszerzenie `src/services/orderService.js` o funkcję `fetchOrderDetails(orderId)`.
2.  **Implementacja `orderService.js`:**
    -   Dodać funkcję `fetchOrderDetails(orderId)` wysyłającą żądanie `GET /orders/{orderId}`.
3.  **Implementacja `OrderDetailPage.js`:**
    -   Dodać routing dla `/orders/:orderId` w głównym konfiguratorze routera, zabezpieczając go dla roli "Buyer".
    -   Użyć `useParams` do pobrania `orderId`.
    -   Zaimplementować stany: `order`, `isLoading`, `error`.
    -   W `useEffect` (zależnym od `orderId`):
        -   Jeśli `orderId` istnieje, wywołać `orderService.fetchOrderDetails(orderId)`.
        -   Obsłużyć sukces: zmapować DTO na VM, zaktualizować stan `order`.
        -   Obsłużyć błędy: zaktualizować stan `error`.
        -   Zarządzać stanem `isLoading`.
    -   Renderować `OrderDetailsPanel`, `ItemsListInOrder` lub komunikaty o ładowaniu/błędzie.
    -   Dodać link powrotny do `/orders`.
4.  **Implementacja `OrderDetailsPanel.js`:**
    -   Przyjmować część `order: OrderDetailVM` jako props.
    -   Wyświetlić ogólne informacje o zamówieniu (`displayId`, `createdAt`, `statusDisplay` z `StatusBadge`, `totalAmount`).
5.  **Implementacja `ItemsListInOrder.js`:**
    -   Przyjmować `items: OrderItemVM[]` jako props.
    -   Renderować tabelę (`table` z Bootstrap) z nagłówkami.
    -   Mapować `items` na `OrderItemDetailRow` w `tbody`.
6.  **Implementacja `OrderItemDetailRow.js`:**
    -   Przyjmować `item: OrderItemVM` jako props.
    -   Renderować wiersz tabeli (`tr`) z komórkami (`td`) dla `item.offerTitle`, `item.quantity`, `item.priceAtPurchaseFormatted`, `item.itemSumFormatted`.
7.  **Mapowanie DTO na VM:**
    -   Stworzyć funkcje pomocnicze (np. w `OrderDetailPage.js` lub w serwisie) do mapowania:
        -   `OrderDetailDTO` na `OrderDetailVM`.
        -   `OrderItemDTO` na `OrderItemVM` (wewnątrz mapowania `OrderDetailDTO`).
    -   Funkcje te powinny formatować daty i kwoty, tworzyć `displayId`, mapować statusy (używając `orderStatusMap`), obliczać sumy pozycji.
8.  **Stylizacja:**
    -   Użyć klas Bootstrap 5 dla responsywności i wyglądu (np. `container`, `card`, `table`, `table-hover`).
9.  **Testowanie:**
    -   Sprawdzić poprawne ładowanie i wyświetlanie szczegółów zamówienia dla poprawnego `orderId`.
    -   Przetestować obsługę błędów dla nieistniejącego `orderId` (404), braku uprawnień (403) i błędów serwera (500).
    -   Sprawdzić poprawność wyświetlanych danych (daty, kwoty, statusy, pozycje zamówienia).
    -   Przetestować link powrotny.
    -   Sprawdzić ochronę trasy (dostęp tylko dla zalogowanego Kupującego i tylko do jego zamówień).

</rewritten_file> 