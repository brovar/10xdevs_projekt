# Plan implementacji widoku OfferDetailPage (Szczegóły Oferty)

## 1. Przegląd
Widok "Szczegóły Oferty" (`OfferDetailPage`) służy do prezentacji pełnych informacji o wybranej ofercie. Umożliwia użytkownikom (szczególnie Kupującym) zapoznanie się ze szczegółami produktu, takimi jak opis, cena, zdjęcia, informacje o sprzedawcy i kategorii, a także dodanie produktu do koszyka, jeśli jest on dostępny i użytkownik ma odpowiednie uprawnienia.

## 2. Routing widoku
-   **Ścieżka:** `/offers/:offerId` (gdzie `:offerId` to UUID oferty).
-   **Ochrona:** Wymaga zalogowanego użytkownika. Kupujący widzą tylko oferty aktywne. Sprzedający mogą widzieć swoje oferty (różne statusy), Administratorzy widzą wszystkie. Niezalogowany użytkownik próbujący uzyskać dostęp zostanie przekierowany na stronę logowania. Próba dostępu do oferty niezgodnej z uprawnieniami (np. Kupujący do oferty nieaktywnej) powinna skutkować błędem 403/404 lub przekierowaniem.

## 3. Struktura komponentów
```
OfferDetailPage (src/pages/offers/OfferDetailPage.js)
├── ImageGallery (src/components/offers/ImageGallery.js) // Na razie pojedynczy obrazek
├── OfferInfoPanel (src/components/offers/OfferInfoPanel.js)
│   ├── StatusBadge (src/components/shared/StatusBadge.js)
│   └── SellerInfoBadge (src/components/offers/SellerInfoBadge.js) // Opcjonalny, mały komponent z nazwą sprzedawcy
└── AddToCartButton (src/components/cart/AddToCartButton.js) // Warunkowo renderowany
```

## 4. Szczegóły komponentów

### `OfferDetailPage`
-   **Opis komponentu:** Główny komponent kontenerowy dla widoku `/offers/:offerId`. Odpowiedzialny za pobranie szczegółów oferty na podstawie `offerId` z URL, zarządzanie stanem ładowania, błędów i przekazywanie danych do komponentów podrzędnych.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Kontener `div` (np. z klasami Bootstrap `container`, `row`, `col`).
    -   W lewej kolumnie: `ImageGallery`.
    -   W prawej kolumnie: `OfferInfoPanel` i `AddToCartButton`.
    -   Elementy do wyświetlania stanu ładowania (np. `Spinner`) i komunikatów o błędach (np. "Oferta nie znaleziona.", "Brak dostępu.").
    -   Link "Wróć do listy ofert" (`<Link to="/offers">` lub `/`).
-   **Obsługiwane interakcje:** Brak bezpośrednich, orkiestruje pobieranie danych.
-   **Obsługiwana walidacja:** Sprawdzenie `offerId` (jak w `OrderDetailPage`).
-   **Typy:** `OfferDetailVM`, `UserRole` (z kontekstu autoryzacji).
-   **Propsy:** Brak (pobiera `offerId` z `useParams`).

### `ImageGallery`
-   **Opis komponentu:** Wyświetla główny obraz produktu. W MVP będzie to pojedynczy obrazek. W przyszłości może obsługiwać galerię wielu zdjęć.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Element `<img>` z `src` ustawionym na `offer.imageUrl` i odpowiednim `alt` textem (np. tytuł oferty).
    -   Stylowanie Bootstrap (np. `img-fluid`, `rounded`).
-   **Obsługiwane interakcje:** Brak w MVP.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** Brak specyficznych.
-   **Propsy:**
    -   `imageUrl: string | null`
    -   `altText: string`

