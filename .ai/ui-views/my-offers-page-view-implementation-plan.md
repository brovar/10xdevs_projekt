# Plan implementacji widoku "Moje Oferty"

## 1. Przegląd
Widok "Moje Oferty" (`/seller/offers`) umożliwia zalogowanym użytkownikom z rolą Sprzedawcy przeglądanie, filtrowanie, sortowanie i zarządzanie własnymi ofertami. Wyświetla listę ofert wraz z kluczowymi informacjami i opcjami edycji, zmiany statusu oraz usuwania/archiwizacji. Widok wykorzystuje paginację do obsługi dużej liczby ofert.

## 2. Routing widoku
- **Ścieżka**: `/seller/offers`
- **Framework**: React Router (zgodnie z `frontend-react-react_router` wytycznymi, np. używając `createBrowserRouter`)
- **Ochrona**: Trasa powinna być chroniona i dostępna tylko dla użytkowników z rolą `UserRole.SELLER`. W przypadku braku autoryzacji lub nieodpowiedniej roli, użytkownik powinien zostać przekierowany (np. na stronę logowania lub stronę główną z komunikatem).

## 3. Struktura komponentów
```
MyOffersPage (Container)
├── OfferFilterControls
│   ├── SearchInput (dla `search`)
│   ├── CategorySelect (dla `category_id`)
│   ├── StatusSelect (dla `status`)
│   └── SortSelect (dla `sort`)
├── OfferList
│   └── OfferListItem (mapowany dla każdej oferty)
│       ├── OfferThumbnailImage
│       ├── OfferDetailsSection (tytuł, cena, ilość, status)
│       └── OfferActionsSection (przyciski: Edytuj, Zmień Status, Usuń)
├── PaginationControls
└── ChangeStatusModal (Modal do zmiany statusu oferty)
└── ConfirmDeleteModal (Modal do potwierdzenia usunięcia oferty)
```

## 4. Szczegóły komponentów

### `MyOffersPage`
- **Opis komponentu**: Główny komponent strony, odpowiedzialny za pobieranie danych ofert sprzedawcy, zarządzanie stanem filtrów, sortowania, paginacji oraz wyświetlanie komponentów podrzędnych. Obsługuje również logikę otwierania modali akcji.
- **Główne elementy HTML**: Kontener (np. `div`) dla całej strony, zawierający filtry, listę ofert i paginację.
- **Obsługiwane interakcje**:
    - Zmiana wartości filtrów (wyszukiwanie, kategoria, status).
    - Zmiana kryterium sortowania.
    - Zmiana strony w paginacji.
    - Inicjowanie akcji edycji, zmiany statusu, usunięcia oferty (delegowane do `OfferListItem`).
- **Obsługiwana walidacja**: Sprawdzenie roli użytkownika (Sprzedawca) przed renderowaniem treści.
- **Typy**:
    - Stan: `SellerOfferListQueryParamsViewModel`, `OfferListResponse | null`, `boolean` (isLoading), `ErrorResponse | string | null` (error), `CategoryDTO[]` (dla filtra kategorii).
    - Propsy: Brak (komponent trasowany).
- **Propsy**: Brak (jest to komponent strony/trasy).

### `OfferFilterControls`
- **Opis komponentu**: Odpowiada za renderowanie kontrolek filtrowania (pole wyszukiwania, dropdowny dla kategorii, statusu i sortowania).
- **Główne elementy HTML**: Formularz lub `div` grupujący kontrolki: `input[type="search"]`, `select` dla kategorii, `select` dla statusu, `select` dla sortowania. Użycie komponentów Bootstrap 5 (np. `Form.Control`, `Form.Select`).
- **Obsługiwane interakcje**:
    - Wprowadzanie tekstu w polu wyszukiwania.
    - Wybór opcji z dropdownów kategorii, statusu, sortowania.
- **Obsługiwana walidacja**: Brak bezpośredniej walidacji, przekazuje zmiany do rodzica.
- **Typy**:
    - Propsy: `currentFilters: SellerOfferListQueryParamsViewModel`, `categories: CategoryDTO[]`, `availableStatuses: OfferStatus[]`, `availableSortOptions: { value: string, label: string }[]`, `onFiltersChange: (newFilters: Partial<SellerOfferListQueryParamsViewModel>) => void`.
- **Propsy**:
    - `currentFilters: SellerOfferListQueryParamsViewModel`
    - `categories: CategoryDTO[]`
    - `availableStatuses: OfferStatus[]`
    - `availableSortOptions: { value: string, label: string }[]`
    - `onFiltersChange: (newFilters: Partial<SellerOfferListQueryParamsViewModel>) => void` (callback do aktualizacji filtrów w `MyOffersPage`, może przyjmować pojedynczą zmianę lub cały obiekt)

