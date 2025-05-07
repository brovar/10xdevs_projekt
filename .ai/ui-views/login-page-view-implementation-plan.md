# Plan implementacji widoku LoginPage

## 1. Przegląd
Widok `LoginPage` służy do uwierzytelniania zarejestrowanych użytkowników w systemie Steambay. Użytkownicy podają swój adres email i hasło, aby uzyskać dostęp do swoich kont i funkcji specyficznych dla ich ról. Widok zapewnia prosty i szybki proces logowania, obsługuje walidację wprowadzanych danych oraz wyświetla komunikaty o błędach w przypadku nieprawidłowych danych logowania, nieaktywnego konta lub innych problemów. Po pomyślnym zalogowaniu, sesja użytkownika jest ustanawiana za pomocą bezpiecznego ciasteczka HttpOnly, a użytkownik jest przekierowywany do odpowiedniej części aplikacji.

## 2. Routing widoku
- **Ścieżka:** `/login`

## 3. Struktura komponentów
```
LoginPage (strona/kontener)
├── Header (komponent layoutu, jeśli globalny)
├── LoginForm (komponent formularza logowania)
│   ├── EmailInput (pole email, generyczny TextInput)
│   ├── PasswordInput (pole hasła, generyczny TextInput)
│   └── SubmitButton (przycisk wysłania formularza, generyczny Button)
├── Link (do strony rejestracji `/register`)
└── Footer (komponent layoutu, jeśli globalny)
└── (Globalny system powiadomień typu Toast, np. przez Context)
```

## 4. Szczegóły komponentów

### `LoginPage`
-   **Opis komponentu:** Główny komponent strony logowania. Odpowiada za zarządzanie stanem logowania (ładowanie, błędy API), interakcję z `AuthContext` lub serwisem uwierzytelniania oraz nawigację po udanym lub nieudanym logowaniu.
-   **Główne elementy HTML i komponenty dzieci:** Kontener (np. `div` lub `Container` z Bootstrapa) dla `LoginForm` i linku do rejestracji. Wyświetla komunikaty błędów API, które nie są specyficzne dla pól.
-   **Obsługiwane zdarzenia:** Przekazanie funkcji `onSubmit` do `LoginForm`.
-   **Warunki walidacji:** Pośrednio, przez obsługę błędów zwróconych z API po próbie logowania.
-   **Typy (DTO i ViewModel):** Stan lokalny: `isLoading: boolean`, `apiError: string | null`.
-   **Propsy:** Brak specyficznych propsów, komponent głównie zarządza własnym stanem i logiką wywołania API.

### `LoginForm`
-   **Opis komponentu:** Komponent zawierający właściwy formularz logowania. Używa biblioteki React Hook Form do zarządzania stanem pól, walidacji po stronie klienta i obsługi procesu wysyłania danych.
-   **Główne elementy HTML i komponenty dzieci:** Element `<form>`, komponenty `EmailInput`, `PasswordInput`, `SubmitButton`.
-   **Obsługiwane zdarzenia:** Wprowadzanie danych przez użytkownika w polach formularza, zdarzenie `onSubmit` formularza.
-   **Warunki walidacji (klient-side, React Hook Form):
    -   Email: Wymagany, musi być poprawnym formatem adresu email.
    -   Hasło: Wymagane, nie może być puste.
-   **Typy (DTO i ViewModel):
    -   Dane formularza (ViewModel): `LoginFormData` (zdefiniowany poniżej).
    -   Typ danych wysyłanych do API: `LoginUserRequestDto` (zdefiniowany poniżej, zgodny z `schemas.py`).
-   **Propsy:**
    -   `onSubmit: (data: LoginUserRequestDto) => Promise<void>` (funkcja wywoływana po pomyślnej walidacji i wysłaniu formularza, przekazana z `LoginPage`).
    -   `isLoading: boolean` (do kontrolowania stanu przycisku wysyłania, przekazana z `LoginPage`).

### `EmailInput` (jako instancja generycznego `TextInput`)
-   **Opis komponentu:** Pole do wprowadzania adresu email użytkownika.
-   **Główne elementy HTML i komponenty dzieci:** Element `<label>`, `<input type="email">`, kontener na komunikat błędu walidacji. Stylowany za pomocą klas Bootstrap.
-   **Obsługiwane zdarzenia:** Wprowadzanie tekstu przez użytkownika (`onChange`).
-   **Warunki walidacji:** Jak zdefiniowano w `LoginForm` (wymagane, poprawny format email).
-   **Typy (DTO i ViewModel):** Wartość pola: `string`.
-   **Propsy:** `name: string`, `label: string`, `register: UseFormRegister<any>` (z React Hook Form), `errors: FieldErrors` (z React Hook Form).

