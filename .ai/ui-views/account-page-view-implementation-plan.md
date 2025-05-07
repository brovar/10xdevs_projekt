# Plan implementacji widoku AccountPage (Moje Konto)

## 1. Przegląd
Widok "Moje Konto" (`AccountPage`) umożliwia zalogowanym użytkownikom (Kupujący, Sprzedający, Admin) przeglądanie informacji o ich koncie oraz zarządzanie profilem, w tym zmianę hasła oraz aktualizację imienia i nazwiska. Widok agreguje dane użytkownika i udostępnia formularze do modyfikacji tych danych.

## 2. Routing widoku
-   **Ścieżka:** `/account`
-   **Ochrona:** Wymaga zalogowanego użytkownika. Przekierowanie na `/login` w przypadku braku autoryzacji.

## 3. Struktura komponentów
```
AccountPage (src/pages/account/AccountPage.js)
├── UserProfileInfo (src/components/account/UserProfileInfo.js)
├── UpdateProfileForm (src/components/account/UpdateProfileForm.js)
└── ChangePasswordForm (src/components/account/ChangePasswordForm.js)
```

## 4. Szczegóły komponentów

### `AccountPage`
-   **Opis komponentu:** Główny komponent kontenerowy dla widoku `/account`. Odpowiedzialny za pobranie danych użytkownika, zarządzanie stanem ładowania i błędów oraz przekazywanie danych i funkcji do komponentów podrzędnych.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Sekcja dla `UserProfileInfo`.
    -   Sekcja dla `UpdateProfileForm`.
    -   Sekcja dla `ChangePasswordForm`.
    -   Elementy do wyświetlania stanu ładowania (np. `Spinner`) i komunikatów o błędach.
-   **Obsługiwane interakcje:** Brak bezpośrednich interakcji, orkiestruje interakcje w komponentach podrzędnych.
-   **Obsługiwana walidacja:** Brak bezpośredniej walidacji.
-   **Typy:**
    -   `UserVM` (do przechowywania danych użytkownika).
-   **Propsy:** Brak.

### `UserProfileInfo`
-   **Opis komponentu:** Komponent prezentacyjny wyświetlający statyczne informacje o profilu użytkownika.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Elementy `div` lub `p` do wyświetlania etykiet (np. "Email:", "Rola:", "Status:", "Data utworzenia:") i odpowiadających im wartości.
    -   Stylowanie za pomocą Bootstrap 5 (np. `card`, `list-group`).
-   **Obsługiwane interakcje:** Brak.
-   **Obsługiwana walidacja:** Brak.
-   **Typy:** `UserVM`.
-   **Propsy:**
    -   `userData: UserVM | null` - obiekt zawierający dane zalogowanego użytkownika.

### `UpdateProfileForm`
-   **Opis komponentu:** Formularz umożliwiający użytkownikowi aktualizację imienia i nazwiska. Wykorzystuje React Hook Form do zarządzania stanem formularza i walidacją.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Element `<form>` (React Hook Form).
    -   `TextInput` dla imienia (`firstName`).
    -   `TextInput` dla nazwiska (`lastName`).
    -   Przycisk `Button` typu `submit` (np. "Zapisz zmiany").
    -   Komunikaty walidacyjne wyświetlane obok pól.
-   **Obsługiwane interakcje:**
    -   Wprowadzanie tekstu w polach imienia i nazwiska.
    -   Przesłanie formularza.
-   **Obsługiwana walidacja:**
    -   `firstName`: opcjonalne, jeśli podane, maksymalnie 100 znaków.
    -   `lastName`: opcjonalne, jeśli podane, maksymalnie 100 znaków.
    -   Co najmniej jedno pole musi być wypełnione, aby umożliwić wysłanie (logika w `onSubmit` lub walidacja React Hook Form).
-   **Typy:** `UpdateProfileFormData`, `UserVM` (dla wartości początkowych).
-   **Propsy:**
    -   `initialData: { firstName: string, lastName: string }` - początkowe wartości dla pól formularza.
    -   `onSubmit: (data: UpdateProfileFormData) => Promise<void>` - funkcja wywoływana po pomyślnym przesłaniu i walidacji formularza.
    -   `isSubmitting: boolean` - informuje, czy formularz jest w trakcie przetwarzania.
    -   `error: string | null` - komunikat błędu dotyczący operacji zapisu.

