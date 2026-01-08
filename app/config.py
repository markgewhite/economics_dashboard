"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
from datetime import time
from pathlib import Path
import logging
import os

from dotenv import load_dotenv


@dataclass
class Config:
    """Application configuration."""

    # API base URLs
    boe_base_url: str
    land_registry_base_url: str
    ons_base_url: str

    # Cache settings
    cache_dir: Path

    # Refresh schedule (UK time)
    monetary_check_time: time
    housing_check_time: time
    economic_check_time: time

    # Application settings
    timezone: str
    log_level: str
    debug: bool

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        load_dotenv()

        config = cls(
            boe_base_url=os.getenv(
                "BOE_API_BASE_URL",
                "https://www.bankofengland.co.uk/boeapps/database",
            ),
            land_registry_base_url=os.getenv(
                "LAND_REGISTRY_API_BASE_URL",
                "http://landregistry.data.gov.uk",
            ),
            ons_base_url=os.getenv(
                "ONS_API_BASE_URL",
                "https://api.beta.ons.gov.uk/v1",
            ),
            cache_dir=Path(os.getenv("CACHE_DIR", "./storage")),
            monetary_check_time=cls._parse_time(
                os.getenv("MONETARY_CHECK_TIME", "10:00")
            ),
            housing_check_time=cls._parse_time(
                os.getenv("HOUSING_CHECK_TIME", "15:00")
            ),
            economic_check_time=cls._parse_time(
                os.getenv("ECONOMIC_CHECK_TIME", "12:00")
            ),
            timezone=os.getenv("TIMEZONE", "Europe/London"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
        )

        # Configure logging
        config.configure_logging()

        return config

    @staticmethod
    def _parse_time(time_str: str) -> time:
        """Parse HH:MM string to time object."""
        try:
            hours, minutes = map(int, time_str.split(":"))
            return time(hours, minutes)
        except (ValueError, AttributeError):
            # Return default if parsing fails
            return time(10, 0)

    def configure_logging(self) -> None:
        """Configure application logging based on settings."""
        log_level = getattr(logging, self.log_level.upper(), logging.INFO)

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Reduce noise from third-party libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)

    def ensure_cache_dirs(self) -> None:
        """Create cache directories if they don't exist."""
        for subdir in ["raw", "processed", "metadata"]:
            (self.cache_dir / subdir).mkdir(parents=True, exist_ok=True)
