# Plan implementacji widoku RegisterPage

## 1. Przegląd
Widok `RegisterPage` umożliwia nowym użytkownikom tworzenie konta w systemie Steambay. Użytkownik może zarejestrować się jako Kupujący (Buyer) lub Sprzedający (Seller), podając swój adres email, hasło (zgodne z polityką bezpieczeństwa) oraz potwierdzając hasło. Po pomyślnej rejestracji, użytkownik jest informowany o sukcesie i może przejść do strony logowania. Widok obsługuje walidację pól formularza oraz wyświetla odpowiednie komunikaty o błędach, zarówno te pochodzące z walidacji frontentowej, jak i z odpowiedzi API backendu.

## 2. Routing widoku
- **Ścieżka:** `/register`

## 3. Struktura komponentów
```
RegisterPage (strona/kontener)
├── Header (komponent layoutu)
├── RegistrationForm (komponent formularza)
│   ├── EmailInput (pole email)
│   ├── PasswordInput (pole hasła)
│   │   └── PasswordPolicyDisplay (wyświetlacz polityki haseł)
│   ├── ConfirmPasswordInput (pole potwierdzenia hasła)
│   ├── RoleSelect (wybór roli)
│   ├── SubmitButton (przycisk wysłania formularza)
│   └── Link (do strony logowania)
├── Footer (komponent layoutu)
└── (Globalny system powiadomień typu Toast, np. przez Context)
```

## 4. Szczegóły komponentów

### `RegisterPage`
- **Opis komponentu:** Główny komponent strony rejestracji. Odpowiada za logikę wysyłania danych rejestracyjnych do API, obsługę odpowiedzi (sukces/błąd) oraz nawigację po pomyślnej rejestracji.
- **Główne elementy:** Kontener dla `RegistrationForm`, obsługa stanu ładowania i błędów API.
- **Obsługiwane interakcje:** Przekazanie funkcji `onSubmit` do `RegistrationForm`.
- **Obsługiwana walidacja:** Pośrednio, poprzez delegację do `RegistrationForm` i obsługę błędów z API.
- **Typy:**
    - Stan: `isLoading: boolean`, `apiError: string | null`
- **Propsy:** Brak bezpośrednich propsów wpływających na logikę.

### `RegistrationForm`
- **Opis komponentu:** Komponent zawierający formularz rejestracyjny. Wykorzystuje React Hook Form do zarządzania stanem pól, walidacji i procesu wysyłania.
- **Główne elementy:** Pola `EmailInput`, `PasswordInput`, `ConfirmPasswordInput`, `RoleSelect`, przycisk `SubmitButton`, link do strony logowania.
- **Obsługiwane interakcje:** Wprowadzanie danych przez użytkownika, wysłanie formularza.
- **Obsługiwana walidacja:**
    - Email: wymagany, poprawny format email.
    - Hasło: wymagane; min. 10 znaków; musi zawierać małą literę, dużą literę; musi zawierać cyfrę lub znak specjalny.
    - Potwierdź Hasło: wymagane, musi być identyczne z hasłem.
    - Rola: wymagana (wybór "Buyer" lub "Seller").
- **Typy:**
    - Dane formularza (ViewModel): `RegistrationFormData`
    - Typ danych wysyłanych do API: `RegisterUserRequestDto`
- **Propsy:**
    - `onSubmit: (data: RegisterUserRequestDto) => Promise<void>` (funkcja wywoływana po pomyślnej walidacji i wysłaniu formularza)
    - `isLoading: boolean` (do kontrolowania stanu przycisku wysyłania)

### `EmailInput` (lub generyczny `TextInput`)
- **Opis komponentu:** Pole do wprowadzania adresu email.
- **Główne elementy:** `<label>`, `<input type="email">`, kontener na komunikat błędu. Stylowany za pomocą Bootstrap.
- **Obsługiwane interakcje:** Wprowadzanie tekstu.
- **Obsługiwana walidacja:** (przez React Hook Form) Wymagane, poprawny format email.
- **Typy:** Wartość pola: `string`.
- **Propsy:** `name: string`, `label: string`, `register: UseFormRegister<any>`, `errors: FieldErrors`

