# benches_ui.py
from __future__ import annotations
from typing import Callable, Iterable, Optional
import math
import flet as ft

# ---------- Scaling constants ----------
MIN_PX = 40   # minimum height to keep visible and clickable
MAX_PX = 80
GAMMA = 0.6   # nonlinear scaling for visibility

# ---------- Colors ----------
UNSEL_BG = "#D9D9D9"      # unselected background
UNSEL_BORDER = "#000000"
UNSEL_TEXT = "#333333"

SEL_BG = "#BFD9FF"        # selected background
SEL_BORDER = "#2563EB"
SEL_TEXT = "#000000"

BORDER_W = 2


def _scale_height(thickness_ft: Optional[float], tmin: float, tmax: float) -> int:
    """Convert real thickness into scaled display height (px)."""
    if thickness_ft is None or thickness_ft <= 0:
        return MIN_PX
    if tmax <= 0 or math.isclose(tmin, tmax):
        return int((MIN_PX + MAX_PX) / 2)

    x = (thickness_ft - tmin) / (tmax - tmin)
    x = min(1.0, max(0.0, x))
    x = pow(x, GAMMA)
    h = int(MIN_PX + x * (MAX_PX - MIN_PX))
    return max(MIN_PX, min(MAX_PX, h))


class IntervalSelector(ft.Row):
    """
    Vertical stratigraphic column with benches.
    Left: clickable bench rectangles (scaled by thickness).
    Right: matching checklist.
    """

    def __init__(
        self,
        rows: Iterable[dict],
        on_change: Callable[[list[str]], None] | None = None,
        panel_height: int = 480,
        checks_width: int = 280,
        tiles_width: int = 500,
    ):
        super().__init__(spacing=16, alignment=ft.MainAxisAlignment.CENTER)
        self._rows = sorted(list(rows), key=lambda r: int(r.get("display_order", 0)))
        self._on_change = on_change
        self._panel_height = panel_height
        self._checks_width = checks_width
        self._tiles_width = tiles_width
        self._selected: set[str] = set()

        thks = [
            float(r["thickness_ft"])
            for r in self._rows
            if r.get("thickness_ft") not in (None, "", "None")
        ]
        self._tmin = min(thks) if thks else 0.0
        self._tmax = max(thks) if thks else 0.0

        self._tiles_lv = ft.ListView(height=self._panel_height, spacing=0)
        self._checks_lv = ft.ListView(height=self._panel_height, spacing=6)

        self._tiles_frame = ft.Container(
            content=self._tiles_lv,
            width=self._tiles_width,
            padding=0,
            border_radius=8,
        )
        self._checks_frame = ft.Container(
            content=self._checks_lv,
            width=self._checks_width,
            padding=8,
        )

        self.controls = [self._tiles_frame, self._checks_frame]
        self._rebuild()

    # ---------- Public API ----------
    def selected(self) -> list[str]:
        return sorted(self._selected)

    def set_selected(self, names: list[str]):
        self._selected = set(names)
        self._refresh_styles()

    def set_rows(self, rows: Iterable[dict]):
        self._rows = sorted(list(rows), key=lambda r: int(r.get("display_order", 0)))
        self._selected.clear()
        thks = [
            float(r["thickness_ft"])
            for r in self._rows
            if r.get("thickness_ft") not in (None, "", "None")
        ]
        self._tmin = min(thks) if thks else 0.0
        self._tmax = max(thks) if thks else 0.0
        self._rebuild()

    def set_panel_height(self, new_height: int):
        """Adjust panel height dynamically when the window resizes."""
        self._panel_height = new_height
        self._tiles_lv.height = new_height
        self._checks_lv.height = new_height
        self.update()

    # ---------- UI logic ----------
    def _toggle(self, bench_name: str):
        if bench_name in self._selected:
            self._selected.remove(bench_name)
        else:
            self._selected.add(bench_name)
        self._refresh_styles()
        if callable(self._on_change):
            self._on_change(self.selected())

    def _refresh_styles(self):
        for c in self._tiles_lv.controls:
            if isinstance(c, ft.Container) and isinstance(c.content, ft.Text):
                name = c.content.value
                if name in self._selected:
                    c.bgcolor = SEL_BG
                    c.border = ft.border.all(BORDER_W, SEL_BORDER)
                    c.content.color = SEL_TEXT
                else:
                    c.bgcolor = UNSEL_BG
                    c.border = ft.border.all(BORDER_W, UNSEL_BORDER)
                    c.content.color = UNSEL_TEXT

        for chk in self._checks_lv.controls:
            if isinstance(chk, ft.Checkbox):
                chk.value = chk.label in self._selected

        if self.page:
            self.update()

    def _rebuild(self):
        self._tiles_lv.controls.clear()
        self._checks_lv.controls.clear()

        for r in self._rows:
            name = str(r.get("bench", ""))
            thk = r.get("thickness_ft", None)
            thk = float(thk) if thk not in (None, "", "None") else None
            height_px = _scale_height(thk, self._tmin, self._tmax)

            tile = ft.Container(
                content=ft.Text(
                    name,
                    size=14,
                    weight=ft.FontWeight.W_600,
                    no_wrap=False,  # allow wrapping if needed
                    overflow=ft.TextOverflow.CLIP,
                ),
                padding=ft.padding.symmetric(horizontal=10, vertical=8),
                height=height_px,
                alignment=ft.alignment.center_left,
                bgcolor=UNSEL_BG,
                border=ft.border.all(BORDER_W, UNSEL_BORDER),
                on_click=lambda e, n=name: self._toggle(n),
            )
            self._tiles_lv.controls.append(tile)

            chk = ft.Checkbox(
                label=name,
                value=False,
                on_change=lambda e, n=name: self._toggle(n),
            )
            self._checks_lv.controls.append(chk)

        self._refresh_styles()
