# Plan implementacji widoku HomePage / OfferListPage (Strona Główna / Lista Ofert)

## 1. Przegląd
Widok ten pełni podwójną rolę: strony głównej (`/`) oraz strony listy ofert/wyników wyszukiwania (`/offers`). Jego głównym celem jest umożliwienie użytkownikom przeglądania, wyszukiwania i filtrowania dostępnych ofert produktów. Wyświetla listę ofert w formie siatki lub listy, wraz z paginacją i opcjonalnymi filtrami.

## 2. Routing widoku
-   **Ścieżka dla Strony Głównej:** `/`
-   **Ścieżka dla Listy Ofert:** `/offers`
    -   Obie ścieżki będą renderować ten sam główny komponent, który dostosuje swoje zachowanie na podstawie ścieżki i parametrów query.
-   **Ochrona:** Dostępny dla wszystkich użytkowników (niezalogowanych i zalogowanych). Wymaga uwierzytelnienia do pobrania listy kategorii i pełnej listy ofert (zgodnie z rolą). Dla niezalogowanych może być wyświetlana ograniczona liczba ofert lub zachęta do logowania/rejestracji.

## 3. Struktura komponentów
```
OfferDiscoveryPage (src/pages/offers/OfferDiscoveryPage.js) // Komponent nadrzędny dla / i /offers
├── SearchBar (src/components/offers/SearchBar.js)
├── SearchFilters (src/components/offers/SearchFilters.js) // Opcjonalne, może zawierać filtr kategorii
├── OfferList (src/components/offers/OfferList.js) // Lub OfferGrid
│   └── OfferCard (src/components/offers/OfferCard.js) // mapowany
│       └── Link (React Router, do /offers/:offerId)
└── Pagination (src/components/common/Pagination.js)
```

## 4. Szczegóły komponentów

### `OfferDiscoveryPage`
-   **Opis komponentu:** Główny komponent kontenerowy dla widoków `/` i `/offers`. Odpowiedzialny za:
    -   Pobieranie listy kategorii (dla `SearchFilters`).
    -   Pobieranie listy ofert na podstawie aktualnych parametrów wyszukiwania, filtrowania, sortowania i paginacji.
    -   Zarządzanie stanami wyszukiwania (searchTerm), filtrowania (selectedCategory), sortowania (currentSort), paginacji (currentPage).
    -   Obsługę stanu ładowania i błędów.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Nagłówek strony (np. "Witaj w Steambay!" lub "Wyniki wyszukiwania").
    -   Komponent `SearchBar`.
    -   Komponent `SearchFilters` (zawierający np. dropdown z kategoriami).
    -   Komponent `OfferList` (lub `OfferGrid`).
    -   Komponent `Pagination`.
    -   Elementy do wyświetlania stanu ładowania (np. `Spinner`, skeleton cards) i komunikatów o błędach lub braku wyników.
-   **Obsługiwane interakcje:**
    -   Zmiana wartości w `SearchBar` (aktualizacja `searchTerm`).
    -   Zmiana wybranej kategorii w `SearchFilters` (aktualizacja `selectedCategory`).
    -   Zmiana strony w `Pagination` (aktualizacja `currentPage`).
    -   (Opcjonalnie) Zmiana kryterium sortowania.
-   **Obsługiwana walidacja:** Przekazuje parametry do API zgodnie z ich definicją.
-   **Typy:** `OfferSummaryVM[]`, `CategoryVM[]`, `PaginationVM`, `OfferListQueryParams`.
-   **Propsy:** Brak (zarządza stanem na podstawie parametrów URL i interakcji użytkownika).

### `SearchBar`
-   **Opis komponentu:** Komponent umożliwiający użytkownikowi wprowadzenie frazy wyszukiwania.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Element `<form>` (lub `div`).
    -   `TextInput` dla frazy wyszukiwania.
    -   Przycisk `Button` "Szukaj" lub wyszukiwanie "na żywo" (debounced).
