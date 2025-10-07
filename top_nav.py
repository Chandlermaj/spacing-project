# top_nav.py
from __future__ import annotations
import flet as ft

ACTIVE_BG = "#1f3b57"
ACTIVE_FG = "#BBD6F2"
IDLE_FG   = "#606670"

class TopNav(ft.Container):
    """
    Right-aligned top navigation with glyph 'tabs'.
    Tabs: benches (△), map (🗺️)
    Calls on_change(tab_id) when selected.
    """
    def __init__(self, active: str, on_change):
        super().__init__(padding=8, bgcolor=None)
        self._active = active
        self._on_change = on_change

        self._benches_btn = self._make_tab_button("benches", "△  Benches", "Benches (Alt+D)")
        self._map_btn     = self._make_tab_button("map",     "🗺️  Map",    "Map (Alt+M)")

        self.content = ft.Row(
            controls=[self._benches_btn, self._map_btn],
            alignment=ft.MainAxisAlignment.START,
            spacing=8,
        )
        self._refresh()

    def _make_tab_button(self, tab_id: str, label: str, tooltip: str):
        def click(_):
            self._active = tab_id
            self._refresh()
            self.update()
            if callable(self._on_change):
                self._on_change(tab_id)

        # TextButton gives us a very reliable click surface
        btn = ft.TextButton(
            text=label,
            tooltip=tooltip,
            on_click=click,
            style=ft.ButtonStyle(
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                shape=ft.RoundedRectangleBorder(radius=8),
                bgcolor={},
                color={},  # we’ll set via container below
            ),
        )

        # Put the button in a container so we can color its background for "active"
        wrapper = ft.Container(content=btn, border_radius=8, padding=0)
        wrapper.data = {"tab_id": tab_id, "button": btn}
        return wrapper

    def _refresh(self):
        for c in self.content.controls:
            if isinstance(c, ft.Container) and isinstance(c.data, dict):
                is_active = (c.data.get("tab_id") == self._active)
                btn: ft.TextButton = c.data.get("button")
                c.bgcolor = ACTIVE_BG if is_active else None
                if btn:
                    btn.text_style = ft.TextStyle(
                        color=ACTIVE_FG if is_active else IDLE_FG,
                        weight=ft.FontWeight.W_600,
                        size=14,
                    )

    def set_active(self, tab_id: str):
        self._active = tab_id
        self._refresh()
        self.update()
