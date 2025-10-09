# main.py
from __future__ import annotations
import os
import subprocess
import flet as ft
import pandas as pd

from benches_data import load_benches, basins_list, benches_for_basin
from benches_ui import IntervalSelector
from map_view import MapPanel
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import geojson
from fastapi.middleware.cors import CORSMiddleware


# Create the FastAPI app
app = FastAPI()

# Allow requests from any origin (you can restrict later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to ["http://localhost", "https://yourfrontend.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Base route (just for testing)
@app.get("/")
def home():
    return {"message": "Hello from Railway!"}

# Wells route (Mapbox will call this)
@app.get("/wells")
def get_wells(bbox: str = Query(...)):
    """
    Return GeoJSON wells within the map bounding box.
    bbox format: "lon_min,lat_min,lon_max,lat_max"
    """
    lon1, lat1, lon2, lat2 = map(float, bbox.split(","))

    # Temporary mock points for now (you'll replace with real Supabase/PostGIS query later)
    features = [
        geojson.Feature(geometry=geojson.Point((lon1, lat1))),
        geojson.Feature(geometry=geojson.Point((lon2, lat2))),
    ]

    return geojson.FeatureCollection(features)


APP_NAME = "Well Spacing"
DEFAULT_WELLS_PATH = os.path.join(os.getcwd(), "data", "Wells")


# --------------------------
# On-Demand Basin Downloader
# --------------------------
def download_basin_data(basin_name: str):
    """
    Downloads a single basin's data from Kaggle if it's not already present.
    Keeps Render lightweight by fetching only when needed.
    """
    dataset = "chandlermajusiak/spacing-data"
    basin_folder = os.path.join("data", "Wells", basin_name)

    if os.path.exists(basin_folder) and os.listdir(basin_folder):
        print(f"📂 {basin_name} already downloaded — skipping.")
        return

    print(f"📦 Downloading {basin_name} data from Kaggle...")

    os.makedirs("data/Wells", exist_ok=True)
    subprocess.run(["pip", "install", "kaggle"], check=True)

    if not os.getenv("KAGGLE_USERNAME") or not os.getenv("KAGGLE_KEY"):
        raise EnvironmentError("❌ Missing Kaggle credentials — set KAGGLE_USERNAME and KAGGLE_KEY.")

    # Download the full zip (contains all basins)
    subprocess.run([
        "kaggle", "datasets", "download",
        "-d", dataset,
        "--unzip",
        "-p", "data"
    ], check=True)

    # Optionally remove other basins to save space
    wells_root = os.path.join("data", "Wells")
    for folder in os.listdir(wells_root):
        if folder.lower() != basin_name.lower():
            folder_path = os.path.join(wells_root, folder)
            if os.path.isdir(folder_path):
                print(f"🧹 Removing unused basin: {folder}")
                subprocess.run(["rm", "-rf", folder_path])

    print(f"✅ {basin_name} data downloaded successfully.")


