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
'patterns' : Settings
    'absolute attachment link' : re.Pattern
        The pattern of a markdown link containing an absolute path to a file.
        The first capture group is the file's name and extension.
    'h1 content' : re.Pattern
        The pattern of a header of level 1.
    'link path' : re.Pattern
        The pattern of a markdown link containing a path to a file or website,
        and the path may be either relative or absolute.
    'md ext in link' : re.Pattern
        The pattern of a markdown file path extension in a markdown link.
    'md link' : re.Pattern
        The pattern of a markdown link.
    'published tag' : re.Pattern
        The pattern of the ``#published`` tag.
    'single codeblock' : re.Pattern
        The pattern of a codeblock delimited by single backticks (an inline 
        codeblock).
    'tag' : re.Pattern
        The pattern of a tag, including a #. Assumes the tag is not at the very
        beginning of the string.
    'triple codeblock' : re.Pattern
        The pattern of a codeblock delimited by triple backticks.
    'zettel link id' : re.Pattern
        The pattern of a zettelkasten-style internal link that follows Zettlr's
        default settings (double square braces surrounding a 14-digit number).
'site folder path' : str
    The absolute path to the root folder of the site's files.
'site subfolder name' : str
    The name of the folder within the site folder that most of the HTML
    pages will be placed in by default.
'site title' : str
    The title that will appear at the top of the site.
'zettelkasten path' : str
    The absolute path to the zettelkasten folder.
"""
# 'internal zk link start' : str
#     The text that indicates the start of an internal zettelkasten link.
# 'internal zk link end' : str
#     The text that indicates the end of an internal zettelkasten link.
from datetime import datetime
import sys
import os
import re
import PySimpleGUI as sg  # https://pysimplegui.readthedocs.io/en/latest/
from tkinter.filedialog import askdirectory
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


def request_site_folder_path() -> str:
    """Prompts the user for the site's root folder path.

    Returns
    -------
    str
        The path to the site's root folder.
    """
    sg.PopupOK("Please select the folder that will contain the site's files.")
    return askdirectory(title="site folder", mustexist=True)


def request_zettelkasten_path() -> str:
    """Prompts the user for the zettelkasten folder path.

    Returns
    -------
    str
        The path to the zettelkasten folder.
    """
    sg.PopupOK("Please select the folder that contains the zettelkasten.")
    return askdirectory(title="zettelkasten folder", mustexist=True)


settings_folder_path = os.path.dirname(os.path.abspath(__file__))
settings_file_path = os.path.join(settings_folder_path, "settings.json")
this_year = datetime.now().year
settings = Settings(
    settings_file_path=settings_file_path,
    prompt_user_for_all_settings=show_settings_window,
    default_factories={
        "site folder path": request_site_folder_path,
        "zettelkasten path": request_zettelkasten_path,
    },
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
        "patterns": Settings(
            setting_dumper=lambda x: x.pattern,
            setting_loader=re.compile,
            data={
                "absolute attachment link": re.compile(
                    r"(?<=]\()(?:file://)?(?:[a-zA-Z]:|/)[^\n]*?([^\\/\n]+\.[a-zA-Z0-9]+)(?=\))"
                ),
                "link path": re.compile(r"(?<=]\().+(?=\))"),
                "h1 content": re.compile(r"(?<=#\s).+"),
                "md ext in link": re.compile(r"(?<=\S)\.md(?=\))"),
                "md link": re.compile(r"\[(.+)]\((.+)\)"),
                "published tag": re.compile(r"(?<=\s)#published(?=\s)"),
                "single codeblock": re.compile(r"(`[^`]+?`)"),
                "tag": re.compile(r"(?<=\s)#[a-zA-Z0-9_-]+"),
                "triple codeblock": re.compile(r"(?<=\n)(`{3}(.|\n)*?(?<=\n)`{3})"),
                "zettel link id": re.compile(r"(?<=\[\[)\d{14}(?=\]\])"),
            },
        ),
        "site subfolder name": "pages",
        "site title": "Site Title Here",
    },
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
        create_folder_chooser("site folder path", settings),
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