### `PasswordInput` (dla pola Hasło i Potwierdź Hasło)
- **Opis komponentu:** Pole do wprowadzania hasła. Dla głównego pola hasła może opcjonalnie wyświetlać `PasswordPolicyDisplay`.
- **Główne elementy:** `<label>`, `<input type="password">`, kontener na komunikat błędu. Dla pola "Hasło" może zawierać osadzony `PasswordPolicyDisplay`. Stylowany za pomocą Bootstrap.
- **Obsługiwane interakcje:** Wprowadzanie tekstu.
- **Obsługiwana walidacja:** (przez React Hook Form)
    - Dla "Hasło": Wymagane, zgodność z polityką haseł.
    - Dla "Potwierdź Hasło": Wymagane, zgodność z polem "Hasło".
- **Typy:** Wartość pola: `string`.
- **Propsy:** `name: string`, `label: string`, `register: UseFormRegister<any>`, `errors: FieldErrors`, `watch?: UseFormWatch<any>` (dla walidacji "Potwierdź Hasło" i `PasswordPolicyDisplay`), `getValues?: UseFormGetValues<any>` (dla walidacji "Potwierdź Hasło").

### `PasswordPolicyDisplay`
- **Opis komponentu:** Wyświetla dynamicznie aktualizowaną listę wymagań polityki haseł, wskazując, które z nich są spełnione przez aktualnie wpisywane hasło.
- **Główne elementy:** Lista (`<ul>`) z elementami (`<li>`) dla każdego kryterium polityki haseł. Stylowany za pomocą Bootstrap, umieszczony po prawej stronie pola hasła.
- **Obsługiwane interakcje:** Brak bezpośrednich interakcji, reaguje na zmiany w polu hasła.
- **Obsługiwana walidacja:** Wizualne wskazanie spełnienia/niespełnienia poszczególnych kryteriów.
- **Typy:** Wartość hasła: `string`.
- **Propsy:** `passwordValue: string`

### `RoleSelect` (lub generyczny `SelectInput`)
- **Opis komponentu:** Pole wyboru typu konta (Kupujący/Sprzedający).
- **Główne elementy:** `<label>`, `<select>`, `<option>`. Stylowany za pomocą Bootstrap.
- **Obsługiwane interakcje:** Wybór opcji z listy.
- **Obsługiwana walidacja:** (przez React Hook Form) Wymagane.
- **Typy:** Wartość pola: `"Buyer" | "Seller"`.
- **Propsy:** `name: string`, `label: string`, `options: Array<{ value: string; label: string }>`, `register: UseFormRegister<any>`, `errors: FieldErrors`

### `SubmitButton` (lub generyczny `Button`)
- **Opis komponentu:** Przycisk do wysłania formularza rejestracji.
- **Główne elementy:** `<button type="submit">`. Stylowany za pomocą Bootstrap.
- **Obsługiwane interakcje:** Kliknięcie.
- **Obsługiwana walidacja:** Stan `disabled` zależny od stanu ładowania (`isLoading`) lub stanu walidacji formularza.
- **Typy:** Brak specyficznych.
- **Propsy:** `label: string`, `isLoading: boolean`, `disabled?: boolean`

## 5. Typy

### DTO (Data Transfer Objects - dla komunikacji z API)

-   `RegisterUserRequestDto`:
    ```typescript
    interface RegisterUserRequestDto {
      email: string;
      password: string;
      role: "Buyer" | "Seller"; // Zgodnie z enum UserRole w schemas.py
    }
    ```

-   `RegisterUserResponseDto`:
    ```typescript
    interface RegisterUserResponseDto {
      id: string; // UUID
      email: string;
      role: "Buyer" | "Seller" | "Admin"; // UserRole
      status: "Active" | "Inactive" | "Deleted"; // UserStatus
      first_name?: string | null;
      last_name?: string | null;
      created_at: string; // ISO datetime string
    }
    ```
-   `ApiErrorResponseDto`:
    ```typescript
    interface ApiErrorResponseDto {
      error_code: string;
      message: string;
      detail?: any; // Np. dla błędów walidacji wielu pól
    }
    ```