### `OfferInfoPanel`
-   **Opis komponentu:** Wyświetla kluczowe informacje tekstowe o ofercie.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Tytuł oferty (`<h1>` lub `<h2>`).
    -   `StatusBadge` pokazujący `offer.statusDisplay`.
    -   Cena (`<p class="h3">{offer.priceFormatted}</p>`).
    -   Pełny opis (`<p>{offer.description}</p>`).
    -   Kategoria (`<p>Kategoria: {offer.categoryName}</p>`).
    -   Informacje o sprzedawcy (`SellerInfoBadge` lub `<p>Sprzedawca: {offer.sellerName}</p>`).
    -   Dostępna ilość (`<p>Dostępna ilość: {offer.quantity}</p>`).
    -   Data utworzenia/modyfikacji (opcjonalnie).
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `OfferDetailVM` (część dotycząca informacji tekstowych).
-   **Propsy:**
    -   `offer: Pick<OfferDetailVM, 'title' | 'statusDisplay' | 'statusClassName' | 'priceFormatted' | 'description' | 'categoryName' | 'sellerName' | 'quantity'> | null`

### `SellerInfoBadge` (Opcjonalny, mały komponent)
-   **Opis komponentu:** Wyświetla nazwę sprzedawcy, potencjalnie jako link do jego profilu/ofert (poza MVP).
-   **Główne elementy HTML i komponenty dzieci:** Prosty `<span>` lub `<p>`.
-   **Propsy:** `sellerName: string`.

### `AddToCartButton`
-   **Opis komponentu:** Przycisk umożliwiający Kupującemu dodanie oferty do koszyka. Wyświetlany warunkowo.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Przycisk `Button` (Bootstrap) z tekstem "Dodaj do koszyka" i ikoną koszyka.
-   **Obsługiwane interakcje:** Kliknięcie przycisku.
-   **Obsługiwana walidacja:** Przycisk jest aktywny/widoczny tylko jeśli `offer.status === 'active'`, `offer.quantity > 0` i użytkownik jest Kupującym.
-   **Typy:** Brak specyficznych.
-   **Propsy:**
    -   `offerId: string`
    -   `offerTitle: string` // Dla potwierdzenia w powiadomieniu
    -   `isDisabled: boolean`
    -   `onClick: (offerId: string, offerTitle: string) => void` // Funkcja z kontekstu koszyka

### `StatusBadge` (zgodnie z poprzednimi planami)
-   Propsy: `statusDisplay: string`, `statusClassName: string`.

## 5. Typy

### `SellerInfoDTO` (z `schemas.SellerInfoDTO`, część odpowiedzi API)
```typescript
interface SellerInfoDTO {
  id: string; // UUID
  first_name?: string | null;
  last_name?: string | null;
}
```

### `CategoryInfoDTO` (z `schemas.CategoryDTO` - nazwa ujednolicona, część odpowiedzi API)
```typescript
interface CategoryInfoDTO { // Zamiast CategoryDTO dla spójności z SellerInfoDTO
  id: number;
  name: string;
}
```

### `OfferDetailResponseDTO` (z `schemas.OfferDetailDTO`, odpowiedź API `GET /offers/{offer_id}`)
```typescript
interface OfferDetailResponseDTO {
  id: string; // UUID
  seller_id: string;
  category_id: number;
  title: string;
  description: string | null;
  price: string; // np. "99.99"
  image_filename: string | null;
  quantity: number;
  status: 'active' | 'inactive' | 'sold' | 'moderated' | 'archived';
  created_at: string; // ISO datetime string
  updated_at?: string | null;
  seller: SellerInfoDTO;
  category: CategoryInfoDTO;
}
```

### `OfferDetailVM` (ViewModel dla `OfferDetailPage`)
```typescript
interface OfferDetailVM {
  id: string;
  title: string;
  description: string;
  price: number; // Jako liczba
  priceFormatted: string; // np. "99,99 USD"
  imageUrl: string | null; // Pełny URL do obrazka
  quantity: number;
  status: 'active' | 'inactive' | 'sold' | 'moderated' | 'archived';
  statusDisplay: string; // Polska nazwa statusu
  statusClassName: string; // Klasa CSS dla StatusBadge
  categoryName: string;
  sellerName: string; // "Imię Nazwisko" lub "Sprzedawca ID"
  sellerId: string;
  // Pola do logiki przycisku "Dodaj do koszyka"
  canBeAddedToCart: boolean; // (status === 'active' && quantity > 0)
}
```
-   Mapowanie `status` na `statusDisplay` i `statusClassName` (jak w poprzednich planach, `offerStatusMap`).
-   `sellerName`: Łączenie `first_name` i `last_name` sprzedawcy. Jeśli brak, użyć np. `Sprzedawca #${seller.id.substring(0,8)}`.

