"""
Geothermal Resource Assessment Module
======================================

Volumetric heat-in-place estimation using Monte Carlo simulation.
Implements the USGS-style volumetric method for geothermal resource
assessment with probabilistic uncertainty quantification.

Reference: Williams et al. (2008) — USGS Assessment of Moderate- and
High-Temperature Geothermal Resources of the United States.

Author: David Rocha
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple
import warnings


class VolumetricAssessment:
    """
    Monte Carlo-based volumetric heat-in-place estimation.

    The volumetric method estimates the thermal energy stored in a
    geothermal reservoir using:

        Q = A * h * rho * Cp * (T_res - T_ref)

    Where:
        Q = Heat in place (Joules)
        A = Reservoir area (m²)
        h = Reservoir thickness (m)
        rho = Rock density (kg/m³)
        Cp = Specific heat capacity (J/(kg·K))
        T_res = Reservoir temperature (°C)
        T_ref = Reference/rejection temperature (°C)
    """

    def __init__(self, n_simulations: int = 10000, seed: int = 42):
        """
        Parameters
        ----------
        n_simulations : int
            Number of Monte Carlo iterations.
        seed : int
            Random seed for reproducibility.
        """
        self.n_simulations = n_simulations
        self.seed = seed
        self.results = None
        self.parameters = {}

    def set_parameters(
        self,
        area_km2: Tuple[float, float, float],
        thickness_m: Tuple[float, float, float],
        temperature_c: Tuple[float, float, float],
        porosity: Tuple[float, float, float] = (0.05, 0.10, 0.20),
        rock_density_kg_m3: float = 2700.0,
        rock_heat_capacity_j_kg_k: float = 900.0,
        water_density_kg_m3: float = 1000.0,
        water_heat_capacity_j_kg_k: float = 4186.0,
        reference_temp_c: float = 15.0,
        recovery_factor: Tuple[float, float, float] = (0.05, 0.15, 0.25),
        conversion_efficiency: float = 0.12,
    ) -> None:
        """
        Set reservoir parameters as triangular distribution (min, mode, max).

        Parameters
        ----------
        area_km2 : tuple
            Reservoir area in km² (min, mode, max).
        thickness_m : tuple
            Reservoir thickness in metres (min, mode, max).
        temperature_c : tuple
            Reservoir temperature in °C (min, mode, max).
        porosity : tuple
            Rock porosity fraction (min, mode, max).
        rock_density_kg_m3 : float
            Bulk rock density.
        rock_heat_capacity_j_kg_k : float
            Rock specific heat capacity.
        reference_temp_c : float
            Surface/rejection temperature.
        recovery_factor : tuple
            Fraction of heat recoverable (min, mode, max).
        conversion_efficiency : float
            Thermal-to-electric conversion efficiency.
        """
        self.parameters = {
            "area_km2": area_km2,
            "thickness_m": thickness_m,
            "temperature_c": temperature_c,
            "porosity": porosity,
            "rock_density": rock_density_kg_m3,
            "rock_Cp": rock_heat_capacity_j_kg_k,
            "water_density": water_density_kg_m3,
            "water_Cp": water_heat_capacity_j_kg_k,
            "reference_temp_c": reference_temp_c,
            "recovery_factor": recovery_factor,
            "conversion_efficiency": conversion_efficiency,
        }

    def run_simulation(self) -> pd.DataFrame:
        """
        Execute Monte Carlo simulation.

        Returns
        -------
        pd.DataFrame with columns: heat_in_place_PJ, recoverable_heat_PJ,
        electric_capacity_MWe, and all sampled parameters.
        """
        if not self.parameters:
            raise ValueError("Set parameters first with set_parameters()")

        np.random.seed(self.seed)
        n = self.n_simulations
        p = self.parameters

        # Sample from triangular distributions
        area = np.random.triangular(*p["area_km2"], size=n) * 1e6  # km² to m²
        thickness = np.random.triangular(*p["thickness_m"], size=n)
        temperature = np.random.triangular(*p["temperature_c"], size=n)
        porosity = np.random.triangular(*p["porosity"], size=n)
        recovery = np.random.triangular(*p["recovery_factor"], size=n)

        # Volume
        volume = area * thickness  # m³

        # Heat in place (rock + water contribution)
        rho_rock = p["rock_density"]
        cp_rock = p["rock_Cp"]
        rho_water = p["water_density"]
        cp_water = p["water_Cp"]
        t_ref = p["reference_temp_c"]
        delta_t = temperature - t_ref

        # Weighted volumetric heat: Q = V * [(1-phi)*rho_r*Cp_r + phi*rho_w*Cp_w] * dT
        heat_capacity_bulk = (1 - porosity) * rho_rock * cp_rock + porosity * rho_water * cp_water
        heat_in_place_j = volume * heat_capacity_bulk * delta_t
        heat_in_place_pj = heat_in_place_j / 1e15  # Convert to PetaJoules

        # Recoverable heat
        recoverable_pj = heat_in_place_pj * recovery

        # Electric capacity (MWe) — assuming 30-year plant life
        plant_life_seconds = 30 * 365.25 * 24 * 3600
        electric_capacity_mwe = (
            recoverable_pj * 1e15 * p["conversion_efficiency"] / plant_life_seconds / 1e6
        )

        self.results = pd.DataFrame({
            "area_km2": area / 1e6,
            "thickness_m": thickness,
            "temperature_c": temperature,
            "porosity": porosity,
            "recovery_factor": recovery,
            "heat_in_place_PJ": heat_in_place_pj,
            "recoverable_heat_PJ": recoverable_pj,
            "electric_capacity_MWe": electric_capacity_mwe,
        })

        return self.results

    def get_statistics(self) -> dict:
        """
        Compute P10, P50, P90 and summary statistics.

        P10 = 10th percentile (conservative estimate)
        P50 = median (most likely)
        P90 = 90th percentile (optimistic estimate)
        """
        if self.results is None:
            raise ValueError("Run simulation first")

        metrics = ["heat_in_place_PJ", "recoverable_heat_PJ", "electric_capacity_MWe"]
        stats = {}

        for metric in metrics:
            values = self.results[metric]
            stats[metric] = {
                "P10": np.percentile(values, 10),
                "P50": np.percentile(values, 50),
                "P90": np.percentile(values, 90),
                "mean": values.mean(),
                "std": values.std(),
                "min": values.min(),
                "max": values.max(),
            }

        return stats

    def sensitivity_analysis(self) -> pd.DataFrame:
        """
        Compute Spearman rank correlation between input parameters
        and output metrics to identify key uncertainty drivers.

        Returns
        -------
        pd.DataFrame with correlation coefficients.
        """
        if self.results is None:
            raise ValueError("Run simulation first")

        inputs = ["area_km2", "thickness_m", "temperature_c", "porosity", "recovery_factor"]
        outputs = ["electric_capacity_MWe"]

        correlations = []
        for inp in inputs:
            for out in outputs:
                corr = self.results[inp].corr(self.results[out], method="spearman")
                correlations.append({
                    "input_parameter": inp,
                    "output_metric": out,
                    "spearman_correlation": corr,
                    "abs_correlation": abs(corr),
                })

        result = pd.DataFrame(correlations).sort_values("abs_correlation", ascending=False)
        return result

    def print_report(self) -> None:
        """Print a formatted summary report."""
        stats = self.get_statistics()

        print("=" * 60)
        print("GEOTHERMAL RESOURCE ASSESSMENT — MONTE CARLO RESULTS")
        print(f"Simulations: {self.n_simulations:,}")
        print("=" * 60)

        for metric, values in stats.items():
            unit = metric.split("_")[-1]
            clean_name = metric.replace("_", " ").title()
            print(f"\n{clean_name}:")
            print(f"  P10 (conservative) : {values['P10']:>10.2f} {unit}")
            print(f"  P50 (median)       : {values['P50']:>10.2f} {unit}")
            print(f"  P90 (optimistic)   : {values['P90']:>10.2f} {unit}")
            print(f"  Mean ± Std         : {values['mean']:>10.2f} ± {values['std']:.2f}")

        print("\n" + "=" * 60)
        print("SENSITIVITY ANALYSIS (Spearman Rank Correlation)")
        print("-" * 60)
        sensitivity = self.sensitivity_analysis()
        for _, row in sensitivity.iterrows():
            bar = "█" * int(abs(row["spearman_correlation"]) * 30)
            print(f"  {row['input_parameter']:20s} | r = {row['spearman_correlation']:+.3f} | {bar}")


if __name__ == "__main__":
    # Example: hypothetical geothermal prospect in BCS, Mexico
    assessment = VolumetricAssessment(n_simulations=10000)

    assessment.set_parameters(
        area_km2=(5.0, 10.0, 20.0),           # Reservoir area
        thickness_m=(500, 1000, 2000),          # Reservoir thickness
        temperature_c=(180, 220, 260),          # Reservoir temperature
        porosity=(0.05, 0.10, 0.20),            # Rock porosity
        recovery_factor=(0.05, 0.15, 0.25),     # Recovery factor
        reference_temp_c=20.0,                   # Surface temperature
        conversion_efficiency=0.12,              # Binary plant efficiency
    )

    results = assessment.run_simulation()
    assessment.print_report()