### `ChangePasswordForm`
-   **Opis komponentu:** Formularz umożliwiający użytkownikowi zmianę hasła. Wykorzystuje React Hook Form.
-   **Główne elementy HTML i komponenty dzieci:**
    -   Element `<form>` (React Hook Form).
    -   `TextInput` typu `password` dla aktualnego hasła (`currentPassword`).
    -   `TextInput` typu `password` dla nowego hasła (`newPassword`).
    -   `TextInput` typu `password` dla potwierdzenia nowego hasła (`confirmNewPassword`).
    -   Przycisk `Button` typu `submit` (np. "Zmień hasło").
    -   Informacja o polityce haseł (np. "Minimum 10 znaków, mała i duża litera, cyfra lub znak specjalny").
    -   Komunikaty walidacyjne.
-   **Obsługiwane interakcje:**
    -   Wprowadzanie tekstu w polach haseł.
    -   Przesłanie formularza.
-   **Obsługiwana walidacja (zgodnie z PRD i `schemas.py`):**
    -   `currentPassword`: pole wymagane.
    -   `newPassword`:
        -   Pole wymagane.
        -   Minimum 10 znaków.
        -   Musi zawierać co najmniej jedną małą literę.
        -   Musi zawierać co najmniej jedną dużą literę.
        -   Musi zawierać co najmniej jedną cyfrę lub znak specjalny.
    -   `confirmNewPassword`:
        -   Pole wymagane.
        -   Musi być identyczne z `newPassword`.
-   **Typy:** `ChangePasswordFormData`.
-   **Propsy:**
    -   `onSubmit: (data: ChangePasswordFormData) => Promise<void>` - funkcja wywoływana po pomyślnym przesłaniu i walidacji formularza.
    -   `isSubmitting: boolean` - informuje, czy formularz jest w trakcie przetwarzania.
    -   `error: string | null` - komunikat błędu dotyczący operacji zmiany hasła.
    -   `successMessage: string | null` - komunikat o pomyślnej zmianie hasła.

## 5. Typy

### `UserDTO` (z backendu, `schemas.UserDTO`)
```typescript
interface UserDTO {
  id: string; // UUID
  email: string;
  role: 'Buyer' | 'Seller' | 'Admin';
  status: 'Active' | 'Inactive';
  first_name?: string | null;
  last_name?: string | null;
  created_at: string; // ISO datetime string
  updated_at?: string | null; // ISO datetime string
}
```

### `UserVM` (ViewModel dla frontendu)
```typescript
interface UserVM {
  id: string;
  email: string;
  role: string; // np. "Kupujący", "Sprzedający", "Administrator"
  status: string; // np. "Aktywny", "Nieaktywny"
  firstName: string; // Pusty string, jeśli null/undefined z DTO
  lastName: string;  // Pusty string, jeśli null/undefined z DTO
  createdAt: string; // Sformatowana data, np. "DD.MM.YYYY"
}
```
-   **Cel:** Używany do wyświetlania danych w `UserProfileInfo` oraz jako wartości inicjalne w `UpdateProfileForm`. Pola `firstName` i `lastName` są normalizowane do pustych stringów dla uproszczenia obsługi w formularzach. `createdAt` jest formatowana dla lepszej czytelności.

### `UpdateProfileFormData`
```typescript
interface UpdateProfileFormData {
  firstName: string;
  lastName: string;
}
```
-   **Cel:** Reprezentuje dane z formularza `UpdateProfileForm`.

### `ChangePasswordFormData`
```typescript
interface ChangePasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmNewPassword: string;
}
```
-   **Cel:** Reprezentuje dane z formularza `ChangePasswordForm`.

### `ChangePasswordRequestDTO` (do wysłania do API `PUT /account/password`)
```typescript
interface ChangePasswordRequestDTO {
  current_password: string;
  new_password: string;
}
```

### `UpdateUserRequestDTO` (do wysłania do API `PATCH /account`)
```typescript
interface UpdateUserRequestDTO {
  first_name?: string;
  last_name?: string;
}
```