### ViewModel (dla stanu formularza w komponencie)

-   `RegistrationFormData`:
    ```typescript
    interface RegistrationFormData {
      email: string;
      password: string;
      confirmPassword: string;
      role: "Buyer" | "Seller" | ""; // Pusty string dla wartości początkowej/niewybranej
    }
    ```
-   `RoleOption`:
    ```typescript
    interface RoleOption {
      value: "Buyer" | "Seller";
      label: string; // Np. "Kupujący", "Sprzedający"
    }
    ```

## 6. Zarządzanie stanem

-   **Stan lokalny komponentu `RegisterPage`**:
    -   `isLoading: boolean`: Zarządza wyświetlaniem wskaźnika ładowania podczas komunikacji z API. Inicjalizowany na `false`.
    -   `apiError: string | null`: Przechowuje ogólne komunikaty błędów z API, które nie są specyficzne dla konkretnego pola. Inicjalizowany na `null`.

-   **Stan formularza w `RegistrationForm`**:
    -   Zarządzany przez bibliotekę **React Hook Form**. Biblioteka ta będzie odpowiedzialna za:
        -   Przechowywanie wartości poszczególnych pól (`email`, `password`, `confirmPassword`, `role`).
        -   Śledzenie stanu walidacji każdego pola.
        -   Przechowywanie komunikatów błędów walidacji dla każdego pola.
        -   Obsługę procesu wysyłania formularza (`handleSubmit`).

-   **Stan globalny (przez Context API)**:
    -   `NotificationContext`: Używany do wyświetlania globalnych powiadomień typu toast o sukcesie rejestracji lub o błędach. `RegisterPage` będzie używać hooka dostarczonego przez ten kontekst (np. `useNotifications`) do wywoływania funkcji `addSuccess(message)` lub `addError(message)`.
    -   `AuthContext`: Potencjalnie używany do sprawdzenia, czy użytkownik jest już zalogowany. Jeśli tak, `RegisterPage` może przekierować na stronę główną.

-   **Niestandardowe hooki**:
    -   Dla tego widoku nie przewiduje się tworzenia nowych, specyficznych custom hooków. Wykorzystane zostaną istniejące hooki (np. `useNotifications` z `NotificationContext`, `useNavigate` z `react-router-dom`) oraz funkcjonalności React Hook Form.

## 7. Integracja API

-   **Endpoint**: `POST /auth/register`
-   **Cel**: Rejestracja nowego użytkownika.
-   **Wywołanie**:
    -   Po pomyślnej walidacji formularza po stronie klienta, funkcja `onSubmit` w `RegistrationForm` przekaże przetworzone dane do `RegisterPage`.
    -   `RegisterPage` wywoła funkcję serwisu API (np. `authService.register(data: RegisterUserRequestDto)`), która wykona żądanie `POST`.
-   **Typ żądania (Request Body)**: `RegisterUserRequestDto`
    ```json
    {
      "email": "user@example.com",
      "password": "Password123!",
      "role": "Buyer" // lub "Seller"
    }
    ```
-   **Typy odpowiedzi (Response Body)**:
    -   **Sukces (201 Created)**: `RegisterUserResponseDto`
        ```json
        {
          "id": "uuid-user-id",
          "email": "user@example.com",
          "role": "Buyer",
          "status": "Active",
          "first_name": null,
          "last_name": null,
          "created_at": "timestamp"
        }
        ```
    -   **Błąd**: `ApiErrorResponseDto` (dla kodów 400, 409, 500)
        -   Np. dla `EMAIL_EXISTS` (409):
            ```json
            {
              "error_code": "EMAIL_EXISTS",
              "message": "Użytkownik o podanym adresie email już istnieje."
            }
            ```
        -   Np. dla `PASSWORD_POLICY_VIOLATED` (400):
            ```json
            {
              "error_code": "INVALID_PASSWORD", // Lub PASSWORD_POLICY_VIOLATED zgodnie z opisem API
              "message": "Hasło musi zawierać co najmniej 10 znaków, wielką literę, małą literę."
            }
            ```
