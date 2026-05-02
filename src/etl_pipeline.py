"""
Geothermal ETL Pipeline
=======================

Automated data ingestion, cleaning, and transformation for geothermal
well-log and geochemistry datasets.

Handles common data quality issues:
- Missing values (interpolation for continuous, mode for categorical)
- Unit conversion (Fahrenheit to Celsius, feet to metres)
- Outlier detection using IQR method
- Duplicate removal and index standardization

Author: David Rocha
"""

import pandas as pd
import numpy as np
from typing import Optional


class GeothermalETL:
    """End-to-end ETL pipeline for geothermal exploration data."""

    # Standard column mappings for common field variations
    COLUMN_MAP = {
        "well_name": "well_id",
        "wellname": "well_id",
        "Well Name": "well_id",
        "Well_Name": "well_id",
        "temp_c": "temperature_c",
        "temperature": "temperature_c",
        "Temperature (C)": "temperature_c",
        "temp_f": "temperature_f",
        "Temperature (F)": "temperature_f",
        "depth_m": "depth_m",
        "Depth (m)": "depth_m",
        "depth_ft": "depth_ft",
        "Depth (ft)": "depth_ft",
        "lat": "latitude",
        "Latitude": "latitude",
        "lon": "longitude",
        "lng": "longitude",
        "Longitude": "longitude",
    }

    def __init__(self, filepath: str, separator: str = ","):
        """
        Initialize the ETL pipeline.

        Parameters
        ----------
        filepath : str
            Path to the raw data file (CSV, Excel, or TSV).
        separator : str
            Column separator for CSV/TSV files.
        """
        self.filepath = filepath
        self.separator = separator
        self.raw_data = None
        self.clean_data = None
        self.processing_log = []

    def ingest(self) -> pd.DataFrame:
        """Load raw data from file."""
        if self.filepath.endswith((".xlsx", ".xls")):
            self.raw_data = pd.read_excel(self.filepath)
        else:
            self.raw_data = pd.read_csv(self.filepath, sep=self.separator)

        self._log(f"Ingested {len(self.raw_data)} rows, {len(self.raw_data.columns)} columns")
        return self.raw_data

    def standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename columns to standard names using COLUMN_MAP."""
        renamed = {}
        for col in df.columns:
            if col in self.COLUMN_MAP:
                renamed[col] = self.COLUMN_MAP[col]
            else:
                # Normalize: lowercase, strip, replace spaces with underscores
                renamed[col] = col.strip().lower().replace(" ", "_").replace("(", "").replace(")", "")

        df = df.rename(columns=renamed)
        self._log(f"Standardized {len(renamed)} column names")
        return df

    def convert_units(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert imperial units to metric."""
        # Fahrenheit to Celsius
        if "temperature_f" in df.columns and "temperature_c" not in df.columns:
            df["temperature_c"] = (df["temperature_f"] - 32) * 5 / 9
            self._log("Converted temperature: Fahrenheit → Celsius")

        # Feet to metres
        if "depth_ft" in df.columns and "depth_m" not in df.columns:
            df["depth_m"] = df["depth_ft"] * 0.3048
            self._log("Converted depth: feet → metres")

        return df

    def handle_missing_values(self, df: pd.DataFrame, strategy: str = "interpolate") -> pd.DataFrame:
        """
        Handle missing values in the dataset.

        Parameters
        ----------
        strategy : str
            'interpolate' (default) — linear interpolation for numeric columns
            'drop' — remove rows with any missing values
            'fill_mean' — fill numeric columns with their mean
        """
        missing_before = df.isnull().sum().sum()

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns

        if strategy == "interpolate":
            df[numeric_cols] = df[numeric_cols].interpolate(method="linear", limit_direction="both")
        elif strategy == "drop":
            df = df.dropna()
        elif strategy == "fill_mean":
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())

        # Fill categorical with mode
        for col in categorical_cols:
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown")

        missing_after = df.isnull().sum().sum()
        self._log(f"Missing values: {missing_before} → {missing_after} (strategy: {strategy})")
        return df

    def detect_outliers(self, df: pd.DataFrame, columns: Optional[list] = None,
                        iqr_factor: float = 1.5) -> pd.DataFrame:
        """
        Flag outliers using the IQR method.

        Adds a boolean column '{col}_outlier' for each analyzed column.
        """
        if columns is None:
            columns = ["temperature_c", "depth_m"]
            columns = [c for c in columns if c in df.columns]

        outlier_count = 0
        for col in columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - iqr_factor * iqr
            upper = q3 + iqr_factor * iqr
            mask = (df[col] < lower) | (df[col] > upper)
            df[f"{col}_outlier"] = mask
            outlier_count += mask.sum()

        self._log(f"Detected {outlier_count} outliers across {len(columns)} columns")
        return df

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows."""
        before = len(df)
        df = df.drop_duplicates()
        removed = before - len(df)
        self._log(f"Removed {removed} duplicate rows")
        return df

    def add_computed_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add derived columns useful for geothermal analysis."""
        # Temperature gradient (°C/km) — requires depth and temperature
        if "temperature_c" in df.columns and "depth_m" in df.columns:
            # Avoid division by zero
            df["gradient_c_per_km"] = np.where(
                df["depth_m"] > 0,
                (df["temperature_c"] / df["depth_m"]) * 1000,
                np.nan
            )
            self._log("Computed temperature gradient (°C/km)")

        # Depth category
        if "depth_m" in df.columns:
            bins = [0, 500, 1500, 3000, np.inf]
            labels = ["Shallow (<500m)", "Intermediate (500-1500m)", "Deep (1500-3000m)", "Ultra-Deep (>3000m)"]
            df["depth_category"] = pd.cut(df["depth_m"], bins=bins, labels=labels)
            self._log("Added depth category feature")

        return df

    def run_pipeline(self, missing_strategy: str = "interpolate") -> pd.DataFrame:
        """
        Execute the full ETL pipeline.

        Returns
        -------
        pd.DataFrame
            Cleaned, standardized, feature-enriched dataset.
        """
        self._log("=== ETL Pipeline Start ===")

        df = self.ingest()
        df = self.standardize_columns(df)
        df = self.convert_units(df)
        df = self.remove_duplicates(df)
        df = self.handle_missing_values(df, strategy=missing_strategy)
        df = self.detect_outliers(df)
        df = self.add_computed_features(df)

        self.clean_data = df
        self._log(f"=== ETL Pipeline Complete: {len(df)} rows, {len(df.columns)} columns ===")
        return df

    def get_summary(self) -> dict:
        """Return a summary of the processed dataset."""
        if self.clean_data is None:
            return {"status": "Pipeline has not been run yet"}

        df = self.clean_data
        summary = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "wells": df["well_id"].nunique() if "well_id" in df.columns else "N/A",
            "depth_range_m": f"{df['depth_m'].min():.0f} – {df['depth_m'].max():.0f}" if "depth_m" in df.columns else "N/A",
            "temp_range_c": f"{df['temperature_c'].min():.1f} – {df['temperature_c'].max():.1f}" if "temperature_c" in df.columns else "N/A",
            "missing_values": df.isnull().sum().sum(),
            "processing_steps": len(self.processing_log),
        }
        return summary

    def export(self, output_path: str) -> None:
        """Export cleaned data to CSV or Excel."""
        if self.clean_data is None:
            raise ValueError("Run the pipeline first with run_pipeline()")

        if output_path.endswith(".xlsx"):
            self.clean_data.to_excel(output_path, index=False)
        else:
            self.clean_data.to_csv(output_path, index=False)

        self._log(f"Exported to {output_path}")

    def _log(self, message: str) -> None:
        """Add a message to the processing log."""
        self.processing_log.append(message)
        print(f"[ETL] {message}")


if __name__ == "__main__":
    # Example usage
    etl = GeothermalETL("data/sample_wells.csv")
    clean_data = etl.run_pipeline()
    print("\nDataset Summary:")
    for key, value in etl.get_summary().items():
        print(f"  {key}: {value}")