### `PasswordInput` (jako instancja generycznego `TextInput`)
-   **Opis komponentu:** Pole do wprowadzania hasła użytkownika.
-   **Główne elementy HTML i komponenty dzieci:** Element `<label>`, `<input type="password">`, kontener na komunikat błędu walidacji. Stylowany za pomocą klas Bootstrap.
-   **Obsługiwane zdarzenia:** Wprowadzanie tekstu przez użytkownika (`onChange`).
-   **Warunki walidacji:** Jak zdefiniowano w `LoginForm` (wymagane).
-   **Typy (DTO i ViewModel):** Wartość pola: `string`.
-   **Propsy:** `name: string`, `label: string`, `register: UseFormRegister<any>` (z React Hook Form), `errors: FieldErrors` (z React Hook Form).

### `SubmitButton` (jako instancja generycznego `Button`)
-   **Opis komponentu:** Przycisk do wysłania formularza logowania.
-   **Główne elementy HTML i komponenty dzieci:** Element `<button type="submit">`. Stylowany za pomocą klas Bootstrap.
-   **Obsługiwane zdarzenia:** Kliknięcie przez użytkownika (`onClick`), które triggeruje `onSubmit` formularza.
-   **Warunki walidacji:** Stan `disabled` zależny od `isLoading` (przekazanego z `LoginPage`) lub stanu walidacji formularza zarządzanego przez React Hook Form.
-   **Typy (DTO i ViewModel):** Brak specyficznych.
-   **Propsy:** `label: string` (np. "Zaloguj się"), `isLoading: boolean`, `disabled?: boolean`.

## 5. Typy

### DTO (Data Transfer Objects - dla komunikacji z API, zgodne z `schemas.py`)

-   **`LoginUserRequestDto`**: Odpowiada `LoginUserRequest` ze `schemas.py`.
    ```typescript
    interface LoginUserRequestDto {
      email: string; // EmailStr
      password: string;
    }
    ```

-   **`LoginUserResponseDto`**: Odpowiada `LoginUserResponse` ze `schemas.py`.
    ```typescript
    interface LoginUserResponseDto {
      message: string;
    }
    ```

-   **`ApiErrorResponseDto`**: Generyczny typ dla odpowiedzi błędów z API.
    ```typescript
    interface ApiErrorResponseDto {
      error_code: string;
      message: string;
      detail?: any; // Może zawierać dodatkowe informacje o błędach pól
    }
    ```

### ViewModel (dla stanu formularza w komponencie `LoginForm`)

-   **`LoginFormData`**:
    ```typescript
    interface LoginFormData {
      email: string;
      password: string;
    }
    ```

## 6. Zarządzanie stanem

-   **Stan lokalny komponentu `LoginPage`**:
    -   `isLoading: boolean`: Flaga wskazująca, czy trwa proces komunikacji z API. Inicjalizowana na `false`. Używana do deaktywacji przycisku wysyłania i wyświetlania wskaźnika ładowania.
    -   `apiError: string | null`: Przechowuje globalne komunikaty błędów zwrócone przez API, które nie są bezpośrednio związane z konkretnym polem formularza (np. ogólny błąd serwera). Inicjalizowany na `null`.

-   **Stan formularza w `LoginForm`**:
    -   Zarządzany przez bibliotekę **React Hook Form**. Odpowiada za:
        -   Przechowywanie wartości pól `email` i `password`.
        -   Śledzenie stanu walidacji dla każdego pola.
        -   Przechowywanie komunikatów błędów walidacji dla każdego pola (np. "Pole wymagane", "Nieprawidłowy format email").
        -   Obsługę procesu wysyłania formularza (`handleSubmit`).

-   **Stan globalny (przez Context API)**:
    -   **`AuthContext`**: Kluczowy dla logowania. `LoginPage` (lub dedykowany hook `useAuth`) będzie zawierał funkcję `login(credentials: LoginUserRequestDto)`. Po pomyślnym zalogowaniu, ta funkcja zaktualizuje globalny stan uwierzytelnienia (np. dane zalogowanego użytkownika, flaga `isAuthenticated`). `LoginPage` również użyje tego kontekstu do sprawdzenia, czy użytkownik jest już zalogowany (np. w `useEffect`) i ewentualnego przekierowania go na stronę główną.
    -   **`NotificationContext`**: Używany do wyświetlania globalnych powiadomień typu toast informujących o sukcesie logowania lub o błędach (np. "Nieprawidłowe dane logowania", "Błąd serwera"). `LoginPage` użyje hooka (np. `useNotifications`) do wywołania funkcji `addSuccess(message)` lub `addError(message)`.

