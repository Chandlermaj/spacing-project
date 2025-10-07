# basin_selector.py
import flet as ft

BASINS = [
    "Austin Chalk",
    "WCSB",
    "Fayetteville",
    "North Slope",
    "Anadarko",
    "Bakken",
    "DJ",
    "Eagle Ford",
    "Haynesville",
    "Marcellus",
    "Uinta",
    "Barnett",
    "San Juan",
    "Utica",
    "Powder River",
    "Central Basin Platform",
    "Delaware",
    "Midland",
]

def build_basin_dropdown(on_select) -> ft.Dropdown:
    """
    Returns a Dropdown pre-populated with basins.
    Calls on_select(value: str) whenever the user picks a basin.
    """
    dd = ft.Dropdown(
        label="Select basin",
        options=[ft.dropdown.Option(b) for b in BASINS],
        width=360,
    )

    def _changed(e):
        if dd.value and callable(on_select):
            on_select(dd.value)

    dd.on_change = _changed
    return dd
