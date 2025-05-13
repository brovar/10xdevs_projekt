# Plan implementacji widoków Panelu Administratora

## 1. Przegląd
Panel Administratora to zestaw widoków przeznaczonych wyłącznie dla użytkowników z rolą "Admin". Umożliwia zarządzanie użytkownikami (listowanie, blokowanie/odblokowywanie, przeglądanie szczegółów), ofertami (listowanie wszystkich, moderowanie/odmoderowywanie), zamówieniami (listowanie wszystkich, przeglądanie szczegółów, anulowanie) oraz przeglądanie logów systemowych. Główne widoki to `AdminDashboardPage` (z zakładkami), `AdminUserDetailPage` oraz `AdminOrderDetailPage`.

## 2. Routing widoku
Aplikacja React będzie wykorzystywać `react-router-dom` z `createBrowserRouter`.

-   **Panel Administratora (Dashboard):**
    -   Ścieżka: `/admin`
    -   Komponent: `AdminDashboardPage`
    -   Nawigacja w zakładkach będzie zarządzana przez parametr URL query, np. `/admin?tab=users`, `/admin?tab=offers`, `/admin?tab=orders`, `/admin?tab=logs`. Domyślną zakładką może być "Users".
-   **Szczegóły Użytkownika (Admin):**
    -   Ścieżka: `/admin/users/:userId`
    -   Komponent: `AdminUserDetailPage`
-   **Szczegóły Zamówienia (Admin):**
    -   Ścieżka: `/admin/orders/:orderId`
    -   Komponent: `AdminOrderDetailPage`

Wszystkie powyższe ścieżki powinny być chronione przez komponent `ProtectedRoute`, który sprawdza, czy zalogowany użytkownik ma rolę `Admin`.

## 3. Struktura komponentów

```
<App>
  <Router>
    <Routes>
      {/* ... inne trasy ... */}
      <Route path="/admin" element={<ProtectedRoute role="Admin />}>
        <Route index element={<AdminDashboardPage />} /> {/* Obsługuje /admin i /admin?tab=... */}
        <Route path="users/:userId" element={<AdminUserDetailPage />} />
        <Route path="orders/:orderId" element={<AdminOrderDetailPage />} />
      </Route>
      {/* ... inne trasy ... */}
    </Routes>
  </Router>
</App>

AdminDashboardPage (/admin?tab=...)
├── TabsComponent (np. z Bootstrap `Nav` i `TabContent`)
│   ├── UsersManagementTab (wyświetlana gdy tab=users)
│   │   ├── UserFiltersComponent (opcjonalne filtry wyszukiwania, roli, statusu)
│   │   ├── UserListTable
│   │   │   └── UserActions (przyciski Akcji dla każdego wiersza)
│   │   │       └── StatusBadge
│   │   ├── PaginationComponent
│   │   └── ConfirmationModal (dla blokowania/odblokowywania)
│   ├── OffersManagementTab (wyświetlana gdy tab=offers)
│   │   ├── OfferFiltersComponent (opcjonalne filtry wyszukiwania, kategorii, sprzedawcy, statusu)
│   │   ├── AdminOfferListTable
│   │   │   └── OfferModerationActions (przyciski Akcji dla każdego wiersza)
│   │   │       └── StatusBadge
│   │   ├── PaginationComponent
│   │   └── ConfirmationModal (dla moderowania/odmoderowywania)
│   ├── OrdersManagementTab (wyświetlana gdy tab=orders)
│   │   ├── OrderFiltersComponent (opcjonalne filtry statusu, kupującego, sprzedawcy)
│   │   ├── AdminOrderListTable
│   │   │   └── OrderCancelAction (przycisk Akcji dla każdego wiersza)
│   │   │       └── StatusBadge
│   │   ├── PaginationComponent
│   │   └── ConfirmationModal (dla anulowania zamówienia)
│   └── LogsViewerTab (wyświetlana gdy tab=logs)
│       ├── LogFiltersComponent (filtry daty, IP, typu zdarzenia)
│       ├── LogsTable
│       └── PaginationComponent

AdminUserDetailPage (/admin/users/:userId)
└── UserDetailsPanel
    └── UserInfoItem (komponent powtarzalny dla każdego pola danych)

AdminOrderDetailPage (/admin/orders/:orderId)
└── OrderDetailsPanel
    ├── ItemsListInOrder
    ├── StatusBadge (dla statusu zamówienia)
    ├── CancelOrderButtonComponent (przycisk anulowania zamówienia)
    └── ConfirmationModal (dla anulowania zamówienia)
```