-   **Niestandardowe hooki**:
    -   **`useAuth`**: Prawdopodobnie będzie istniał hook dostarczający logikę uwierzytelniania i dostęp do danych użytkownika z `AuthContext`. Będzie zawierał funkcję `login`.
    -   **`useNotifications`**: Dostarczony przez `NotificationContext` do zarządzania powiadomieniami.

## 7. Integracja API

-   **Endpoint**: `POST /auth/login`
-   **Cel**: Uwierzytelnienie użytkownika i ustanowienie sesji.
-   **Wywołanie**:
    -   Po pomyślnej walidacji formularza logowania po stronie klienta, funkcja `onSubmit` (przekazana przez React Hook Form do `LoginForm`) wywoła funkcję `handleLoginSubmit` w `LoginPage`.
    -   `handleLoginSubmit` (lub funkcja `login` z `useAuth`) wywoła serwis API (np. `authService.login(credentials: LoginUserRequestDto)`), który wykona żądanie `POST` na `/auth/login`.
-   **Typ żądania (Request Body)**: `LoginUserRequestDto`.
    ```json
    {
      "email": "user@example.com",
      "password": "Password123!"
    }
    ```
-   **Typy odpowiedzi (Response Body)**:
    -   **Sukces (200 OK)**: `LoginUserResponseDto`. Backend dodatkowo ustawi ciasteczko sesyjne HttpOnly Secure.
        ```json
        {
          "message": "Login successful"
        }
        ```
    -   **Błąd**: `ApiErrorResponseDto` (dla kodów 400, 401, 500).
        -   `INVALID_CREDENTIALS` (401): `{"error_code": "INVALID_CREDENTIALS", "message": "Nieprawidłowy email lub hasło."}`
        -   `USER_INACTIVE` (401): `{"error_code": "USER_INACTIVE", "message": "Konto użytkownika jest nieaktywne."}`
        -   `INVALID_INPUT` (400): `{"error_code": "INVALID_INPUT", "message": "Nieprawidłowe dane wejściowe."}`
        -   `LOGIN_FAILED` (500): `{"error_code": "LOGIN_FAILED", "message": "Wystąpił błąd serwera."}`
-   **Akcje po odpowiedzi**:
    -   **Sukces**: `isLoading` ustawiane na `false`. Funkcja `login` z `useAuth` aktualizuje globalny stan uwierzytelnienia. Opcjonalnie wyświetlany toast o sukcesie. Użytkownik jest przekierowywany na stronę główną (`/`) lub inną domyślną stronę po zalogowaniu (np. `/account`).
    -   **Błąd**: `isLoading` ustawiane na `false`. Komunikat błędu z `ApiErrorResponseDto.message` jest wyświetlany za pomocą `NotificationContext` (toast). Użytkownik pozostaje na stronie logowania.

## 8. Interakcje użytkownika

1.  **Wprowadzanie danych w pole Email**:
    -   Użytkownik wpisuje swój adres email.
    -   React Hook Form aktualizuje stan pola i przeprowadza walidację formatu w locie lub po utracie fokusu.
2.  **Wprowadzanie danych w pole Hasło**:
    -   Użytkownik wpisuje swoje hasło.
    -   React Hook Form aktualizuje stan pola.
3.  **Kliknięcie przycisku "Zaloguj się"**:
    -   React Hook Form uruchamia walidację wszystkich pól (email i hasło muszą być wypełnione, email musi mieć poprawny format).
    -   **Jeśli walidacja frontentowa nie powiedzie się**: Komunikaty o błędach są wyświetlane przy odpowiednich polach. Wysyłanie do API jest blokowane.
    -   **Jeśli walidacja frontentowa powiedzie się**:
        -   Stan `isLoading` w `LoginPage` jest ustawiany na `true`.
        -   Przycisk "Zaloguj się" jest deaktywowany i/lub wyświetla wskaźnik ładowania.
        -   Wysyłane jest żądanie `POST /auth/login` z danymi `email` i `password`.
        -   Po otrzymaniu odpowiedzi z API:
            -   **Sukces (200 OK)**: `isLoading` jest ustawiane na `false`. Globalny stan uwierzytelnienia jest aktualizowany. Użytkownik jest przekierowywany na stronę główną lub panel konta.
            -   **Błąd (400, 401, 500)**: `isLoading` jest ustawiane na `false`. Odpowiedni komunikat błędu jest wyświetlany jako toast. Użytkownik pozostaje na stronie logowania.