### `MessageResponseDTO` (odpowiedź z API `PUT /account/password`)
```typescript
interface MessageResponseDTO {
  message: string;
}
```

## 6. Zarządzanie stanem

Stan będzie zarządzany głównie w komponencie `AccountPage` przy użyciu hooków `useState` i `useEffect`.

-   `userData: UserVM | null`: Przechowuje dane zalogowanego użytkownika. Inicjalnie `null`. Ustawiane po pomyślnym pobraniu danych z `GET /account`.
-   `isLoading: boolean`: Wskazuje, czy trwa pobieranie danych użytkownika. Używane do wyświetlania np. komponentu `Spinner`.
-   `error: string | null`: Przechowuje komunikat błędu, jeśli pobieranie danych użytkownika nie powiodło się.
-   `isUpdatingProfile: boolean`: Wskazuje, czy trwa aktualizacja profilu (`PATCH /account`).
-   `updateProfileError: string | null`: Komunikat błędu dla operacji aktualizacji profilu.
-   `isChangingPassword: boolean`: Wskazuje, czy trwa zmiana hasła (`PUT /account/password`).
-   `changePasswordError: string | null`: Komunikat błędu dla operacji zmiany hasła.
-   `changePasswordSuccess: string | null`: Komunikat o pomyślnej zmianie hasła, używany do wyświetlenia np. `ToastNotification` i przekazania do `ChangePasswordForm` aby wyczyścić pola.

Rozważenie stworzenia niestandardowego hooka `useAccountManagement` jest zasadne, aby zamknąć logikę pobierania danych, aktualizacji profilu i zmiany hasła, wraz z obsługą stanów ładowania i błędów. Hook ten mógłby korzystać z serwisów API.

Przykład stanu w `AccountPage`:
```javascript
const [userData, setUserData] = useState<UserVM | null>(null);
const [isLoading, setIsLoading] = useState(true);
const [error, setError] = useState<string | null>(null);
// ... pozostałe stany dla formularzy
```

Formularze (`UpdateProfileForm`, `ChangePasswordForm`) będą używać biblioteki `react-hook-form` do wewnętrznego zarządzania stanem pól, walidacją i procesem przesyłania.

## 7. Integracja API

Komunikacja z API będzie realizowana poprzez dedykowany serwis, np. `src/services/accountService.js`.

### `GET /account`
-   **Cel:** Pobranie danych zalogowanego użytkownika.
-   **Akcja:** Wywoływane przy montowaniu komponentu `AccountPage`.
-   **Odpowiedź (sukces 200 OK):** `UserDTO`. Frontend mapuje `UserDTO` na `UserVM`.
    ```json
    {
      "id": "uuid-user-id",
      "email": "user@example.com",
      "role": "Buyer",
      "status": "Active",
      "first_name": "John",
      "last_name": "Doe",
      "created_at": "timestamp",
      "updated_at": "timestamp"
    }
    ```
-   **Błędy:**
    -   `401 Unauthorized (NOT_AUTHENTICATED)`: Globalna obsługa (przekierowanie na login).
    -   `404 Not Found (USER_NOT_FOUND)`: Wyświetlenie błędu na stronie.
    -   `500 Internal Server Error`: Wyświetlenie ogólnego błędu.

### `PATCH /account`
-   **Cel:** Aktualizacja imienia i/lub nazwiska użytkownika.
-   **Akcja:** Wywoływane po przesłaniu `UpdateProfileForm`.
-   **Żądanie:** `UpdateUserRequestDTO`
    ```json
    {
      "first_name": "NoweImię", // Opcjonalne
      "last_name": "NoweNazwisko" // Opcjonalne
    }
    ```
-   **Odpowiedź (sukces 200 OK):** `UserDTO` (zaktualizowane dane). Frontend aktualizuje stan `userData` i wyświetla `ToastNotification` o sukcesie.
-   **Błędy:**
    -   `400 Bad Request (INVALID_INPUT)`: Wyświetlenie błędu w formularzu.
    -   `401 Unauthorized (NOT_AUTHENTICATED)`: Globalna obsługa.
    -   `404 Not Found (USER_NOT_FOUND)`: Wyświetlenie ogólnego błędu.
    -   `500 Internal Server Error (PROFILE_UPDATE_FAILED)`: Wyświetlenie `ToastNotification` z błędem.

