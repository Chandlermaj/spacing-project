from __future__ import annotations
import os, threading, time, pathlib
import geopandas as gpd
import pandas as pd
import plotly.express as px
import flet as ft
from flet.plotly_chart import PlotlyChart
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello from Railway!"}

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


# ---------- Main MapPanel ----------
class MapPanel(ft.Container):
    """Interactive Mapbox map panel with persistent zoom and source toggles."""

    def __init__(self, basin_name: str, map_style: str = "dark"):
        super().__init__(expand=True, padding=0)
        self.basin_name = basin_name
        self.map_style = map_style
        self._df = None
        self._last_center = None
        self._last_zoom = None

        self._loading = ft.ProgressBar(width=1000, color="#00BFFF")
        self._loading_text = ft.Text(f"Loading map for {basin_name}...", color="#ccc", size=13)

        self._surface_chk = ft.Checkbox(label="Surface Holes", value=True, on_change=self._update_map)
        self._laterals_chk = ft.Checkbox(label="Laterals", value=False, on_change=self._update_map)
        self._filter_row = ft.Row(
            [ft.Text("Source:", color="#ccc"), self._surface_chk, self._laterals_chk],
            alignment=ft.MainAxisAlignment.START,
            spacing=15,
        )

        self._chart_container = ft.Container(
            width=1000,
            height=500,
            bgcolor="#0B132B",
            border_radius=10,
            border=ft.border.all(1, "#333"),
            content=ft.Column(
                [
                    ft.Container(height=20),
                    ft.Row([self._loading], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([self._loading_text], alignment=ft.MainAxisAlignment.CENTER),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            ),
        )

        self.content = ft.Column([self._filter_row, self._chart_container], spacing=8, expand=True)

    # ---------- Async loader ----------
    def load(self):
        threading.Thread(target=self._load_async, daemon=True).start()

    def _load_async(self):
        try:
            px.set_mapbox_access_token(MAPBOX_TOKEN)
            df = _load_shapefiles_fast(self.basin_name)
            self._df = df
            time.sleep(0.3)
            if df.empty:
                self._loading_text.value = f"No shapefiles found for {self.basin_name}"
                self.update()
                return
            self._draw_map(df[df["Source"] == "Surface_Hole"])
        except Exception as ex:
            self._loading_text.value = f"❌ Error loading: {ex}"
            print(f"❌ Error loading map: {ex}")
            self.update()

    # ---------- Update toggles ----------
    def _update_map(self, e=None):
        if self._df is None or self._df.empty:
            return
        sources = []
        if self._surface_chk.value:
            sources.append("Surface_Hole")
        if self._laterals_chk.value:
            sources.append("Laterals")
        if not sources:
            self._chart_container.content = ft.Container(
                width=1000, height=500, bgcolor="#0B132B",
                content=ft.Row([ft.Text("No sources selected.", color="#ccc")],
                               alignment=ft.MainAxisAlignment.CENTER),
            )
            self.update()
            return
        self._draw_map(self._df[self._df["Source"].isin(sources)])

    # ---------- Draw map ----------
    def _draw_map(self, df: pd.DataFrame):
        if df.empty:
            self._chart_container.content = ft.Container(
                width=1000, height=500, bgcolor="#0B132B",
                content=ft.Row([ft.Text("No wells to display.", color="#ccc")],
                               alignment=ft.MainAxisAlignment.CENTER),
            )
            self.update()
            return

        # Compute bounds
        lat_min, lat_max = df["Latitude"].min(), df["Latitude"].max()
        lon_min, lon_max = df["Longitude"].min(), df["Longitude"].max()
        center_lat, center_lon = (lat_min + lat_max) / 2, (lon_min + lon_max) / 2

        lat_span, lon_span = max(lat_max - lat_min, 0.01), max(lon_max - lon_min, 0.01)
        zoom = 9 - max(lat_span, lon_span) * 40
        zoom = max(3.5, min(11.5, zoom))

        if self._last_center is not None:
            center_lat, center_lon = self._last_center
            zoom = self._last_zoom

        fig = px.scatter_mapbox(
            df,
            lat="Latitude",
            lon="Longitude",
            color="Source",
            color_discrete_map={"Surface_Hole": "#00BFFF", "Laterals": "#FF8C00"},
            hover_data={"Latitude": ':.4f', "Longitude": ':.4f'},
            height=500,
            width=1000,
        )

        fig.update_layout(
            mapbox=dict(
                accesstoken=MAPBOX_TOKEN,
                style=self.map_style,
                center=dict(lat=center_lat, lon=center_lon),
                zoom=zoom,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="#0B132B",
            legend=dict(bgcolor="rgba(17,17,17,0.66)", font=dict(color="#ccc")),
        )

        # ✅ Use compatibility wrapper (interactive on web, fallback locally)
        self._chart_container.content = get_plotly_chart(fig, expand=True)
        self.update()

        # Store for persistence
        self._last_center = (center_lat, center_lon)
        self._last_zoom = zoom
        print(f"✅ Map rendered: {len(df)} points | center=({center_lat:.3f},{center_lon:.3f}) zoom={zoom:.2f}")