4.  **Kliknięcie linku "Nie masz konta? Zarejestruj się"**:
    -   Użytkownik jest przekierowywany na stronę rejestracji (`/register`).

## 9. Warunki i walidacja

Walidacja danych wejściowych jest kluczowa dla bezpieczeństwa i poprawnego działania procesu logowania.

### Walidacja Frontend (React Hook Form w `LoginForm`):
-   **Pole Email**:
    -   **Warunek**: Pole nie może być puste (wymagane).
    -   **Warunek**: Wartość musi być poprawnym formatem adresu email (np. przy użyciu wbudowanego walidatora RHF lub regex).
    -   **Stan interfejsu**: Jeśli warunki nie są spełnione, przy polu email wyświetlany jest komunikat błędu (np. "Adres email jest wymagany", "Nieprawidłowy format adresu email").
-   **Pole Hasło**:
    -   **Warunek**: Pole nie może być puste (wymagane).
    -   **Stan interfejsu**: Jeśli warunek nie jest spełniony, przy polu hasła wyświetlany jest komunikat błędu (np. "Hasło jest wymagane").

### Przycisk Wyślij (`SubmitButton`):
-   **Warunek**: Przycisk jest nieaktywny (`disabled`), gdy `isLoading` jest `true` (trwa komunikacja z API) lub gdy formularz nie przeszedł walidacji frontentowej (np. jedno z pól jest puste).

## 10. Obsługa błędów

-   **Błędy walidacji frontentowej**:
    -   Obsługiwane przez React Hook Form. Komunikaty są wyświetlane dynamicznie przy polach, których walidacja nie powiodła się.
    -   Format: Czerwony tekst po prawej stronie pola (zgodnie z wcześniejszymi ustaleniami) lub pod polem, w zależności od projektu UI.

-   **Błędy z API (po stronie serwera)**:
    -   Przechwytywane w funkcji obsługującej wysyłanie formularza w `LoginPage` (lub w funkcji `login` z `useAuth`).
    -   Na podstawie `error_code` z `ApiErrorResponseDto`:
        -   `INVALID_CREDENTIALS` (401): Wyświetlenie komunikatu toast: "Nieprawidłowy email lub hasło."
        -   `USER_INACTIVE` (401): Wyświetlenie komunikatu toast: "Twoje konto jest nieaktywne. Skontaktuj się z administratorem."
        -   `INVALID_INPUT` (400): Wyświetlenie komunikatu toast: "Wprowadzone dane są nieprawidłowe. Prosimy sprawdzić formularz."
        -   `LOGIN_FAILED` (500) lub inne błędy serwera: Wyświetlenie ogólnego komunikatu toast: "Wystąpił nieoczekiwany błąd podczas logowania. Spróbuj ponownie później."
    -   Po każdym błędzie API, stan `isLoading` jest ustawiany na `false`.

-   **Błędy sieciowe**:
    -   Obsługiwane w logice serwisu API lub w `catch` bloku wywołania API.
    -   Wyświetlenie komunikatu toast: "Błąd połączenia. Sprawdź swoje połączenie internetowe i spróbuj ponownie."
    -   Ustawienie `isLoading` na `false`.

-   **Użytkownik już zalogowany**:
    -   W `useEffect` komponentu `LoginPage`, przy użyciu danych z `AuthContext` (np. `currentUser` lub `isAuthenticated`).
    -   Jeśli użytkownik jest już zalogowany, automatyczne przekierowanie na stronę główną (`/`) lub panel konta (`/account`) za pomocą `useNavigate` z `react-router-dom`.

## 11. Kroki implementacji

1.  **Utworzenie struktury plików**:
    -   Utwórz plik `src/pages/auth/LoginPage.tsx` (lub `.jsx`).
    -   Utwórz plik dla komponentu formularza `src/components/auth/LoginForm.tsx`.
    -   Upewnij się, że istnieją reużywalne komponenty pól (`TextInput`, `Button`) w `src/components/common/` lub utwórz je.

