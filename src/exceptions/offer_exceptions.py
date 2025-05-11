from fastapi import HTTPException, status
from uuid import UUID

class OfferBaseException(Exception):
    """Base exception for offer-related errors."""
    pass

class OfferNotFoundException(OfferBaseException):
    """Raised when an offer is not found."""
    def __init__(self, offer_id: UUID = None):
        message = f"Offer {offer_id} not found" if offer_id else "Offer not found"
        super().__init__(message)

class NotOfferOwnerException(OfferBaseException):
    """Raised when a user tries to modify an offer they don't own."""
    def __init__(self, offer_id: UUID = None):
        message = f"You can only modify your own offers"
        super().__init__(message)

class InvalidStatusTransitionException(OfferBaseException):
    """Raised when an invalid offer status transition is attempted."""
    def __init__(self, current_status: str, target_status: str):
        message = f"Cannot change offer status from '{current_status}' to '{target_status}'"
        super().__init__(message)

class OfferAlreadySoldException(OfferBaseException):
    """Raised when trying to modify an already sold offer."""
    def __init__(self, offer_id: UUID = None):
        message = "Offer is already marked as sold"
        super().__init__(message)

class OfferAlreadyInactiveException(OfferBaseException):
    """Raised when trying to deactivate an already inactive offer."""
    def __init__(self, offer_id: UUID = None):
        message = "Offer is already inactive"
        super().__init__(message)

class OfferModificationFailedException(OfferBaseException):
    """Raised when offer modification fails for an unspecified reason."""
    def __init__(self, operation: str, details: str = None):
        message = f"Failed to {operation} offer"
        if details:
            message += f": {details}"
        self.operation = operation
        self.details = details
        super().__init__(message) 