### `OfferList`
- **Opis komponentu**: Renderuje listę ofert (`OfferListItem`) lub komunikat o braku ofert.
- **Główne elementy HTML**: `div` lub `ul` jako kontener listy. Warunkowe renderowanie komunikatu (np. "Nie masz jeszcze żadnych ofert." lub "Brak ofert spełniających kryteria.").
- **Obsługiwane interakcje**: Brak.
- **Obsługiwana walidacja**: Brak.
- **Typy**:
    - Propsy: `offers: OfferSummaryDTO[]`, `onEditOffer: (offerId: string) => void`, `onOpenChangeStatusModal: (offer: OfferSummaryDTO) => void`, `onOpenDeleteModal: (offerId: string) => void`.
- **Propsy**:
    - `offers: OfferSummaryDTO[]`
    - `onEditOffer: (offerId: string) => void`
    - `onOpenChangeStatusModal: (offer: OfferSummaryDTO) => void`
    - `onOpenDeleteModal: (offerId: string) => void`

### `OfferListItem`
- **Opis komponentu**: Reprezentuje pojedynczą pozycję na liście ofert. Wyświetla kluczowe informacje o ofercie oraz przyciski akcji.
- **Główne elementy HTML**: Element listy (np. `li` lub `div` w stylu karty Bootstrap). Zawiera:
    - `OfferThumbnailImage`: `img` dla miniaturki.
    - `OfferDetailsSection`: `div` z tytułem (`h5`/`h6`), ceną (`p`), ilością (`p`), statusem (`span` z odpowiednią klasą Bootstrap np. `Badge`).
    - `OfferActionsSection`: `div` z przyciskami Bootstrap (`Button`) dla "Edytuj", "Zmień status", "Usuń".
- **Obsługiwane interakcje**: Kliknięcie przycisków akcji.
- **Obsługiwana walidacja**: Przyciski akcji mogą być włączone/wyłączone w zależności od statusu oferty (np. nie można edytować oferty sprzedanej - `OfferStatus.SOLD`).
- **Typy**:
    - Propsy: `offer: OfferSummaryDTO`, `onEdit: (offerId: string) => void`, `onChangeStatusRequest: (offer: OfferSummaryDTO) => void`, `onDeleteRequest: (offerId: string) => void`.
- **Propsy**:
    - `offer: OfferSummaryDTO`
    - `onEdit: (offerId: string) => void`
    - `onChangeStatusRequest: (offer: OfferSummaryDTO) => void`
    - `onDeleteRequest: (offerId: string) => void`

### `OfferThumbnailImage`
- **Opis komponentu**: Wyświetla miniaturkę zdjęcia oferty lub placeholder.
- **Główne elementy HTML**: `img` tag.
- **Obsługiwane interakcje**: Brak.
- **Obsługiwana walidacja**: Brak.
- **Typy**:
    - Propsy: `imageFilename: string | null | undefined`, `offerId: string`, `title: string`.
- **Propsy**:
    - `imageFilename: string | null | undefined`
    - `offerId: string` (do konstrukcji URL, jeśli potrzebne)
    - `title: string` (dla `alt` textu obrazka)

### `PaginationControls`
- **Opis komponentu**: Renderuje kontrolki paginacji.
- **Główne elementy HTML**: Komponent paginacji Bootstrap 5 (`Pagination`).
- **Obsługiwane interakcje**: Kliknięcie na numery stron, przyciski "następna"/"poprzednia".
- **Obsługiwana walidacja**: Przyciski "poprzednia"/"następna" są wyłączone na pierwszej/ostatniej stronie.
- **Typy**:
    - Propsy: `currentPage: number`, `totalPages: number`, `onPageChange: (page: number) => void`.
- **Propsy**:
    - `currentPage: number`
    - `totalPages: number`
    - `onPageChange: (page: number) => void`

### `ChangeStatusModal`
- **Opis komponentu**: Modal pozwalający sprzedawcy wybrać nowy status dla oferty.
- **Główne elementy HTML**: Komponent `Modal` z Bootstrap. Zawiera `Form.Select` do wyboru nowego statusu.
- **Obsługiwane interakcje**: Wybór statusu, potwierdzenie, anulowanie.
- **Obsługiwana walidacja**: Upewnienie się, że wybrano poprawny nowy status.
- **Typy**:
    - Propsy: `show: boolean`, `offerToUpdate: OfferSummaryDTO | null`, `availableTargetStatuses: OfferStatus[]`, `onConfirm: (newStatus: OfferStatus) => void`, `onHide: () => void`.
