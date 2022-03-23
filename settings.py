"""Manages the app's settings.

Settings
--------
'body background color' : str
    The color of the background of the site as a hex RGB string.
'body hover color' : str
    The color of links in the body when they are hovered over, as a hex RGB
    string.
'body link color' : str
    The color of links in the body, as a hex RGB string.
'copyright text' : str
    The copyright notice that will appear at the bottom of the index page.
'header background color' : str
    The color of the background of the header as a hex RGB string.
'header hover color' : str
    The color of links in the header when they are hovered over, as a hex
    RGB string.
'header text color' : str
    The color of the text in the header as a hex RGB string.
'hide chrono index dates' : bool
    If true, file creation dates will not be shown in the chronological
    index.
'hide tags' : bool
    If true, tags will be removed from the copied zettels when generating
    the site.
'internal html link prefix' : str
    Text that will be prepended to internal links. This setting can be an empty
    string.
# 'internal zk link start' : str
#     The text that indicates the start of an internal zettelkasten link.
# 'internal zk link end' : str
#     The text that indicates the end of an internal zettelkasten link.
'site path' : str
    The absolute path to the root folder of the site's files.
'site subfolder name' : str
    The name of the folder within the site folder that most of the HTML
    pages will be placed in by default.
'site title' : str
    The title that will appear at the top of the site.
'zettelkasten path' : str
    The absolute path to the zettelkasten folder.
"""
from datetime import datetime
import sys
import os
import PySimpleGUI as sg  # https://pysimplegui.readthedocs.io/en/latest/
from app_settings_dict import Settings  # https://pypi.org/project/app-settings-dict/


def show_settings_window(settings: Settings) -> Settings:
    """Runs the settings menu and returns the settings.

    Parameters
    ----------
    settings : Settings
        The current application settings.
    """
    settings_are_valid = False
    window = create_settings_window(settings.data)
    while not settings_are_valid:
        event, new_settings = window.read()
        if event == sg.WIN_CLOSED:
            sys.exit(0)
        new_settings = filter_items(new_settings)
        settings_are_valid = validate_settings(new_settings)
        if not settings_are_valid:
            sg.popup(
                "Each setting must be given a value, except the internal html "
                "link prefix setting."
            )
    window.close()
    if event == "cancel":
        return settings
    settings.update(new_settings)
    settings.save()
    return settings


settings_folder_path = os.path.dirname(os.path.abspath(__file__))
settings_file_path = os.path.join(settings_folder_path, "settings.json")
this_year = datetime.now().year
settings = Settings(
    settings_file_path=settings_file_path,
    prompt_user_for_all_settings=show_settings_window,
    data={
        "body background color": "#fffafa",  # snow
        "body hover color": "#3d550c",  # olive green
        "body link color": "#59981a",  # green
        "copyright text": f"© {this_year}, your name",
        "header background color": "#81b622",  # lime green
        "header hover color": "#3d550c",  # olive green
        "header text color": "#ecf87f",  # yellow green
        "hide chrono index dates": True,
        "hide tags": True,
        "internal html link prefix": "[§] ",
        # "internal zk link start": "[[",
        # "internal zk link end": "]]",
        "site path": "",
        "site subfolder name": "pages",
        "site title": "",
        "zettelkasten path": "",
    }
)
settings.load(fallback_option="prompt user")


def create_settings_window(settings: dict = None) -> sg.Window:
    """Creates and displays the settings menu.

    Parameters
    ----------
    settings : dict, None
        The settings to use.
    """
    sg.theme("DarkAmber")

    general_tab_layout = [
        create_text_chooser("site title", settings),
        create_text_chooser("copyright text", settings),
        create_text_chooser("site subfolder name", settings),
        create_text_chooser("internal html link prefix", settings),
        # create_text_chooser("internal zk link start", settings),
        # create_text_chooser("internal zk link end", settings),
        create_folder_chooser("site path", settings),
        create_folder_chooser("zettelkasten path", settings),
        create_checkbox("hide tags", "hide tags", settings),
        create_checkbox(
            "hide dates in the chronological index", "hide chrono index dates", settings
        ),
    ]

    color_tab_layout = [
        create_color_chooser("body background color", settings),
        create_color_chooser("header background color", settings),
        create_color_chooser("header text color", settings),
        create_color_chooser("header hover color", settings),
        create_color_chooser("body link color", settings),
        create_color_chooser("body hover color", settings),
    ]

    layout = [
        [
            sg.TabGroup(
                [
                    [
                        sg.Tab("general", general_tab_layout),
                        sg.Tab("color", color_tab_layout),
                    ]
                ]
            )
        ],
        [sg.HorizontalSeparator()],
        [sg.Button("save"), sg.Button("cancel")],
    ]

    return sg.Window("zk-ssg settings", layout)


def create_text_chooser(name: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for choosing text.

    Parameters
    ----------
    name : str
        The name of the setting and the input element, and the text that
        appears next to that element.
    settings : dict
        The settings to use.
    """
    try:
        default_text = settings[name]
    except KeyError:
        default_text = settings[name] = ""
    finally:
        return [sg.Text(name + ": "), sg.Input(key=name, default_text=default_text)]


def create_checkbox(title: str, key_name: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for a labelled checkbox.

    Parameters
    ----------
    title : str
        The text that appears next to the checkbox.
    key_name : str
        The name of the setting and the key of the checkbox element.
    settings : dict
        The settings to use.
    """
    return [sg.Checkbox(title, key=key_name, default=settings[key_name])]


def create_folder_chooser(name: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for choosing a folder.

    Parameters
    ----------
    name : str
        The name of the setting, the key of the input element, the target of
        the folder browse button element, and the text that button.
    settings : dict
        The settings to use.
    """
    return [
        sg.Text(name + " (folder): "),
        sg.FolderBrowse(target=name),
        sg.Input(key=name, default_text=settings[name]),
    ]


def create_color_chooser(name: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for choosing a color.

    Parameters
    ----------
    name : str
        The name of the setting, the key of the input element, the target of
        the color chooser button element, and the text that appears next to
        the button.
    settings : dict
        The settings to use.
    """
    return [
        sg.Text(name + ": "),
        sg.ColorChooserButton("choose", target=name),
        sg.Input(key=name, default_text=settings[name]),
    ]


def filter_items(settings: dict) -> dict:
    """Removes some dict items automatically generated by PySimpleGUI.

    Removes all items with keys that are not strings or that start with
    an uppercase letter.

    Parameters
    ----------
    settings : dict
        The settings to filter.
    """
    new_settings = dict()
    for key, value in settings.items():
        if isinstance(key, str):
            if key[0].islower():
                new_settings[key] = value
    return new_settings


def validate_settings(settings: dict) -> bool:
    """Detects any empty strings in the settings.

    Parameters
    ----------
    settings : dict
        The settings to validate.
    """
    for key, value in settings.items():
        if isinstance(value, str):
            if not value and key != "internal html link prefix":
                return False
    return True
