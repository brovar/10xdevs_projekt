# Plan implementacji widoku CreateOfferPage

## 1. Przegląd
Widok CreateOfferPage umożliwia użytkownikom z rolą Sprzedającego dodawanie nowych ofert produktów do platformy. Formularz pozwala na wprowadzenie wszystkich wymaganych danych: tytułu, opisu, ceny, ilości, kategorii oraz opcjonalnego zdjęcia produktu. Interfejs zapewnia intuicyjne prowadzenie użytkownika przez proces tworzenia oferty, z czytelną walidacją pól i obsługą przesyłania plików.

## 2. Routing widoku
Widok będzie dostępny pod ścieżką: `/offers/create`. Dostęp do tej strony powinien być ograniczony tylko do zalogowanych użytkowników z rolą Sprzedającego.

## 3. Struktura komponentów
```
CreateOfferPage
└── OfferForm
    ├── TextInput (title)
    ├── TextArea (description)
    ├── NumberInput (price)
    ├── NumberInput (quantity)
    ├── SelectInput (category)
    ├── FileUploadInput (image)
    ├── ValidationError
    └── Button (submit, cancel)
```

## 4. Szczegóły komponentów
### CreateOfferPage
- Opis komponentu: Główny komponent strony, zawierający formularz tworzenia oferty oraz obsługujący logikę nawigacji.
- Główne elementy: Nagłówek strony, komponent OfferForm, przyciski akcji.
- Obsługiwane interakcje: Przekierowanie po pomyślnym utworzeniu oferty lub anulowaniu akcji.
- Obsługiwana walidacja: Sprawdzenie uprawnień użytkownika (rola Sprzedającego).
- Typy: Nie wymaga specjalnych typów.
- Propsy: Brak - komponent najwyższego poziomu.

### OfferForm
- Opis komponentu: Główny formularz do wprowadzania danych oferty z obsługą walidacji i przesyłania danych.
- Główne elementy: Komponenty pól formularza (TextInput, TextArea, NumberInput, SelectInput, FileUploadInput), przyciski akcji.
- Obsługiwane interakcje: 
  - onSubmit: Walidacja i wysłanie formularza
  - onChange: Aktualizacja stanu formularza przy zmianie pól
  - onCancel: Anulowanie tworzenia oferty
- Obsługiwana walidacja:
  - Wymagalność pól (tytuł, cena, kategoria)
  - Poprawność wartości liczbowych (cena > 0, ilość >= 0)
  - Poprawność formatu i rozmiaru pliku zdjęcia
- Typy: CreateOfferFormData, CreateOfferFormErrors, CategoryDTO[]
- Propsy: onSuccess, onCancel

### TextInput
- Opis komponentu: Reużywalny komponent dla pojedynczego pola tekstowego.
- Główne elementy: Label, input, komunikat błędu.
- Obsługiwane interakcje: onChange, onBlur
- Obsługiwana walidacja: Wymagalność, długość tekstu.
- Typy: TextInputProps
- Propsy: label, name, value, onChange, onBlur, error, required, placeholder

### TextArea
- Opis komponentu: Reużywalny komponent dla wieloliniowego pola tekstowego.
- Główne elementy: Label, textarea, komunikat błędu.
- Obsługiwane interakcje: onChange, onBlur
- Obsługiwana walidacja: Opcjonalność, maksymalna długość tekstu.
- Typy: TextAreaProps
- Propsy: label, name, value, onChange, onBlur, error, required, placeholder, rows

### NumberInput
- Opis komponentu: Reużywalny komponent dla pola liczbowego z obsługą wartości dziesiętnych i całkowitych.
- Główne elementy: Label, input (typ number lub text), komunikat błędu.
- Obsługiwane interakcje: onChange, onBlur
- Obsługiwana walidacja: Wymagalność, wartość minimalna, format liczbowy.
- Typy: NumberInputProps
- Propsy: label, name, value, onChange, onBlur, error, required, min, step, isDecimal, placeholder

### SelectInput
- Opis komponentu: Reużywalny komponent dla pola wyboru z listy rozwijanej.
- Główne elementy: Label, select, opcje, komunikat błędu.
- Obsługiwane interakcje: onChange, onBlur
- Obsługiwana walidacja: Wymagalność wyboru.
- Typy: SelectInputProps, OptionType[]
- Propsy: label, name, value, options, onChange, onBlur, error, required, placeholder