- **Propsy**:
    - `show: boolean`
    - `offerToUpdate: OfferSummaryDTO | null`
    - `availableTargetStatuses: OfferStatus[]` (statusy, na które można zmienić z obecnego)
    - `onConfirm: (newStatus: OfferStatus) => void`
    - `onHide: () => void`

### `ConfirmDeleteModal`
- **Opis komponentu**: Modal do potwierdzenia akcji usunięcia/archiwizacji oferty.
- **Główne elementy HTML**: Komponent `Modal` z Bootstrap. Zawiera tekst potwierdzenia i przyciski "Potwierdź", "Anuluj".
- **Obsługiwane interakcje**: Potwierdzenie, anulowanie.
- **Obsługiwana walidacja**: Brak.
- **Typy**:
    - Propsy: `show: boolean`, `offerIdToDelete: string | null`, `onConfirm: () => void`, `onHide: () => void`.
- **Propsy**:
    - `show: boolean`
    - `offerIdToDelete: string | null`
    - `onConfirm: () => void`
    - `onHide: () => void`

## 5. Typy

### DTO (bezpośrednio z `src/schemas.py` lub definicji API)
-   `OfferSummaryDTO`:
    -   `id`: `string` (UUID)
    -   `seller_id`: `string` (UUID)
    -   `category_id`: `number`
    -   `title`: `string`
    -   `price`: `string` (Decimal, np. "49.99")
    -   `image_filename`: `string | null`
    -   `quantity`: `number`
    -   `status`: `OfferStatus` (enum: `'active'`, `'inactive'`, `'sold'`, `'moderated'`, `'archived'`)
    -   `created_at`: `string` (ISO datetime)
-   `OfferListResponse`:
    -   `items`: `OfferSummaryDTO[]`
    -   `total`: `number`
    -   `page`: `number`
    -   `limit`: `number`
    -   `pages`: `number`
-   `CategoryDTO`:
    -   `id`: `number`
    -   `name`: `string`
-   `ErrorResponse`:
    -   `error_code`: `string`
    -   `message`: `string`
-   `OfferStatus` (Enum string): `'active'`, `'inactive'`, `'sold'`, `'moderated'`, `'archived'` (zgodnie z endpointem).

### ViewModels / Interfejsy Prospów (Frontend)
-   `SellerOfferListQueryParamsViewModel`:
    -   `search?`: `string`
    -   `category_id?`: `number`
    -   `status?`: `OfferStatus`
    -   `sort?`: `string` (np. `'price_asc'`, `'price_desc'`, `'created_at_desc'`)
    -   `page?`: `number`
    -   `limit?`: `number`
-   `SortOption`:
    -   `value`: `string`
    -   `label`: `string`

## 6. Zarządzanie stanem

- **Główny stan (`MyOffersPage`):**
    - `offersData: OfferListResponse | null` - przechowuje odpowiedź API.
    - `isLoading: boolean` - status ładowania danych.
    - `error: ErrorResponse | string | null` - błędy API.
    - `filters: SellerOfferListQueryParamsViewModel` - aktualne filtry, sortowanie i strona. Inicjalizowane z `{ page: 1, limit: 100, sort: 'created_at_desc' }`.
    - `categories: CategoryDTO[]` - lista kategorii dla filtra.
    - `showChangeStatusModal: boolean`, `offerToChangeStatus: OfferSummaryDTO | null`
    - `showDeleteModal: boolean`, `offerIdToDelete: string | null`

- **Custom Hook (`useSellerOffers` - sugerowany):**
    - Cel: Hermetyzacja logiki pobierania ofert, zarządzania stanem ładowania/błędu, aktualizacji filtrów.
    - Wewnętrzny stan: `offersData`, `isLoading`, `error`, `currentFilters`.
    - Funkcje zwracane: `offersData`, `isLoading`, `error`, `updateFilters(newFilters: Partial<SellerOfferListQueryParamsViewModel>)`, `setPage(page: number)`.
    - `useEffect` wewnątrz hooka do pobierania danych przy zmianie `currentFilters`.
    - Może również zawierać logikę pobierania kategorii (`useCategories` jako osobny hook lub część tego).

