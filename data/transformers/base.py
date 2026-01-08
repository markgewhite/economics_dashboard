"""Base transformer class for data transformation."""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional
import logging

import pandas as pd

T = TypeVar("T")


class BaseTransformer(ABC, Generic[T]):
    """
    Base class for data transformers.

    Transformers convert raw API responses (DataFrames) into
    domain models suitable for the presentation layer.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._warnings: list[str] = []

    @abstractmethod
    def transform(self, raw_data: pd.DataFrame) -> T:
        """
        Transform raw data into domain model.

        Override in subclasses.
        """
        pass

    @property
    def warnings(self) -> list[str]:
        """Data quality warnings from last transformation."""
        return self._warnings.copy()

    def _add_warning(self, message: str):
        """Add a data quality warning."""
        self._warnings.append(message)
        self.logger.warning(message)

    def _clear_warnings(self):
        """Clear warnings before new transformation."""
        self._warnings = []

    def _handle_missing_values(
        self,
        df: pd.DataFrame,
        columns: list[str],
        strategy: str = "forward_fill",
    ) -> pd.DataFrame:
        """
        Apply missing value handling strategy.

        Args:
            df: DataFrame to process
            columns: Columns to handle
            strategy: One of "forward_fill", "interpolate", "drop"

        Returns:
            DataFrame with missing values handled
        """
        df = df.copy()

        for col in columns:
            if col not in df.columns:
                continue

            missing_count = df[col].isna().sum()
            if missing_count > 0:
                self._add_warning(
                    f"Column {col}: {missing_count} missing values "
                    f"({missing_count/len(df)*100:.1f}%)"
                )

                if strategy == "forward_fill":
                    df[col] = df[col].ffill()
                elif strategy == "interpolate":
                    df[col] = df[col].interpolate(method="linear")
                elif strategy == "drop":
                    df = df.dropna(subset=[col])

        return df

    def _calculate_change(
        self,
        series: pd.Series,
        periods: int = 1,
    ) -> pd.Series:
        """Calculate percentage change over specified periods."""
        return series.pct_change(periods=periods) * 100

    def _calculate_yoy_change(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
    ) -> Optional[float]:
        """
        Calculate year-over-year change for latest value.

        Returns percentage change or None if insufficient data.
        """
        if len(df) < 2:
            return None

        if value_col not in df.columns:
            return None

        df = df.sort_values(date_col)
        latest_date = df[date_col].max()
        latest_value = df[df[date_col] == latest_date][value_col].iloc[0]

        if pd.isna(latest_value):
            return None

        # Find value from ~1 year ago
        target_date = latest_date - pd.DateOffset(years=1)

        # Find closest date to 1 year ago
        past_df = df[df[date_col] <= target_date]
        if past_df.empty:
            return None

        past_value = past_df[value_col].iloc[-1]

        if past_value == 0 or pd.isna(past_value):
            return None

        return ((latest_value - past_value) / past_value) * 100

    def _calculate_yoy_point_change(
        self,
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
    ) -> Optional[float]:
        """
        Calculate year-over-year point change (not percentage) for latest value.

        Useful for values that are already percentages (e.g., interest rates).

        Returns point change or None if insufficient data.
        """
        if len(df) < 2:
            return None

        if value_col not in df.columns:
            return None

        df = df.sort_values(date_col)
        latest_date = df[date_col].max()
        latest_value = df[df[date_col] == latest_date][value_col].iloc[0]

        if pd.isna(latest_value):
            return None

        # Find value from ~1 year ago
        target_date = latest_date - pd.DateOffset(years=1)

        # Find closest date to 1 year ago
        past_df = df[df[date_col] <= target_date]
        if past_df.empty:
            return None

        past_value = past_df[value_col].iloc[-1]

        if pd.isna(past_value):
            return None

        return latest_value - past_value

    def _validate_range(
        self,
        df: pd.DataFrame,
        column: str,
        min_val: float,
        max_val: float,
    ) -> pd.DataFrame:
        """Flag values outside expected range."""
        if column not in df.columns:
            return df

        outliers = df[(df[column] < min_val) | (df[column] > max_val)]
        if len(outliers) > 0:
            self._add_warning(
                f"Column {column}: {len(outliers)} values outside "
                f"expected range [{min_val}, {max_val}]"
            )

        return df
