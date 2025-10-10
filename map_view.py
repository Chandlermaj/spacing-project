from __future__ import annotations
import os
import requests
import flet as ft
from flet.plotly_chart import PlotlyChart
import plotly.express as px
import plotly.io as pio

# ===============================================================
# Disable Kaleido and force JS-based interactive rendering
# ===============================================================
pio.kaleido.scope = None
pio.renderers.default = "plotly_mimetype+notebook_connected+json"

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")


# ===============================================================
# Utility: Always return an interactive PlotlyChart
# ===============================================================
def get_plotly_chart(fig):
    """Return a PlotlyChart that stays interactive even in web builds."""
    try:
        return PlotlyChart(fig, expand=True, interactive=True)
    except TypeError:
        print("⚠️ Fallback PlotlyChart (no 'interactive' param supported)")
        return PlotlyChart(fig, expand=True)


# ===============================================================
# MapPanel: main interactive map component
# ===============================================================
class MapPanel(ft.Container):
    """Map view panel that fetches wells dynamically from Supabase API."""

    def __init__(self, map_style="dark"):
        super().__init__(expand=True, padding=0)
        self.map_style = map_style
        self._current_bbox = [-106, 31, -101, 35]  # Default Delaware view
        self._chart_container = ft.Container(expand=True)

        self.content = ft.Column(
            [
                ft.Text("Spacing Project Map", color="#ccc", size=16),
                self._chart_container,
            ],
            spacing=8,
            expand=True,
        )

        # Draw initial blank map
        self._draw_map([])
        # Load wells inside default bounding box
        self.load_visible_wells(self._current_bbox)

    # -----------------------------------------------------------
    # Fetch wells from backend API (Railway FastAPI service)
    # -----------------------------------------------------------
    def load_visible_wells(self, bbox):
        bbox_str = ",".join(map(str, bbox))
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")

        # Ensure the API URL has a scheme
        if not api_url.startswith("http"):
            api_url = f"https://{api_url}"

        url = f"{api_url}/wells_bbox?bbox={bbox_str}"
        print(f"📡 Fetching wells for bbox {bbox_str} from {url}")

        try:
            resp = requests.get(url)
            wells = resp.json()
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

    # -----------------------------------------------------------
    # Draw Plotly map (interactive)
    # -----------------------------------------------------------
    def _draw_map(self, points):
        if points:
            lats, lons = zip(*points)
        else:
            lats, lons = [], []

        fig = px.scatter_mapbox(
            lat=lats,
            lon=lons,
            zoom=7,
            height=None,  # auto-resize
        )

        fig.update_layout(
            mapbox=dict(
                accesstoken=MAPBOX_TOKEN,
                style=self.map_style,
                center=dict(
                    lat=32.0 if not lats else sum(lats) / len(lats),
                    lon=-103.0 if not lons else sum(lons) / len(lons),
                ),
                zoom=7,
            ),
            margin=dict(l=0, r=0, t=0, b=0),
        )

        self._chart_container.content = get_plotly_chart(fig)
        self.update()
