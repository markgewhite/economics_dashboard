"""Base API client with retry logic and session management."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic, Optional
import logging
import time

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

T = TypeVar("T")


@dataclass
class FetchResult(Generic[T]):
    """Result of an API fetch operation."""

    success: bool
    data: Optional[T]
    error_message: Optional[str] = None
    response_time_ms: float = 0.0

    @classmethod
    def ok(cls, data: T, response_time_ms: float = 0.0) -> "FetchResult[T]":
        """Create successful result."""
        return cls(success=True, data=data, response_time_ms=response_time_ms)

    @classmethod
    def error(cls, message: str) -> "FetchResult[T]":
        """Create error result."""
        return cls(success=False, data=None, error_message=message)


class BaseAPIClient(ABC):
    """
    Abstract base class for all API clients.

    Provides:
    - Lazy-initialized requests session
    - Retry logic with exponential backoff
    - Response timing
    - Logging
    """

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.logger = logging.getLogger(self.__class__.__name__)
        self._session: Optional[requests.Session] = None

    @property
    def session(self) -> requests.Session:
        """Lazy-initialized requests session."""
        if self._session is None:
            self._session = self._create_session()
        return self._session

    def _create_session(self) -> requests.Session:
        """
        Create configured session.

        Override in subclasses to add custom headers.
        """
        session = requests.Session()
        session.headers.update({
            "Accept": "text/csv,application/json",
        })
        return session

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    )
    def _make_request(
        self,
        url: str,
        method: str = "GET",
        **kwargs,
    ) -> requests.Response:
        """
        Make HTTP request with retry logic.

        Retries on:
        - Connection errors
        - Timeouts

        Does not retry on:
        - 4xx/5xx HTTP errors (handled by caller)
        """
        self.logger.debug(f"Requesting: {url}")

        response = self.session.request(
            method=method,
            url=url,
            timeout=self.timeout,
            **kwargs,
        )

        self.logger.debug(f"Response status: {response.status_code}")
        return response

    def _timed_request(self, url: str, **kwargs) -> tuple[requests.Response, float]:
        """Make request and return response with timing."""
        start = time.perf_counter()
        response = self._make_request(url, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return response, elapsed_ms

    @abstractmethod
    def fetch(self, **params) -> FetchResult:
        """
        Fetch data from API.

        Override in subclasses with appropriate parameters.
        """
        pass

    def close(self):
        """Close the session."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False
