from __future__ import annotations
import os
import threading
import requests
import flet as ft
import plotly.express as px
import plotly.io as pio
from flet.plotly_chart import PlotlyChart

# ----------------------------------------------------------------------
#  Disable Kaleido static image export (prevents Chrome errors on Railway)
# ----------------------------------------------------------------------
pio.kaleido.scope.default_format = None

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")


# ---------- PlotlyChart helper ----------
def get_plotly_chart(fig, expand=True, on_event=None):
    """Wrapper to create PlotlyChart safely across environments."""
    try:
        chart = PlotlyChart(fig, interactive=True, expand=expand)
    except TypeError:
        print("⚠️ 'interactive' not supported — using fallback.")
        chart = PlotlyChart(fig, expand=expand)

    if on_event:
        chart.on_plotly_event = on_event
    return chart


# ---------- Map Panel ----------
class MapPanel(ft.Container):
    """Interactive Mapbox map that fetches wells from Supabase API."""

    def __init__(self, basin_name: str = "Delaware", map_style: str = "dark"):
        super().__init__(expand=True, padding=0)
        self.basin_name = basin_name
        self.map_style = map_style
        self._current_bbox = [-106, 31, -101, 35]  # Default Delaware view
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

        # Draw blank map initially
        self._draw_map([])

        # Load wells asynchronously
        threading.Thread(
            target=self._load_visible_wells_thread,
            args=(self._current_bbox,),
            daemon=True,
        ).start()

    # ---------------- Data Fetch ----------------
    def _load_visible_wells_thread(self, bbox):
        """Background thread to fetch wells without blocking UI."""
        try:
            self.load_visible_wells(bbox)
        except Exception as e:
            print(f"❌ Background load failed: {e}")

    def load_visible_wells(self, bbox):
        bbox_str = ",".join(map(str, bbox))
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        if not api_url.startswith("http"):
            api_url = "https://" + api_url  # ✅ ensure valid URL scheme

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

    # ---------------- Map Drawing ----------------
    def _draw_map(self, points):
        """Render Plotly mapbox scatter."""
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

        try:
            self._chart_container.content = get_plotly_chart(
                fig, expand=True, on_event=self._on_map_event
            )
        except Exception as ex:
            print(f"⚠️ Plotly fallback (no Chrome): {ex}")
            self._chart_container.content = ft.Text(
                "Interactive map unavailable — Chrome missing.",
                color="#ccc",
            )

        if self.page:
            self.update()

    # ---------------- Map Event Handling ----------------
    def _on_map_event(self, e):
        """Triggered on pan/zoom — refetch wells for new bounding box."""
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