- **React Router Loaders (zgodnie z wytycznymi `frontend-react-react_router`):**
    - Rozważyć użycie funkcji `loader` dla trasy `/seller/offers`.
    - Loader parsuje `URLSearchParams` z obiektu `Request`, wywołuje API `GET /seller/offers`.
    - Zwraca `OfferListResponse` lub `Response` z błędem.
    - Komponent `MyOffersPage` używa `useLoaderData()` do pobrania danych.
    - Filtrowanie/sortowanie/paginacja po stronie klienta po załadowaniu danych lub ponowne ładowanie trasy z nowymi parametrami (`navigate` lub `fetcher.submit` z React Router). Preferowane jest ponowne ładowanie z nowymi parametrami URL, aby loader mógł obsłużyć pobieranie danych.

## 7. Integracja API

- **Endpoint**: `GET /seller/offers`
- **Metoda**: `GET`
- **Parametry zapytania (Query Parameters)**: Przekazywane z obiektu `filters` (`SellerOfferListQueryParamsViewModel`).
    - `search` (string, opcjonalny)
    - `category_id` (integer, opcjonalny)
    - `status` (string, opcjonalny - wartości z `OfferStatus`)
    - `sort` (string, opcjonalny - np. `price_asc`, `created_at_desc`)
    - `page` (integer, opcjonalny, default 1)
    - `limit` (integer, opcjonalny, default 100, max 100)
- **Ciało zapytania (Request Body)**: Brak.
- **Odpowiedź sukcesu (Success Response - 200 OK)**: `OfferListResponse`
- **Obsługa błędów**: Na podstawie kodów `400`, `401`, `403`, `500` i `ErrorResponse`.

- **Pobieranie kategorii**:
    - Endpoint: `GET /categories` (zakładany, na podstawie PRD).
    - Odpowiedź: `CategoriesListResponse` (z `items: CategoryDTO[]`).

- **Zmiana statusu oferty (zakładany endpoint):**
    - Endpoint: `PATCH /seller/offers/{offerId}/status` (przykład)
    - Metoda: `PATCH`
    - Ciało zapytania: `{ "new_status": "active" }`
    - Odpowiedź: Zaktualizowany `OfferSummaryDTO` lub komunikat sukcesu.

- **Usuwanie/Archiwizacja oferty (zakładany endpoint):**
    - Endpoint: `DELETE /seller/offers/{offerId}` (przykład)
    - Metoda: `DELETE`
    - Odpowiedź: Komunikat sukcesu lub `204 No Content`.

## 8. Interakcje użytkownika

- **Ładowanie strony**:
    - Automatyczne pobranie pierwszej strony ofert (z domyślnymi filtrami/sortowaniem) oraz listy kategorii.
- **Filtrowanie/Wyszukiwanie**:
    - Wpisanie tekstu w `SearchInput` (z debouncing) -> aktualizacja parametru `search` -> ponowne pobranie danych (reset do strony 1).
    - Wybór z `CategorySelect`, `StatusSelect` -> aktualizacja `category_id`/`status` -> ponowne pobranie danych (reset do strony 1).
- **Sortowanie**:
    - Wybór z `SortSelect` -> aktualizacja `sort` -> ponowne pobranie danych (reset do strony 1).
- **Paginacja**:
    - Kliknięcie numeru strony w `PaginationControls` -> aktualizacja `page` -> ponowne pobranie danych dla nowej strony.
- **Akcje na ofercie**:
    - Kliknięcie "Edytuj" -> nawigacja do strony edycji oferty (np. `/seller/offers/:offerId/edit`).
    - Kliknięcie "Zmień status":
        - Otwiera `ChangeStatusModal` z aktualną ofertą.
        - Użytkownik wybiera nowy status.
        - Potwierdzenie -> wywołanie API zmiany statusu -> odświeżenie listy / aktualizacja oferty w stanie.
    - Kliknięcie "Usuń":
        - Otwiera `ConfirmDeleteModal`.
        - Potwierdzenie -> wywołanie API usunięcia -> odświeżenie listy.

## 9. Warunki i walidacja

- **Dostęp do strony**: Tylko dla użytkowników z rolą `SELLER`.
- **Parametry `page` i `limit`**: `page >= 1`, `0 < limit <= 100`. Walidacja głównie po stronie backendu, ale frontend może zapobiegać wysyłaniu niepoprawnych wartości.
- **Filtry `status`, `category_id`, `sort`**: Wartości muszą pochodzić z predefiniowanych, dozwolonych list. Dropdowny zapewniają to naturalnie.
- **Przyciski akcji w `OfferListItem`**:
    - "Edytuj": Wyłączony dla ofert ze statusem `sold` lub `archived`.
    - "Zmień status": Logika dostępnych przejść statusów (np. nie można zmienić `sold` na `active`). `ChangeStatusModal` powinien oferować tylko dozwolone nowe statusy.
    - "Usuń": Dostępny dla większości statusów, z wyjątkiem np. już `archived` w pewnych kontekstach.

