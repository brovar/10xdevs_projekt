# Plan implementacji widoku EditOfferPage

## 1. Przegląd
EditOfferPage to widok umożliwiający Sprzedającym edycję istniejących ofert o statusie 'active' lub 'inactive'. Użytkownik może edytować wszystkie pola oferty, w tym tytuł, opis, cenę, ilość, kategorię oraz zdjęcie. Widok korzysta z endpoint'u PUT `/offers/{offer_id}` z formatem danych `multipart/form-data`.

## 2. Routing widoku
Widok dostępny pod ścieżką: `/offers/:offerId/edit` gdzie `offerId` to identyfikator oferty do edycji (UUID).

## 3. Struktura komponentów
```
EditOfferPage
├── LoadingSpinner (podczas ładowania danych)
├── AlertComponent (w przypadku błędów/sukcesu)
└── OfferForm
    ├── [Pola formularza: tytuł, opis, cena, ilość, kategoria]
    ├── ImageUpload
    │   └── [Podgląd zdjęcia, przycisk usuwania]
    └── [Przyciski: Zapisz, Anuluj]
```

## 4. Szczegóły komponentów
### EditOfferPage
- Opis komponentu: Główny komponent strony, odpowiedzialny za pobieranie danych oferty, weryfikację uprawnień użytkownika oraz renderowanie formularza edycji.
- Główne elementy: Kontener strony, komponent OfferForm, komunikaty błędów/sukcesu, spinner ładowania.
- Obsługiwane interakcje: Inicjalizacja formularza danymi oferty, obsługa sukcesu/błędu po zapisie oferty, nawigacja po anulowaniu/zapisaniu.
- Obsługiwana walidacja: Sprawdzenie czy użytkownik jest zalogowany, czy ma rolę Sprzedającego, czy oferta istnieje, czy należy do użytkownika, czy ma odpowiedni status.
- Typy: OfferDetailDTO, ApiError, UserRole, OfferStatus.
- Propsy: Brak (komponent nadrzędny).

### OfferForm
- Opis komponentu: Formularz do edycji danych oferty, zawierający pola dla wszystkich edytowalnych właściwości oferty.
- Główne elementy: Formularz HTML, pola formularza (tytuł, opis, cena, ilość, kategoria), komponent ImageUpload, przyciski akcji.
- Obsługiwane interakcje: Zmiana wartości pól, przesłanie formularza, anulowanie edycji.
- Obsługiwana walidacja:
  - Tytuł: wymagany, maks. długość (określona przez backend)
  - Opis: opcjonalny, maks. długość
  - Cena: wymagana, wartość większa od 0, format liczby dziesiętnej
  - Ilość: wymagana, wartość całkowita większa lub równa 0
  - Kategoria: wymagana, wybór z dostępnej listy
- Typy: OfferFormDataModel, FormErrors, CategoryDTO.
- Propsy: 
  - initialData: dane początkowe formularza (typ OfferDetailDTO)
  - categories: lista dostępnych kategorii (typ CategoryDTO[])
  - onSubmit: funkcja wywoływana po przesłaniu formularza
  - onCancel: funkcja wywoływana po anulowaniu edycji
  - isSubmitting: flaga wskazująca na trwający proces zapisywania
  - submitError: błąd zwrócony przez API podczas zapisywania

### ImageUpload
- Opis komponentu: Komponent do obsługi uploadu i podglądu zdjęcia oferty.
- Główne elementy: Input typu file, podgląd aktualnego zdjęcia, przycisk usuwania zdjęcia.
- Obsługiwane interakcje: Wybór pliku, usunięcie zdjęcia.
- Obsługiwana walidacja:
  - Format pliku: tylko PNG
  - Rozmiar zdjęcia: maksymalnie 1024x768px
  - Rozmiar pliku: maksymalny rozmiar określony przez backend
- Typy: File, błąd walidacji.
- Propsy:
  - currentImage: URL aktualnego zdjęcia
  - onChange: funkcja wywoływana przy zmianie/usunięciu zdjęcia
  - error: komunikat błędu dotyczący zdjęcia

### AlertComponent
- Opis komponentu: Komponent wyświetlający powiadomienia (sukces/błąd).
- Główne elementy: Alert Bootstrap z odpowiednim stylem i treścią.
- Obsługiwane interakcje: Zamknięcie alertu.
- Typy: Typ alertu (success/error), treść.
- Propsy:
  - type: typ alertu ('success', 'danger', 'warning')
  - message: treść komunikatu
  - onClose: funkcja wywoływana przy zamknięciu alertu

### LoadingSpinner
- Opis komponentu: Komponent wyświetlający informację o ładowaniu.
- Główne elementy: Spinner Bootstrap, komunikat tekstowy.
- Propsy:
  - isVisible: flaga określająca widoczność spinnera
  - message: opcjonalny komunikat tekstowy