## 6. Zarządzanie stanem

Stan będzie zarządzany w komponencie `OfferDetailPage` (`useState`, `useEffect`, `useParams`).

-   `offer: OfferDetailVM | null`: Szczegóły pobranej oferty. Inicjalnie `null`.
-   `isLoading: boolean`: Stan ładowania. Domyślnie `true`.
-   `error: string | null`: Komunikat błędu API. Inicjalnie `null`.
-   `offerId: string | undefined`: Z `useParams()`.
-   `currentUserRole: UserRole | null`: Z kontekstu autoryzacji (`AuthContext`).

```javascript
// W OfferDetailPage.js
import { useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext'; // Przykład

const { offerId } = useParams<{ offerId: string }>();
const { user } = useAuth(); // Zakładając, że user zawiera user.role
const currentUserRole = user ? user.role : null;

const [offer, setOffer] = useState<OfferDetailVM | null>(null);
const [isLoading, setIsLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
```
Niestandardowy hook `useOfferDetails(offerId: string | undefined)` mógłby zarządzać pobieraniem danych i stanami.

Stan koszyka będzie zarządzany globalnie przez `CartContext`. `AddToCartButton` będzie korzystał z tego kontekstu do wywołania akcji dodania do koszyka.

## 7. Integracja API

Serwis `src/services/offerService.js`.

### `GET /offers/{offer_id}`
-   **Cel:** Pobranie szczegółów oferty.
-   **Akcja:** Wywoływane przy montowaniu `OfferDetailPage`.
-   **Parametry Ścieżki:** `offer_id`.
-   **Odpowiedź (sukces 200 OK):** `OfferDetailResponseDTO`. Mapowane na `OfferDetailVM`.
-   **Błędy:**
    -   `401 Unauthorized (NOT_AUTHENTICATED)`: Globalna obsługa.
    -   `403 Forbidden (ACCESS_DENIED)`: Ustawienie `error` (np. "Nie masz uprawnień do wyświetlenia tej oferty.").
    -   `404 Not Found (OFFER_NOT_FOUND)`: Ustawienie `error` ("Oferta nie znaleziona.").
    -   `500 Internal Server Error (FETCH_FAILED)`: Ustawienie `error` ("Błąd serwera.").

### `GET /media/offers/{offer_id}/{filename}` (pośrednio)
-   URL do tego endpointu jest konstruowany w `OfferDetailVM.imageUrl`.
-   Używany przez `<img>` w `ImageGallery`.

## 8. Interakcje użytkownika
1.  **Ładowanie strony:**
    -   Użytkownik przechodzi na `/offers/:offerId`.
    -   Pobierany jest `offerId` z URL.
    -   Wyświetlany jest `Spinner`.
    -   Wykonywane jest żądanie `GET /offers/{offerId}`.
    -   Po sukcesie: `Spinner` znika, wyświetlane są `ImageGallery`, `OfferInfoPanel` i (jeśli warunki spełnione) `AddToCartButton`.
    -   Po błędzie: Wyświetlany jest odpowiedni komunikat.
2.  **Dodanie do koszyka:**
    -   Użytkownik (Kupujący) klika `AddToCartButton`.
    -   Wywoływana jest funkcja z `CartContext` (`addItemToCart(offerDetailVM)`).
    -   Wyświetlane jest powiadomienie `ToastNotification` ("Dodano {offer.title} do koszyka.").
    -   Przycisk może stać się nieaktywny lub zmienić tekst (np. "W koszyku"), jeśli oferta jest już w koszyku (logika CartContext).

## 9. Warunki i walidacja
-   **Widoczność `AddToCartButton`:**
    -   Użytkownik musi mieć rolę `BUYER`.
    -   `offer.status` musi być `active`.
    -   `offer.quantity` musi być `> 0`.