2.  **Implementacja komponentu `LoginPage`**:
    -   Zdefiniuj podstawowy layout strony (tytuł "Logowanie", miejsce na formularz, link do rejestracji).
    -   Zaimplementuj stany lokalne `isLoading: boolean` i `apiError: string | null`.
    -   Zintegruj z `AuthContext` (przez hook `useAuth`) w celu:
        -   Sprawdzenia, czy użytkownik jest już zalogowany (w `useEffect` i przekierowania).
        -   Uzyskania funkcji `login(credentials: LoginUserRequestDto)`.
    -   Zintegruj z `NotificationContext` (przez hook `useNotifications`) do wyświetlania toastów.
    -   Zaimplementuj funkcję `handleLoginSubmit(data: LoginFormData)`:
        -   Ustaw `isLoading` na `true`.
        -   Wywołaj `auth.login(data)`.
        -   W bloku `then/catch` (lub `async/await` z `try/catch`):
            -   **Sukces**: Wywołaj `auth.setCurrentUser()` (lub podobne, co robi funkcja `login` w kontekście), wyświetl toast sukcesu, przekieruj użytkownika (np. `navigate('/')`).
            -   **Błąd**: Pobierz `error_code` i `message` z odpowiedzi błędu, wyświetl odpowiedni toast, ustaw `apiError` jeśli to błąd ogólny.
        -   Na końcu (w `finally` lub obu gałęziach) ustaw `isLoading` na `false`.
    -   Renderuj komponent `LoginForm`, przekazując `onSubmit={handleLoginSubmit}` i `isLoading={isLoading}`.
    -   Dodaj link `react-router-dom Link` do strony rejestracji (`/register`).

3.  **Implementacja komponentu `LoginForm`**:
    -   Zainicjuj React Hook Form (`useForm<LoginFormData>`).
    -   Zdefiniuj zasady walidacji dla pól `email` i `password`.
    -   Renderuj komponenty pól (`EmailInput`, `PasswordInput`), przekazując im `register`, `errors` z RHF.
    -   Renderuj `SubmitButton`, przekazując `isLoading` i `label`.
    -   Podłącz funkcję `handleSubmit` z RHF do zdarzenia `onSubmit` elementu `<form>`.

4.  **Implementacja lub dostosowanie komponentów pól (`TextInput`, `Button`)**:
    -   Upewnij się, że akceptują `register` i `errors` dla integracji z RHF.
    -   Upewnij się, że `Button` poprawnie obsługuje stan `disabled` i `isLoading`.
    -   Zastosuj odpowiednie style Bootstrap 5.

5.  **Konfiguracja routingu**:
    -   Dodaj ścieżkę `/login` w głównym pliku routingu aplikacji (np. `src/routes/index.tsx`), mapując ją do komponentu `LoginPage`.

6.  **Serwis API (`authService`)**:
    -   Upewnij się, że istnieje funkcja (np. `loginUser(credentials: LoginUserRequestDto): Promise<LoginUserResponseDto>`) w serwisie (np. `src/services/authService.ts`).
    -   Funkcja ta powinna wykonywać żądanie `POST` na `/auth/login`, poprawnie obsługiwać typy i rzucać błędy w przypadku problemów sieciowych lub nieudanych odpowiedzi HTTP, które mogą być przechwycone w komponencie.

7.  **Styling**:
    -   Zastosuj klasy Bootstrap 5 dla layoutu strony i elementów formularza, zapewniając spójny wygląd z resztą aplikacji.
    -   Upewnij się, że komunikaty walidacyjne są czytelne i poprawnie umiejscowione.

8.  **Testowanie**:
    -   Testy jednostkowe dla logiki walidacji w `LoginForm` (jeśli jest złożona, choć RHF upraszcza to).
    -   Testy komponentów dla `LoginPage` i `LoginForm` (np. sprawdzanie renderowania, interakcji, stanu `disabled` przycisku).
    -   Testy integracyjne dla przepływu logowania, włączając interakcję z mockowanym `AuthContext` i serwisem API.
    -   Testy E2E dla pełnego scenariusza logowania użytkownika.
    -   Testy dostępności (A11y).

9.  **Dostępność (A11y)**:
    -   Upewnij się, że wszystkie pola formularza mają powiązane etykiety (`<label htmlFor="...">`).
    -   Komunikaty błędów są powiązane z polami (np. przez `aria-describedby`).
    -   Stany fokusu dla elementów interaktywnych są wyraźne.
    -   Nawigacja za pomocą klawiatury jest w pełni funkcjonalna.

10. **Dokumentacja**: Zaktualizuj wszelką relevantną dokumentację projektu. 