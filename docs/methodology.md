# Methodology

## Geothermal Resource Assessment Framework

This toolkit implements standard geoscience methods adapted for computational analysis.

### Temperature Gradient Analysis

The temperature gradient (dT/dz) is the rate of temperature increase with depth. In geothermal systems, anomalously high gradients indicate subsurface heat sources (magmatic intrusions, fault-controlled fluid circulation).

**Method:**
- Linear regression of temperature vs. depth for each well
- Gradient expressed in °C/km
- Quality assessed via R² and standard error
- Classification: Low (<30), Normal (30-60), High (60-100), Exceptional (>100 °C/km)

### Volumetric Heat-in-Place (Monte Carlo)

The USGS volumetric method estimates stored thermal energy:

```
Q = V × [(1-φ)ρᵣCᵣ + φρwCw] × (Tᵣ - Tref)
```

Where:
- V = Reservoir volume (A × h)
- φ = Porosity
- ρ, C = Density and heat capacity (rock/water)
- Tᵣ = Reservoir temperature
- Tref = Reference temperature

**Uncertainty quantification** uses Monte Carlo simulation with triangular distributions for input parameters, producing P10/P50/P90 estimates.

### Geospatial Analysis

- Prospect mapping with Folium (interactive HTML maps)
- Heatmap overlays for gradient intensity
- Integration with GeoPandas for spatial queries

### References

1. Williams, C.F., et al. (2008). Assessment of Moderate- and High-Temperature Geothermal Resources of the United States. USGS Fact Sheet 2008-3082.
2. Beardsmore, G.R., & Cull, J.P. (2001). Crustal Heat Flow: A Guide to Measurement and Modelling. Cambridge University Press.
3. DiPippo, R. (2012). Geothermal Power Plants: Principles, Applications, Case Studies and Environmental Impact. Elsevier.