### FileUploadInput
- Opis komponentu: Reużywalny komponent do przesyłania plików ze wsparciem dla podglądu obrazu.
- Główne elementy: Label, input file, przycisk upload, podgląd obrazu, przycisk usuwania, komunikat błędu.
- Obsługiwane interakcje: onChange, onRemove
- Obsługiwana walidacja: Format pliku (PNG, JPEG, WebP), maksymalny rozmiar obrazu (1024x768px).
- Typy: FileInputProps, File
- Propsy: label, name, onChange, onRemove, error, accept, maxSize, preview

### ValidationError
- Opis komponentu: Komponent do wyświetlania komunikatów o błędach walidacji.
- Główne elementy: Tekst błędu z odpowiednim formatowaniem.
- Obsługiwane interakcje: Brak.
- Obsługiwana walidacja: Brak.
- Typy: ValidationErrorProps
- Propsy: message

### Button
- Opis komponentu: Reużywalny komponent przycisku.
- Główne elementy: Button z odpowiednim stylem i treścią.
- Obsługiwane interakcje: onClick
- Obsługiwana walidacja: Brak.
- Typy: ButtonProps
- Propsy: text, type, variant, onClick, disabled, isLoading

## 5. Typy

### Typy modelu danych (DTO)
```typescript
// Typy zdefiniowane w schemacie API
enum OfferStatus {
  ACTIVE = "active",
  INACTIVE = "inactive",
  SOLD = "sold",
  MODERATED = "moderated",
  ARCHIVED = "archived",
  DELETED = "deleted"
}

// DTO dla kategorii
interface CategoryDTO {
  id: number;
  name: string;
}

// DTO dla tworzenia oferty (wysyłane do API)
interface CreateOfferRequest {
  title: string;
  description?: string;
  price: string; // Decimal jako string
  quantity: number;
  category_id: number;
  // obraz jest przesyłany jako część FormData
}

// DTO dla odpowiedzi z API przy tworzeniu oferty
interface OfferSummaryDTO {
  id: string; // UUID
  seller_id: string; // UUID
  category_id: number;
  title: string;
  price: string; // Decimal jako string
  image_filename: string | null;
  quantity: number;
  status: OfferStatus;
  created_at: string; // ISO date string
}

// DTO dla błędu z API
interface ApiError {
  error_code: string;
  message: string;
  details?: any;
}
```

### Typy komponentów (ViewModels)
```typescript
// Model danych formularza
interface CreateOfferFormData {
  title: string;
  description: string;
  price: string; // String dla obsługi inputu
  quantity: string; // String dla obsługi inputu
  categoryId: string; // String dla obsługi selecta
  image: File | null;
  imagePreview: string | null; // URL lub Base64 dla podglądu
}

// Model błędów formularza
interface CreateOfferFormErrors {
  title?: string;
  description?: string;
  price?: string;
  quantity?: string;
  categoryId?: string;
  image?: string;
  form?: string; // Ogólny błąd formularza
}

// Props dla komponentów formularza
interface TextInputProps {
  label: string;
  name: string;
  value: string;
  onChange: (name: string, value: string) => void;
  onBlur?: () => void;
  error?: string;
  required?: boolean;
  placeholder?: string;
}

interface TextAreaProps extends TextInputProps {
  rows?: number;
}

interface NumberInputProps {
  label: string;
  name: string;
  value: string;
  onChange: (name: string, value: string) => void;
  onBlur?: () => void;
  error?: string;
  required?: boolean;
  min?: number;
  step?: string;
  isDecimal?: boolean;
  placeholder?: string;
}

interface OptionType {
  value: string;
  label: string;
}

interface SelectInputProps {
  label: string;
  name: string;
  value: string;
  options: OptionType[];
  onChange: (name: string, value: string) => void;
  onBlur?: () => void;
  error?: string;
  required?: boolean;
  placeholder?: string;
}

interface FileInputProps {
  label: string;
  name: string;
  onChange: (file: File | null) => void;
  onRemove?: () => void;
  error?: string;
  accept?: string;
  maxSize?: number;
  preview?: string | null;
}

interface ValidationErrorProps {
  message?: string;
}

interface ButtonProps {
  text: string;
  type?: "button" | "submit" | "reset";
  variant?: "primary" | "secondary" | "danger" | "success" | "outline-primary";
  onClick?: () => void;
  disabled?: boolean;
  isLoading?: boolean;
}
```

