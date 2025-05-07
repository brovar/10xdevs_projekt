# Plan implementacji akcji wylogowania

## 1. Przegląd
Akcja wylogowania pozwala zalogowanym użytkownikom (Kupujący, Sprzedający, Admin) bezpiecznie zakończyć ich sesję w aplikacji Steambay. Nie jest to osobny widok/strona, lecz funkcja wywoływana zazwyczaj przez element interfejsu użytkownika, taki jak przycisk lub opcja w menu, dostępna tylko dla uwierzytelnionych użytkowników. Proces obejmuje wysłanie żądania do backendu w celu unieważnienia sesji (wyczyszczenia ciasteczka sesyjnego), aktualizację globalnego stanu uwierzytelnienia w aplikacji frontendowej oraz przekierowanie użytkownika do publicznej części aplikacji (np. strony głównej).

## 2. Routing widoku
Akcja wylogowania nie posiada dedykowanej ścieżki routingu. Jest inicjowana z komponentów dostępnych na różnych (chronionych) ścieżkach, najczęściej z globalnego nagłówka lub menu użytkownika.

## 3. Struktura komponentów
Nie dotyczy w kontekście dedykowanego widoku. Komponenty zaangażowane w inicjację wylogowania to:

```
[Komponent zawierający opcję wylogowania, np. Header/Navbar/UserMenu]
├── LogoutButton / LogoutMenuItem (element UI inicjujący akcję)
└── (korzysta z hooka useAuth do wywołania logiki wylogowania)

[Globalny Kontekst]
└── AuthProvider (zarządza stanem i logiką uwierzytelnienia, w tym wylogowaniem)
    └── AuthContext
```

## 4. Szczegóły komponentów

### `LogoutButton` / `LogoutMenuItem`
-   **Opis komponentu:** Przycisk lub element menu rozwijanego, widoczny tylko dla zalogowanych użytkowników, służący do zainicjowania procesu wylogowania.
-   **Główne elementy HTML i komponenty dzieci:** Element `<button>` lub element listy `<li>` z odpowiednim stylem i tekstem (np. "Wyloguj"). Może zawierać ikonę.
-   **Obsługiwane zdarzenia:** `onClick`.
-   **Warunki walidacji:** Komponent jest renderowany warunkowo, tylko gdy użytkownik jest zalogowany (na podstawie stanu z `AuthContext`).
-   **Typy (DTO i ViewModel):** Brak specyficznych.
-   **Propsy:** Brak standardowych propsów, ale komponent będzie pobierał funkcję `logout` z `AuthContext` za pomocą hooka `useAuth`.

### `useAuth` (Custom Hook)
-   **Opis komponentu:** Hook React dostarczający dostęp do stanu uwierzytelnienia i funkcji związanych z autentykacją (login, logout, register, currentUser, isAuthenticated, isLoading).
-   **Główne elementy HTML i komponenty dzieci:** Nie dotyczy (jest to hook).
-   **Obsługiwane zdarzenia:** Udostępnia funkcję `logout()` do wywołania.
-   **Warunki walidacji:** Funkcja `logout()` może wewnętrznie obsługiwać logikę CSRF i wywołanie API.
-   **Typy (DTO i ViewModel):** Zarządza stanem `currentUser: User | null`, `isAuthenticated: boolean`, `isLoading: boolean`.
-   **Propsy:** Nie dotyczy.

## 5. Typy

### DTO (Data Transfer Objects - dla komunikacji z API, zgodne z `schemas.py`)

-   **Żądanie**: Brak (ciało żądania jest puste dla `POST /auth/logout`).
-   **Odpowiedź Sukces (200 OK)**: `LogoutUserResponseDto` (zgodny z `LogoutUserResponse` w `schemas.py`).
    ```typescript
    interface LogoutUserResponseDto {
      message: string; // np. "Logout successful"
    }
    ```
-   **Odpowiedź Błąd**: `ApiErrorResponseDto` (generyczny).
    ```typescript
    interface ApiErrorResponseDto {
      error_code: string; // np. "LOGOUT_FAILED", "NOT_AUTHENTICATED", potencjalny błąd CSRF
      message: string;
    }
    ```

### ViewModel
Nie dotyczy, ponieważ nie ma dedykowanego widoku ani formularza dla akcji wylogowania.

## 6. Zarządzanie stanem

