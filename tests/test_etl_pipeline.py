"""
Unit tests for the Geothermal ETL Pipeline.

Run with: python -m pytest tests/test_etl_pipeline.py -v
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from etl_pipeline import GeothermalETL


@pytest.fixture
def sample_data(tmp_path):
    """Create a temporary CSV file with sample well data."""
    data = pd.DataFrame({
        "well_id": ["W001"] * 5 + ["W002"] * 5,
        "depth_m": [100, 300, 500, 800, 1200, 150, 400, 600, 900, 1500],
        "temperature_c": [25, 35, 52, 78, 115, 22, None, 42, 55, 70],
        "latitude": [24.5] * 10,
        "longitude": [-110.5] * 10,
        "lithology": ["Granite"] * 10,
    })
    filepath = tmp_path / "test_wells.csv"
    data.to_csv(filepath, index=False)
    return str(filepath)


class TestGeothermalETL:
    """Tests for GeothermalETL class."""

    def test_ingest_loads_data(self, sample_data):
        etl = GeothermalETL(sample_data)
        df = etl.ingest()
        assert len(df) == 10
        assert "well_id" in df.columns

    def test_standardize_columns(self, sample_data):
        etl = GeothermalETL(sample_data)
        df = etl.ingest()
        df = etl.standardize_columns(df)
        assert "well_id" in df.columns
        assert "depth_m" in df.columns

    def test_handle_missing_values_interpolate(self, sample_data):
        etl = GeothermalETL(sample_data)
        df = etl.ingest()
        missing_before = df.isnull().sum().sum()
        df = etl.handle_missing_values(df, strategy="interpolate")
        missing_after = df.isnull().sum().sum()
        assert missing_after <= missing_before

    def test_detect_outliers_adds_column(self, sample_data):
        etl = GeothermalETL(sample_data)
        df = etl.ingest()
        df = etl.detect_outliers(df, columns=["temperature_c"])
        assert "temperature_c_outlier" in df.columns

    def test_remove_duplicates(self, sample_data):
        etl = GeothermalETL(sample_data)
        df = etl.ingest()
        # Add a duplicate row
        df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
        original_len = len(df)
        df = etl.remove_duplicates(df)
        assert len(df) < original_len

    def test_add_computed_features(self, sample_data):
        etl = GeothermalETL(sample_data)
        df = etl.ingest()
        df = etl.add_computed_features(df)
        assert "gradient_c_per_km" in df.columns
        assert "depth_category" in df.columns

    def test_full_pipeline(self, sample_data):
        etl = GeothermalETL(sample_data)
        result = etl.run_pipeline()
        assert len(result) > 0
        assert etl.clean_data is not None

    def test_get_summary(self, sample_data):
        etl = GeothermalETL(sample_data)
        etl.run_pipeline()
        summary = etl.get_summary()
        assert "total_rows" in summary
        assert "wells" in summary
        assert summary["total_rows"] > 0

    def test_unit_conversion_fahrenheit(self, tmp_path):
        data = pd.DataFrame({
            "well_id": ["W001"] * 3,
            "depth_ft": [328, 984, 1640],
            "temperature_f": [77, 95, 125.6],
        })
        filepath = tmp_path / "test_imperial.csv"
        data.to_csv(filepath, index=False)

        etl = GeothermalETL(str(filepath))
        df = etl.ingest()
        df = etl.standardize_columns(df)
        df = etl.convert_units(df)
        assert "temperature_c" in df.columns
        assert "depth_m" in df.columns
        assert abs(df["temperature_c"].iloc[0] - 25.0) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