## 4. Szczegóły komponentów

### `AdminDashboardPage`
-   **Opis komponentu:** Główny kontener dla panelu admina, wyświetla zakładki i zarządza przełączaniem między nimi na podstawie parametru `tab` w URL.
-   **Główne elementy HTML i komponenty dzieci:** `TabsComponent`, oraz dynamicznie renderowany komponent zakładki (`UsersManagementTab`, `OffersManagementTab`, `OrdersManagementTab`, `LogsViewerTab`).
-   **Obsługiwane interakcje:** Wybór zakładki (aktualizuje parametr `tab` w URL).
-   **Obsługiwana walidacja:** N/A (ochrona trasy realizowana wyżej).
-   **Typy:** `URLSearchParams` do odczytu `tab`.
-   **Propsy:** Brak.

### `TabsComponent`
-   **Opis komponentu:** Komponent nawigacyjny wyświetlający dostępne zakładki (Użytkownicy, Oferty, Zamówienia, Logi).
-   **Główne elementy HTML i komponenty dzieci:** Elementy `Nav` i `NavItem` z Bootstrapa lub odpowiedniki.
-   **Obsługiwane interakcje:** Kliknięcie na zakładkę.
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** `activeTabKey: string`, `onSelectTab: (tabKey: string) => void`.
-   **Propsy:** `tabs: { key: string, title: string }[]`, `activeTabKey: string`, `onTabSelect: (tabKey: string) => void`.

### `UsersManagementTab`
-   **Opis komponentu:** Zarządza wyświetlaniem listy użytkowników, filtrowaniem, paginacją oraz akcjami blokowania/odblokowywania.
-   **Główne elementy HTML i komponenty dzieci:** `UserFiltersComponent` (opcjonalnie), `UserListTable`, `PaginationComponent`, `ConfirmationModal`.
-   **Obsługiwane interakcje:** Zmiana filtrów, zmiana strony paginacji, kliknięcie "Blokuj"/"Odblokuj", kliknięcie "Pokaż szczegóły".
-   **Obsługiwana walidacja:** Potwierdzenie akcji blokowania/odblokowania.
-   **Typy:** `UserDTO`, `UserListResponse`, `UserListQueryParams`.
-   **Propsy:** Brak (zarządza własnym stanem za pomocą hooka).

### `UserListTable`
-   **Opis komponentu:** Tabela wyświetlająca listę użytkowników.
-   **Główne elementy HTML i komponenty dzieci:** `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`. Dla każdego użytkownika `UserActions` i `StatusBadge`. Link do `AdminUserDetailPage`.
-   **Obsługiwane interakcje:** Kliknięcie na akcje (propagowane do rodzica).
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** `UserDTO[]`.
-   **Propsy:** `users: UserDTO[]`, `onBlock: (userId: UUID) => void`, `onUnblock: (userId: UUID) => void`, `onViewDetails: (userId: UUID) => void`.

### `UserActions`
-   **Opis komponentu:** Przyciski akcji dla użytkownika w tabeli ("Blokuj", "Odblokuj", "Szczegóły").
-   **Główne elementy HTML i komponenty dzieci:** `<button>`.
-   **Obsługiwane interakcje:** Kliknięcie przycisku.
-   **Obsługiwana walidacja:** Przycisk "Blokuj" aktywny jeśli status to `Active`. Przycisk "Odblokuj" aktywny jeśli status to `Inactive`.
-   **Typy:** `UserDTO`.
-   **Propsy:** `user: UserDTO`, `onBlock: () => void`, `onUnblock: () => void`, `onViewDetails: () => void`.

