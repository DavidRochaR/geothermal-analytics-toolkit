# Data Directory

## Datasets

| File | Description | Records |
|------|-------------|---------|
| `sample_wells.csv` | Synthetic well-log data (depth, temperature, lithology, location) | ~230 measurements across 20 wells |
| `sample_geochemistry.csv` | Synthetic geochemical analysis (major ions, pH, TDS) | 20 samples |

## Important Note

All data in this directory is **synthetic but geologically realistic**. It was generated to mimic patterns observed in real geothermal fields in volcanic arc settings (e.g., Baja California Sur, Mexico). No confidential or proprietary data is included.

## Column Descriptions

### sample_wells.csv

| Column | Type | Description |
|--------|------|-------------|
| `well_id` | string | Unique well identifier |
| `latitude` | float | Well location (decimal degrees) |
| `longitude` | float | Well location (decimal degrees) |
| `depth_m` | float | Measurement depth (metres) |
| `temperature_c` | float | Temperature at depth (°C) |
| `lithology` | string | Rock type at depth |
| `formation` | string | Geological formation name |

### sample_geochemistry.csv

| Column | Type | Description |
|--------|------|-------------|
| `well_id` | string | Well identifier |
| `sample_date` | date | Sampling date |
| `pH` | float | Fluid acidity |
| `TDS_mg_L` | float | Total Dissolved Solids (mg/L) |
| `SiO2_mg_L` | float | Silica concentration (mg/L) — used for geothermometry |
| `Na_mg_L`, `K_mg_L`, etc. | float | Major ion concentrations (mg/L) |
| `reservoir_type` | string | Classification of the geothermal system |

## Public Data Sources (for reference)

- [USGS Geothermal Resource Data](https://www.usgs.gov/programs/volcano-hazards/geothermal-resource-investigations)
- [Global Heat Flow Database (IHFC)](https://ihfc-iugg.org/products/global-heat-flow-database)
- [SGM Mexico — Open Geological Data](https://www.sgm.gob.mx/)