### `PUT /account/password`
-   **Cel:** Zmiana hasła użytkownika.
-   **Akcja:** Wywoływane po przesłaniu `ChangePasswordForm`.
-   **Żądanie:** `ChangePasswordRequestDTO`
    ```json
    {
      "current_password": "StareHaslo1!",
      "new_password": "NoweSuperHaslo123!"
    }
    ```
-   **Odpowiedź (sukces 200 OK):** `MessageResponseDTO`
    ```json
    {
      "message": "Password updated successfully"
    }
    ```
    Frontend wyświetla `ToastNotification` o sukcesie i czyści pola formularza zmiany hasła.
-   **Błędy:**
    -   `400 Bad Request (INVALID_INPUT, PASSWORD_POLICY_VIOLATED)`: Wyświetlenie błędu w formularzu (np. "Nowe hasło nie spełnia wymagań polityki.").
    -   `401 Unauthorized (NOT_AUTHENTICATED)`: Globalna obsługa.
    -   `401 Unauthorized (INVALID_CURRENT_PASSWORD)`: Wyświetlenie błędu w formularzu ("Podane aktualne hasło jest nieprawidłowe.").
    -   `500 Internal Server Error (PASSWORD_UPDATE_FAILED)`: Wyświetlenie `ToastNotification` z błędem.

## 8. Interakcje użytkownika
1.  **Ładowanie strony:**
    -   Użytkownik przechodzi na `/account`.
    -   Wyświetlany jest wskaźnik ładowania.
    -   Wykonywane jest żądanie `GET /account`.
    -   Po otrzymaniu danych, wskaźnik ładowania znika, a `UserProfileInfo` wypełnia się danymi. `UpdateProfileForm` inicjalizuje się imieniem i nazwiskiem użytkownika.
2.  **Aktualizacja profilu (imię/nazwisko):**
    -   Użytkownik modyfikuje pola "Imię" i/lub "Nazwisko" w `UpdateProfileForm`.
    -   Klika przycisk "Zapisz zmiany".
    -   Formularz jest walidowany po stronie klienta.
    -   Jeśli walidacja przejdzie, wysyłane jest żądanie `PATCH /account`. Przycisk "Zapisz zmiany" może pokazywać stan ładowania.
    -   **Sukces:** `UserProfileInfo` oraz pola w `UpdateProfileForm` aktualizują się nowymi danymi. Wyświetlany jest `ToastNotification` ("Profil zaktualizowany pomyślnie.").
    -   **Błąd:** Wyświetlany jest odpowiedni komunikat błędu (w formularzu lub jako `ToastNotification`).
3.  **Zmiana hasła:**
    -   Użytkownik wypełnia pola "Aktualne hasło", "Nowe hasło", "Potwierdź nowe hasło" w `ChangePasswordForm`.
    -   Klika przycisk "Zmień hasło".
    -   Formularz jest walidowany po stronie klienta (wymagane pola, zgodność nowych haseł, polityka nowego hasła).
    -   Jeśli walidacja przejdzie, wysyłane jest żądanie `PUT /account/password`. Przycisk "Zmień hasło" może pokazywać stan ładowania.
    -   **Sukces:** Pola formularza zmiany hasła są czyszczone. Wyświetlany jest `ToastNotification` ("Hasło zmienione pomyślnie.").
    -   **Błąd:** Wyświetlany jest odpowiedni komunikat błędu (w formularzu lub jako `ToastNotification`, np. "Nieprawidłowe aktualne hasło.").

## 9. Warunki i walidacja
### `UpdateProfileForm`
-   **Imię (`firstName`):**
    -   Warunek: Maksymalnie 100 znaków.
    -   Weryfikacja: React Hook Form, `maxLength: 100`.
    -   Wpływ: Wyświetlenie komunikatu błędu przy polu, blokada wysłania formularza.
-   **Nazwisko (`lastName`):**
    -   Warunek: Maksymalnie 100 znaków.
    -   Weryfikacja: React Hook Form, `maxLength: 100`.
    -   Wpływ: Wyświetlenie komunikatu błędu przy polu, blokada wysłania formularza.
