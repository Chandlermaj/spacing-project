from __future__ import annotations
import flet as ft
from flet.plotly_chart import PlotlyChart
import plotly.express as px
import requests
import os

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

def get_plotly_chart(fig, expand=True, on_event=None):
    try:
        chart = PlotlyChart(fig, interactive=True, expand=expand)
    except TypeError:
        print("⚠️ 'interactive' not supported — using fallback.")
        chart = PlotlyChart(fig, expand=expand)

    if on_event:
        chart.on_plotly_event = on_event
    return chart


class MapPanel(ft.Container):
    """Map view panel that auto-fetches wells from Supabase on pan/zoom."""
    def __init__(self, map_style="dark"):
        super().__init__(expand=True, padding=0)
        self.map_style = map_style
        self._chart_container = ft.Container(width=1000, height=600)
        self.content = ft.Column(
            [ft.Text("Spacing Project Map", color="#ccc", size=16),
             self._chart_container],
            spacing=8,
            expand=True
        )
        self._current_bbox = [-106, 31, -101, 35]  # Default Delaware view
        self._draw_map([])  # Draw initial blank map
        self.load_visible_wells(self._current_bbox)

    # ---------------------- Data fetch ----------------------
    def load_visible_wells(self, bbox):
        bbox_str = ",".join(map(str, bbox))
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        url = f"{api_url}/wells_bbox?bbox={bbox_str}"
        print(f"📡 Fetching wells for bbox {bbox_str}")

        try:
            response = requests.get(url)
            wells = response.json()
        except Exception as e:
            print("⚠️ Failed to reach API:", e)
            return

        if not isinstance(wells, list) or len(wells) == 0:
            print("⚠️ No wells returned.")
            self._draw_map([])
            return

        lats = [float(w["Latitude"]) for w in wells if w.get("Latitude")]
        lons = [float(w["Longitude"]) for w in wells if w.get("Longitude")]

        self._draw_map(list(zip(lats, lons)))

    # ---------------------- Map drawing ----------------------
    def _draw_map(self, points):
        if points:
            lats, lons = zip(*points)
        else:
            lats, lons = [], []

        fig = px.scatter_mapbox(
            lat=lats,
            lon=lons,
            zoom=7,
            height=600
        )

        fig.update_layout(
            mapbox=dict(
                accesstoken=MAPBOX_TOKEN,
                style=self.map_style,
                zoom=7,
                center=dict(
                    lat=32.0 if not lats else sum(lats) / len(lats),
                    lon=-103.0 if not lons else sum(lons) / len(lons)
                )
            ),
            margin=dict(l=0, r=0, t=0, b=0)
        )

        self._chart_container.content = get_plotly_chart(
            fig,
            expand=True,
            on_event=self._on_map_event
        )
        self.update()

    # ---------------------- Event handling ----------------------
    def _on_map_event(self, e):
        """Triggered when map view changes (pan/zoom)."""
        if not e.data or "relayoutData" not in e.data:
            return
        layout = e.data["relayoutData"]

        # Extract bounding box coordinates from map move
        if "mapbox._derived" in layout:
            derived = layout["mapbox._derived"]
            lon_min, lat_min, lon_max, lat_max = (
                derived["coordinates"][0][0],
                derived["coordinates"][1][1],
                derived["coordinates"][2][0],
                derived["coordinates"][0][1],
            )
            self._current_bbox = [lon_min, lat_min, lon_max, lat_max]
            print(f"🗺️ Map moved — new bbox: {self._current_bbox}")
            self.load_visible_wells(self._current_bbox)
