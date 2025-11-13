"""Custom exception classes for the inventory system."""


class InventoryException(Exception):
    """Base exception for inventory operations."""
    pass


class ProductNotFoundException(InventoryException):
    """Raised when product is not found."""
    pass


class InsufficientStockException(InventoryException):
    """Raised when stock adjustment would result in negative stock."""
    pass


class BarcodeNotFoundException(InventoryException):
    """Raised when barcode lookup fails."""
    pass


class UnauthorizedException(InventoryException):
    """Raised when authentication fails."""
    pass


class ValidationException(InventoryException):
    """Raised when data validation fails."""
    pass


class NotFoundException(InventoryException):
    """Raised when a resource is not found."""
    pass
