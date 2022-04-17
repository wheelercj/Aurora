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
    'zk id' : re.Pattern
        The pattern of a zettel ID.
'root pages' : List[str]
    The list of file names (excluding the file extension) of the pages in the
    root folder of the site.
'site folder path' : str
    The absolute path to the root folder of the site's files.
'site subfolder name' : str
    The name of the folder within the site folder that most of the HTML
    pages will be placed in by default.
'site title' : str
    The title that will appear at the top of the site.
'zettel file types' : List[str]
    The list of file extensions that are considered to be zettels, including
    the period. All of the letters are lowercase. If this is changed, the
    "md ext in link" pattern will need to be updated.
'zettelkasten path' : str
    The absolute path to the zettelkasten folder.
'zk link end' : str
    The text that indicates the end of an internal zettelkasten link.
'zk link start' : str
    The text that indicates the start of an internal zettelkasten link.
"""


from datetime import datetime
import sys
import os
import re
from copy import deepcopy
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
    window = create_settings_window(settings.dump_to_dict())
    new_settings_obj = deepcopy(settings)
    settings_are_valid = False
    while not settings_are_valid:
        event, new_settings_dict = window.read()
        if event == sg.WIN_CLOSED:
            sys.exit(0)
        new_settings_dict = nest_items(filter_items(new_settings_dict))
        new_settings_obj.load_from_dict(new_settings_dict)
        settings_are_valid = validate_settings(new_settings_obj)
    window.close()
    if event == "cancel":
        return settings
    settings = new_settings_obj
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
        "patterns": Settings(
            setting_dumper=lambda x: x.pattern,
            setting_loader=re.compile,
            data={
                "absolute attachment link": re.compile(
                    r"(?<=]\()(?:file://)?(?:[a-zA-Z]:|/)[^\n]*?([^\\/\n]+\.[a-zA-Z0-9_-]+)(?=\))"
                ),
                "link path": re.compile(r"(?<=]\().+(?=\))"),
                "h1 content": re.compile(r"^# (.+)$"),
                "md ext in link": re.compile(r"(?i)(?<=\S)\.m(d|arkdown)(?=\))"),
                "md link": re.compile(r"\[(.+)]\((.+)\)"),
                "published tag": re.compile(r"(?<=\s)#published(?=\s)"),
                "single codeblock": re.compile(r"(`[^`]+?`)"),
                "tag": re.compile(r"(?<=\s)#[a-zA-Z0-9_-]+"),
                "triple codeblock": re.compile(r"(?<=\n)(`{3}(.|\n)*?(?<=\n)`{3})"),
                "zk id": re.compile(r"(\d{14})"),
            },
        ),
        "root pages": [
            "index",
            "about",
            "alphabetical-index",
            "chronological-index",
        ],
        "site folder path": "",
        "site subfolder name": "pages",
        "site title": "Site Title Here",
        "zettel file types": [".md", ".markdown"],
        "zettelkasten path": "",
        "zk link end": "]]",
        "zk link start": "[[",
    },
)


def get_zk_link_contents_pattern() -> re.Pattern:
    """Gets the pattern of the contents of a zettelkasten link.

    The pattern must contain either 0 or 1 capture groups.
    """
    zk_link_start = re.escape(settings["zk link start"])
    zk_link_end = re.escape(settings["zk link end"])
    return re.compile(f"{zk_link_start}(.+){zk_link_end}")


def get_zk_id_not_in_link_pattern() -> re.Pattern:
    """Gets the pattern of a zettel ID that is not in a zettelkasten link."""
    zk_link_start = re.escape(settings["zk link start"])
    zk_id_pattern = settings["patterns"]["zk id"].pattern
    return re.compile(rf"(?<!\\)(?<!{zk_link_start}){zk_id_pattern}")


def create_settings_window(settings: dict) -> sg.Window:
    """Creates and displays the settings menu.

    Parameters
    ----------
    settings : dict
        The settings data dictionary.
    """
    sg.theme("DarkAmber")

    general_tab_layout = [
        create_text_chooser("site title: ", "site title", settings),
        create_text_chooser("copyright text: ", "copyright text", settings),
        create_text_chooser("site subfolder name: ", "site subfolder name", settings),
        create_text_chooser(
            "internal HTML link prefix: ", "internal html link prefix", settings
        ),
        create_text_chooser(
            "ID regular expression: ", "patterns.zk id", settings["patterns"]
        ),
        create_text_chooser("link start: ", "zk link start", settings),
        create_text_chooser("link end: ", "zk link end", settings),
        create_folder_chooser(
            "site folder path (folder): ", "site folder path", settings
        ),
        create_folder_chooser(
            "zettelkasten path (folder): ", "zettelkasten path", settings
        ),
        create_checkbox("hide tags", "hide tags", settings),
        create_checkbox(
            "hide dates in the chronological index", "hide chrono index dates", settings
        ),
    ]

    color_tab_layout = [
        create_color_chooser(
            "body background color: ", "body background color", settings
        ),
        create_color_chooser(
            "header background color: ", "header background color", settings
        ),
        create_color_chooser("header text color: ", "header text color", settings),
        create_color_chooser("header hover color: ", "header hover color", settings),
        create_color_chooser("body link color: ", "body link color", settings),
        create_color_chooser("body hover color: ", "body hover color", settings),
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


def create_text_chooser(title: str, key: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for choosing text.

    Parameters
    ----------
    title : str
        The text that appears next to the input element.
    key : str
        The key of the setting. If the key contains periods, only the last part
        after all the periods is used as the key when accessing the settings
        dictionary.
    settings : dict
        The settings data dictionary.
    """
    try:
        default_text = settings[key.split(".")[-1]]
    except KeyError:
        default_text = settings[key.split(".")[-1]] = ""
    finally:
        return [sg.Text(title), sg.Input(key=key, default_text=default_text)]


