"""Domain exceptions for error handling."""

from typing import Optional


class DomainError(Exception):
    """Base exception for domain layer errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
    ) -> None:
        """
        Initialize domain error.

        Args:
            message: Error message
            error_code: Optional error code for categorization
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class EntityNotFoundError(DomainError):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, identifier: str) -> None:
        """
        Initialize entity not found error.

        Args:
            entity_type: Type of entity
            identifier: Entity identifier
        """
        message = f"{entity_type} with identifier '{identifier}' not found"
        super().__init__(message, error_code="ENTITY_NOT_FOUND")
        self.entity_type = entity_type
        self.identifier = identifier


class ValidationError(DomainError):
    """Raised when validation fails."""

    def __init__(self, message: str, field: Optional[str] = None) -> None:
        """
        Initialize validation error.

        Args:
            message: Validation message
            field: Optional field name
        """
        super().__init__(message, error_code="VALIDATION_ERROR")
        self.field = field


class BusinessRuleViolationError(DomainError):
    """Raised when a business rule is violated."""

    def __init__(self, rule_name: str, details: str) -> None:
        """
        Initialize business rule violation error.

        Args:
            rule_name: Name of the violated rule
            details: Details about the violation
        """
        message = f"Business rule '{rule_name}' violated: {details}"
        super().__init__(message, error_code="BUSINESS_RULE_VIOLATION")
        self.rule_name = rule_name
        self.details = details