## 10. Obsługa błędów

- **Błędy API (`400`, `401`, `403`, `500`)**:
    - `401 Unauthorized`: Globalny handler powinien przekierować na stronę logowania.
    - `403 Forbidden`: Jeśli rola nie jest `SELLER` (powinno być obsłużone przez ochronę trasy), wyświetlić komunikat o braku dostępu lub przekierować.
    - `400 Bad Request`, `500 Internal Server Error`: Wyświetlić komunikat błędu (np. z `ErrorResponse.message` lub generyczny) w `MyOffersPage`.
- **Brak ofert**: `OfferList` wyświetla stosowny komunikat (np. "Nie masz jeszcze żadnych ofert" lub "Brak ofert pasujących do filtrów").
- **Błąd ładowania kategorii**: Filtr kategorii może być wyłączony lub wyświetlić błąd, ale reszta strony powinna działać.
- **Błąd ładowania obrazka oferty**: `OfferThumbnailImage` wyświetla placeholder.
- **Błędy operacji (zmiana statusu, usunięcie)**: Wyświetlić powiadomienie (np. toast) o błędzie.

## 11. Kroki implementacji

1.  **Konfiguracja trasy**: Dodać trasę `/seller/offers` w `createBrowserRouter`, chronioną dla roli `SELLER`. Rozważyć implementację funkcji `loader` dla tej trasy do początkowego pobrania danych.
2.  **Stworzenie komponentu `MyOffersPage`**:
    -   Implementacja logiki pobierania danych (z `useLoaderData()` jeśli używany loader, lub przez `useEffect` i `fetch`).
    -   Zarządzanie stanami `isLoading`, `error`, `filters`, `offersData`, `categories`.
    -   Pobranie listy kategorii dla filtrów.
3.  **Stworzenie komponentu `OfferFilterControls`**:
    -   Dodanie inputów i selectów (Bootstrap) dla `search`, `category_id`, `status`, `sort`.
    -   Implementacja `onFiltersChange` do komunikacji z `MyOffersPage`. Dodanie debouncingu dla pola `search`.
4.  **Stworzenie komponentu `OfferList` i `OfferListItem`**:
    -   `OfferList`: Iteracja po `offersData.items` i renderowanie `OfferListItem`. Obsługa pustego stanu.
    -   `OfferListItem`: Wyświetlanie danych oferty (`OfferThumbnailImage`, szczegóły, status). Dodanie przycisków akcji (na razie jako placeholdery lub z nawigacją do edycji).
5.  **Stworzenie komponentu `OfferThumbnailImage`**: Logika wyświetlania obrazka lub placeholdera. URL obrazka: `/app/media/offers/<offer_id>/<image_filename>` (lub przez dedykowany endpoint backendowy, np. `/media/offers/...`).
6.  **Stworzenie komponentu `PaginationControls`**: Implementacja logiki paginacji i callbacku `onPageChange`.
7.  **Implementacja akcji "Zmień Status"**:
    -   Stworzenie komponentu `ChangeStatusModal`.
    -   W `MyOffersPage` dodanie stanu do zarządzania widocznością modala i wybraną ofertą.
    -   Implementacja logiki API (PATCH) do zmiany statusu. Aktualizacja listy po sukcesie.
8.  **Implementacja akcji "Usuń/Archiwizuj"**:
    -   Stworzenie komponentu `ConfirmDeleteModal`.
    -   W `MyOffersPage` dodanie stanu do zarządzania widocznością modala i ID oferty.
    -   Implementacja logiki API (DELETE) do usunięcia/archiwizacji. Aktualizacja listy po sukcesie.
9.  **Styling**: Dopasowanie wyglądu komponentów przy użyciu Bootstrap 5 i ewentualnych własnych stylów.
10. **Obsługa błędów**: Implementacja wyświetlania komunikatów o błędach API i przypadków brzegowych.
11. **Testowanie**: Przetestowanie wszystkich interakcji, filtrów, paginacji, obsługi błędów.
12. **Refaktoryzacja i optymalizacja**: Przejrzenie kodu, ewentualne wydzielenie logiki do custom hooks (np. `useSellerOffers`). Zastosowanie `React.memo` gdzie to zasadne.