-   **Stan globalny (`AuthContext`)**: Kluczowy dla procesu wylogowania. Przechowuje stan uwierzytelnienia (`isAuthenticated: boolean`, `currentUser: User | null`, `isLoading: boolean`).
-   **Hook `useAuth`**: Udostępnia funkcję `logout()`. Wywołanie tej funkcji:
    1.  Ustawia globalny stan `isLoading` na `true`.
    2.  Wywołuje serwis API (`authService.logout()`).
    3.  Po otrzymaniu odpowiedzi (sukces lub błąd):
        -   W przypadku sukcesu (200 OK), aktualizuje stan globalny: `isAuthenticated = false`, `currentUser = null`. Czyści ewentualne inne dane użytkownika (poza koszykiem w localStorage).
        -   W przypadku błędu, stan globalny zazwyczaj pozostaje niezmieniony (chyba że błąd 401/403 sugeruje nieważną sesję).
    4.  Ustawia globalny stan `isLoading` na `false`.
    5.  Wywołuje odpowiednie akcje dodatkowe (nawigacja, powiadomienia).
-   **Stan lokalny**: Komponent inicjujący (`LogoutButton`/`LogoutMenuItem`) może posiadać lokalny stan `isLoggingOut: boolean`, aby zarządzać własnym wskaźnikiem ładowania, jeśli globalny `isLoading` z `AuthContext` jest niewystarczający.
-   **`NotificationContext`**: Używany przez hook `useAuth` lub bezpośrednio w komponencie do wyświetlania powiadomień toast o wyniku operacji wylogowania (sukces lub błąd).

## 7. Integracja API

-   **Endpoint**: `POST /auth/logout`
-   **Cel**: Zakończenie sesji użytkownika po stronie backendu.
-   **Wywołanie**: Realizowane przez funkcję `logout()` w hooku `useAuth`, która wywołuje dedykowaną funkcję w serwisie API (np. `authService.logout()`).
-   **Nagłówki**: Żądanie musi zawierać poprawny nagłówek `X-CSRF-Token`. Konfiguracja klienta HTTP (np. Axios interceptor) jest odpowiedzialna za automatyczne dołączanie tego nagłówka na podstawie wartości z odpowiedniego ciasteczka (np. `csrf_token`).
-   **Typ żądania (Request Body)**: Brak (puste).
-   **Typy odpowiedzi (Response Body)**:
    -   **Sukces (200 OK)**: `LogoutUserResponseDto` (`{ message: string }`).
    -   **Błąd**: `ApiErrorResponseDto` (`{ error_code: string, message: string }`) dla kodów 401, 403 (CSRF), 500.
-   **Akcje po odpowiedzi**: Zdefiniowane w logice funkcji `logout()` w `useAuth`:
    -   **Sukces**: Aktualizacja `AuthContext`, czyszczenie danych lokalnych (opcjonalnie), wyświetlenie toastu (opcjonalnie), przekierowanie użytkownika.
    -   **Błąd**: Wyświetlenie toastu z błędem.

## 8. Interakcje użytkownika

1.  Zalogowany użytkownik klika przycisk/link "Wyloguj".
2.  (Opcjonalnie) Przycisk/link przechodzi w stan ładowania.
3.  Aplikacja wysyła żądanie `POST /auth/logout` do backendu.
4.  Po otrzymaniu pomyślnej odpowiedzi:
    -   Stan aplikacji jest aktualizowany (użytkownik wylogowany).
    -   Użytkownik jest przekierowywany na stronę główną (`/`) lub logowania (`/login`).
    -   (Opcjonalnie) Wyświetlane jest powiadomienie toast o pomyślnym wylogowaniu.
5.  Po otrzymaniu odpowiedzi błędu:
    -   Wyświetlane jest powiadomienie toast z informacją o błędzie.
    -   Stan ładowania przycisku/linku jest usuwany.
    -   Użytkownik pozostaje zalogowany (chyba że błąd sugeruje inaczej).

## 9. Warunki i walidacja

-   **Warunek Frontendowy**: Opcja "Wyloguj" jest widoczna i dostępna tylko dla użytkowników, którzy są aktualnie zalogowani (`isAuthenticated === true` w `AuthContext`).
-   **Warunek API (CSRF)**: Poprawny i aktualny token CSRF musi zostać wysłany w nagłówku `X-CSRF-Token` żądania `POST`. Walidacja tokena odbywa się po stronie backendu.
-   **Walidacja Frontendowa (interakcja)**: Zablokowanie możliwości wielokrotnego kliknięcia przycisku "Wyloguj" podczas trwania procesu wylogowywania (gdy `isLoading` jest `true`).

## 10. Obsługa błędów