-   **Ogólne formularza:**
    -   Warunek: Co najmniej jedno z pól (imię lub nazwisko) musi być zmodyfikowane i różne od wartości początkowych, aby uzasadnić wysłanie (lub backend obsłuży brak zmian). Preferowane jest, aby przycisk "Zapisz" był aktywny tylko jeśli są zmiany.

### `ChangePasswordForm`
-   **Aktualne hasło (`currentPassword`):**
    -   Warunek: Pole wymagane.
    -   Weryfikacja: React Hook Form, `required: true`.
    -   Wpływ: Wyświetlenie komunikatu błędu, blokada wysłania.
-   **Nowe hasło (`newPassword`):**
    -   Warunek: Pole wymagane.
    -   Weryfikacja: React Hook Form, `required: true`.
    -   Wpływ: Wyświetlenie komunikatu błędu, blokada wysłania.
    -   Warunek: Minimum 10 znaków.
    -   Weryfikacja: React Hook Form, `minLength: 10`.
    -   Wpływ: Wyświetlenie komunikatu błędu, blokada wysłania.
    -   Warunek: Co najmniej jedna mała litera, jedna duża litera, jedna cyfra lub znak specjalny.
    -   Weryfikacja: React Hook Form, `pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9!@#$%^&*(),.?":{}|<>]).{10,}$/` (regex z `schemas.py` dostosowany).
    -   Wpływ: Wyświetlenie komunikatu błędu o niespełnieniu polityki, blokada wysłania.
-   **Potwierdź nowe hasło (`confirmNewPassword`):**
    -   Warunek: Pole wymagane.
    -   Weryfikacja: React Hook Form, `required: true`.
    -   Wpływ: Wyświetlenie komunikatu błędu, blokada wysłania.
    -   Warunek: Musi być identyczne z wartością pola "Nowe hasło".
    -   Weryfikacja: React Hook Form, custom validator `validate: value => value === getValues('newPassword')`.
    -   Wpływ: Wyświetlenie komunikatu "Hasła nie są zgodne", blokada wysłania.

## 10. Obsługa błędów
-   **Błąd pobierania danych użytkownika (`GET /account`):**
    -   Wyświetlić komunikat na całą stronę lub w miejscu komponentów: "Nie udało się załadować danych konta. Spróbuj odświeżyć stronę."
    -   Jeśli błąd to 401, globalny `AuthContext` powinien przekierować na `/login`.
-   **Błędy walidacji formularzy (po stronie klienta):**
    -   Wyświetlane bezpośrednio przy odpowiednich polach formularza. React Hook Form zarządza tym automatycznie.
-   **Błędy API przy aktualizacji profilu (`PATCH /account`):**
    -   `400 INVALID_INPUT`: Wyświetlić ogólny błąd przy formularzu `UpdateProfileForm`: "Wprowadzone dane są nieprawidłowe."
    -   `401 NOT_AUTHENTICATED`: Globalna obsługa.
    -   `404 USER_NOT_FOUND`: Mało prawdopodobne. Wyświetlić ogólny `ToastNotification` "Wystąpił błąd."
    -   `500 PROFILE_UPDATE_FAILED`: Wyświetlić `ToastNotification`: "Nie udało się zaktualizować profilu. Spróbuj ponownie później."
-   **Błędy API przy zmianie hasła (`PUT /account/password`):**
    -   `400 INVALID_INPUT`: Ogólny błąd przy formularzu `ChangePasswordForm`.
    -   `400 PASSWORD_POLICY_VIOLATED`: Błąd przy polu "Nowe hasło": "Nowe hasło nie spełnia wymagań bezpieczeństwa."
    -   `401 NOT_AUTHENTICATED`: Globalna obsługa.
    -   `401 INVALID_CURRENT_PASSWORD`: Błąd przy polu "Aktualne hasło": "Podane aktualne hasło jest nieprawidłowe."
    -   `500 PASSWORD_UPDATE_FAILED`: Wyświetlić `ToastNotification`: "Nie udało się zmienić hasła. Spróbuj ponownie później."