-   **Akcje po odpowiedzi**:
    -   **Sukces**: Wyświetlenie powiadomienia toast o sukcesie. Opcjonalne wyczyszczenie formularza. Przekierowanie na stronę logowania (`/login`) lub wyświetlenie wyraźnego linku/przycisku do logowania.
    -   **Błąd**: Wyświetlenie odpowiedniego powiadomienia toast z komunikatem błędu. Jeśli błąd dotyczy konkretnego pola (np. `EMAIL_EXISTS`), można użyć `setError` z React Hook Form, aby wyświetlić błąd przy tym polu.

## 8. Interakcje użytkownika

1.  **Wprowadzanie danych w pole Email**:
    -   Użytkownik wpisuje tekst.
    -   React Hook Form aktualizuje stan pola.
2.  **Wprowadzanie danych w pole Hasło**:
    -   Użytkownik wpisuje tekst.
    -   React Hook Form aktualizuje stan pola.
    -   `PasswordPolicyDisplay` dynamicznie aktualizuje wskazówki dotyczące spełnienia polityki haseł.
3.  **Wprowadzanie danych w pole Potwierdź Hasło**:
    -   Użytkownik wpisuje tekst.
    -   React Hook Form aktualizuje stan pola i waliduje zgodność z polem Hasło.
4.  **Wybór Roli**:
    -   Użytkownik wybiera opcję "Kupujący" lub "Sprzedający" z listy.
    -   React Hook Form aktualizuje stan pola.
5.  **Kliknięcie przycisku "Zarejestruj się"**:
    -   React Hook Form uruchamia walidację wszystkich pól.
    -   **Jeśli walidacja frontentowa nie powiedzie się**: Komunikaty o błędach są wyświetlane przy odpowiednich polach. Wysyłanie do API jest blokowane.
    -   **Jeśli walidacja frontentowa powiedzie się**:
        -   Stan `isLoading` w `RegisterPage` ustawiany jest na `true`.
        -   Przycisk "Zarejestruj się" może zostać zablokowany i/lub wyświetlić wskaźnik ładowania.
        -   Wysyłane jest żądanie `POST /auth/register` z danymi z formularza.
        -   Po otrzymaniu odpowiedzi z API:
            -   **Sukces**: `isLoading` ustawiane na `false`. Wyświetlany jest toast o sukcesie. Użytkownik jest przekierowywany lub widzi link do strony logowania.
            -   **Błąd**: `isLoading` ustawiane na `false`. Wyświetlany jest toast z błędem. Błędy specyficzne dla pól mogą być ustawione w React Hook Form.
6.  **Kliknięcie linku "Masz już konto? Zaloguj się"**:
    -   Użytkownik jest przekierowywany na stronę `/login`.

## 9. Warunki i walidacja

Walidacja będzie realizowana na dwóch poziomach: frontend (React Hook Form) i backend (Pydantic w FastAPI).

### Walidacja Frontend (React Hook Form):

-   **Pole Email (`EmailInput`)**:
    -   **Warunek**: Musi być wypełnione (required).
    -   **Warunek**: Musi być poprawnym formatem adresu email.
    -   **Stan interfejsu**: Jeśli niespełnione, wyświetlany komunikat błędu przy polu.
-   **Pole Hasło (`PasswordInput`)**:
    -   **Warunek**: Musi być wypełnione (required).
    -   **Warunek**: Długość min. 10 znaków.
    -   **Warunek**: Musi zawierać co najmniej jedną małą literę.
    -   **Warunek**: Musi zawierać co najmniej jedną dużą literę.
    -   **Warunek**: Musi zawierać co najmniej jedną cyfrę LUB jeden znak specjalny.
    -   **Stan interfejsu**: Jeśli niespełnione, wyświetlany komunikat błędu przy polu. `PasswordPolicyDisplay` wskazuje niespełnione kryteria.
-   **Pole Potwierdź Hasło (`ConfirmPasswordInput`)**:
    -   **Warunek**: Musi być wypełnione (required).
    -   **Warunek**: Wartość musi być identyczna jak w polu Hasło.
    -   **Stan interfejsu**: Jeśli niespełnione, wyświetlany komunikat błędu przy polu.