-   **Obsługiwane interakcje:** Wprowadzanie tekstu, kliknięcie przycisku "Szukaj" (lub automatyczne wywołanie po debounce).
-   **Obsługiwana walidacja:** Brak (API obsługuje pusty `search`).
-   **Typy:** Brak specyficznych.
-   **Propsy:**
    -   `initialSearchTerm: string`
    -   `onSearch: (searchTerm: string) => void`
    -   `placeholder?: string` (np. "Wyszukaj produkty...")

### `SearchFilters`
-   **Opis komponentu:** Komponent zawierający opcje filtrowania listy ofert, np. po kategorii.
-   **Główne elementy HTML i komponenty dzieci:**
    -   `SelectInput` (lub podobny) dla wyboru kategorii.
    -   Etykieta "Filtruj według kategorii".
-   **Obsługiwane interakcje:** Wybór kategorii z listy.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `CategoryVM[]`.
-   **Propsy:**
    -   `categories: CategoryVM[]`
    -   `selectedCategoryId: number | null`
    -   `onCategoryChange: (categoryId: number | null) => void`

### `OfferList` (lub `OfferGrid`)
-   **Opis komponentu:** Komponent prezentacyjny wyświetlający listę (lub siatkę) kart ofert.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Kontener `div` z klasami Bootstrap dla siatki (np. `row`, `col-md-4`).
    -   Mapowanie tablicy `offers` na komponenty `OfferCard`.
    -   Komunikat "Brak ofert spełniających kryteria.", jeśli lista jest pusta.
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `OfferSummaryVM[]`.
-   **Propsy:**
    -   `offers: OfferSummaryVM[]`
    -   `isLoading: boolean` (do wyświetlania np. skeletonów dla każdej karty).

### `OfferCard`
-   **Opis komponentu:** Komponent prezentacyjny dla pojedynczej oferty na liście/siatce.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Element `div` z klasą `card` (Bootstrap).
    -   Obrazek oferty (`<img>`), którego źródło to `offer.imageUrl`.
    -   Tytuł oferty (`<h5>` lub `<h4>`).
    -   Cena oferty (`<p>`).
    -   (Opcjonalnie, zgodnie z PRD) Krótki opis, kategoria, nazwa sprzedawcy, ilość.
    -   Komponent `Link` z `react-router-dom` kierujący do `offer.detailsLink` (np. `/offers/${offer.id}`), obejmujący całą kartę lub przycisk "Zobacz".
-   **Obsługiwane interakcje:** Kliknięcie karty/linku prowadzące do szczegółów oferty.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `OfferSummaryVM`.
-   **Propsy:**
    -   `offer: OfferSummaryVM`

### `Pagination` (zgodnie z poprzednimi planami)
-   Propsy: `currentPage: number`, `totalPages: number`, `onPageChange: (page: number) => void`

## 5. Typy

### `OfferSummaryDTO` (z `schemas.OfferSummaryDTO`, odpowiedź API `GET /offers`)
```typescript
interface OfferSummaryDTO {
  id: string; // UUID
  seller_id: string; // UUID
  category_id: number;
  title: string;
  price: string; // np. "99.99"
  image_filename: string | null;
  quantity: number;
  status: 'active' | 'inactive' | 'sold' | 'moderated' | 'archived';
  created_at: string; // ISO datetime string
}
```

### `OfferListResponseDTO` (z `schemas.OfferListResponse`, odpowiedź API `GET /offers`)
```typescript
interface OfferListResponseDTO {
  items: OfferSummaryDTO[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}
```

### `CategoryDTO` (z `schemas.CategoryDTO`, odpowiedź API `GET /categories`)
```typescript
interface CategoryDTO {
  id: number;
  name: string;
}
```

### `CategoriesListResponseDTO` (z `schemas.CategoriesListResponse`, odpowiedź API `GET /categories`)
```typescript
interface CategoriesListResponseDTO {
  items: CategoryDTO[];
}
```

