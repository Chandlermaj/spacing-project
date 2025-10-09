from __future__ import annotations
import os
import flet as ft
import pandas as pd
from benches_data import load_benches, basins_list, benches_for_basin
from benches_ui import IntervalSelector
from map_view import MapPanel

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# --- FastAPI app ---
app = FastAPI()

# Allow cross-origin requests (for Flet/Mapbox)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Supabase connection ---
SUPABASE_URL = os.getenv("https://kjaevdkcvucazcyaapry.supabase.co")
SUPABASE_KEY = os.getenv("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtqYWV2ZGtjdnVjYXpjeWFhcHJ5Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTkwNDgyNywiZXhwIjoyMDc1NDgwODI3fQ.J-sEleEXff1D2vLyEYogVXEqWr3OsE7bs8Uol0tVy70")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Root route (sanity check) ---
@app.get("/")
def home():
    return {"message": "Spacing Project API is live"}

# --- Bounding-box query route ---
@app.get("/wells_bbox")
def wells_bbox(bbox: str = Query(...)):
    """
    Return wells inside the map's bounding box.
    bbox format: 'lon_min,lat_min,lon_max,lat_max'
    """
    lon1, lat1, lon2, lat2 = map(float, bbox.split(","))

    sql = f"""
        SELECT "API_UWI","Latitude","Longitude"
        FROM wells
        WHERE geom && ST_MakeEnvelope({lon1},{lat1},{lon2},{lat2},4326)
        LIMIT 5000;
    """

    try:
        data = supabase.rpc("execute_sql", {"sql": sql}).execute().data
        return JSONResponse(data)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# -----------------  Flet GUI  -----------------

APP_NAME = "Well Spacing"

def main(page: ft.Page):
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO

    # Header
    title = ft.Text(APP_NAME, size=28, weight=ft.FontWeight.BOLD)
    subtitle1 = ft.Text("Created by Chandler Majusiak", size=16)
    subtitle2 = ft.Text("Version 1.0", size=12, italic=True)

    benches_df = load_benches()

    basin_dd = ft.Dropdown(
        label="Basin",
        options=[ft.dropdown.Option(b) for b in basins_list(benches_df)],
        width=320,
    )

    map_style_dd = ft.Dropdown(
        label="Map Style",
        options=[
            ft.dropdown.Option("dark"),
            ft.dropdown.Option("streets"),
            ft.dropdown.Option("satellite"),
            ft.dropdown.Option("light"),
            ft.dropdown.Option("outdoors"),
            ft.dropdown.Option("satellite-streets"),
        ],
        value="dark",
        width=250,
        visible=False,
    )

    benches_btn = ft.TextButton("△  Benches")
    map_btn = ft.TextButton("🗺️  Map")

    header_row = ft.Row(
        [ft.Column([title, subtitle1, subtitle2]), ft.Row([benches_btn, map_btn])],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Main container
    center_panel = ft.Container(expand=True)
    status_text = ft.Text("Ready", color="#FFFFFF")
    status = ft.Container(content=status_text, bgcolor="#1F3B57", padding=10, border_radius=6)

    def set_status(msg: str):
        status_text.value = msg
        status_text.update()

    # Tabs logic
    active_tab = "benches"
    interval_selector: IntervalSelector | None = None
    map_panel: MapPanel | None = None

    def show_benches():
        nonlocal active_tab, interval_selector
        active_tab = "benches"
        map_style_dd.visible = False
        basin = basin_dd.value
        if interval_selector is None:
            interval_selector = IntervalSelector(rows=[], on_change=lambda x: None, panel_height=400)
        center_panel.content = interval_selector
        page.update()
        set_status(f"Benches view ({basin or 'none'})")

    def show_map():
        nonlocal active_tab, map_panel
        active_tab = "map"
        map_style_dd.visible = True
        map_style = map_style_dd.value or "dark"
        map_panel = MapPanel(map_style)
        center_panel.content = map_panel
        page.update()

        # initial bbox around Delaware (can be changed later)
        bbox = [-106, 31, -101, 35]
        map_panel.load_visible_wells(bbox)
        set_status("Map loaded from Supabase")

    benches_btn.on_click = lambda e: show_benches()
    map_btn.on_click = lambda e: show_map()

    page.add(header_row, ft.Divider(), center_panel, status)

# Run app
if __name__ == "__main__":
    ft.app(target=main)