-   **Powiadomienia o sukcesie:**
    -   Używać `ToastNotification` dla operacji zakończonych sukcesem (aktualizacja profilu, zmiana hasła).
    -   Treść: "Profil zaktualizowany pomyślnie.", "Hasło zmienione pomyślnie."

## 11. Kroki implementacji
1.  **Utworzenie struktury plików:**
    -   `src/pages/account/AccountPage.js`
    -   `src/components/account/UserProfileInfo.js`
    -   `src/components/account/UpdateProfileForm.js`
    -   `src/components/account/ChangePasswordForm.js`
    -   `src/services/accountService.js` (jeśli jeszcze nie istnieje lub wymaga rozbudowy).
2.  **Implementacja `AccountPage.js`:**
    -   Dodać routing dla `/account` w głównym pliku konfiguracyjnym routera (np. `src/routes/index.js`), zabezpieczając go (`ProtectedRoute`).
    -   Zaimplementować logikę pobierania danych użytkownika (`GET /account`) w `useEffect` przy użyciu `accountService`.
    -   Zarządzać stanami `userData`, `isLoading`, `error`.
    -   Stworzyć funkcje obsługujące submity formularzy (`handleUpdateProfile`, `handleChangePassword`), które będą wywoływać odpowiednie metody z `accountService` i zarządzać stanami ładowania/błędów dla tych operacji.
    -   Przekazać odpowiednie propsy do komponentów `UserProfileInfo`, `UpdateProfileForm`, `ChangePasswordForm`.
    -   Wyświetlać `Spinner` podczas ładowania i komunikaty o błędach.
3.  **Implementacja `UserProfileInfo.js`:**
    -   Stworzyć komponent przyjmujący `userData` jako props.
    -   Wyświetlić dane użytkownika (email, rola, status, sformatowana data utworzenia) używając Bootstrap 5 do stylizacji.
4.  **Implementacja `UpdateProfileForm.js`:**
    -   Zintegrować z React Hook Form.
    -   Dodać pola `firstName`, `lastName` (`TextInput` z Bootstrap).
    -   Zaimplementować walidację (max 100 znaków).
    -   Przekazać `initialData` (z `userData`), `onSubmit` (funkcja z `AccountPage`), `isSubmitting`, `error` jako propsy.
    -   Wyświetlać komunikaty walidacyjne i błędy operacji.
5.  **Implementacja `ChangePasswordForm.js`:**
    -   Zintegrować z React Hook Form.
    -   Dodać pola `currentPassword`, `newPassword`, `confirmNewPassword` (`TextInput` z Bootstrap).
    -   Zaimplementować walidację (wymagane, polityka hasła, zgodność haseł).
    -   Wyświetlić informację o polityce haseł.
    -   Przekazać `onSubmit` (funkcja z `AccountPage`), `isSubmitting`, `error`, `successMessage` jako propsy.
    -   Implementować czyszczenie pól po pomyślnej zmianie hasła (na podstawie `successMessage` lub callbacku).
6.  **Implementacja `accountService.js`:**
    -   Dodać funkcje `fetchAccountDetails()`, `updateAccountDetails(data)`, `changePassword(data)`.
    -   Funkcje te powinny używać `fetch` lub `axios` do komunikacji z API, obsługiwać nagłówki (np. autoryzacyjne) i mapować odpowiedzi/błędy.
7.  **Styling i UX:**
    -   Użyć komponentów i klas Bootstrap 5 do spójnego wyglądu.
    -   Zapewnić responsywność widoku.
    -   Dodać odpowiednie etykiety ARIA dla dostępności.
    -   Zaimplementować `ToastNotification` dla informacji o sukcesie/błędach operacji (np. przy użyciu `react-toastify` lub podobnej biblioteki, jeśli jest w projekcie).
8.  **Testowanie:**
    -   Przetestować wszystkie ścieżki użytkownika: ładowanie danych, aktualizacja profilu (sukces/błąd), zmiana hasła (sukces/różne błędy walidacji i API).
    -   Sprawdzić obsługę błędów i stanów ładowania.
    -   Przetestować walidację po stronie klienta.
    -   Sprawdzić, czy widok jest poprawnie chroniony.
``` 