### `OfferSummaryVM` (ViewModel dla `OfferCard`)
```typescript
interface OfferSummaryVM {
  id: string;
  title: string;
  priceFormatted: string; // np. "99,99 USD"
  imageUrl: string | null; // Pełny URL do obrazka, np. /media/offers/{id}/{image_filename} lub placeholder
  // Opcjonalnie, jeśli potrzebne na karcie:
  // categoryName: string;
  // sellerName: string; // Wymagałoby dodatkowych danych lub modyfikacji DTO
  // quantity: number;
  // status: string; // Polska nazwa statusu, jeśli ma być widoczna dla kupującego
  detailsLink: string; // np. /offers/uuid-offer-id
}
```

### `CategoryVM` (ViewModel dla `SearchFilters`)
```typescript
interface CategoryVM {
  id: number;
  name: string;
}
```

### `PaginationVM` (ViewModel dla `Pagination` - jak w poprzednich planach)

### `OfferListQueryParams` (Parametry do API `GET /offers`)
```typescript
interface OfferListQueryParams {
  search?: string;
  category_id?: number;
  // seller_id?: string; // Admin only
  // status?: string; // Admin/Seller only
  sort?: 'price_asc' | 'price_desc' | 'created_at_desc' | 'relevance';
  page?: number;
  limit?: number;
}
```

## 6. Zarządzanie stanem

Stan będzie zarządzany w komponencie `OfferDiscoveryPage` przy użyciu hooków `useState`, `useEffect` oraz `useSearchParams` (z React Router v6+) do synchronizacji stanu filtrów z URL.

-   `offers: OfferSummaryVM[]`: Lista ofert do wyświetlenia.
-   `categories: CategoryVM[]`: Lista dostępnych kategorii.
-   `paginationData: PaginationVM | null`: Dane paginacji.
-   `isLoadingOffers: boolean`: Stan ładowania listy ofert.
-   `isLoadingCategories: boolean`: Stan ładowania listy kategorii.
-   `error: string | null`: Komunikat błędu API.
-   `queryParams: OfferListQueryParams`: Obiekt trzymający aktualne parametry zapytania do API (`search`, `category_id`, `sort`, `page`, `limit`). Stan ten będzie synchronizowany z parametrami URL.

```javascript
// W OfferDiscoveryPage.js
import { useSearchParams } from 'react-router-dom';

const [searchParams, setSearchParams] = useSearchParams();
const [offers, setOffers] = useState<OfferSummaryVM[]>([]);
const [categories, setCategories] = useState<CategoryVM[]>([]);
const [paginationData, setPaginationData] = useState<PaginationVM | null>(null);
const [isLoadingOffers, setIsLoadingOffers] = useState(true);
const [isLoadingCategories, setIsLoadingCategories] = useState(true);
const [error, setError] = useState<string | null>(null);

// Przykładowe odczytanie parametrów z URL przy inicjalizacji
useEffect(() => {
  const initialPage = parseInt(searchParams.get('page') || '1', 10);
  const initialSearch = searchParams.get('search') || '';
  const initialCategory = searchParams.get('category_id');
  // ... logika ustawiania stanów na podstawie URL i pobierania danych
}, [searchParams]);

// Funkcje aktualizujące searchParams (i przez to wywołujące useEffect do ponownego pobrania danych)
const handleSearch = (term: string) => {
  const newParams = new URLSearchParams(searchParams);
  newParams.set('search', term);
  newParams.set('page', '1'); // Reset do pierwszej strony przy nowym wyszukiwaniu
  setSearchParams(newParams);
};
// ... podobne funkcje dla handleCategoryChange, handlePageChange
```
Niestandardowy hook `useOfferDiscovery` mógłby enkapsulować całą logikę pobierania ofert, kategorii, zarządzania parametrami URL i stanami ładowania/błędów.

## 7. Integracja API

Komunikacja z API będzie realizowana przez dedykowane serwisy, np. `src/services/offerService.js` i `src/services/categoryService.js`.