### `OffersManagementTab`
-   **Opis komponentu:** Zarządza wyświetlaniem listy ofert, filtrowaniem, paginacją oraz akcjami moderowania/odmoderowywania.
-   **Główne elementy HTML i komponenty dzieci:** `OfferFiltersComponent` (opcjonalnie), `AdminOfferListTable`, `PaginationComponent`, `ConfirmationModal`.
-   **Obsługiwane interakcje:** Zmiana filtrów, zmiana strony paginacji, kliknięcie "Moderuj"/"Odmoderuj".
-   **Obsługiwana walidacja:** Potwierdzenie akcji moderowania/odmoderowywania.
-   **Typy:** `OfferSummaryDTO`, `OfferListResponse`, `AdminOfferListQueryParams`.
-   **Propsy:** Brak.

### `AdminOfferListTable`
-   **Opis komponentu:** Tabela wyświetlająca listę ofert.
-   **Główne elementy HTML i komponenty dzieci:** `<table>`. Dla każdej oferty `OfferModerationActions` i `StatusBadge`.
-   **Obsługiwane interakcje:** Kliknięcie na akcje (propagowane do rodzica).
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** `OfferSummaryDTO[]`.
-   **Propsy:** `offers: OfferSummaryDTO[]`, `onModerate: (offerId: UUID) => void`, `onUnmoderate: (offerId: UUID) => void`.

### `OfferModerationActions`
-   **Opis komponentu:** Przyciski akcji dla oferty ("Moderuj", "Odmoderuj").
-   **Główne elementy HTML i komponenty dzieci:** `<button>`.
-   **Obsługiwane interakcje:** Kliknięcie przycisku.
-   **Obsługiwana walidacja:** Przycisk "Moderuj" aktywny jeśli status nie jest `moderated`. Przycisk "Odmoderuj" aktywny jeśli status to `moderated`.
-   **Typy:** `OfferSummaryDTO`.
-   **Propsy:** `offer: OfferSummaryDTO`, `onModerate: () => void`, `onUnmoderate: () => void`.

### `OrdersManagementTab`
-   **Opis komponentu:** Zarządza wyświetlaniem listy zamówień, filtrowaniem, paginacją oraz akcją anulowania zamówień.
-   **Główne elementy HTML i komponenty dzieci:** `OrderFiltersComponent` (opcjonalnie), `AdminOrderListTable`, `PaginationComponent`, `ConfirmationModal`.
-   **Obsługiwane interakcje:** Zmiana filtrów, zmiana strony paginacji, kliknięcie "Anuluj zamówienie", kliknięcie "Pokaż szczegóły".
-   **Obsługiwana walidacja:** Potwierdzenie anulowania zamówienia.
-   **Typy:** `OrderSummaryDTO`, `OrderListResponse`, `AdminOrderListQueryParams`.
-   **Propsy:** Brak.

### `AdminOrderListTable`
-   **Opis komponentu:** Tabela wyświetlająca listę zamówień.
-   **Główne elementy HTML i komponenty dzieci:** `<table>`. Dla każdego zamówienia `OrderCancelAction` i `StatusBadge`. Link do `AdminOrderDetailPage`.
-   **Obsługiwane interakcje:** Kliknięcie na akcje (propagowane do rodzica).
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** `OrderSummaryDTO[]`.
-   **Propsy:** `orders: OrderSummaryDTO[]`, `onCancel: (orderId: UUID) => void`, `onViewDetails: (orderId: UUID) => void`.

### `OrderCancelAction`
-   **Opis komponentu:** Przycisk akcji dla zamówienia ("Anuluj zamówienie").
-   **Główne elementy HTML i komponenty dzieci:** `<button>`.
-   **Obsługiwane interakcje:** Kliknięcie przycisku.
-   **Obsługiwana walidacja:** Przycisk aktywny, jeśli status zamówienia pozwala na anulowanie (np. `pending_payment`, `processing`, `shipped`).
-   **Typy:** `OrderSummaryDTO`.
-   **Propsy:** `order: OrderSummaryDTO`, `onCancel: () => void`.

