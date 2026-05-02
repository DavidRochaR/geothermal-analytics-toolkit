# 🔥 Geothermal Analytics Toolkit

> A Python-based toolkit for geothermal energy exploration data analysis — from raw well-log ingestion to interactive prospect mapping and resource assessment.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Made with Jupyter](https://img.shields.io/badge/Made%20with-Jupyter-orange.svg)](https://jupyter.org/)

---

## Overview

This toolkit automates common workflows in geothermal exploration and development — tasks that are typically done manually in spreadsheets or proprietary GIS software. It demonstrates how open-source Python libraries can process geoscience data at scale, produce publication-quality visualizations, and support data-driven decision-making in renewable energy projects.

**Built from real-world experience:** This project draws on 10+ years of geothermal project management across Mexico (GETERMEX, CFE, XENERCO), including well-log analysis for 13+ geothermal prospects, automated ETL pipelines for exploration datasets, and KPI dashboards for project controls.

## Problem Statement

Geothermal exploration generates large volumes of heterogeneous data — well logs, temperature profiles, geochemical analyses, and geospatial surveys. In many organizations, this data lives in disconnected spreadsheets and legacy databases, making it difficult to:

- Identify spatial patterns across prospects
- Automate repetitive data cleaning and transformation tasks
- Produce consistent, reproducible analyses for stakeholders
- Scale from a single well to a regional assessment

## Approach

This toolkit addresses these challenges through four modules:

| Module | Description | Key Libraries |
|--------|-------------|---------------|
| **Data Ingestion & ETL** | Automated pipeline for cleaning and standardizing geothermal datasets | Pandas, NumPy |
| **Well-Log Analysis** | Temperature gradient computation, lithology classification, anomaly detection | SciPy, Scikit-learn |
| **Geospatial Visualization** | Interactive prospect maps with geological overlays | GeoPandas, Folium, Matplotlib |
| **Resource Assessment** | Volumetric heat-in-place estimation and Monte Carlo simulation | NumPy, SciPy, Plotly |

## Results

### Temperature Gradient Analysis
- Automated processing of well-log data for multiple prospects
- Identified thermal anomalies above 150°C/km in target zones
- Reduced manual data processing time by ~70% compared to spreadsheet workflows

### Interactive Prospect Map
- Geospatial visualization of geothermal prospects with temperature overlays
- Clickable markers with well metadata and gradient summaries
- Exportable HTML maps for stakeholder presentations

### Monte Carlo Resource Estimation
- Probabilistic volumetric assessment (P10/P50/P90) for geothermal reservoirs
- Sensitivity analysis identifying reservoir thickness and temperature as key uncertainty drivers

## How to Run

```bash
# Clone the repository
git clone https://github.com/DavidRochaR/geothermal-analytics-toolkit.git
cd geothermal-analytics-toolkit

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the notebooks
jupyter notebook notebooks/
```

### Quick Start
```python
from src.etl_pipeline import GeothermalETL
from src.well_analysis import TemperatureGradient

# Load and clean well data
etl = GeothermalETL("data/sample_wells.csv")
clean_data = etl.run_pipeline()

# Compute temperature gradients
gradient = TemperatureGradient(clean_data)
results = gradient.compute_all()
print(results[["well_id", "gradient_C_per_km", "max_temp_C"]])
```

## Project Structure

```
geothermal-analytics-toolkit/
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
├── notebooks/
│   ├── 01_data_ingestion_and_cleaning.ipynb
│   ├── 02_well_log_analysis.ipynb
│   ├── 03_geospatial_visualization.ipynb
│   └── 04_monte_carlo_resource_assessment.ipynb
├── src/
│   ├── __init__.py
│   ├── etl_pipeline.py
│   ├── well_analysis.py
│   ├── geospatial_viz.py
│   └── resource_assessment.py
├── data/
│   ├── sample_wells.csv
│   ├── sample_geochemistry.csv
│   └── README.md
├── images/
│   └── (generated visualizations)
├── docs/
│   └── methodology.md
└── tests/
    └── test_etl_pipeline.py
```

## Notebooks

| # | Notebook | Description |
|---|----------|-------------|
| 01 | [Data Ingestion & Cleaning](notebooks/01_data_ingestion_and_cleaning.ipynb) | ETL pipeline for raw well-log data: missing value handling, unit conversion, outlier detection |
| 02 | [Well-Log Analysis](notebooks/02_well_log_analysis.ipynb) | Temperature gradient computation, lithology classification, thermal anomaly detection |
| 03 | [Geospatial Visualization](notebooks/03_geospatial_visualization.ipynb) | Interactive Folium maps with prospect markers, heatmaps, and geological context |
| 04 | [Monte Carlo Assessment](notebooks/04_monte_carlo_resource_assessment.ipynb) | Probabilistic volumetric estimation with sensitivity analysis and P10/P50/P90 reporting |

## Tech Stack

`Python` `Pandas` `NumPy` `SciPy` `Scikit-learn` `GeoPandas` `Folium` `Matplotlib` `Seaborn` `Plotly` `Jupyter`

## Data Sources

All data in this repository is **synthetic but geologically realistic**, generated to mimic patterns observed in real geothermal fields. No confidential or proprietary data is included.

Public data sources that inspired this work:
- [USGS Geothermal Resource Assessment](https://www.usgs.gov/programs/volcano-hazards/geothermal-resource-investigations)
- [Global Heat Flow Database (IHFC)](https://ihfc-iugg.org/products/global-heat-flow-database)
- [SGM Mexico — Geological Data](https://www.sgm.gob.mx/)

## Next Steps

- [ ] Add support for LAS file format (well-log industry standard)
- [ ] Integrate with Open Data Cube for satellite-derived thermal data
- [ ] Build a Streamlit dashboard for interactive exploration
- [ ] Add unit tests for all modules
- [ ] Publish as a PyPI package

## Author

**David Rocha** — Geological Engineer & Renewable Energy PM | Big Data & AI  
📍 Ontario, Canada  
🔗 [LinkedIn](https://www.linkedin.com/in/davidrochar/) | [GitHub](https://github.com/DavidRochaR)

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
