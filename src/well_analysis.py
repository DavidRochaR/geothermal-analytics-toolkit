"""
Well-Log Analysis Module
========================

Temperature gradient computation, thermal anomaly detection,
and lithology-based classification for geothermal wells.

Supports:
- Linear and polynomial gradient fitting
- Anomaly detection using statistical thresholds
- Well comparison and ranking by geothermal potential
- Gradient profile visualization

Author: David Rocha
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
from typing import Optional, Tuple
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)


class TemperatureGradient:
    """Compute and analyze temperature gradients from well-log data."""

    # Reference surface temperature for gradient corrections (°C)
    DEFAULT_SURFACE_TEMP = 20.0

    def __init__(self, data: pd.DataFrame, surface_temp: float = None):
        """
        Parameters
        ----------
        data : pd.DataFrame
            Must contain columns: well_id, depth_m, temperature_c
        surface_temp : float, optional
            Reference surface temperature (°C). Defaults to 20°C.
        """
        required = {"well_id", "depth_m", "temperature_c"}
        missing = required - set(data.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        self.data = data.copy()
        self.surface_temp = surface_temp or self.DEFAULT_SURFACE_TEMP
        self.results = None

    def compute_gradient_linear(self, well_id: str) -> dict:
        """
        Compute linear temperature gradient for a single well.

        Uses linear regression: T = gradient * depth + intercept

        Returns
        -------
        dict with gradient_C_per_km, r_squared, max_temp_C, max_depth_m
        """
        well_data = self.data[self.data["well_id"] == well_id].sort_values("depth_m")

        if len(well_data) < 3:
            return {"well_id": well_id, "gradient_C_per_km": np.nan,
                    "r_squared": np.nan, "status": "insufficient_data"}

        depth = well_data["depth_m"].values
        temp = well_data["temperature_c"].values

        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(depth, temp)

        return {
            "well_id": well_id,
            "gradient_C_per_km": slope * 1000,  # Convert from °C/m to °C/km
            "intercept_C": intercept,
            "r_squared": r_value ** 2,
            "p_value": p_value,
            "std_error": std_err * 1000,
            "max_temp_C": temp.max(),
            "max_depth_m": depth.max(),
            "n_measurements": len(well_data),
            "status": "computed",
        }

    def compute_all(self) -> pd.DataFrame:
        """Compute gradients for all wells in the dataset."""
        wells = self.data["well_id"].unique()
        results = [self.compute_gradient_linear(w) for w in wells]
        self.results = pd.DataFrame(results)

        # Add ranking
        valid = self.results["status"] == "computed"
        self.results.loc[valid, "rank"] = (
            self.results.loc[valid, "gradient_C_per_km"]
            .rank(ascending=False)
            .astype(int)
        )

        return self.results

    def detect_anomalies(self, threshold_percentile: float = 90) -> pd.DataFrame:
        """
        Identify wells with anomalously high temperature gradients.

        Parameters
        ----------
        threshold_percentile : float
            Percentile above which gradients are flagged as anomalous.

        Returns
        -------
        pd.DataFrame with anomaly flag and classification.
        """
        if self.results is None:
            self.compute_all()

        valid = self.results[self.results["status"] == "computed"].copy()
        threshold = np.percentile(valid["gradient_C_per_km"].dropna(), threshold_percentile)

        valid["is_anomaly"] = valid["gradient_C_per_km"] >= threshold
        valid["classification"] = pd.cut(
            valid["gradient_C_per_km"],
            bins=[0, 30, 60, 100, np.inf],
            labels=["Low (<30)", "Normal (30-60)", "High (60-100)", "Exceptional (>100)"]
        )

        return valid

    def get_prospect_ranking(self, top_n: int = 10) -> pd.DataFrame:
        """Return the top N wells ranked by geothermal potential."""
        if self.results is None:
            self.compute_all()

        ranked = (
            self.results[self.results["status"] == "computed"]
            .sort_values("gradient_C_per_km", ascending=False)
            .head(top_n)
        )

        return ranked[["rank", "well_id", "gradient_C_per_km", "max_temp_C",
                        "max_depth_m", "r_squared"]]

    def compute_heat_flow(self, thermal_conductivity: float = 2.5) -> pd.DataFrame:
        """
        Estimate conductive heat flow for each well.

        Q = k * dT/dz

        Parameters
        ----------
        thermal_conductivity : float
            Thermal conductivity in W/(m·K). Default: 2.5 (typical crusite)

        Returns
        -------
        pd.DataFrame with heat_flow_mW_m2 column added.
        """
        if self.results is None:
            self.compute_all()

        results = self.results.copy()
        # Convert gradient from °C/km to °C/m, then multiply by k
        results["heat_flow_mW_m2"] = (
            results["gradient_C_per_km"] / 1000 * thermal_conductivity * 1000
        )

        return results


class WellProfile:
    """Analyze and compare individual well temperature profiles."""

    def __init__(self, data: pd.DataFrame):
        self.data = data

    def get_profile(self, well_id: str) -> pd.DataFrame:
        """Get sorted depth-temperature profile for a single well."""
        profile = (
            self.data[self.data["well_id"] == well_id]
            .sort_values("depth_m")
            [["depth_m", "temperature_c"]]
            .reset_index(drop=True)
        )
        return profile

    def compute_bht_correction(self, well_id: str, circulation_time_hrs: float = 8.0,
                                shut_in_time_hrs: float = 24.0) -> float:
        """
        Apply simplified Horner correction to bottom-hole temperature.

        BHT_corrected = BHT_measured + correction_factor

        This is a simplified version; real corrections require multiple
        shut-in measurements (Horner plot method).

        Parameters
        ----------
        well_id : str
        circulation_time_hrs : float
            Duration of mud circulation before measurement.
        shut_in_time_hrs : float
            Time after circulation stopped before temperature measurement.

        Returns
        -------
        float : Estimated static formation temperature (°C)
        """
        profile = self.get_profile(well_id)
        if profile.empty:
            return np.nan

        bht_measured = profile["temperature_c"].iloc[-1]

        # Simplified Horner correction factor
        horner_ratio = (circulation_time_hrs + shut_in_time_hrs) / shut_in_time_hrs
        correction = bht_measured * 0.05 * np.log(horner_ratio)  # Empirical approximation

        return bht_measured + correction

    def identify_gradient_changes(self, well_id: str, window: int = 5) -> pd.DataFrame:
        """
        Detect zones where the temperature gradient changes significantly,
        which may indicate lithological boundaries or fluid flow.

        Uses a rolling window derivative approach.
        """
        profile = self.get_profile(well_id)
        if len(profile) < window * 2:
            return pd.DataFrame()

        # Compute local gradient in rolling windows
        profile["local_gradient"] = (
            profile["temperature_c"].diff() / profile["depth_m"].diff() * 1000
        )

        # Smooth and detect changes
        profile["gradient_smooth"] = profile["local_gradient"].rolling(window, center=True).mean()
        profile["gradient_change"] = profile["gradient_smooth"].diff().abs()

        # Flag significant changes (> 2 standard deviations)
        threshold = profile["gradient_change"].mean() + 2 * profile["gradient_change"].std()
        profile["is_boundary"] = profile["gradient_change"] > threshold

        return profile


if __name__ == "__main__":
    # Example usage with sample data
    sample = pd.DataFrame({
        "well_id": ["W001"] * 5 + ["W002"] * 5,
        "depth_m": [100, 300, 500, 800, 1200] * 2,
        "temperature_c": [25, 35, 52, 78, 115, 22, 30, 42, 55, 70],
    })

    tg = TemperatureGradient(sample)
    results = tg.compute_all()
    print("Temperature Gradient Results:")
    print(results[["well_id", "gradient_C_per_km", "max_temp_C", "r_squared"]].to_string(index=False))

    print("\nProspect Ranking:")
    print(tg.get_prospect_ranking().to_string(index=False))