### `LogsViewerTab`
-   **Opis komponentu:** Zarządza wyświetlaniem logów systemowych, filtrowaniem i paginacją.
-   **Główne elementy HTML i komponenty dzieci:** `LogFiltersComponent`, `LogsTable`, `PaginationComponent`.
-   **Obsługiwane interakcje:** Zmiana filtrów, zmiana strony paginacji.
-   **Obsługiwana walidacja:** Poprawność zakresu dat w filtrach.
-   **Typy:** `LogDTO`, `LogListResponse`, `AdminLogListQueryParams`.
-   **Propsy:** Brak.

### `LogFiltersComponent`
-   **Opis komponentu:** Formularz z polami do filtrowania logów (zakres dat, adres IP, typ zdarzenia).
-   **Główne elementy HTML i komponenty dzieci:** Pola `<input type="datetime-local">`, `<input type="text">`, `<select>`.
-   **Obsługiwane interakcje:** Wprowadzanie wartości, wybór opcji, zatwierdzenie filtrów.
-   **Obsługiwana walidacja:** `end_date` musi być późniejszy lub równy `start_date`. Adres IP może być walidowany pod kątem formatu.
-   **Typy:** `AdminLogListQueryParams`.
-   **Propsy:** `currentFilters: Partial<AdminLogListQueryParams>`, `onFilterChange: (filters: Partial<AdminLogListQueryParams>) => void`.

### `LogsTable`
-   **Opis komponentu:** Tabela wyświetlająca logi. Kolumny: Data/godzina, Typ zdarzenia, IP klienta, Komunikat.
-   **Główne elementy HTML i komponenty dzieci:** `<table>`.
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** `LogDTO[]`.
-   **Propsy:** `logs: LogDTO[]`.

### `PaginationComponent`
-   **Opis komponentu:** Generyczny komponent do obsługi paginacji.
-   **Główne elementy HTML i komponenty dzieci:** Przyciski "Poprzednia", "Następna", numery stron.
-   **Obsługiwane interakcje:** Kliknięcie na numer strony lub przyciski nawigacyjne.
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** `PaginationInfo { currentPage: number, totalPages: number, limit: number, totalItems: number }`.
-   **Propsy:** `paginationInfo: PaginationInfo`, `onPageChange: (page: number) => void`.

### `ConfirmationModal`
-   **Opis komponentu:** Generyczny modal do potwierdzania akcji.
-   **Główne elementy HTML i komponenty dzieci:** Bootstrap Modal lub odpowiednik, tekst pytania, przyciski "Potwierdź", "Anuluj".
-   **Obsługiwane interakcje:** Kliknięcie "Potwierdź" lub "Anuluj".
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** Brak.
-   **Propsy:** `isOpen: boolean`, `title: string`, `message: string`, `onConfirm: () => void`, `onCancel: () => void`, `confirmButtonText?: string`, `cancelButtonText?: string`.

### `StatusBadge`
-   **Opis komponentu:** Wyświetla status (np. użytkownika, oferty, zamówienia) z odpowiednim stylem (np. kolor tła).
-   **Główne elementy HTML i komponenty dzieci:** Bootstrap `Badge` lub `<span>` ze stylami.
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** `statusValue: UserStatus | OfferStatus | OrderStatus | string`.
-   **Propsy:** `status: statusValue`.

### `AdminUserDetailPage`
-   **Opis komponentu:** Wyświetla szczegółowe informacje o konkretnym użytkowniku.
-   **Główne elementy HTML i komponenty dzieci:** `UserDetailsPanel`.
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** `userId` z URL.
-   **Typy:** `UserDTO`.
-   **Propsy:** Brak (pobiera `userId` z `useParams`).

