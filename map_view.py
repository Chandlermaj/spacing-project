from __future__ import annotations
import flet as ft
from flet.plotly_chart import PlotlyChart
import plotly.express as px
import requests
import os

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")

def get_plotly_chart(fig, expand=True):
    try:
        return PlotlyChart(fig, interactive=True, expand=expand)
    except TypeError:
        print("⚠️ 'interactive' not supported in this Flet version — using fallback.")
        return PlotlyChart(fig, expand=expand)

class MapPanel(ft.Container):
    """Map view panel that fetches wells dynamically from Supabase."""
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

    def load_visible_wells(self, bbox):
        """Fetch wells within a bounding box from the FastAPI endpoint."""
        bbox_str = ",".join(map(str, bbox))
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")  # local default
        url = f"{api_url}/wells_bbox?bbox={bbox_str}"
        print(f"📡 Fetching wells from {url}")

        try:
            response = requests.get(url)
            data = response.json()
        except Exception as e:
            print("⚠️ API request failed:", e)
            return

        if not isinstance(data, list) or len(data) == 0:
            print("⚠️ No wells found in bbox.")
            self._draw_blank_map()
            return

        lats = [float(w["Latitude"]) for w in data if w.get("Latitude")]
        lons = [float(w["Longitude"]) for w in data if w.get("Longitude")]

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
                center=dict(lat=sum(lats)/len(lats), lon=sum(lons)/len(lons)),
                zoom=7
            ),
            margin=dict(l=0, r=0, t=0, b=0)
        )

        self._chart_container.content = get_plotly_chart(fig, expand=True)
        self.update()

    def _draw_blank_map(self):
        fig = px.scatter_mapbox(lat=[], lon=[], height=600)
        fig.update_layout(
            mapbox=dict(
                accesstoken=MAPBOX_TOKEN,
                style=self.map_style,
                zoom=5,
                center=dict(lat=32.0, lon=-103.0)
            ),
            margin=dict(l=0, r=0, t=0, b=0)
        )
        self._chart_container.content = get_plotly_chart(fig, expand=True)
        self.update()
