# Use `pyinstaller -wF gui.py` to create an .exe for Windows.
from typing import Optional
import PySimpleGUI as sg
from generate_site import generate_site
from settings import show_settings_window


def show_main_menu() -> None:
    """Runs the main menu."""
    window = create_main_menu_window()
    settings = None
    while True:
        event, _ = window.read()
        if event == sg.WIN_CLOSED or event == "exit":
            window.close()
            return
        window.Hide()
        settings = respond_to_main_menu_event(event, settings)
        window.UnHide()


def create_main_menu_window() -> sg.Window:
    """Creates and displays the main menu."""
    sg.theme("DarkAmber")
    layout = [
        [sg.Button("generate site", size=(14, 1), pad=(40, 5))],
        [sg.Button("settings", size=(14, 1), pad=(40, 5))],
        [sg.Button("exit", size=(14, 1), pad=(40, 5))],
    ]
    return sg.Window("zk-ssg", layout)


def respond_to_main_menu_event(event: str, settings: dict = None) -> Optional[dict]:
    """Handles main menu events.

    Parameters
    ----------
    event : str
        The event that was triggered.
    settings : dict, None
        The settings dictionary. If not provided, the settings will be loaded.
    """
    if event == "generate site":
        generate_site(settings)
    elif event == "settings":
        settings = show_settings_window(settings)
    return settings


if __name__ == "__main__":
    show_main_menu()
