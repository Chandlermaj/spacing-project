from __future__ import annotations
import os
import threading
import flet as ft
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from benches_data import load_benches, basins_list, benches_for_basin
from benches_ui import IntervalSelector
from map_view import MapPanel
from dotenv import load_dotenv
import uvicorn

# ===============================================================
# 1. Environment
# ===============================================================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
API_URL = os.getenv("API_URL")

print(f"🔍 SUPABASE_URL = {SUPABASE_URL}")
print(f"🔍 MAPBOX_TOKEN starts with: {str(MAPBOX_TOKEN)[:8]}")

# ===============================================================
# 2. Supabase client
# ===============================================================
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ===============================================================
# 3. FastAPI backend
# ===============================================================
app = FastAPI(title="Spacing Project API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Backend running — UI is on / (port 8550)"}

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

@app.get("/wells_bbox")
def wells_bbox(bbox: str):
    """
    Temporary endpoint to simulate spatial filtering.
    Replace with real Supabase query later.
    """
    print(f"➡️  /wells_bbox received bbox={bbox}")
    # Static fake wells for testing
    return [
        {"Latitude": 31.8, "Longitude": -103.4},
        {"Latitude": 32.1, "Longitude": -103.0},
        {"Latitude": 31.6, "Longitude": -102.7},
        {"Latitude": 31.9, "Longitude": -103.2},
    ]

# ===============================================================
# 4. Flet Web App
# ===============================================================
APP_NAME = "Well Spacing"
DEFAULT_BASIN = "Delaware"

def main(page: ft.Page):
    page.title = APP_NAME
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 780
    page.padding = 16
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
    center_panel = ft.Container(expand=True, alignment=ft.alignment.center)

    def show_benches(e=None):
        subset = benches_for_basin(benches_df, basin_dd.value)
        interval_selector = IntervalSelector(rows=subset.to_dict("records"))
        center_panel.content = interval_selector
        page.update()

    def show_map(e=None):
        style = map_style_dd.value or "dark"
        map_panel = MapPanel(style)
        center_panel.content = map_panel
        page.update()

    benches_btn.on_click = show_benches
    map_btn.on_click = show_map
    header = ft.Row([basin_dd, map_style_dd, benches_btn, map_btn], spacing=12)
    page.add(header, ft.Divider(), center_panel)
    show_map()

# ===============================================================
# 5. Run both backend + UI together
# ===============================================================
if __name__ == "__main__":
    threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000),
        daemon=True,
    ).start()
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
