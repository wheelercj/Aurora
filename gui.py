# Use `pyinstaller -wF gui.py` to create an .exe for Windows.
from typing import Optional

import PySimpleGUI as sg

from ssg.generate_site import generate_site
from ssg.settings import settings  # noqa


def show_main_menu() -> None:
    """Runs the main menu."""
    global settings
    window = create_main_menu_window()
    while True:
        event, _ = window.read()
        if event == sg.WIN_CLOSED or event == "exit":
            window.close()
            return
        window.Hide()
        settings = respond_to_main_menu_event(event)
        window.UnHide()


def create_main_menu_window() -> sg.Window:
    """Creates and displays the main menu."""
    sg.theme("DarkAmber")
    layout = [
        [sg.Button("generate site", size=(14, 1), pad=(40, 5))],
        [sg.Button("settings", size=(14, 1), pad=(40, 5))],
        [sg.Button("exit", size=(14, 1), pad=(40, 5))],
    ]
    return sg.Window("Aurora", layout)


def respond_to_main_menu_event(event: str) -> Optional[dict]:
    """Handles main menu events.

    Parameters
    ----------
    event : str
        The event that was triggered.
    """
    global settings
    if event == "generate site":
        generate_site()
    elif event == "settings":
        settings = settings.prompt_user_for_all_settings(settings)
    return settings


if __name__ == "__main__":
    show_main_menu()
