"""
Geospatial Visualization Module
================================

Interactive mapping for geothermal prospects using Folium and Matplotlib.
Generates HTML maps with clickable markers, heatmaps, and geological overlays.

Author: David Rocha
"""

import pandas as pd
import numpy as np
import folium
from folium.plugins import HeatMap, MarkerCluster
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from typing import Optional, List


def create_prospect_map(
    data: pd.DataFrame,
    center: Optional[tuple] = None,
    zoom_start: int = 8,
    color_by: str = "gradient_C_per_km",
    title: str = "Geothermal Prospect Map",
) -> folium.Map:
    """
    Create an interactive Folium map with geothermal prospect markers.

    Parameters
    ----------
    data : pd.DataFrame
        Must contain: latitude, longitude, well_id.
        Optionally: gradient_C_per_km, max_temp_C, depth_m.
    center : tuple, optional
        (lat, lon) for map centre. Auto-computed if not provided.
    zoom_start : int
        Initial zoom level.
    color_by : str
        Column to use for marker colour gradient.
    title : str
        Map title for the legend.

    Returns
    -------
    folium.Map
    """
    required = {"latitude", "longitude", "well_id"}
    if not required.issubset(data.columns):
        raise ValueError(f"Missing columns: {required - set(data.columns)}")

    # Auto-centre
    if center is None:
        center = (data["latitude"].mean(), data["longitude"].mean())

    # Create base map
    m = folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # Add satellite tile layer
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Satellite",
    ).add_to(m)

    # Colour scale
    if color_by in data.columns and data[color_by].notna().any():
        vmin = data[color_by].min()
        vmax = data[color_by].max()
        colormap = plt.cm.YlOrRd
    else:
        color_by = None

    # Add markers
    marker_cluster = MarkerCluster(name="Well Markers").add_to(m)

    for _, row in data.iterrows():
        # Determine marker colour
        if color_by and pd.notna(row.get(color_by)):
            norm_val = (row[color_by] - vmin) / (vmax - vmin) if vmax > vmin else 0.5
            rgba = colormap(norm_val)
            hex_color = mcolors.to_hex(rgba)
        else:
            hex_color = "#3388ff"

        # Build popup HTML
        popup_html = _build_popup(row)

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=8,
            color=hex_color,
            fill=True,
            fill_color=hex_color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row["well_id"],
        ).add_to(marker_cluster)

    # Layer control
    folium.LayerControl().add_to(m)

    # Title
    title_html = f"""
    <div style="position: fixed; top: 10px; left: 60px; z-index: 1000;
         background-color: white; padding: 10px; border-radius: 5px;
         box-shadow: 2px 2px 5px rgba(0,0,0,0.3); font-family: Arial;">
        <b>{title}</b>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    return m


def create_heatmap(
    data: pd.DataFrame,
    value_col: str = "gradient_C_per_km",
    radius: int = 25,
) -> folium.Map:
    """
    Create a heatmap layer showing geothermal gradient intensity.

    Parameters
    ----------
    data : pd.DataFrame
        Must contain: latitude, longitude, and the value_col.
    value_col : str
        Column to use for heat intensity.
    radius : int
        Heatmap point radius.

    Returns
    -------
    folium.Map
    """
    center = (data["latitude"].mean(), data["longitude"].mean())
    m = folium.Map(location=center, zoom_start=8, tiles="CartoDB positron")

    heat_data = data[["latitude", "longitude", value_col]].dropna().values.tolist()

    HeatMap(
        heat_data,
        min_opacity=0.4,
        radius=radius,
        blur=15,
        gradient={0.2: "blue", 0.4: "cyan", 0.6: "lime", 0.8: "yellow", 1.0: "red"},
        name="Gradient Heatmap",
    ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


def plot_gradient_comparison(
    data: pd.DataFrame,
    top_n: int = 15,
    figsize: tuple = (12, 6),
    save_path: Optional[str] = None,
) -> plt.Figure:
    """
    Horizontal bar chart comparing temperature gradients across wells.

    Parameters
    ----------
    data : pd.DataFrame
        Must contain: well_id, gradient_C_per_km.
    top_n : int
        Number of top wells to display.
    save_path : str, optional
        Path to save the figure.

    Returns
    -------
    matplotlib.figure.Figure
    """
    plot_data = (
        data.dropna(subset=["gradient_C_per_km"])
        .nlargest(top_n, "gradient_C_per_km")
        .sort_values("gradient_C_per_km")
    )

    fig, ax = plt.subplots(figsize=figsize)

    colors = plt.cm.YlOrRd(np.linspace(0.3, 1.0, len(plot_data)))

    bars = ax.barh(plot_data["well_id"], plot_data["gradient_C_per_km"], color=colors)

    # Add value labels
    for bar, val in zip(bars, plot_data["gradient_C_per_km"]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", fontsize=9)

    ax.set_xlabel("Temperature Gradient (°C/km)", fontsize=12)
    ax.set_ylabel("Well ID", fontsize=12)
    ax.set_title("Top Geothermal Prospects by Temperature Gradient", fontsize=14, fontweight="bold")
    ax.axvline(x=60, color="red", linestyle="--", alpha=0.5, label="High-grade threshold (60°C/km)")
    ax.legend(loc="lower right")

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")

    return fig


def _build_popup(row: pd.Series) -> str:
    """Build HTML popup content for a map marker."""
    html = f"<b>{row['well_id']}</b><br>"

    if "gradient_C_per_km" in row.index and pd.notna(row.get("gradient_C_per_km")):
        html += f"Gradient: {row['gradient_C_per_km']:.1f} °C/km<br>"

    if "max_temp_C" in row.index and pd.notna(row.get("max_temp_C")):
        html += f"Max Temp: {row['max_temp_C']:.1f} °C<br>"

    if "max_depth_m" in row.index and pd.notna(row.get("max_depth_m")):
        html += f"Max Depth: {row['max_depth_m']:.0f} m<br>"

    if "r_squared" in row.index and pd.notna(row.get("r_squared")):
        html += f"R²: {row['r_squared']:.3f}<br>"

    if "classification" in row.index and pd.notna(row.get("classification")):
        html += f"Class: {row['classification']}<br>"

    html += f"Coords: ({row['latitude']:.4f}, {row['longitude']:.4f})"
    return html


if __name__ == "__main__":
    # Example with synthetic data
    np.random.seed(42)
    demo = pd.DataFrame({
        "well_id": [f"W{i:03d}" for i in range(1, 21)],
        "latitude": np.random.uniform(24.0, 25.5, 20),
        "longitude": np.random.uniform(-111.0, -109.5, 20),
        "gradient_C_per_km": np.random.uniform(20, 120, 20),
        "max_temp_C": np.random.uniform(80, 250, 20),
    })

    m = create_prospect_map(demo, title="BCS Geothermal Prospects (Demo)")
    m.save("images/demo_prospect_map.html")
    print("Demo map saved to images/demo_prospect_map.html")