-   **Błąd CSRF (np. 403 Forbidden)**:
    -   *Obsługa*: Wyświetlenie powiadomienia toast (np. "Błąd sesji. Odśwież stronę i spróbuj ponownie.").
    -   *Stan*: `isLoading` ustawione na `false`, stan uwierzytelnienia bez zmian.
-   **Błąd serwera (500 `LOGOUT_FAILED`)**:
    -   *Obsługa*: Wyświetlenie powiadomienia toast (np. "Wystąpił błąd serwera podczas wylogowania.").
    -   *Stan*: `isLoading` ustawione na `false`, stan uwierzytelnienia bez zmian.
-   **Błąd sieciowy**:
    -   *Obsługa*: Wyświetlenie powiadomienia toast (np. "Błąd połączenia. Nie można się wylogować.").
    -   *Stan*: `isLoading` ustawione na `false`, stan uwierzytelnienia bez zmian.
-   **Błąd `NOT_AUTHENTICATED` (401)**:
    -   *Obsługa*: Ten błąd nie powinien wystąpić, jeśli opcja wylogowania jest dostępna tylko dla zalogowanych. Jeśli jednak wystąpi, można go zignorować lub potraktować jak sukces (wyczyścić stan frontendowy i przekierować), ponieważ oznacza, że użytkownik i tak nie był zalogowany.

## 11. Kroki implementacji

1.  **Konfiguracja CSRF w kliencie HTTP (jeśli jeszcze nie zrobiona)**:
    -   Skonfiguruj interceptor Axios (lub odpowiednik dla innego klienta), aby automatycznie odczytywał token CSRF z ciasteczka (np. `csrf_token`, nazwa zgodna z backendem) i dodawał go do nagłówka `X-CSRF-Token` dla żądań typu `POST`, `PUT`, `PATCH`, `DELETE`.

2.  **Aktualizacja `AuthContext` i `useAuth` hooka**:
    -   Dodaj funkcję `logout: () => Promise<void>` do kontekstu i hooka `useAuth`.
    -   Implementacja logiki `logout` w `useAuth`:
        -   Ustawienie `isLoading` na `true`.
        -   Wywołanie `authService.logout()` w bloku `try...catch...finally`.
        -   W `try` (po sukcesie): wywołanie `setCurrentUser(null)` (lub odpowiednik), `setIsAuthenticated(false)`, nawigacja do `/` lub `/login`, opcjonalny toast sukcesu.
        -   W `catch` (po błędzie): pobranie komunikatu błędu, wyświetlenie toastu błędu.
        -   W `finally`: ustawienie `isLoading` na `false`.

3.  **Implementacja Serwisu API (`authService`)**:
    -   Dodaj funkcję `logout(): Promise<LogoutUserResponseDto>`.
    -   Funkcja ta powinna wykonać żądanie `POST` na `/auth/logout` (bez ciała żądania).
    -   Powinna poprawnie obsługiwać odpowiedź sukcesu (200 OK) i rzucać błędy (np. z `ApiErrorResponseDto`) w przypadku nieudanych odpowiedzi lub błędów sieciowych.

4.  **Implementacja elementu UI (`LogoutButton`/`LogoutMenuItem`)**:
    -   Umieść komponent w odpowiednim miejscu interfejsu (np. `Header`, `UserMenu`), tak aby był widoczny tylko dla zalogowanych użytkowników (użyj `isAuthenticated` z `useAuth`).
    -   Pobierz funkcję `logout` i stan `isLoading` z hooka `useAuth`.
    -   Podłącz wywołanie `logout()` do zdarzenia `onClick` komponentu.
    -   (Opcjonalnie) Dodaj lokalny stan `isLoggingOut` do komponentu, jeśli potrzebna jest bardziej granularna kontrola nad stanem ładowania tylko dla tej akcji.
    -   Ustaw stan `disabled={isLoading || isLoggingOut}` na przycisku/elemencie.

5.  **Obsługa przekierowania**: Upewnij się, że po wywołaniu `logout` w `useAuth` i udanej odpowiedzi z API, następuje przekierowanie za pomocą `useNavigate` (z `react-router-dom`).

6.  **Testowanie**:
    -   Testy hooka `useAuth`, szczególnie funkcji `logout`, mockując serwis API.
    -   Testy komponentu zawierającego `LogoutButton`, sprawdzające warunkowe renderowanie i wywoływanie funkcji `logout` po kliknięciu.
    -   Testy integracyjne sprawdzające cały przepływ: kliknięcie -> aktualizacja stanu -> przekierowanie.
    -   Testy E2E scenariusza wylogowania. 