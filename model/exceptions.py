"""Domain exceptions for the space debris tracking system."""


class CatalogValidationException(Exception):
    """Raised when a debris catalog fails schema or content validation."""


class InvalidInputException(Exception):
    """Raised when user or system input values are invalid."""


class AnalysisException(Exception):
    """Raised when collision analysis fails unexpectedly."""

    def __init__(self, message: str, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class PropagationException(Exception):
    """Raised when trajectory propagation cannot be performed."""
