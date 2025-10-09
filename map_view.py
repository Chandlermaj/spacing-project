from __future__ import annotations
import plotly.express as px
import flet as ft
from flet.plotly_chart import PlotlyChart

# Your Mapbox access token
MAPBOX_TOKEN = "pk.eyJ1IjoiY2hhbmRsZXJtYWoiLCJhIjoiY2xqbjV6N3gyMTIwbzNscW1ldXNrdGgybSJ9.dVuuiCN9yxDM8NMyE56qww"


# ---------- Compatibility helper ----------
def get_plotly_chart(fig, expand=True):
    """Try to create an interactive PlotlyChart if supported by this Flet version."""
    try:
        return PlotlyChart(fig, interactive=True, expand=expand)
    except TypeError:
        print("⚠️ 'interactive' not supported in this Flet version — using fallback.")
        return PlotlyChart(fig, expand=expand)


# ---------- Simple MapPanel (no shapefiles) ----------
class MapPanel(ft.Container):
    """Simple static Mapbox map in Flet."""

    def __init__(self, map_style: str = "dark"):
        super().__init__(expand=True, padding=0)
        self.map_style = map_style
        self._last_center = (33.0, -103.0)   # Default center (lat, lon)
        self._last_zoom = 6

        # Container that holds the map
        self._chart_container = ft.Container(
            expand=True,
            bgcolor="#0B132B",
            border_radius=10,
            border=ft.border.all(1, "#333"),
        )

        # Column layout for the title + map
        self.content = ft.Column(
            [
                ft.Text("Spacing Project Map", color="#ccc", size=16),
                self._chart_container
            ],
            spacing=8,
            expand=True
        )

        # Draw the base map immediately
        self._draw_blank_map()

    def _draw_blank_map(self):
        """Render a blank Mapbox basemap (no shapefiles yet)."""
        px.set_mapbox_access_token(MAPBOX_TOKEN)

        # Create a blank Mapbox figure
        fig = px.scatter_mapbox(lat=[], lon=[], height=600, width=1000)
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

        # Display the map in the chart container
        self._chart_container.content = get_plotly_chart(fig, expand=True)