### `UserDetailsPanel`
-   **Opis komponentu:** Panel wyświetlający dane użytkownika.
-   **Główne elementy HTML i komponenty dzieci:** Seria komponentów `UserInfoItem` dla każdego pola (ID, email, rola, status, imię, nazwisko, data utworzenia, data ostatniej modyfikacji).
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** `UserDTO`.
-   **Propsy:** `user: UserDTO`.

### `UserInfoItem`
-   **Opis komponentu:** Wyświetla pojedynczą informację (etykieta + wartość).
-   **Główne elementy HTML i komponenty dzieci:** `<div>` lub `<p>` z etykietą i wartością.
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** Brak.
-   **Propsy:** `label: string`, `value: string | number | Date`.

### `AdminOrderDetailPage`
-   **Opis komponentu:** Wyświetla szczegółowe informacje o konkretnym zamówieniu i umożliwia jego anulowanie.
-   **Główne elementy HTML i komponenty dzieci:** `OrderDetailsPanel`, `CancelOrderButtonComponent` (jeśli dotyczy), `ConfirmationModal`.
-   **Obsługiwane interakcje:** Kliknięcie "Anuluj zamówienie".
-   **Obsługiwana walidacja:** `orderId` z URL, potwierdzenie anulowania.
-   **Typy:** `OrderDetailDTO`.
-   **Propsy:** Brak (pobiera `orderId` z `useParams`).

### `OrderDetailsPanel`
-   **Opis komponentu:** Panel wyświetlający dane zamówienia, w tym listę produktów.
-   **Główne elementy HTML i komponenty dzieci:** Informacje o zamówieniu (ID, data, status), dane kupującego, `ItemsListInOrder`, łączna kwota. `StatusBadge` dla statusu.
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** `OrderDetailDTO`.
-   **Propsy:** `order: OrderDetailDTO`.

### `ItemsListInOrder`
-   **Opis komponentu:** Lista produktów w zamówieniu.
-   **Główne elementy HTML i komponenty dzieci:** `<ul>` lub tabela z produktami (tytuł, ilość, cena jednostkowa, cena całkowita pozycji).
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** N/A.
-   **Typy:** `OrderItemDTO[]`.
-   **Propsy:** `items: OrderItemDTO[]`.

### `CancelOrderButtonComponent`
-   **Opis komponentu:** Przycisk do anulowania zamówienia.
-   **Główne elementy HTML i komponenty dzieci:** `<button>`.
-   **Obsługiwane interakcje:** Kliknięcie przycisku.
-   **Obsługiwana walidacja:** Przycisk aktywny, jeśli status zamówienia pozwala na anulowanie.
-   **Typy:** `OrderDetailDTO`.
-   **Propsy:** `order: OrderDetailDTO`, `onCancel: () => void`.

## 5. Typy
Większość typów DTO będzie bezpośrednio mapowana z `schemas.py`. Dodatkowo:

-   `TabDefinition`:
    ```typescript
    interface TabDefinition {
      key: string; // np. 'users', 'offers'
      title: string; // Tytuł zakładki
      component: React.FC; // Komponent do wyrenderowania
    }
    ```
-   `PaginationData`:
    ```typescript
    interface PaginationData {
      currentPage: number;
      totalPages: number;
      totalItems: number;
      limit: number;
    }
    ```
-   Typy dla stanów filtrów w każdej zakładce, np.:
    `UserFiltersState` (odpowiadający polom z `UserListQueryParams` używanym na froncie).
    `OfferFiltersState` (odpowiadający polom z `AdminOfferListQueryParams`).
    `OrderFiltersState` (odpowiadający polom z `AdminOrderListQueryParams`).
    `LogFiltersState` (odpowiadający polom z `AdminLogListQueryParams`).

## 6. Zarządzanie stanem
Każda główna zakładka w `AdminDashboardPage` (`UsersManagementTab`, `OffersManagementTab`, etc.) oraz strony szczegółów (`AdminUserDetailPage`, `AdminOrderDetailPage`) będą zarządzać swoim stanem lokalnie, prawdopodobnie przy użyciu niestandardowych hooków.

