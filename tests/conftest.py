"""Pytest fixtures for UK Economic Dashboard tests."""

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_boe_response(fixtures_dir: Path) -> str:
    """Load sample Bank of England response."""
    return (fixtures_dir / "sample_boe_response.csv").read_text()


@pytest.fixture
def sample_land_registry_response(fixtures_dir: Path) -> str:
    """Load sample Land Registry response."""
    return (fixtures_dir / "sample_land_registry.csv").read_text()


@pytest.fixture
def sample_ons_response(fixtures_dir: Path) -> str:
    """Load sample ONS response."""
    return (fixtures_dir / "sample_ons_response.csv").read_text()
