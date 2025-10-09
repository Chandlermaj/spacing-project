from __future__ import annotations
import flet as ft
from flet.plotly_chart import PlotlyChart
import plotly.express as px
import requests
import os
import threading
import time

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")


# ---------- Helper ----------
def get_plotly_chart(fig, expand=True, on_event=None):
    """Compatibility wrapper for PlotlyChart (interactive or fallback)."""
    try:
        chart = PlotlyChart(fig, interactive=True, expand=expand)
    except TypeError:
        print("⚠️ 'interactive' not supported — using fallback.")
        chart = PlotlyChart(fig, expand=expand)

    if on_event:
        chart.on_plotly_event = on_event
    return chart


# ---------- Main Map Panel ----------
class MapPanel(ft.Container):
    """
    Map view panel that auto-fetches wells from Supabase API
    when panned or zoomed. Matches main.py call: MapPanel(basin_name, map_style)
    """

    def __init__(self, basin_name: str = "Delaware", map_style: str = "dark"):
        super().__init__(expand=True, padding=0)
        self.basin_name = basin_name
        self.map_style = map_style
        self._current_bbox = [-106, 31, -101, 35]  # Default Delaware area
        self._chart_container = ft.Container(width=1000, height=600)

        # Header
        self._title = ft.Text(
            f"Spacing Project Map — {self.basin_name}",
            color="#ccc",
            size=16,
        )

        # Layout
        self.content = ft.Column(
            [self._title, self._chart_container],
            spacing=8,
            expand=True,
        )

        # Draw initial map (no data yet)
        self._draw_map([])

        # Load wells async (threaded)
        threading.Thread(
            target=self._load_visible_wells_thread,
            args=(self._current_bbox,),
            daemon=True,
        ).start()

    # ---------------------- Data fetch ----------------------
    def _load_visible_wells_thread(self, bbox):
        """Run in background thread to avoid blocking UI."""
        try:
            self.load_visible_wells(bbox)
        except Exception as e:
            print(f"❌ Background load failed: {e}")

    def load_visible_wells(self, bbox):
        bbox_str = ",".join(map(str, bbox))
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        url = f"{api_url}/wells_bbox?bbox={bbox_str}"

        print(f"📡 Fetching wells for bbox {bbox_str} from {url}")

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            wells = response.json()
        except Exception as e:
            print(f"⚠️ Failed to reach API: {e}")
            self._draw_map([])
            return

        if not isinstance(wells, list) or len(wells) == 0:
            print("⚠️ No wells returned.")
            self._draw_map([])
            return

        lats = [float(w["Latitude"]) for w in wells if w.get("Latitude")]
        lons = [float(w["Longitude"]) for w in wells if w.get("Longitude")]
        points = list(zip(lats, lons))

        print(f"✅ Loaded {len(points)} wells")
        self._draw_map(points)

    # ---------------------- Map drawing ----------------------
    def _draw_map(self, points):
        """Render map with given well coordinates."""
        if points:
            lats, lons = zip(*points)
        else:
            lats, lons = [], []

        fig = px.scatter_mapbox(
            lat=lats,
            lon=lons,
            zoom=7,
            height=600,
        )

        fig.update_layout(
            mapbox=dict(
                accesstoken=MAPBOX_TOKEN,
                style=self.map_style,
                zoom=7,
                center=dict(
                    lat=32.0 if not lats else sum(lats) / len(lats),
                    lon=-103.0 if not lons else sum(lons) / len(lons),
                ),
            ),
            margin=dict(l=0, r=0, t=0, b=0),
        )

        self._chart_container.content = get_plotly_chart(
            fig, expand=True, on_event=self._on_map_event
        )

        # Only update if attached to page
        if self.page:
            self.update()

    # ---------------------- Event handling ----------------------
    def _on_map_event(self, e):
        """Triggered when user pans/zooms the map."""
        if not e.data or "relayoutData" not in e.data:
            return
        layout = e.data["relayoutData"]

        if "mapbox._derived" in layout:
            derived = layout["mapbox._derived"]
            try:
                lon_min, lat_min, lon_max, lat_max = (
                    derived["coordinates"][0][0],
                    derived["coordinates"][1][1],
                    derived["coordinates"][2][0],
                    derived["coordinates"][0][1],
                )
                self._current_bbox = [lon_min, lat_min, lon_max, lat_max]
                print(f"🗺️ Map moved — new bbox: {self._current_bbox}")
                threading.Thread(
                    target=self._load_visible_wells_thread,
                    args=(self._current_bbox,),
                    daemon=True,
                ).start()
            except Exception as ex:
                print(f"⚠️ Bbox parse failed: {ex}")