-   **Pole Rola (`RoleSelect`)**:
    -   **Warunek**: Musi być wybrane (required).
    -   **Stan interfejsu**: Jeśli niespełnione, wyświetlany komunikat błędu przy polu.

### Komunikaty walidacyjne:
-   Wyświetlane po prawej stronie odpowiedniego pola.
-   Tekst koloru czerwonego.
-   Bez dodatkowych ikon.

### Przycisk Wyślij (`SubmitButton`):
-   Stan `disabled` jeśli formularz nie jest poprawny (według React Hook Form) lub gdy `isLoading` jest `true`.

## 10. Obsługa błędów

-   **Błędy walidacji frontentowej**:
    -   Obsługiwane przez React Hook Form. Komunikaty wyświetlane są dynamicznie przy odpowiednich polach formularza.
    -   Format: Czerwony tekst po prawej stronie pola.

-   **Błędy z API (po stronie serwera)**:
    -   Przechwytywane w `RegisterPage` po wysłaniu żądania.
    -   Na podstawie `error_code` z odpowiedzi API (`ApiErrorResponseDto`):
        -   `EMAIL_EXISTS` (409):
            -   Komunikat toast: "Użytkownik o podanym adresie email już istnieje."
            -   Opcjonalnie: `setError('email', { type: 'server', message: '...' })` w React Hook Form.
        -   `PASSWORD_POLICY_VIOLATED` / `INVALID_PASSWORD` (400):
            -   Komunikat toast: "Hasło nie spełnia wymagań polityki bezpieczeństwa."
            -   Opcjonalnie: `setError('password', { type: 'server', message: '...' })`.
        -   `INVALID_INPUT` (400):
            -   Jeśli `detail` zawiera informacje o polach, spróbuj zmapować do błędów pól w React Hook Form.
            -   W przeciwnym razie, ogólny komunikat toast: "Wprowadzone dane są nieprawidłowe. Sprawdź formularz."
        -   `INVALID_ROLE` (400):
            -   Komunikat toast: "Wybrana rola jest nieprawidłowa." (mniej prawdopodobne przy poprawnym frontendzie).
        -   `REGISTRATION_FAILED` (500) lub inne błędy serwera:
            -   Ogólny komunikat toast: "Wystąpił nieoczekiwany błąd podczas rejestracji. Spróbuj ponownie później."
    -   Wszystkie błędy API powinny również ustawiać `isLoading` na `false`.

-   **Błędy sieciowe**:
    -   Jeśli żądanie do API nie powiedzie się z powodu problemów z siecią (np. brak połączenia).
    -   Obsługiwane w logice serwisu API.
    -   Komunikat toast: "Błąd połączenia. Sprawdź swoje połączenie internetowe i spróbuj ponownie."
    -   Ustawienie `isLoading` na `false`.

-   **Użytkownik już zalogowany**:
    -   W `useEffect` komponentu `RegisterPage`, sprawdzić stan uwierzytelnienia (np. z `AuthContext`).
    -   Jeśli użytkownik jest zalogowany, przekierować go na stronę główną (`/`) lub inną odpowiednią stronę.

## 11. Kroki implementacji

1.  **Utworzenie struktury plików**:
    -   Utwórz plik `src/pages/auth/RegisterPage.jsx` (lub `.tsx`).
    -   Utwórz plik dla komponentu formularza, np. `src/components/auth/RegistrationForm.jsx`.
    -   Przygotuj lub zidentyfikuj reużywalne komponenty pól (`EmailInput`, `PasswordInput`, `RoleSelect`, `SubmitButton`) oraz `PasswordPolicyDisplay` w katalogu `src/components/common/` lub `src/components/shared/forms/`.