-   **`useAdminData<DataType, QueryParamsType, ResponseType extends PaginatedResponse>`:**
    -   Cel: Generyczny hook do pobierania paginowanych danych dla list (użytkownicy, oferty, zamówienia, logi).
    -   Stan wewnętrzny: `data: DataType[]`, `paginationData: PaginationData | null`, `filters: QueryParamsType`, `isLoading: boolean`, `error: Error | null`.
    -   Funkcje: `fetchData(newFilters?: Partial<QueryParamsType>, page?: number)`, `setFilters`, `setPage`.
    -   Użycie: `const { data, paginationData, isLoading, error, fetchData, setFilters, setPage } = useAdminData(apiFunction, initialFilters);`

-   **`useAdminEntity<EntityType, EntityIdType>` (dla stron szczegółów):**
    -   Cel: Pobieranie i zarządzanie stanem pojedynczej encji (użytkownik, zamówienie).
    -   Stan wewnętrzny: `entity: EntityType | null`, `isLoading: boolean`, `error: Error | null`.
    -   Funkcje: `fetchEntity(id: EntityIdType)`.
    -   Użycie: `const { entity, isLoading, error } = useAdminEntity(apiFunctionForEntity, entityIdFromParams);`

-   **Stan dla modali potwierdzających:**
    -   Lokalny stan w komponencie zakładki/strony, np. `const [showConfirmModal, setShowConfirmModal] = useState(false);`
    -   `const [actionToConfirm, setActionToConfirm] = useState<{ type: string, id: UUID } | null>(null);`

-   **Nawigacja zakładkami:**
    -   `useSearchParams` z `react-router-dom` do odczytu i ustawiania parametru `?tab=`.

## 7. Integracja API
Integracja z API będzie realizowana za pomocą `fetch` API lub biblioteki typu `axios`.

-   **Użytkownicy:**
    -   `GET /admin/users`: Pobranie listy użytkowników.
        -   Request Query Params: `UserListQueryParams`.
        -   Response: `UserListResponse`.
    -   `GET /admin/users/{userId}`: Pobranie szczegółów użytkownika.
        -   Response: `UserDTO`.
    -   `POST /admin/users/{userId}/block`: Blokowanie użytkownika.
        -   Response: `UserDTO`. (Wymaga obsługi CSRF, jeśli backend tego wymaga - `admin_router.py` wskazuje na to)
    -   `POST /admin/users/{userId}/unblock`: Odblokowywanie użytkownika.
        -   Response: `UserDTO`. (Wymaga obsługi CSRF)
-   **Oferty:**
    -   `GET /admin/offers`: Pobranie listy ofert.
        -   Request Query Params: `AdminOfferListQueryParams`.
        -   Response: `OfferListResponse`.
    -   `POST /admin/offers/{offerId}/moderate`: Moderowanie oferty.
        -   Response: `OfferDetailDTO`.
    -   `POST /admin/offers/{offerId}/unmoderate`: Odmoderowywanie oferty.
        -   Response: `OfferDetailDTO`.
-   **Zamówienia:**
    -   `GET /admin/orders`: Pobranie listy zamówień.
        -   Request Query Params: `AdminOrderListQueryParams`.
        -   Response: `OrderListResponse`.
    -   `GET /admin/orders/{orderId}`: Pobranie szczegółów zamówienia.
        -   Response: `OrderDetailDTO`.
    -   `POST /admin/orders/{orderId}/cancel`: Anulowanie zamówienia.
        -   Response: `OrderDetailDTO`.
-   **Logi:**
    -   `GET /admin/logs`: Pobranie listy logów.
        -   Request Query Params: `AdminLogListQueryParams`.
        -   Response: `LogListResponse`.

Wszystkie żądania modyfikujące dane (POST) powinny być odpowiednio zabezpieczone (np. CSRF, jeśli skonfigurowano) i obsługiwać mechanizm potwierdzenia przez użytkownika.

