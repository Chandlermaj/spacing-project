from __future__ import annotations
import os
import flet as ft
import pandas as pd
import geojson
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from benches_data import load_benches, basins_list, benches_for_basin
from benches_ui import IntervalSelector
from map_view import MapPanel

# ------------------------------------------------------------------
# 1. Load environment variables
# ------------------------------------------------------------------
from dotenv import load_dotenv
load_dotenv()  # Helps locally; Railway injects automatically

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
API_URL = os.getenv("API_URL")

print(f"🔍 SUPABASE_URL = {SUPABASE_URL}")
print(f"🔍 SUPABASE_SERVICE_KEY starts with: {str(SUPABASE_SERVICE_KEY)[:10]}")
print(f"🔍 MAPBOX_TOKEN starts with: {str(MAPBOX_TOKEN)[:8]}")
print(f"🔍 API_URL = {API_URL}")

# ------------------------------------------------------------------
# 2. Initialize Supabase client
# ------------------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ------------------------------------------------------------------
# 3. FastAPI setup
# ------------------------------------------------------------------
app = FastAPI(title="Spacing Project API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Hello from Railway + Supabase!"}


# ------------------------------------------------------------------
# 4. Wells endpoint (live from Supabase)
# ------------------------------------------------------------------
@app.get("/wells")
def get_wells(limit: int = 1000):
    """Return well data from Supabase."""
    print("📡 Fetching wells from Supabase...")
    try:
        response = supabase.table("wells").select("*").limit(limit).execute()
        data = response.data or []
        print(f"✅ Retrieved {len(data)} wells")
        return {"count": len(data), "data": data}
    except Exception as e:
        print(f"❌ Supabase fetch error: {e}")
        return {"error": str(e)}


# ------------------------------------------------------------------
# 5. Flet UI App
# ------------------------------------------------------------------
APP_NAME = "Well Spacing"
DEFAULT_BASIN = "Delaware"

def main(page: ft.Page):
    page.title = APP_NAME
    page.window_width = 1200
    page.window_height = 780
    page.padding = 16
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO

    benches_df = load_benches()

    basin_dd = ft.Dropdown(
        label="Basin",
        options=[ft.dropdown.Option(b) for b in basins_list(benches_df)],
        value=DEFAULT_BASIN,
        width=320,
    )

    map_style_dd = ft.Dropdown(
        label="Map Style",
        options=[
            ft.dropdown.Option("dark"),
            ft.dropdown.Option("streets"),
            ft.dropdown.Option("satellite"),
            ft.dropdown.Option("outdoors"),
        ],
        value="dark",
        width=250,
    )

    benches_btn = ft.TextButton("△ Benches")
    map_btn = ft.TextButton("🗺️ Map")
    center_panel = ft.Container(expand=True)

    # ---------- Show Benches ----------
    def show_benches(e=None):
        subset = benches_for_basin(benches_df, basin_dd.value)
        interval_selector = IntervalSelector(rows=subset.to_dict("records"))
        center_panel.content = interval_selector
        page.update()

    # ---------- Show Map ----------
    def show_map(e=None):
        basin = basin_dd.value or DEFAULT_BASIN
        style = map_style_dd.value or "dark"

        # Create and display the map panel
        map_panel = MapPanel(basin, style)
        center_panel.content = map_panel
        page.update()          # ✅ must update first
        map_panel.load()       # ✅ safe to call after page.update()

    benches_btn.on_click = show_benches
    map_btn.on_click = show_map

    header = ft.Row([basin_dd, map_style_dd, benches_btn, map_btn], spacing=12)
    page.add(header, ft.Divider(), center_panel)

    # ✅ Start safely with map
    show_map()

# ------------------------------------------------------------------
# 6. Run App
# ------------------------------------------------------------------
if __name__ == "__main__":
    ft.app(target=main)
