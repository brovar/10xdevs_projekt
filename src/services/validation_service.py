import re
from fastapi import HTTPException
from typing import Tuple, Dict, Any, Optional, List
from email_validator import validate_email, EmailNotValidError

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
        Normalize an email address to its canonical form.
        This includes lowercase, and normalization of the domain part.
        
        Args:
            email: The email to normalize
            
        Returns:
            Normalized email address
            
        Raises:
            ValidationError: If the email is invalid
        """
        try:
            # For development purposes, skip domain validation
            valid = validate_email(email, check_deliverability=False)
            return valid.normalized
        except EmailNotValidError as e:
            raise ValidationError(
                error_code="INVALID_EMAIL",
                message=f"Nieprawidłowy adres email: {str(e)}"
            )
    
    @staticmethod
    def validate_password(password: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate a password against security criteria.
        
        Args:
            password: The password to validate
            
        Returns:
            Tuple of (is_valid, details) where details contains information about validation
        """
        # Initialize validation details
        details = {
            "length": len(password) >= 10,
            "has_uppercase": bool(re.search(r'[A-Z]', password)),
            "has_lowercase": bool(re.search(r'[a-z]', password)),
            "has_digit_or_special": bool(re.search(r'[0-9!@#$%^&*(),.?":{}|<>]', password)),
        }
        
        # Calculate strength as percentage of criteria met
        criteria_count = sum(1 for v in details.values() if v)
        details["strength"] = int((criteria_count / 4) * 100)
        
        # Password is valid if at least 3 of 4 criteria are met
        is_valid = criteria_count >= 3
        
        return is_valid, details
    
    @staticmethod
    def validate_user_role(role: str) -> bool:
        """
        Validate that a user role is one of the allowed values.
        
        Args:
            role: The role to validate
            
        Returns:
            True if the role is valid, False otherwise
        """
        from schemas import UserRole
        
        try:
            # Log the received role for debugging
            print(f"Validating role: {role} of type {type(role)}")
            
            # Check if the role is already a UserRole enum
            if hasattr(role, 'value') and role in [UserRole.BUYER, UserRole.SELLER]:
                return True
                
            # Check if the role is a valid string value
            if isinstance(role, str):
                return role in ["Buyer", "Seller"] or role in [UserRole.BUYER.value, UserRole.SELLER.value]
                
            return False
        except Exception as e:
            print(f"Error validating role: {str(e)}")
            return False
    
    @staticmethod
    def get_password_error_message(validation_details: Dict[str, Any]) -> str:
        """
        Get a human-readable error message based on password validation details.
        
        Args:
            validation_details: The validation details returned by validate_password
            
        Returns:
            A message describing what aspects of the password need to be fixed
        """
        messages = []
        
        if not validation_details["length"]:
            messages.append("co najmniej 10 znaków")
        
        if not validation_details["has_uppercase"]:
            messages.append("wielką literę (A-Z)")
        
        if not validation_details["has_lowercase"]:
            messages.append("małą literę (a-z)")
        
        if not validation_details["has_digit_or_special"]:
            messages.append("cyfrę (0-9) lub znak specjalny")
        
        if not messages:
            return "Hasło jest za słabe."
        
        if len(messages) == 1:
            return f"Hasło musi zawierać {messages[0]}."
        
        return f"Hasło musi zawierać: {', '.join(messages[:-1])} oraz {messages[-1]}." 