2.  **Implementacja komponentu `RegisterPage`**:
    -   Podstawowy layout strony (np. tytuł "Rejestracja").
    -   Implementacja stanu `isLoading` i `apiError`.
    -   Funkcja `handleRegisterSubmit` do wywołania serwisu API.
        -   Obsługa logiki `try/catch` dla wywołania API.
        -   Ustawianie `isLoading` przed i po wywołaniu.
        -   Obsługa odpowiedzi sukcesu (toast, nawigacja/link do logowania).
        -   Obsługa odpowiedzi błędu (mapowanie `error_code` na komunikaty toast, ewentualne przekazanie błędów pól do `RegistrationForm` jeśli to możliwe lub konieczne).
    -   Integracja z `NotificationContext` do wyświetlania toastów.
    -   Integracja z `AuthContext` (jeśli istnieje) do sprawdzenia, czy użytkownik jest już zalogowany i ewentualnego przekierowania.
    -   Renderowanie komponentu `RegistrationForm`, przekazując `onSubmit={handleRegisterSubmit}` i `isLoading={isLoading}`.

3.  **Implementacja komponentu `RegistrationForm`**:
    -   Inicjalizacja React Hook Form (`useForm<RegistrationFormData>`).
    -   Definicja schematu walidacji (np. z Zod lub Yup, lub bezpośrednio w `register` RHF) dla pól: `email`, `password`, `confirmPassword`, `role`.
        -   Walidacja `confirmPassword` powinna sprawdzać zgodność z polem `password` (używając `watch` i `getValues` z RHF).
    -   Renderowanie poszczególnych pól formularza (`EmailInput`, `PasswordInput` itd.), przekazując im odpowiednie `register`, `errors` z RHF.
    -   Implementacja logiki wyświetlania `PasswordPolicyDisplay` obok pola hasła, przekazując aktualną wartość hasła (z `watch`).
    -   Implementacja linku do strony logowania (`/login`).
    -   Podpięcie funkcji `handleSubmit` z RHF do `onSubmit` formularza, która wywoła prop `onSubmit` przekazany z `RegisterPage` z poprawnymi danymi.

4.  **Implementacja komponentów pól (jeśli nie są reużywalne i gotowe)**:
    -   `EmailInput`, `PasswordInput`, `RoleSelect`, `SubmitButton` z odpowiednimi propsami i stylami Bootstrap.
    -   `PasswordPolicyDisplay`: logika sprawdzania poszczególnych kryteriów polityki haseł i ich wizualna prezentacja.

5.  **Konfiguracja routingu**:
    -   Dodaj nową ścieżkę `/register` w głównym pliku routingu aplikacji (np. `src/routes/AppRouter.jsx`), mapując ją do komponentu `RegisterPage`.

6.  **Serwis API**:
    -   Utwórz lub zaktualizuj serwis (np. `src/services/authService.js`) o funkcję `register(data: RegisterUserRequestDto): Promise<RegisterUserResponseDto>`.
    -   Funkcja ta powinna wykonywać żądanie `POST` na `/auth/register` i obsługiwać błędy sieciowe oraz odpowiedzi HTTP inne niż 201.

7.  **Styling**:
    -   Zastosuj klasy Bootstrap 5 do wszystkich elementów formularza i layoutu strony dla spójnego wyglądu.
    -   Upewnij się, że komunikaty walidacyjne i `PasswordPolicyDisplay` są poprawnie umiejscowione (np. po prawej stronie pola hasła).

8.  **Testowanie**:
    -   Testy jednostkowe dla logiki walidacji (jeśli jest bardziej skomplikowana).
    -   Testy komponentów dla `RegistrationForm` i poszczególnych pól.
    -   Testy integracyjne dla przepływu rejestracji, włączając interakcję z mockowanym API.
    -   Testy E2E dla pełnego scenariusza rejestracji.
    -   Testy dostępności.

9.  **Dostępność (A11y)**:
    -   Upewnij się, że wszystkie pola formularza mają powiązane etykiety (`<label htmlFor="...">`).
    -   Komunikaty błędów są powiązane z polami za pomocą `aria-describedby`.
    -   Stany fokusu są wyraźne.
    -   Nawigacja klawiaturą jest w pełni możliwa.

10. **Dokumentacja**:
    -   Komentarze w kodzie dla bardziej skomplikowanych fragmentów.
    -   Aktualizacja dokumentacji projektu, jeśli jest prowadzona.

To kompleksowy plan, który powinien umożliwić sprawne wdrożenie widoku rejestracji. 