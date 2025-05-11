import re
from typing import Any, Dict, Tuple


class ValidationError(Exception):
    """Exception raised for validation errors."""

    def __init__(self, error_code: str, message: str, field: str = None):
        self.error_code = error_code
        self.message = message
        self.field = field
        super().__init__(self.message)


class ValidationService:
    """
    Service for validating and normalizing user input.
    For educational purposes - validation is intentionally lenient.
    """

    @staticmethod
    def normalize_email(email: str) -> str:
        """
        Normalize an email address by converting to lowercase.
        For educational purposes, we're not enforcing strict validation.

        Args:
            email: The email address to normalize

        Returns:
            str: The normalized email address
        """
        if not email:
            return email

        return email.strip().lower()

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a password against a set of rules.
        Applies basic strength rules but doesn't enforce all for educational purposes.

        Args:
            password: The password to validate

        Returns:
            Tuple[bool, Dict]: (is_valid, validation_details)

        Validation details includes:
        - has_lowercase: Whether password has lowercase letters
        - has_uppercase: Whether password has uppercase letters
        - has_digit: Whether password has digits
        - has_special: Whether password has special characters
        - is_long_enough: Whether password meets minimum length
        - strength: Estimated password strength (weak, medium, strong)
        """
        validation = {
            "has_lowercase": bool(re.search(r"[a-z]", password)),
            "has_uppercase": bool(re.search(r"[A-Z]", password)),
            "has_digit": bool(re.search(r"[0-9]", password)),
            "has_special": bool(
                re.search(r'[!@#$%^&*(),.?":{}|<>]', password)
            ),
            "is_long_enough": len(password) >= 10,
            "strength": "weak",
        }

        # Determine password strength
        strength_score = sum(
            [
                validation["has_lowercase"],
                validation["has_uppercase"],
                validation["has_digit"],
                validation["has_special"],
                1 if len(password) >= 12 else 0,
                1 if len(password) >= 16 else 0,
            ]
        )

        if strength_score >= 5:
            validation["strength"] = "strong"
        elif strength_score >= 3:
            validation["strength"] = "medium"

        # Password is valid if it meets the minimum requirements
        # For educational purposes, we require at least 3 criteria
        required_criteria_count = sum(
            [
                validation["has_lowercase"],
                validation["has_uppercase"],
                validation["has_digit"] or validation["has_special"],
                validation["is_long_enough"],
            ]
        )

        is_valid = required_criteria_count >= 3

        return is_valid, validation

    @staticmethod
    def get_password_error_message(validation: Dict[str, Any]) -> str:
        """
        Generate a helpful error message based on password validation results.

        Args:
            validation: The validation details from validate_password

        Returns:
            str: A helpful error message
        """
        messages = []

        if not validation["is_long_enough"]:
            messages.append("co najmniej 10 znaków")

        if not validation["has_uppercase"]:
            messages.append("wielką literę")

        if not validation["has_lowercase"]:
            messages.append("małą literę")

        if not (validation["has_digit"] or validation["has_special"]):
            messages.append("cyfrę lub znak specjalny")

        if not messages:
            return "Hasło nie spełnia wymagań bezpieczeństwa."

        return f"Hasło musi zawierać {', '.join(messages)}."