## 5. Typy
### Typy DTO z API:
```typescript
// Typy definiowane przez backend (schemas.py)
enum OfferStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  SOLD = "sold",
  MODERATED = "moderated",
  ARCHIVED = "archived",
  DELETED = "deleted"
}

interface CategoryDTO {
  id: number;
  name: string;
}

interface SellerInfoDTO {
  id: string; // UUID
  first_name: string | null;
  last_name: string | null;
}

interface OfferDetailDTO {
  id: string; // UUID
  seller_id: string; // UUID
  category_id: number;
  title: string;
  description: string | null;
  price: string; // Decimal jako string
  image_filename: string | null;
  quantity: number;
  status: OfferStatus;
  created_at: string; // Data ISO
  updated_at: string | null; // Data ISO
  seller: SellerInfoDTO;
  category: CategoryDTO;
}
```

### Typy ViewModel dla komponentów:
```typescript
// Modele wewnętrzne dla komponentów
interface OfferFormDataModel {
  title: string;
  description: string | null;
  price: string; // Reprezentacja ceny jako string dla input
  quantity: number;
  category_id: number;
  image: File | null; // Nowe zdjęcie do przesłania
  currentImage: string | null; // URL do aktualnego zdjęcia
}

interface FormErrors {
  title?: string;
  description?: string;
  price?: string;
  quantity?: string;
  category_id?: string;
  image?: string;
  general?: string;
}

interface ApiError {
  error_code: string;
  message: string;
  details?: any;
}
```

## 6. Zarządzanie stanem
Stan w widoku będzie zarządzany za pomocą hooków React:

### EditOfferPage:
```javascript
// Stan danych oferty
const [offer, setOffer] = useState(null);
const [loading, setLoading] = useState(true);
const [error, setError] = useState(null);

// Stan procesu edycji
const [submitting, setSubmitting] = useState(false);
const [submitError, setSubmitError] = useState(null);
const [submitSuccess, setSubmitSuccess] = useState(false);

// Stan listy kategorii
const [categories, setCategories] = useState([]);
```

### Niestandardowe hooki:
1. `useOfferData(offerId)` - Hook do pobierania danych oferty
   - Odpowiedzialny za pobranie danych oferty z API
   - Zwraca obiekt zawierający dane oferty, stan ładowania i błąd

2. `useCategories()` - Hook do pobierania listy kategorii
   - Odpowiedzialny za pobranie listy kategorii z API
   - Zwraca obiekt zawierający listę kategorii, stan ładowania i błąd

3. `useOfferForm(initialData)` - Hook do zarządzania stanem formularza
   - Inicjalizuje stan formularza danymi początkowymi
   - Udostępnia metody do manipulacji stanem i walidacji

## 7. Integracja API
Integracja z API będzie realizowana poprzez trzy główne wywołania:

1. **Pobieranie danych oferty**:
   - `GET /offers/{offerId}`
   - Wywoływane podczas inicjalizacji komponentu
   - Parametry: offerId (z parametru ścieżki)
   - Odpowiedź: OfferDetailDTO
   - Obsługa błędów: 404 (oferta nie istnieje), 403 (brak uprawnień)

2. **Pobieranie listy kategorii**:
   - `GET /categories`
   - Wywoływane podczas inicjalizacji komponentu
   - Odpowiedź: Lista CategoryDTO
   - Obsługa błędów: ogólne błędy sieci

3. **Aktualizacja oferty**:
   - `PUT /offers/{offerId}`
   - Wywoływane po przesłaniu formularza
   - Parametry: FormData (format multipart/form-data)
   - Pola: title, description, price, quantity, category_id, image (opcjonalne)
   - Odpowiedź: OfferDetailDTO (zaktualizowana oferta)
   - Obsługa błędów: 400 (błędy walidacji), 403 (brak uprawnień), 404 (oferta nie istnieje), 500 (błędy serwera)

## 8. Interakcje użytkownika
1. **Wejście na stronę edycji**:
   - System pobiera dane oferty
   - Jeśli oferta istnieje i użytkownik ma uprawnienia:
     - Formularz zostaje wypełniony danymi oferty
   - W przeciwnym przypadku:
     - Wyświetlany jest komunikat błędu
     - Użytkownik zostaje przekierowany do listy ofert

2. **Edycja pól formularza**:
   - Użytkownik może edytować wszystkie pola oferty
   - Zmiana wartości pola aktualizuje stan formularza
   - Walidacja w czasie rzeczywistym dla wybranych pól

3. **Upload/usunięcie zdjęcia**:
   - Użytkownik może dodać nowe zdjęcie poprzez komponent ImageUpload
   - Po wybraniu pliku wyświetlany jest podgląd
   - Użytkownik może usunąć istniejące zdjęcie przyciskiem "Usuń"

4. **Przesłanie formularza**:
   - Kliknięcie przycisku "Zapisz"
   - System waliduje wszystkie pola formularza
   - Jeśli dane są poprawne:
     - Formularz jest przesyłany do API
     - Wyświetlany jest spinner ładowania
   - Po otrzymaniu odpowiedzi:
     - W przypadku sukcesu:
       - Wyświetlany jest komunikat sukcesu
       - Użytkownik zostaje przekierowany do szczegółów oferty
     - W przypadku błędu:
       - Wyświetlany jest odpowiedni komunikat błędu