## 6. Zarządzanie stanem

Do zarządzania stanem formularza najlepiej wykorzystać niestandardowy hook:

```typescript
const useCreateOfferForm = () => {
  // Stan formularza
  const [formData, setFormData] = useState<CreateOfferFormData>({
    title: '',
    description: '',
    price: '',
    quantity: '1', // Wartość domyślna
    categoryId: '',
    image: null,
    imagePreview: null
  });
  
  // Stan błędów walidacji
  const [errors, setErrors] = useState<CreateOfferFormErrors>({});
  
  // Stan procesu wysyłania
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  
  // Obsługa zmian w polach tekstowych i liczbowych
  const handleInputChange = (name: string, value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    // Opcjonalne czyszczenie błędów przy zmianie wartości
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };
  
  // Obsługa uploadu pliku
  const handleFileChange = (file: File | null) => {
    if (file) {
      // Generowanie podglądu
      const imagePreview = URL.createObjectURL(file);
      setFormData(prev => ({ ...prev, image: file, imagePreview }));
    } else {
      // Czyszczenie pliku
      setFormData(prev => ({ ...prev, image: null, imagePreview: null }));
    }
    
    // Czyszczenie błędu
    if (errors.image) {
      setErrors(prev => ({ ...prev, image: undefined }));
    }
  };
  
  // Walidacja formularza przed wysłaniem
  const validateForm = (): boolean => {
    const newErrors: CreateOfferFormErrors = {};
    
    // Walidacja tytułu
    if (!formData.title.trim()) {
      newErrors.title = "Tytuł jest wymagany";
    }
    
    // Walidacja ceny
    if (!formData.price) {
      newErrors.price = "Cena jest wymagana";
    } else {
      const priceValue = parseFloat(formData.price);
      if (isNaN(priceValue) || priceValue <= 0) {
        newErrors.price = "Cena musi być liczbą większą od 0";
      }
    }
    
    // Walidacja ilości
    if (formData.quantity) {
      const quantityValue = parseInt(formData.quantity, 10);
      if (isNaN(quantityValue) || quantityValue < 0) {
        newErrors.quantity = "Ilość musi być liczbą nieujemną";
      }
    }
    
    // Walidacja kategorii
    if (!formData.categoryId) {
      newErrors.categoryId = "Kategoria jest wymagana";
    }
    
    // Walidacja obrazu (jeśli został wybrany)
    if (formData.image) {
      // Walidacja typu pliku - może być realizowana na poziomie komponentu
      // Walidacja rozmiaru - może być realizowana na poziomie komponentu
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // Wysyłanie formularza
  const submitForm = async () => {
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    setApiError(null);
    
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('title', formData.title);
      if (formData.description) {
        formDataToSend.append('description', formData.description);
      }
      formDataToSend.append('price', formData.price);
      formDataToSend.append('quantity', formData.quantity || '1');
      formDataToSend.append('category_id', formData.categoryId);
      
      if (formData.image) {
        formDataToSend.append('image', formData.image);
      }
      
      const response = await fetch('/offers', {
        method: 'POST',
        body: formDataToSend,
        // Brak nagłówka 'Content-Type' - zostanie ustawiony automatycznie dla FormData
      });
      
      if (!response.ok) {
        const errorData: ApiError = await response.json();
        throw new Error(errorData.message || 'Wystąpił błąd podczas tworzenia oferty');
      }
      
      const newOffer: OfferSummaryDTO = await response.json();
      setIsSuccess(true);
      return newOffer;
    } catch (error) {
      setApiError(error.message || 'Wystąpił nieznany błąd');
      return null;
    } finally {
      setIsSubmitting(false);
    }
  };
  
  return {
    formData,
    errors,
    isSubmitting,
    isSuccess,
    apiError,
    handleInputChange,
    handleFileChange,
    validateForm,
    submitForm,
  };
};
```

Dodatkowo potrzebny będzie hook do pobierania listy kategorii:

```typescript
const useCategoriesList = () => {
  const [categories, setCategories] = useState<CategoryDTO[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await fetch('/categories');
        
        if (!response.ok) {
          throw new Error('Nie udało się pobrać kategorii');
        }
        
        const data = await response.json();
        setCategories(data.items || []);
      } catch (error) {
        setError(error.message || 'Wystąpił błąd podczas pobierania kategorii');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchCategories();
  }, []);
  
  return { categories, isLoading, error };
};
```

## 7. Integracja API

### Pobieranie listy kategorii
```typescript
// GET /categories
// Użycie w komponencie:
const { categories, isLoading } = useCategoriesList();

// Mapowanie kategorii do formatu wymaganego przez SelectInput
const categoryOptions = categories.map(cat => ({
  value: cat.id.toString(),
  label: cat.name
}));
```

### Tworzenie oferty
```typescript
// POST /offers
// Format: multipart/form-data
// Użycie w komponencie:
const { submitForm, isSubmitting, isSuccess } = useCreateOfferForm();

const handleSubmit = async (e) => {
  e.preventDefault();
  const newOffer = await submitForm();
  if (newOffer) {
    // Przekierowanie do listy ofert lub szczegółów nowej oferty
    navigate('/seller/offers');
  }
};
```

## 8. Interakcje użytkownika

1. **Wprowadzanie danych do pól formularza**
   - Użytkownik wpisuje tytuł, opis, cenę, ilość
   - System aktualizuje stan formularza i czyści błędy walidacji dla zmienionych pól

2. **Wybór kategorii z listy rozwijanej**
   - Użytkownik wybiera kategorię z dostępnych opcji
   - System aktualizuje stan formularza i czyści błąd walidacji dla kategorii

3. **Upload zdjęcia**
   - Użytkownik klika przycisk "Wybierz plik" i wybiera obraz
   - System waliduje typ pliku i rozmiar
   - System generuje podgląd obrazu i aktualizuje stan formularza
   - Jeśli plik jest nieprawidłowy, system wyświetla odpowiedni komunikat błędu

4. **Usunięcie zdjęcia**
   - Użytkownik klika przycisk "Usuń" przy podglądzie zdjęcia
   - System usuwa zdjęcie ze stanu formularza i czyści podgląd

5. **Walidacja formularza (blur)**
   - Użytkownik przechodzi do następnego pola (blur)
   - System waliduje opuszczone pole i wyświetla błąd, jeśli występuje

6. **Przesłanie formularza**
   - Użytkownik klika przycisk "Zapisz"
   - System przeprowadza walidację wszystkich pól
   - Jeśli walidacja się nie powiedzie, system wyświetla błędy przy odpowiednich polach
   - Jeśli walidacja się powiedzie, system wysyła dane do API
   - Podczas wysyłania system wyświetla wskaźnik ładowania
   - Po sukcesie system przekierowuje użytkownika do listy ofert
   - W przypadku błędu API system wyświetla komunikat błędu

7. **Anulowanie tworzenia oferty**
   - Użytkownik klika przycisk "Anuluj"
   - System przekierowuje użytkownika do listy ofert bez zapisywania danych

## 9. Warunki i walidacja

### Walidacja pól formularza

1. **Tytuł**
   - Warunek: Pole jest wymagane
   - Komponent: TextInput
   - Efekt UI: Czerwony komunikat błędu "Tytuł jest wymagany" przy pustym polu

2. **Opis**
   - Warunek: Pole jest opcjonalne
   - Komponent: TextArea
   - Brak specjalnej walidacji

3. **Cena**
   - Warunki:
     - Pole jest wymagane
     - Wartość musi być liczbą
     - Wartość musi być większa od 0
   - Komponent: NumberInput
   - Efekty UI:
     - Czerwony komunikat "Cena jest wymagana" przy pustym polu
     - Czerwony komunikat "Cena musi być liczbą większą od 0" przy nieprawidłowej wartości

4. **Ilość**
   - Warunki:
     - Pole może być puste (domyślnie 1)
     - Wartość musi być liczbą całkowitą
     - Wartość musi być nieujemna (>= 0)
   - Komponent: NumberInput
   - Efekt UI: Czerwony komunikat "Ilość musi być liczbą nieujemną" przy nieprawidłowej wartości

5. **Kategoria**
   - Warunek: Pole jest wymagane
   - Komponent: SelectInput
   - Efekt UI: Czerwony komunikat "Kategoria jest wymagana" przy braku wyboru

