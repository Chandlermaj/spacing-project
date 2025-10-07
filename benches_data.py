# benches_data.py
from __future__ import annotations
import os, sys
import pandas as pd

PHASE_COLORS = {"Oil": "#d95f02", "Gas": "#1b9e77", "Liquids": "#7570b3"}

_FALLBACK_ROWS = [
    # Midland Basin
    ("Midland", "Spraberry", "Upper Spraberry", 1, "Oil", "", None),
    ("Midland", "Spraberry", "Middle Spraberry", 2, "Oil", "", None),
    ("Midland", "Spraberry", "Lower Spraberry", 3, "Oil", "", None),
    ("Midland", "Wolfcamp", "Wolfcamp A", 4, "Oil", "", 320),
    ("Midland", "Wolfcamp", "Wolfcamp B", 5, "Oil", "", 290),
    ("Midland", "Wolfcamp", "Wolfcamp C", 6, "Oil", "", 300),
    ("Midland", "Wolfcamp", "Wolfcamp D", 7, "Oil", "", 180),

    # Delaware Basin
    ("Delaware", "Bone Spring", "1st Bone Spring", 1, "Oil", "", 950),
    ("Delaware", "Bone Spring", "2nd Bone Spring", 2, "Oil", "", 950),
    ("Delaware", "Bone Spring", "3rd Bone Spring", 3, "Oil", "", 950),
    ("Delaware", "Avalon", "Avalon", 4, "Oil", "", 1150),
    ("Delaware", "Wolfcamp", "Wolfcamp A", 5, "Oil", "", 300),
    ("Delaware", "Wolfcamp", "Wolfcamp B", 6, "Oil", "", 250),
    ("Delaware", "Wolfcamp", "Wolfcamp C", 7, "Oil", "", 250),
    ("Delaware", "Wolfcamp", "Wolfcamp D", 8, "Oil", "", 200),

    # Central Basin Platform
    ("Central Basin Platform", "San Andres", "San Andres", 1, "Oil", "", 250),
    ("Central Basin Platform", "Grayburg", "Grayburg", 2, "Oil", "", 200),
    ("Central Basin Platform", "Clearfork", "Upper Clearfork", 3, "Oil", "", 180),
    ("Central Basin Platform", "Clearfork", "Lower Clearfork", 4, "Oil", "", 160),
    ("Central Basin Platform", "Tubb", "Tubb", 5, "Oil", "", 120),
    ("Central Basin Platform", "Ellenburger", "Ellenburger", 6, "Oil", "", 300),

    # Eagle Ford
    ("Eagle Ford", "Eagle Ford", "Upper Eagle Ford", 1, "Oil", "", 180),
    ("Eagle Ford", "Eagle Ford", "Lower Eagle Ford", 2, "Oil", "", 220),

    # Austin Chalk
    ("Austin Chalk", "Austin Chalk", "Austin Chalk", 1, "Oil", "Limestone reservoir", 100),

    # Bakken
    ("Bakken", "Bakken", "Middle Bakken", 1, "Oil", "", 60),
    ("Bakken", "Three Forks", "Upper Three Forks", 2, "Oil", "", 50),
    ("Bakken", "Three Forks", "Lower Three Forks", 3, "Oil", "", 50),

    # Marcellus
    ("Marcellus", "Marcellus", "Upper Marcellus", 1, "Gas", "", 120),
    ("Marcellus", "Marcellus", "Lower Marcellus", 2, "Gas", "", 120),

    # Utica
    ("Utica", "Utica", "Point Pleasant", 1, "Gas", "", 200),
    ("Utica", "Utica", "Upper Utica", 2, "Gas", "", 120),
    ("Utica", "Utica", "Lower Utica", 3, "Gas", "", 120),

    # Haynesville
    ("Haynesville", "Haynesville", "Haynesville", 1, "Gas", "", 250),
    ("Haynesville", "Bossier", "Mid-Bossier", 2, "Gas", "", 550),

    # DJ Basin
    ("DJ", "Niobrara", "Niobrara A", 1, "Oil", "", 320),
    ("DJ", "Niobrara", "Niobrara B", 2, "Oil", "", 320),
    ("DJ", "Niobrara", "Niobrara C", 3, "Oil", "", 320),
    ("DJ", "Codell", "Codell", 4, "Oil", "", 20),

    # Powder River
    ("Powder River", "Turner", "Turner", 1, "Oil", "", 40),
    ("Powder River", "Niobrara", "Niobrara A", 2, "Oil", "", 260),
    ("Powder River", "Niobrara", "Niobrara B", 3, "Oil", "", 260),
    ("Powder River", "Niobrara", "Niobrara C", 4, "Oil", "", 260),
    ("Powder River", "Mowry", "Mowry", 5, "Oil", "", 60),

    # Anadarko Basin
    ("Anadarko", "Meramec", "Meramec Upper", 1, "Liquids", "", 160),
    ("Anadarko", "Meramec", "Meramec Lower", 2, "Liquids", "", 160),
    ("Anadarko", "Woodford", "Woodford", 3, "Gas", "", 150),
    ("Anadarko", "Osage", "Osage", 4, "Liquids", "", 100),
    ("Anadarko", "Springer", "Springer", 5, "Liquids", "", 120),
    ("Anadarko", "Sycamore", "Sycamore", 6, "Liquids", "", 120),

    # Uinta
    ("Uinta", "Green River", "Uteland Butte", 1, "Oil", "", 120),
    ("Uinta", "Green River", "Castle Peak", 2, "Oil", "", 180),
    ("Uinta", "Wasatch", "Wasatch", 3, "Oil", "", 160),

    # San Juan
    ("San Juan", "Mesaverde", "Mesaverde", 1, "Gas", "", 220),
    ("San Juan", "Mancos", "Mancos", 2, "Gas", "", 300),
    ("San Juan", "Gallup", "Gallup", 3, "Oil", "", 80),

    # Barnett
    ("Barnett", "Barnett", "Barnett", 1, "Gas", "", 300),

    # Fayetteville
    ("Fayetteville", "Fayetteville", "Fayetteville", 1, "Gas", "", 200),

    # WCSB (Western Canada)
    ("WCSB", "Montney", "Upper Montney", 1, "Liquids", "", 300),
    ("WCSB", "Montney", "Middle Montney", 2, "Liquids", "", 320),
    ("WCSB", "Montney", "Lower Montney", 3, "Gas", "", 300),
    ("WCSB", "Duvernay", "Upper Duvernay", 4, "Liquids", "", 120),
    ("WCSB", "Duvernay", "Middle Duvernay", 5, "Liquids", "", 140),
    ("WCSB", "Duvernay", "Lower Duvernay", 6, "Gas", "", 120),

    # North Slope
    ("North Slope", "Brookian", "Nanushuk", 1, "Oil", "", 600),
    ("North Slope", "Brookian", "Torok", 2, "Oil", "", 1000),
    ("North Slope", "Kuparuk", "Kuparuk A", 3, "Oil", "", 50),
    ("North Slope", "Kuparuk", "Kuparuk B", 4, "Oil", "", 50),
    ("North Slope", "Kuparuk", "Kuparuk C", 5, "Oil", "", 50),
    ("North Slope", "Sadlerochit", "Ivishak", 6, "Oil", "", 300),
]