### `GET /offers`
-   **Cel:** Pobranie paginowanej i filtrowanej listy ofert.
-   **Akcja:** Wywoływane przy montowaniu `OfferDiscoveryPage` i przy każdej zmianie parametrów (`search`, `category_id`, `page`, `sort`).
-   **Parametry Query:** Zgodnie z `OfferListQueryParams` (np. `search=laptop&category_id=1&page=2&limit=20&sort=price_asc`).
-   **Odpowiedź (sukces 200 OK):** `OfferListResponseDTO`. Frontend mapuje `items` na `OfferSummaryVM[]` i aktualizuje stany.
-   **Błędy:**
    -   `400 Bad Request (INVALID_QUERY_PARAM)`: Wyświetlenie błędu.
    -   `401 Unauthorized (NOT_AUTHENTICATED)`: Jeśli wymagane, obsługa globalna.
    -   `500 Internal Server Error (FETCH_FAILED)`: Wyświetlenie błędu.

### `GET /categories`
-   **Cel:** Pobranie listy wszystkich kategorii produktów.
-   **Akcja:** Wywoływane raz przy montowaniu `OfferDiscoveryPage`.
-   **Odpowiedź (sukces 200 OK):** `CategoriesListResponseDTO`. Frontend mapuje `items` na `CategoryVM[]`.
-   **Błędy:**
    -   `401 Unauthorized (NOT_AUTHENTICATED)`: Jeśli wymagane, obsługa globalna.
    -   `500 Internal Server Error (FETCH_FAILED)`: Wyświetlenie błędu (może być mniej krytyczne niż błąd ofert).

### `GET /media/offers/{offer_id}/{filename}`
-   **Cel:** Pobranie obrazka dla oferty.
-   **Akcja:** URL do tego endpointu będzie konstruowany w `OfferSummaryVM` jako `imageUrl`. Komponent `<img>` w `OfferCard` będzie go używał jako `src`.
-   **Dostępność:** Publicznie dostępne dla aktywnych ofert.

## 8. Interakcje użytkownika
1.  **Ładowanie strony (Strona Główna `/` lub `/offers`):**
    -   Pobierane są kategorie (`GET /categories`).
    -   Pobierane są oferty (`GET /offers` z domyślnymi/URL parametrami).
    -   Wyświetlane są `SearchBar`, `SearchFilters` (z wypełnionymi kategoriami), lista ofert i paginacja.
2.  **Wyszukiwanie:**
    -   Użytkownik wpisuje frazę w `SearchBar` i klika "Szukaj" (lub po debounce).
    -   `OfferDiscoveryPage` aktualizuje parametr `search` w URL (i stan `queryParams`).
    -   Ponownie pobierane są oferty z nowym `search` i `page=1`. Lista i paginacja się aktualizują.
3.  **Filtrowanie po kategorii:**
    -   Użytkownik wybiera kategorię z `SearchFilters`.
    -   `OfferDiscoveryPage` aktualizuje parametr `category_id` w URL (i stan `queryParams`).
    -   Ponownie pobierane są oferty z nowym `category_id` i `page=1`. Lista i paginacja się aktualizują.
4.  **Zmiana strony paginacji:**
    -   Użytkownik klika numer strony w `Pagination`.
    -   `OfferDiscoveryPage` aktualizuje parametr `page` w URL (i stan `queryParams`).
    -   Ponownie pobierane są oferty z nowym `page`. Lista się aktualizuje.
5.  **Kliknięcie na ofertę:**
    -   Użytkownik klika na `OfferCard`.
    -   Następuje przekierowanie na `/offers/:offerId` (obsługiwane przez `Link` w `OfferCard`).

## 9. Warunki i walidacja
-   **Parametry URL:** `page`, `limit` powinny być liczbami dodatnimi. `category_id` powinno być liczbą. `sort` powinien być jedną z dozwolonych wartości. `OfferDiscoveryPage` powinien obsługiwać parsowanie i domyślne wartości dla tych parametrów z URL.
-   Nie ma walidacji formularzy po stronie klienta w tym widoku, poza ewentualnym ograniczeniem długości `searchTerm`.

## 10. Obsługa błędów
-   **Błąd pobierania ofert (`GET /offers`):**
    -   Wyświetlić komunikat "Nie udało się załadować ofert. Spróbuj ponownie później." w miejscu listy ofert.
    -   Możliwość ponowienia próby (np. przycisk "Odśwież").
