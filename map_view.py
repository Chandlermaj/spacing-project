from __future__ import annotations
import os, threading, time, pathlib
import geopandas as gpd
import pandas as pd
import plotly.express as px
import flet as ft
from flet.plotly_chart import PlotlyChart


MAPBOX_TOKEN = "pk.eyJ1IjoiY2hhbmRsZXJtYWoiLCJhIjoiY2xqbjV6N3gyMTIwbzNscW1ldXNrdGgybSJ9.dVuuiCN9yxDM8NMyE56qww"
WELLS_ROOT = pathlib.Path(__file__).parent / "data" / "Wells"
MAX_POINTS = 75000


def _load_shapefiles_fast(basin_name: str) -> pd.DataFrame:
    """Load shapefiles (Surface_Hole and Laterals) quickly into a dataframe."""
    basin_path = os.path.join(WELLS_ROOT, basin_name)
    if not os.path.exists(basin_path):
        raise FileNotFoundError(f"Basin folder not found: {basin_path}")

    dfs = []
    for subdir in ["Surface_Hole", "Laterals"]:
        shp_dir = os.path.join(basin_path, subdir)
        if not os.path.exists(shp_dir):
            continue
        for fname in os.listdir(shp_dir):
            if not fname.lower().endswith(".shp"):
                continue
            shp_path = os.path.join(shp_dir, fname)
            try:
                gdf = gpd.read_file(shp_path)
                if gdf.empty:
                    continue
                if gdf.crs is None:
                    gdf.set_crs(epsg=4326, inplace=True)
                # Convert polygons/lines to centroids for plotting
                if gdf.geometry.iloc[0].geom_type != "Point":
                    gdf_proj = gdf.to_crs(epsg=3857)
                    centroids = gdf_proj.geometry.centroid.to_crs(epsg=4326)
                    gdf["Longitude"] = centroids.x
                    gdf["Latitude"] = centroids.y
                else:
                    gdf["Longitude"] = gdf.geometry.x
                    gdf["Latitude"] = gdf.geometry.y
                gdf["Source"] = subdir
                dfs.append(gdf[["Latitude", "Longitude", "Source"]])
            except Exception as ex:
                print(f"⚠️ Error loading {shp_path}: {ex}")

    if not dfs:
        print(f"⚠️ No shapefiles found for {basin_name}")
        return pd.DataFrame(columns=["Latitude", "Longitude", "Source"])

    df = pd.concat(dfs, ignore_index=True).dropna(subset=["Latitude", "Longitude"])
    if len(df) > MAX_POINTS:
        df = df.sample(MAX_POINTS, random_state=42).reset_index(drop=True)
    print(f"✅ Loaded {len(df)} points for {basin_name}")
    return df


# ---------- Compatibility helper ----------
def get_plotly_chart(fig, expand=True):
    """Try to create an interactive PlotlyChart if supported by this Flet version."""
    try:
        return PlotlyChart(fig, interactive=True, expand=expand)
    except TypeError:
        # Fallback for Flet versions without the 'interactive' argument
        print("⚠️ 'interactive' not supported in this Flet version — using fallback.")
        return PlotlyChart(fig, expand=expand)


# ---------- Simple MapPanel (no shapefiles) ----------
class MapPanel(ft.Container):
    """Simple static Mapbox map in Flet."""

    def __init__(self, map_style: str = "dark"):
        super().__init__(expand=True, padding=0)
        self.map_style = map_style
        self._last_center = (33.0, -103.0)   # Default center (lon, lat)
        self._last_zoom = 6

        self._chart_container = ft.Container(
            width=1000,
            height=500,
            bgcolor="#0B132B",
            border_radius=10,
            border=ft.border.all(1, "#333"),
        )

        self.content = ft.Column(
            [
                ft.Text("Spacing Project Map", color="#ccc", size=16),
                self._chart_container
            ],
            spacing=8,
            expand=True
        )

        self._draw_blank_map()

    def _draw_blank_map(self):
        import plotly.express as px
        px.set_mapbox_access_token(MAPBOX_TOKEN)

        # Create an empty Plotly Mapbox figure
        fig = px.scatter_mapbox(
            lat=[],
            lon=[],
            height=500,
            width=1000
        )
        fig.update_layout(
            mapbox=dict(
                accesstoken=MAPBOX_TOKEN,
                style=self.map_style,
                center=dict(lat=self._last_center[0], lon=self._last_center[1]),
                zoom=self._last_zoom,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="#0B132B",
        )

        self._chart_container.content = get_plotly_chart(fig, expand=True)
        self.update()



        # Store for persistence
        self._last_center = (center_lat, center_lon)
        self._last_zoom = zoom
        print(f"✅ Map rendered: {len(df)} points | center=({center_lat:.3f},{center_lon:.3f}) zoom={zoom:.2f}")