# --------------------------
# Main App
# --------------------------
def main(page: ft.Page):
    page.title = APP_NAME
    page.window_width = 1200
    page.window_height = 780
    page.padding = 16
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO

    # ---------- Header ----------
    title = ft.Text(APP_NAME, size=28, weight=ft.FontWeight.BOLD)
    subtitle1 = ft.Text("Created by Chandler Majusiak", size=16)
    subtitle2 = ft.Text("Version 1.0", size=12, italic=True)

    benches_df = load_benches()
    name_tf = ft.TextField(label="Your name", width=260)
    enter_btn = ft.ElevatedButton(text="Enter")

    basin_dd = ft.Dropdown(
        label="Basin",
        options=[ft.dropdown.Option(b) for b in basins_list(benches_df)],
        width=320,
    )

    # ✅ Map style dropdown
    map_style_dd = ft.Dropdown(
        label="Map style",
        options=[
            ft.dropdown.Option("dark"),
            ft.dropdown.Option("streets"),
            ft.dropdown.Option("satellite"),
            ft.dropdown.Option("outdoors"),
            ft.dropdown.Option("light"),
            ft.dropdown.Option("satellite-streets"),
        ],
        value="dark",
        width=250,
        visible=False,
    )

    benches_btn = ft.TextButton("△  Benches", tooltip="Benches (Alt+D)")
    map_btn = ft.TextButton("🗺️  Map", tooltip="Map (Alt+M)")

    # Header layout
    top_controls_row = ft.Row(
        [name_tf, enter_btn, basin_dd, map_style_dd],
        spacing=12,
        alignment=ft.MainAxisAlignment.START,
    )

    left_header = ft.Column(
        [title, subtitle1, subtitle2, top_controls_row],
        spacing=4,
        expand=True,
    )

    nav_bar = ft.Row([benches_btn, map_btn], spacing=8)
    header_row = ft.Row(
        [left_header, nav_bar],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # ---------- Main container ----------
    center_panel = ft.Container(expand=True)
    status_text = ft.Text("Ready", color="#FFFFFF")
    status = ft.Container(content=status_text, bgcolor="#1F3B57", padding=10, border_radius=6)

    def set_status(msg: str):
        status_text.value = msg
        status_text.update()

    # ---------- State ----------
    active_tab = "benches"
    interval_selector: IntervalSelector | None = None
    map_panel: MapPanel | None = None

    def calc_panel_height() -> int:
        return max(320, int(page.window_height - 300))

    # ---------- Benches UI ----------
    def on_intervals_change(selected: list[str]):
        cur_basin = basin_dd.value
        set_status(f"Basin: {cur_basin or '—'} | Selected: {', '.join(selected) if selected else 'none'}")

    def ensure_benches_ui(basin: str | None):
        nonlocal interval_selector
        if interval_selector is None:
            interval_selector = IntervalSelector(
                rows=[],
                on_change=on_intervals_change,
                panel_height=calc_panel_height(),
                checks_width=300,
                tiles_width=520,
            )
        if not basin:
            return
        subset = benches_for_basin(benches_df, basin)
        rows = [
            {
                "bench": r["bench"],
                "group": r["group"],
                "phase_tag": r["phase_tag"],
                "display_order": int(r["display_order"]),
                "thickness_ft": (
                    None if "thickness_ft" not in r or pd.isna(r["thickness_ft"])
                    else float(r["thickness_ft"])
                ),
            }
            for _, r in subset.iterrows()
        ]
        interval_selector.set_rows(rows)

    def set_basin(basin: str | None):
        if not basin:
            center_panel.content = None
            set_status("Select a basin to view intervals.")
            page.update()
            return

        # ⬇️ NEW: download basin data only when selected
        download_basin_data(basin)

        ensure_benches_ui(basin)
        if active_tab == "benches":
            center_panel.content = interval_selector
        set_status(f"Basin: {basin}")
        page.update()

    basin_dd.on_change = lambda e: set_basin(basin_dd.value)

    # ---------- Name entry ----------
    def enter_action(_):
        if not name_tf.value.strip():
            set_status("Please enter your name first.")
            return
        name_tf.visible = False
        enter_btn.visible = False
        set_status(f"Welcome, {name_tf.value}! Choose a basin or open the map.")
        page.update()
        show_benches()

    enter_btn.on_click = enter_action
    name_tf.on_submit = enter_action

    def on_resized(e):
        if isinstance(center_panel.content, IntervalSelector):
            center_panel.content._panel_height = calc_panel_height()
    page.on_resized = on_resized

    # ---------- Tabs ----------
    def style_nav():
        benches_btn.style = ft.ButtonStyle(color={"": ("#FFFFFF" if active_tab == "benches" else "#606670")})
        map_btn.style = ft.ButtonStyle(color={"": ("#FFFFFF" if active_tab == "map" else "#606670")})
        benches_btn.update()
        map_btn.update()

    def show_benches():
        nonlocal active_tab
        active_tab = "benches"
        map_style_dd.visible = False
        basin = basin_dd.value
        ensure_benches_ui(basin)
        center_panel.content = interval_selector
        style_nav()
        set_status("Benches view active")
        page.update()

    def show_map():
        nonlocal active_tab, map_panel
        active_tab = "map"
        map_style_dd.visible = True
        basin = basin_dd.value or "Anadarko"
        map_style = map_style_dd.value or "dark"
        map_panel = MapPanel(basin, map_style)
        center_panel.content = map_panel
        page.update()
        map_panel.load()
        set_status(f"Map view loaded for {basin}")
        style_nav()

    benches_btn.on_click = lambda e: show_benches()
    map_btn.on_click = lambda e: show_map()
    map_style_dd.on_change = lambda e: show_map()

    # ---------- Layout ----------
    page.add(header_row, ft.Divider(), center_panel, status)
    show_benches()


# --------------------------
# Run App
# --------------------------
if __name__ == "__main__":
    # 💡 No full dataset download on startup — only fetch when basin selected
    ft.app(target=main)