-   **Dostęp do widoku:**
    -   Jeśli `currentUserRole === BUYER`, API powinno zwrócić 403/404 jeśli oferta nie jest `active`.
    -   Frontend powinien obsłużyć te błędy, wyświetlając stosowny komunikat.

## 10. Obsługa błędów
-   **Błędy API (`GET /offers/{offerId}`):**
    -   `401`: Przekierowanie na `/login` (globalnie).
    -   `403`: Wyświetlenie komunikatu "Nie masz uprawnień do wyświetlenia tej oferty." lub "Ta oferta jest obecnie niedostępna."
    -   `404`: Wyświetlenie komunikatu "Oferta o podanym ID nie została znaleziona."
    -   `500`: Wyświetlenie komunikatu "Wystąpił błąd serwera. Spróbuj ponownie później."
-   **Błąd ładowania obrazka:** Przeglądarka wyświetli standardowy błąd. Można dodać `onError` do `<img>` aby pokazać placeholder.

## 11. Kroki implementacji
1.  **Utworzenie struktury plików:**
    -   `src/pages/offers/OfferDetailPage.js`
    -   `src/components/offers/ImageGallery.js`
    -   `src/components/offers/OfferInfoPanel.js`
    -   `src/components/offers/SellerInfoBadge.js` (opcjonalnie)
    -   `src/components/cart/AddToCartButton.js` (jeśli nie istnieje)
    -   Rozszerzenie `src/services/offerService.js` o funkcję `fetchOfferDetails(offerId)`.
2.  **Implementacja `offerService.js`:**
    -   Dodać `fetchOfferDetails(offerId)`.
3.  **Implementacja `OfferDetailPage.js`:**
    -   Routing dla `/offers/:offerId` (zabezpieczony dla zalogowanych).
    -   `useParams` do pobrania `offerId`.
    -   Pobranie `currentUserRole` z `AuthContext`.
    -   Stany: `offer`, `isLoading`, `error`.
    -   `useEffect` do pobierania danych oferty.
    -   Logika renderowania warunkowego `AddToCartButton` (na podstawie `offer.canBeAddedToCart` i `currentUserRole`).
    -   Renderowanie komponentów podrzędnych i obsługa ładowania/błędów.
4.  **Implementacja `ImageGallery.js`:**
    -   Wyświetlenie pojedynczego obrazka z `imageUrl` i `altText`.
5.  **Implementacja `OfferInfoPanel.js`:**
    -   Wyświetlanie informacji o ofercie, użycie `StatusBadge`.
6.  **Implementacja `AddToCartButton.js`:**
    -   Pobranie funkcji `addItemToCart` z `CartContext`.
    -   Przycisk wywołujący `addItemToCart` z odpowiednimi danymi oferty.
    -   Obsługa stanu `isDisabled`.
7.  **Mapowanie DTO na VM:**
    -   Funkcja pomocnicza do mapowania `OfferDetailResponseDTO` na `OfferDetailVM` (formatowanie ceny, tworzenie `imageUrl`, `sellerName`, `statusDisplay`, `statusClassName`, `canBeAddedToCart`).
8.  **Integracja z `CartContext`:**
    -   Upewnić się, że `CartContext` dostarcza funkcję `addItemToCart` i przechowuje stan koszyka.
9.  **Stylizacja:**
    -   Bootstrap 5: `Container`, `Row`, `Col`, `Card`, `Button`, `Badge`.
    -   Responsywny układ zdjęcia i informacji o produkcie.
10. **Testowanie:**
    -   Poprawne ładowanie i wyświetlanie szczegółów dla aktywnej oferty dla Kupującego.
    -   Działanie przycisku "Dodaj do koszyka" (i jego ukrywanie/deaktywacja).
    -   Obsługa błędów (401, 403, 404, 500).
    -   Poprawne wyświetlanie dla Sprzedawcy (jego własne oferty, różne statusy) i Admina (wszystkie oferty) - jeśli logika dostępu jest już w API.
    -   Wyświetlanie placeholderów dla brakujących obrazków.
``` 