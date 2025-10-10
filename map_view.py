from __future__ import annotations
import os
import requests
import flet as ft
from flet.plotly_chart import PlotlyChart
import plotly.express as px
import plotly.io as pio

# ===============================================================
# Force JS-based interactive rendering (disable Kaleido)
# ===============================================================
pio.kaleido.scope = None
pio.renderers.default = "plotly_mimetype+notebook_connected+json"

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")


# ===============================================================
# Utility: Always return an interactive PlotlyChart
# ===============================================================
def get_plotly_chart(fig):
    """Return a PlotlyChart that stays interactive."""
    try:
        return PlotlyChart(fig, expand=True, interactive=True)
    except TypeError:
        print("⚠️ Fallback PlotlyChart (old Flet version)")
        return PlotlyChart(fig, expand=True)


# ===============================================================
# MapPanel: interactive Mapbox map with Enverus-style zoom/pan
# ===============================================================
class MapPanel(ft.Container):
    """Interactive Mapbox panel for visualizing wells dynamically."""

    def __init__(self, map_style="dark"):
        super().__init__(
            expand=False,
            width=900,
            height=550,
            alignment=ft.alignment.center,
            border_radius=12,
            bgcolor="#1e1e1e",
            padding=8,
        )

        self.map_style = map_style
        self._current_bbox = [-106, 31, -101, 35]  # Default Delaware region
        self._chart_container = ft.Container(expand=True)
        self._pending_draw = True

        self.content = ft.Column(
            [
                ft.Text("Spacing Project Map", color="#ccc", size=16, weight=ft.FontWeight.BOLD),
                self._chart_container,
            ],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )

    # -----------------------------------------------------------
    # Lifecycle: only draw after added to page
    # -----------------------------------------------------------
    def did_mount(self):
        if self._pending_draw:
            self._pending_draw = False
            self._draw_map([])
            self.load_visible_wells(self._current_bbox)

    # -----------------------------------------------------------
    # Fetch wells from backend
    # -----------------------------------------------------------
    def load_visible_wells(self, bbox):
        bbox_str = ",".join(map(str, bbox))
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
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
    # Draw interactive Mapbox map
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
            height=520,
        )

        # Marker styling
        fig.update_traces(
            marker=dict(size=8, color="#00FFFF", opacity=0.8),
            hovertemplate="Lat: %{lat}<br>Lon: %{lon}<extra></extra>",
        )

        # Map style + controls
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
            dragmode="pan",
            uirevision=True,
            modebar_add=["zoom", "pan", "resetViewMapbox", "toImage"],
            clickmode="event+select",
        )

        # --- Auto-fit zoom if wells exist ---
        if lats and lons:
            lat_center = (max(lats) + min(lats)) / 2
            lon_center = (max(lons) + min(lons)) / 2
            fig.update_layout(mapbox_center={"lat": lat_center, "lon": lon_center})
            bbox_span = max(max(lats) - min(lats), max(lons) - min(lons))
            zoom = max(5, 8 - bbox_span * 10)
            fig.update_layout(mapbox_zoom=zoom)

        # Assign + update
        self._chart_container.content = get_plotly_chart(fig)
        if self.page:
            self.update()