6. **Zdjęcie**
   - Warunki:
     - Pole jest opcjonalne
     - Plik musi być obrazem (PNG, JPEG, WebP)
     - Wymiary obrazu nie mogą przekraczać 1024x768px
   - Komponent: FileUploadInput
   - Efekty UI:
     - Czerwony komunikat "Nieprawidłowy format pliku" przy złym typie pliku
     - Czerwony komunikat "Obraz nie może przekraczać wymiarów 1024x768px" przy zbyt dużym obrazie

### Walidacja formularza przed wysłaniem
- Wszystkie powyższe warunki są sprawdzane
- Jeśli którykolwiek warunek nie jest spełniony, formularz nie zostanie wysłany
- Przy wysyłaniu system wyświetla wskaźnik ładowania (disabled na przycisku "Zapisz")

## 10. Obsługa błędów

### Obsługa błędów API

1. **401 Unauthorized (NOT_AUTHENTICATED)**
   - Przekierowanie do strony logowania
   - Komunikat: "Musisz być zalogowany, aby utworzyć ofertę"

2. **403 Forbidden (INSUFFICIENT_PERMISSIONS)**
   - Przekierowanie do strony głównej
   - Komunikat: "Nie masz uprawnień do tworzenia ofert. Tylko sprzedawcy mogą tworzyć oferty."

3. **400 Bad Request**
   - **INVALID_INPUT**: Mapowanie błędów do odpowiednich pól formularza
   - **INVALID_FILE_TYPE**: "Nieprawidłowy format pliku. Dozwolone formaty: PNG, JPEG, WebP."
   - **FILE_TOO_LARGE**: "Plik jest zbyt duży. Maksymalny rozmiar to 1024x768px."
   - **INVALID_PRICE**: "Nieprawidłowa cena. Cena musi być większa od 0."
   - **INVALID_QUANTITY**: "Nieprawidłowa ilość. Ilość nie może być ujemna."

4. **404 Not Found (CATEGORY_NOT_FOUND)**
   - Komunikat przy polu kategorii: "Wybrana kategoria nie istnieje"

5. **500 Internal Server Error**
   - **CREATE_FAILED**: "Wystąpił błąd podczas tworzenia oferty. Spróbuj ponownie później."
   - **FILE_UPLOAD_FAILED**: "Nie udało się przesłać pliku. Spróbuj ponownie później."

### Obsługa błędów połączenia
- Komunikat: "Nie można połączyć się z serwerem. Sprawdź swoje połączenie internetowe i spróbuj ponownie."
- Przycisk "Spróbuj ponownie"

## 11. Kroki implementacji

1. **Utworzenie komponentów bazowych**
   - Implementacja reużywalnych komponentów formularza (TextInput, TextArea, NumberInput, SelectInput, FileUploadInput, Button, ValidationError)
   - Każdy komponent powinien obsługiwać odpowiednie propsy i stylowanie zgodne z Bootstrap 5

2. **Implementacja hooków niestandardowych**
   - Implementacja `useCreateOfferForm` do zarządzania stanem formularza
   - Implementacja `useCategoriesList` do pobierania listy kategorii

3. **Implementacja komponentu formularza (OfferForm)**
   - Integracja komponentów bazowych
   - Podłączenie hooków zarządzania stanem
   - Implementacja funkcji obsługi zdarzeń (onChange, onSubmit)
   - Implementacja logiki walidacji
   - Implementacja logiki wysyłania formularza

4. **Implementacja głównego komponentu widoku (CreateOfferPage)**
   - Utworzenie layoutu strony
   - Integracja komponentu OfferForm
   - Implementacja logiki nawigacji (przekierowania po sukcesie/anulowaniu)
   - Obsługa ograniczenia dostępu (sprawdzenie roli użytkownika)

5. **Testowanie**
   - Testowanie walidacji pól formularza
   - Testowanie uploadu plików
   - Testowanie integracji z API
   - Testowanie obsługi błędów
   - Testowanie responsywności i dostępności

6. **Finalizacja i dokumentacja**
   - Dodanie komentarzy do kodu
   - Weryfikacja zgodności z wymaganiami PRD
   - Optymalizacja wydajności (np. memo dla komponentów, które często się renderują) 