5. **Anulowanie edycji**:
   - Kliknięcie przycisku "Anuluj"
   - Użytkownik zostaje przekierowany do szczegółów oferty bez zapisywania zmian

## 9. Warunki i walidacja
### Warunki dostępu do widoku:
- Użytkownik musi być zalogowany
- Użytkownik musi mieć rolę Sprzedającego
- Oferta musi istnieć
- Oferta musi należeć do zalogowanego użytkownika
- Oferta musi mieć status 'active' lub 'inactive'

### Walidacja formularza:
1. **Tytuł**:
   - Pole wymagane
   - Maksymalna długość zgodna z wymaganiami backendu

2. **Opis**:
   - Pole opcjonalne
   - Maksymalna długość zgodna z wymaganiami backendu

3. **Cena**:
   - Pole wymagane
   - Wartość większa od 0
   - Format zgodny z wartością dziesiętną (liczba z opcjonalną częścią ułamkową)

4. **Ilość**:
   - Pole wymagane
   - Wartość całkowita większa lub równa 0

5. **Kategoria**:
   - Pole wymagane
   - Wartość musi być jedną z dostępnych kategorii

6. **Zdjęcie** (jeśli dodawane):
   - Format: PNG
   - Maksymalny rozmiar: 1024x768px
   - Maksymalna wielkość pliku zgodna z wymaganiami backendu

## 10. Obsługa błędów
1. **Błędy pobierania danych**:
   - Oferta nie istnieje (404 OFFER_NOT_FOUND)
     - Wyświetlanie komunikatu "Oferta nie istnieje" i przekierowanie do listy ofert
   - Brak uprawnień (403 INSUFFICIENT_PERMISSIONS/NOT_OFFER_OWNER)
     - Wyświetlanie komunikatu "Brak uprawnień do edycji tej oferty" i przekierowanie

2. **Błędy walidacji formularza**:
   - Wyświetlanie komunikatów przy odpowiednich polach
   - Podświetlanie pól z błędami
   - Wyświetlanie ogólnego komunikatu błędu gdy potrzebne

3. **Błędy API przy zapisie**:
   - Nieprawidłowy status oferty (400 INVALID_STATUS_FOR_EDIT)
     - Wyświetlanie komunikatu "Nie można edytować oferty o statusie X"
   - Nieprawidłowe dane (400 INVALID_INPUT)
     - Wyświetlanie szczegółowych komunikatów dla każdego pola
   - Nieprawidłowy format zdjęcia (400 INVALID_FILE_TYPE)
     - Wyświetlanie komunikatu "Dozwolony tylko format PNG"
   - Zbyt duże zdjęcie (400 FILE_TOO_LARGE)
     - Wyświetlanie komunikatu "Maksymalny rozmiar zdjęcia to 1024x768px"
   - Błąd serwera (500)
     - Wyświetlanie ogólnego komunikatu "Wystąpił błąd podczas zapisywania oferty. Spróbuj ponownie później."

4. **Błędy sieciowe**:
   - Utrata połączenia
     - Wyświetlanie komunikatu "Brak połączenia z serwerem. Sprawdź swoje połączenie internetowe."
   - Timeout
     - Wyświetlanie komunikatu "Przekroczono czas oczekiwania na odpowiedź serwera. Spróbuj ponownie później."

## 11. Kroki implementacji
1. **Utworzenie komponentu EditOfferPage i podstawowego routingu**:
   - Zdefiniowanie ścieżki w systemie routingu
   - Utworzenie podstawowej struktury komponentu z obsługą parametru ścieżki

2. **Implementacja niestandardowych hooków**:
   - useOfferData - pobieranie danych oferty
   - useCategories - pobieranie listy kategorii
   - useOfferForm - zarządzanie stanem formularza

3. **Implementacja komponentów pomocniczych**:
   - LoadingSpinner - wskaźnik ładowania
   - AlertComponent - wyświetlanie komunikatów
   - ImageUpload - obsługa uploadu zdjęć

4. **Implementacja formularza edycji oferty (OfferForm)**:
   - Utworzenie struktury formularza z polami dla wszystkich właściwości oferty
   - Podłączenie walidacji pól
   - Integracja z komponentem ImageUpload

5. **Integracja z API**:
   - Pobieranie danych oferty
   - Pobieranie listy kategorii
   - Implementacja funkcji aktualizacji oferty

6. **Implementacja obsługi błędów**:
   - Błędy pobierania danych
   - Błędy walidacji formularza
   - Błędy API

7. **Implementacja nawigacji**:
   - Przekierowanie po udanej edycji
   - Przekierowanie po anulowaniu
   - Zabezpieczenie przed niezapisanymi zmianami (opcjonalnie)

8. **Testowanie końcowe**:
   - Weryfikacja wszystkich ścieżek użytkownika
   - Weryfikacja poprawności walidacji
   - Weryfikacja obsługi błędów
   - Weryfikacja zgodności z wymaganiami UI/UX 