## 8. Interakcje użytkownika
-   **Wybór zakładki:** Zmienia aktywną zakładkę i aktualizuje URL (`?tab=...`).
-   **Filtrowanie list:** Wprowadzenie wartości w polach filtrów i zatwierdzenie powoduje ponowne pobranie danych z API z nowymi parametrami.
-   **Paginacja:** Kliknięcie na numer strony lub przyciski nawigacyjne paginacji powoduje pobranie odpowiedniej strony danych z API.
-   **Akcje na elementach listy (Blokuj/Odblokuj/Moderuj/Odmoderuj/Anuluj):**
    1.  Kliknięcie przycisku akcji.
    2.  Wyświetlenie `ConfirmationModal` z pytaniem o potwierdzenie.
    3.  Jeśli użytkownik potwierdzi:
        a.  Wysłanie żądania API.
        b.  Po sukcesie: odświeżenie listy danych lub aktualizacja konkretnego elementu na liście, wyświetlenie komunikatu o sukcesie (np. toast).
        c.  Po błędzie: wyświetlenie komunikatu o błędzie.
    4.  Jeśli użytkownik anuluje: zamknięcie modala.
-   **Przejście do szczegółów (użytkownika/zamówienia):** Kliknięcie na odpowiedni link/przycisk w tabeli nawiguje do strony szczegółów (`/admin/users/:userId` lub `/admin/orders/:orderId`).

## 9. Warunki i walidacja
-   **Dostęp do panelu:** Tylko dla użytkowników z rolą `Admin` (realizowane przez `ProtectedRoute`).
-   **Przyciski akcji:**
    -   "Blokuj użytkownika": Aktywny, gdy użytkownik ma status `Active`.
    -   "Odblokuj użytkownika": Aktywny, gdy użytkownik ma status `Inactive`.
    -   "Moderuj ofertę": Aktywny, gdy oferta nie ma statusu `moderated`.
    -   "Odmoderuj ofertę": Aktywny, gdy oferta ma status `moderated`.
    -   "Anuluj zamówienie": Aktywny, gdy status zamówienia na to pozwala (np. `pending_payment`, `processing`, `shipped` - zgodnie z logiką backendu).
-   **Filtry logów:**
    -   Data końcowa nie może być wcześniejsza niż data początkowa.
-   **Paginacja:**
    -   Numery stron muszą być w zakresie od 1 do `totalPages`.
-   **CSRF Token:** Dla operacji `POST /admin/users/{user_id}/block` i `POST /admin/users/{user_id}/unblock` frontend musi zapewnić poprawne przesłanie tokenu CSRF, jeśli jest to wymagane przez konfigurację `fastapi-csrf-protect` na backendzie.

## 10. Obsługa błędów
-   **Błędy API (4xx, 5xx):**
    -   `401 Unauthorized`: Przekierowanie na stronę logowania.
    -   `403 Forbidden`: Wyświetlenie komunikatu "Brak uprawnień" lub przekierowanie. Jeśli błąd CSRF, komunikat "Wystąpił błąd, spróbuj ponownie".
    -   `404 Not Found`: Na stronach szczegółów wyświetlenie "Nie znaleziono zasobu". W przypadku akcji na liście, informacja, że element mógł zostać usunięty i odświeżenie listy.
    -   `400 Bad Request`: Wyświetlenie generycznego komunikatu o błędzie, szczegóły logowane do konsoli. Zapobiegać przez walidację frontendu.
    -   `409 Conflict`: Wyświetlenie specyficznego komunikatu z odpowiedzi API (np. "Użytkownik jest już zablokowany"), odświeżenie danych.
    -   `500 Internal Server Error`: Wyświetlenie generycznego komunikatu "Wystąpił nieoczekiwany błąd serwera."
-   **Błędy sieciowe:** Wyświetlenie komunikatu "Błąd sieci. Sprawdź połączenie."
-   **Wyświetlanie błędów:** Użycie komponentu toast dla globalnych powiadomień lub błędów nieblokujących. Błędy związane z formularzami/filtrami wyświetlane blisko odpowiednich pól.
-   **Stany ładowania:** Wyświetlanie wskaźników ładowania (np. spinner) podczas operacji API.

