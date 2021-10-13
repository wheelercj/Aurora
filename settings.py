from datetime import datetime
import json
from typing import Dict, Union, Optional
import PySimpleGUI as sg  # https://pysimplegui.readthedocs.io/en/latest/


def show_settings_window(settings: Optional[dict] = None) -> Dict[str, Union[str, bool]]:
    """Runs the settings menu."""
    if not settings:
        settings = load_settings(fallback_option='default settings')
    window = create_settings_window(settings)
    event, values = window.read()
    if event != sg.WIN_CLOSED and event != 'cancel':
        save_settings(values)
    window.close()
    return values


def load_settings(fallback_option: str) -> Dict[str, Union[str, bool]]:
    """Gets the user's settings.
    
    The settings are retrieved from settings.json if the file exists and
    is not empty. Otherwise, they are retrieved directly from the user 
    via a settings menu or from default settings in the code depending
    on the chosen fallback option.
    
    Parameters
    ----------
    fallback_option : str
        Can be "default settings" or "prompt user".

    Raises
    ------
    ValueError
        If a valid fallback option was not chosen and is needed.

    Returned Dictionary Items
    -------------------------
    'zettelkasten path' : str
        The absolute path to the zettelkasten folder.
    'site path' : str
        The absolute path to the root folder of the site's files.
    'site title' : str
        The title that will appear at the top of the site.
    'copyright text' : str
        The copyright notice that will appear at the bottom of the 
        index page.
    'site subfolder name' : str
        The name of the folder within the site folder that most of the 
        HTML pages will be placed in by default.
    'body background color' : str
        The color of the background of the site as a hex RGB string.
    'header background color' : str
        The color of the background of the header as a hex RGB string.
    'header text color' : str
        The color of the text in the header as a hex RGB string.
    'header hover color' : str
        The color of links in the header when they are hovered over, as 
        a hex RGB string.
    'body link color' : str
        The color of links in the body, as a hex RGB string.
    'body hover color' : str
        The color of links in the body when they are hovered over, as 
        a hex RGB string.
    'hide tags' : bool
        If true, tags will be removed from the copied zettels when 
        generating the site.
    'hide chrono index dates' : bool
        If true, file creation dates will not be shown in the 
        chronological index.
    """
    try:
        with open('settings.json', 'r', encoding='utf8') as file:
            settings = json.load(file)
        if not settings:
            raise FileNotFoundError
    except FileNotFoundError:
        if fallback_option == 'default settings':
            settings = get_default_settings()
        elif fallback_option == 'prompt user':
            settings = show_settings_window()
        else:
            raise ValueError

    return settings


def save_settings(settings: dict) -> None:
    """Saves the user's settings to settings.json."""
    with open('settings.json', 'w', encoding='utf8') as file:
        json.dump(settings, file)


def get_default_settings() -> Dict[str, Union[str, bool]]:
    """Gets the application's default user settings."""
    this_year = datetime.now().year
    return {
        'zettelkasten path': '',
        'site path': '',
        'site title': '',
        'copyright text': f'© {this_year}, your name',
        'site subfolder name': 'pages',
        'body background color': '#fffafa',  # snow
        'header background color': '#81b622',  # lime green
        'header text color': '#ecf87f',  # yellow green
        'header hover color': '#3d550c',  # olive green
        'body link color': '#59981a',  # green
        'body hover color': '#3d550c',  # olive green
        'hide tags': True,
        'hide chrono index dates': True
    }


def create_settings_window(settings: Optional[dict] = None) -> sg.Window:
    """Creates and displays the settings menu."""
    sg.theme('DarkAmber')

    general_tab_layout = [
        create_text_chooser('site title', settings),
        create_text_chooser('copyright text', settings),
        create_text_chooser('site subfolder name', settings),

        create_folder_chooser('site path', settings),
        create_folder_chooser('zettelkasten path', settings),

        create_checkbox('hide tags', 'hide tags', settings),
        create_checkbox('hide dates in the chronological index',
                        'hide chrono index dates',
                        settings),
    ]

    color_tab_layout = [
        create_color_chooser('body background color', settings),
        create_color_chooser('header background color', settings),
        create_color_chooser('header text color', settings),
        create_color_chooser('header hover color', settings),
        create_color_chooser('body link color', settings),
        create_color_chooser('body hover color', settings),
    ]

    layout = [
        [sg.TabGroup([[
            sg.Tab('general', general_tab_layout),
            sg.Tab('color', color_tab_layout)]])],
        [sg.HorizontalSeparator()],
        [sg.Button('save'), sg.Button('cancel')] ]

    return sg.Window('zk-ssg settings', layout)


def create_text_chooser(name: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for choosing text."""
    try:
        default_text = settings[name]
    except KeyError:
        default_text = settings[name] = ''
    finally:
        return [sg.Text(name + ': '),
                sg.Input(key=name,
                default_text=default_text)]


def create_checkbox(title: str, key_name: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for a labelled checkbox."""
    return [sg.Checkbox(title,
        key=key_name,
        default=settings[key_name])]

    
def create_folder_chooser(name: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for choosing a folder."""
    return [sg.Text(name + ' (folder): '),
        sg.FolderBrowse(target=name),
        sg.Input(key=name,
            default_text=settings[name])]


def create_color_chooser(name: str, settings: dict) -> list:
    """Creates PySimpleGUI elements for choosing a color."""
    return [sg.Text(name + ': '),
        sg.ColorChooserButton('choose',
            target=name),
        sg.Input(key=name,
            default_text=settings[name])]
