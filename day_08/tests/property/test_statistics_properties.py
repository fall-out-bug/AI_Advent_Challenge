"""
Property-based tests for statistics calculations.

Tests mathematical properties and invariants of statistical operations.
"""

import pytest
from hypothesis import example, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import floats, integers, lists, text

from models.data_models import ExperimentResult
from utils.statistics import StatisticsCalculator


class TestStatisticsProperties:
    """Property-based tests for statistics calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = StatisticsCalculator()

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_average_within_bounds(self, values: list[float]):
        """Average should be within min/max of individual values."""
        if not values:
            return

        avg = self.calculator.calculate_average(values)
        # Use tolerance for floating point comparison
        tolerance = 1e-10
        assert (
            min(values) - tolerance <= avg <= max(values) + tolerance
        ), f"Average {avg} outside bounds [{min(values)}, {max(values)}]"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_median_within_bounds(self, values: list[float]):
        """Median should be within min/max of individual values."""
        if not values:
            return

        median = self.calculator.calculate_median(values)
        assert (
            min(values) <= median <= max(values)
        ), f"Median {median} outside bounds [{min(values)}, {max(values)}]"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100),
        percentile=integers(min_value=0, max_value=100),
    )
    @settings(max_examples=50)
    def test_percentile_within_bounds(self, values: list[float], percentile: int):
        """Percentile should be within min/max of individual values."""
        if not values:
            return

        pct = self.calculator.calculate_percentile(values, percentile)
        assert (
            min(values) <= pct <= max(values)
        ), f"Percentile {pct} outside bounds [{min(values)}, {max(values)}]"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_average_equals_sum_divided_by_count(self, values: list[float]):
        """Average should equal sum divided by count."""
        if not values:
            return

        avg = self.calculator.calculate_average(values)
        expected = sum(values) / len(values)
        assert abs(avg - expected) < 1e-10, f"Average {avg} != sum/count {expected}"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_median_symmetric(self, values: list[float]):
        """Median should be symmetric (same for reversed list)."""
        if not values:
            return

        median1 = self.calculator.calculate_median(values)
        median2 = self.calculator.calculate_median(list(reversed(values)))
        assert median1 == median2, f"Median not symmetric: {median1} != {median2}"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_percentile_monotonic(self, values: list[float]):
        """Percentiles should be monotonic (higher percentile >= lower percentile)."""
        if not values:
            return

        pct25 = self.calculator.calculate_percentile(values, 25)
        pct50 = self.calculator.calculate_percentile(values, 50)
        pct75 = self.calculator.calculate_percentile(values, 75)

        assert (
            pct25 <= pct50 <= pct75
        ), f"Percentiles not monotonic: {pct25} <= {pct50} <= {pct75}"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_percentile_edge_cases(self, values: list[float]):
        """Test percentile edge cases (0th and 100th percentiles)."""
        if not values:
            return

        pct0 = self.calculator.calculate_percentile(values, 0)
        pct100 = self.calculator.calculate_percentile(values, 100)

        assert pct0 == min(
            values
        ), f"0th percentile should be minimum: {pct0} != {min(values)}"
        assert pct100 == max(
            values
        ), f"100th percentile should be maximum: {pct100} != {max(values)}"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_average_robust_to_outliers(self, values: list[float]):
        """Average should be robust to outliers."""
        if len(values) < 2:
            return

        # Add an outlier
        outlier_values = values + [max(values) * 10]

        avg_original = self.calculator.calculate_average(values)
        avg_with_outlier = self.calculator.calculate_average(outlier_values)

        # Average should change but not dramatically (allow higher ratio for small values)
        ratio = avg_with_outlier / avg_original if avg_original > 0 else 1
        max_ratio = 20 if avg_original < 1 else 10  # More tolerant for small values
        assert ratio <= max_ratio, f"Average too sensitive to outlier: {ratio}"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_median_robust_to_outliers(self, values: list[float]):
        """Median should be robust to outliers."""
        if len(values) < 2:
            return

        # Add an outlier
        outlier_values = values + [max(values) * 10]

        median_original = self.calculator.calculate_median(values)
        median_with_outlier = self.calculator.calculate_median(outlier_values)

        # Median should change but not dramatically (allow higher ratio for small values)
        ratio = median_with_outlier / median_original if median_original > 0 else 1
        max_ratio = 30 if median_original < 1 else 20  # More tolerant for small values and edge cases
        assert ratio <= max_ratio, f"Median too sensitive to outlier: {ratio}"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_statistics_handle_duplicates(self, values: list[float]):
        """Statistics should handle duplicate values correctly."""
        if not values:
            return

        # Create list with duplicates
        duplicate_values = values * 2

        avg_original = self.calculator.calculate_average(values)
        avg_duplicates = self.calculator.calculate_average(duplicate_values)

        assert (
            abs(avg_original - avg_duplicates) < 1e-9
        ), f"Average should be same with duplicates: {avg_original} != {avg_duplicates}"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_statistics_handle_negative_values(self, values: list[float]):
        """Statistics should handle negative values correctly."""
        if not values:
            return

        # Add negative values
        mixed_values = values + [-v for v in values[: len(values) // 2]]

        avg = self.calculator.calculate_average(mixed_values)
        median = self.calculator.calculate_median(mixed_values)

        # Results should be valid numbers
        assert not (avg != avg), "Average should not be NaN"
        assert not (median != median), "Median should not be NaN"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_statistics_handle_zero_values(self, values: list[float]):
        """Statistics should handle zero values correctly."""
        if not values:
            return

        # Add zero values
        zero_values = values + [0.0] * len(values)

        avg = self.calculator.calculate_average(zero_values)
        median = self.calculator.calculate_median(zero_values)

        # Results should be valid
        assert avg >= 0, f"Average with zeros should be non-negative: {avg}"
        assert median >= 0, f"Median with zeros should be non-negative: {median}"

    @given(
        values=lists(floats(min_value=0.0, max_value=1000.0), min_size=1, max_size=100)
    )
    @settings(max_examples=50)
    def test_statistics_handle_single_value(self, values: list[float]):
        """Statistics should handle single value correctly."""
        if not values:
            return

        single_value = [values[0]]

        avg = self.calculator.calculate_average(single_value)
        median = self.calculator.calculate_median(single_value)
        pct50 = self.calculator.calculate_percentile(single_value, 50)

        assert (
            avg == single_value[0]
        ), f"Average of single value should be the value: {avg}"
        assert (
            median == single_value[0]
        ), f"Median of single value should be the value: {median}"
        assert (
            pct50 == single_value[0]
        ), f"50th percentile of single value should be the value: {pct50}"
