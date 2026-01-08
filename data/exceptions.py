"""Custom exceptions for the UK Economic Dashboard."""


class DashboardError(Exception):
    """Base exception for all dashboard errors."""

    pass


class DataFetchError(DashboardError):
    """Error fetching data from an external API."""

    def __init__(
        self,
        source: str,
        message: str,
        original_error: Exception | None = None,
    ):
        self.source = source
        self.original_error = original_error
        super().__init__(f"Failed to fetch from {source}: {message}")


class DataTransformError(DashboardError):
    """Error transforming raw data into domain models."""

    def __init__(self, transformer: str, message: str):
        self.transformer = transformer
        super().__init__(f"Transform error in {transformer}: {message}")


class CacheError(DashboardError):
    """Error with cache operations (read/write)."""

    pass


class CacheReadError(CacheError):
    """Error reading from cache."""

    def __init__(self, dataset: str, message: str):
        self.dataset = dataset
        super().__init__(f"Failed to read cache for {dataset}: {message}")


class CacheWriteError(CacheError):
    """Error writing to cache."""

    def __init__(self, dataset: str, message: str):
        self.dataset = dataset
        super().__init__(f"Failed to write cache for {dataset}: {message}")


class ConfigurationError(DashboardError):
    """Error with application configuration."""

    pass


class ValidationError(DashboardError):
    """Data validation failed."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"Validation error for {field}: {message}")


class RateLimitError(DataFetchError):
    """API rate limit exceeded."""

    def __init__(self, source: str, retry_after: int | None = None):
        self.retry_after = retry_after
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        super().__init__(source, message)