def create_checkbox(title: str, key: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for a labelled checkbox.

    Parameters
    ----------
    title : str
        The text that appears next to the checkbox.
    key : str
        The key of the setting.
    settings : dict
        The settings data dictionary.
    """
    return [sg.Checkbox(title, key=key, default=settings[key])]


def create_folder_chooser(title: str, key: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for choosing a folder.

    Parameters
    ----------
    title : str
        The text that appears next to the input element.
    key : str
        The key of the setting.
    settings : dict
        The settings data dictionary.
    """
    return [
        sg.Text(title),
        sg.FolderBrowse(target=key),
        sg.Input(key=key, default_text=settings[key]),
    ]


def create_color_chooser(title: str, key: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for choosing a color.

    Parameters
    ----------
    title : str
        The text that appears next to the input element.
    key : str
        The key of the setting.
    settings : dict
        The settings data dictionary.
    """
    return [
        sg.Text(title),
        sg.ColorChooserButton("choose", target=key),
        sg.Input(key=key, default_text=settings[key]),
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


def nest_items(settings: dict) -> dict:
    """Nests dict items whose keys contain one or more periods.

    For example, if a setting is `settings["a.b.c"] = "value"`, it is moved to
    `settings["a"]["b"]["c"] = "value"`. Any settings whose keys do not contain
    periods are not changed.

    Parameters
    ----------
    settings : dict
        The settings to try to nest.
    """
    new_settings = dict()
    for key, value in settings.items():
        if "." in key:
            new_settings[key.split(".")[0]] = nest_items(
                {key.split(".")[1]: value}
            )
        else:
            new_settings[key] = value
    return new_settings


def validate_settings(settings: Settings) -> bool:
    """Detects any invalid settings and can show a popup with an error message.

    Parameters
    ----------
    settings : Settings
        The settings to validate.
    """
    if "patterns" in settings and settings["patterns"]["zk id"].groups > 1:
        sg.popup("The ID regular expression must have one or no capturing groups.")
        return False
    if not os.path.exists(settings["zettelkasten path"]) or not os.path.isdir(
        settings["zettelkasten path"]
    ):
        sg.popup("The zettelkasten path does not exist.")
        return False
    if not os.path.exists(settings["site folder path"]) or not os.path.isdir(
        settings["site folder path"]
    ):
        sg.popup("The site folder path does not exist.")
        return False
    this_dir, _ = os.path.split(__file__)
    settings["site folder path"] = os.path.normpath(settings["site folder path"])
    settings["zettelkasten path"] = os.path.normpath(settings["zettelkasten path"])
    if 3 > len({this_dir, settings["site folder path"], settings["zettelkasten path"]}):
        error_message = (
            "Error: the zettelkasten, the website's files, and this program's files"
            " should be in different folders."
        )
        sg.popup(error_message)
        return False
    for key, value in settings.items():
        if isinstance(value, str):
            if not value and key != "internal html link prefix":
                sg.popup(
                    'Each setting must be given a value, except the "internal html link'
                    ' prefix" setting.'
                )
                return False
    return True


settings.load(fallback_option="prompt user")