## 11. Kroki implementacji
1.  **Konfiguracja Routingu:**
    -   Stworzenie `ProtectedRoute` sprawdzającego rolę Admina.
    -   Zdefiniowanie tras dla `/admin`, `/admin/users/:userId`, `/admin/orders/:orderId`.
2.  **Implementacja `AdminDashboardPage`:**
    -   Stworzenie komponentu `AdminDashboardPage`.
    -   Implementacja `TabsComponent` i logiki przełączania zakładek na podstawie `?tab=` parametru URL (`useSearchParams`).
3.  **Implementacja komponentów współdzielonych:**
    -   `PaginationComponent`.
    -   `ConfirmationModal`.
    -   `StatusBadge`.
    -   `LoadingSpinner` lub podobny.
    -   `ErrorMessageDisplay`.
4.  **Implementacja zakładki Zarządzanie Użytkownikami (`UsersManagementTab`):**
    -   Stworzenie hooka `useAdminUsers` do pobierania danych, obsługi paginacji i filtrów.
    -   Implementacja `UserListTable` i `UserActions`.
    -   Integracja z API `GET /admin/users`, `POST /admin/users/.../block`, `POST /admin/users/.../unblock` (z obsługą CSRF).
    -   Implementacja filtrowania (jeśli projektowane są `UserFiltersComponent`).
    -   Podłączenie `PaginationComponent` i `ConfirmationModal`.
5.  **Implementacja `AdminUserDetailPage`:**
    -   Stworzenie hooka `useAdminUserDetails`.
    -   Implementacja `UserDetailsPanel` i `UserInfoItem`.
    -   Integracja z API `GET /admin/users/:userId`.
6.  **Implementacja zakładki Zarządzanie Ofertami (`OffersManagementTab`):**
    -   Stworzenie hooka `useAdminOffers`.
    -   Implementacja `AdminOfferListTable` i `OfferModerationActions`.
    -   Integracja z API `GET /admin/offers`, `POST /admin/offers/.../moderate`, `POST /admin/offers/.../unmoderate`.
    -   Implementacja filtrowania (jeśli projektowane są `OfferFiltersComponent`).
    -   Podłączenie `PaginationComponent` i `ConfirmationModal`.
7.  **Implementacja zakładki Zarządzanie Zamówieniami (`OrdersManagementTab`):**
    -   Stworzenie hooka `useAdminOrders`.
    -   Implementacja `AdminOrderListTable` i `OrderCancelAction`.
    -   Integracja z API `GET /admin/orders`, `POST /admin/orders/.../cancel`.
    -   Implementacja filtrowania (jeśli projektowane są `OrderFiltersComponent`).
    -   Podłączenie `PaginationComponent` i `ConfirmationModal`.
8.  **Implementacja `AdminOrderDetailPage`:**
    -   Stworzenie hooka `useAdminOrderDetail`.
    -   Implementacja `OrderDetailsPanel`, `ItemsListInOrder`, `CancelOrderButtonComponent`.
    -   Integracja z API `GET /admin/orders/:orderId` oraz ewentualnie `POST /admin/orders/.../cancel` z tej strony.
9.  **Implementacja zakładki Przeglądarka Logów (`LogsViewerTab`):**
    -   Stworzenie hooka `useAdminLogs`.
    -   Implementacja `LogFiltersComponent` z walidacją dat.
    -   Implementacja `LogsTable`.
    -   Integracja z API `GET /admin/logs`.
    -   Podłączenie `PaginationComponent`.
10. **Stylowanie:** Zastosowanie Bootstrap 5 i niestandardowych stylów dla zapewnienia spójnego i czytelnego interfejsu, zgodnego z WCAG na podstawowym poziomie.
11. **Testowanie:** Manualne testowanie wszystkich funkcjonalności, interakcji, obsługi błędów i przypadków brzegowych.
12. **Refaktoryzacja i optymalizacja:** Przegląd kodu, optymalizacja wydajności (np. `React.memo` dla elementów listy, jeśli potrzebne).

</rewritten_file> 