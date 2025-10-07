import flet as ft

def main(page: ft.Page):
    def click(e):
        page.add(ft.Text("✅ Button clicked!"))
    page.add(ft.ElevatedButton("Click me", on_click=click))

ft.app(target=main, view=ft.AppView.FLET_APP)