-   **Błąd pobierania kategorii (`GET /categories`):**
    -   Filtr kategorii może być nieaktywny lub wyświetlać komunikat "Nie udało się załadować kategorii.". Wyszukiwanie i przeglądanie ofert powinno nadal działać.
-   **Brak wyników:**
    -   Jeśli API zwróci pustą listę `items`, wyświetlić komunikat "Brak ofert spełniających wybrane kryteria."
-   **Błąd ładowania obrazka oferty:** Przeglądarka domyślnie wyświetli ikonę zepsutego obrazka. Można dodać `onError` handler do `<img>` w `OfferCard` aby wyświetlić placeholder.

## 11. Kroki implementacji
1.  **Utworzenie struktury plików:**
    -   `src/pages/offers/OfferDiscoveryPage.js`
    -   `src/components/offers/SearchBar.js`
    -   `src/components/offers/SearchFilters.js`
    -   `src/components/offers/OfferList.js` (lub `OfferGrid.js`)
    -   `src/components/offers/OfferCard.js`
    -   Utworzenie/rozszerzenie `src/services/offerService.js` i `src/services/categoryService.js`.
2.  **Implementacja serwisów API:**
    -   `offerService.fetchOffers(params: OfferListQueryParams)`
    -   `categoryService.fetchCategories()`
3.  **Implementacja `OfferDiscoveryPage.js`:**
    -   Dodać routing dla `/` i `/offers`.
    -   Zarządzanie stanami (`offers`, `categories`, `paginationData`, `isLoading*`, `error`).
    -   Integracja z `useSearchParams` do odczytu i zapisu parametrów filtrów/wyszukiwania/paginacji.
    -   Implementacja logiki pobierania danych w `useEffect` (reagującego na zmiany `searchParams`).
    -   Implementacja funkcji obsługi zdarzeń od komponentów dzieci (`handleSearch`, `handleCategoryChange`, `handlePageChange`).
    -   Renderowanie komponentów podrzędnych i obsługa stanów ładowania/błędów.
4.  **Implementacja `SearchBar.js`:**
    -   Formularz z inputem i przyciskiem. Wywołanie `onSearch` z `OfferDiscoveryPage`.
5.  **Implementacja `SearchFilters.js`:**
    -   Dropdown (select) z kategoriami. Wywołanie `onCategoryChange` z `OfferDiscoveryPage`.
6.  **Implementacja `OfferList.js` (lub `OfferGrid.js`):**
    -   Przyjmowanie `offers: OfferSummaryVM[]` i `isLoading` jako props.
    -   Mapowanie `offers` na `OfferCard`. Wyświetlanie skeletonów/spinnera gdy `isLoading`.
7.  **Implementacja `OfferCard.js`:**
    -   Przyjmowanie `offer: OfferSummaryVM` jako props.
    -   Wyświetlanie danych oferty (`imageUrl`, `title`, `priceFormatted`).
    -   Dodanie `Link` do `offer.detailsLink`.
    -   Obsługa placeholderów dla obrazków.
8.  **Implementacja `Pagination.js`** (jeśli nie istnieje, zgodnie z poprzednimi planami).
9.  **Mapowanie DTO na VM:**
    -   Funkcje pomocnicze do mapowania `OfferSummaryDTO` -> `OfferSummaryVM` (formatowanie ceny, konstruowanie `imageUrl`, `detailsLink`).
    -   Funkcje pomocnicze do mapowania `CategoryDTO` -> `CategoryVM`.
10. **Stylizacja:**
    -   Użycie Bootstrap 5 (np. `Container`, `Row`, `Col`, `Card`, `Form`, `Button`, `Dropdown`).
    -   Zapewnienie responsywności siatki/listy ofert.
11. **Testowanie:**
    -   Ładowanie strony głównej i `/offers`.
    -   Działanie wyszukiwania (z frazą i bez).
    -   Działanie filtrowania po kategorii.
    -   Działanie paginacji.
    -   Poprawność linków do szczegółów oferty.
    -   Wyświetlanie stanów ładowania, błędów, braku wyników.
    -   Synchronizacja stanu z URL.
    -   Dostępność dla różnych ról (jeśli są różnice w danych widocznych dla Kupującego).