# === utility functions remain unchanged ===
def _candidate_csv_paths() -> list[str]:
    paths = [os.path.join("data", "benches_master.csv")]
    here = os.path.dirname(os.path.abspath(__file__))
    paths.append(os.path.join(here, "data", "benches_master.csv"))
    if getattr(sys, "frozen", False) and hasattr(sys, "executable"):
        exe_dir = os.path.dirname(sys.executable)
        paths.append(os.path.join(exe_dir, "data", "benches_master.csv"))
    if hasattr(sys, "_MEIPASS"):
        paths.append(os.path.join(sys._MEIPASS, "data", "benches_master.csv"))
    out, seen = [], set()
    for p in paths:
        if p not in seen:
            out.append(p); seen.add(p)
    return out

def _load_csv_if_exists(path: str) -> pd.DataFrame | None:
    try:
        if os.path.isfile(path):
            df = pd.read_csv(path)
            req = {"basin","group","bench","display_order","phase_tag","notes"}
            if req.issubset(df.columns):
                if "thickness_ft" not in df.columns:
                    df["thickness_ft"] = None
                return df
    except Exception:
        return None
    return None

def load_benches(csv_path: str | None = None) -> pd.DataFrame:
    if csv_path:
        df = _load_csv_if_exists(csv_path)
        if df is not None:
            return df
    for p in _candidate_csv_paths():
        df = _load_csv_if_exists(p)
        if df is not None:
            return df
    return pd.DataFrame(
        _FALLBACK_ROWS,
        columns=["basin","group","bench","display_order","phase_tag","notes","thickness_ft"]
    )

def basins_list(df: pd.DataFrame) -> list[str]:
    return sorted(df["basin"].dropna().unique().tolist())

def benches_for_basin(df: pd.DataFrame, basin: str) -> pd.DataFrame:
    sub = df[df["basin"] == basin].copy()
    if "display_order" in sub.columns:
        sub = sub.sort_values(["display_order","group","bench"])
    return sub

def phase_to_color(phase_tag: str) -> str:
    return PHASE_COLORS.get(str(phase_tag), "#999999")
