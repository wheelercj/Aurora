from datetime import datetime
import json
from typing import Dict, Union
import PySimpleGUI as sg


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
        'hide tags': True,
        'hide chrono index dates': True
    }


def show_settings_window() -> Dict[str, Union[str, bool]]:
    """Creates and displays the settings menu."""
    layout = create_settings_window_layout()
    window = sg.Window('zk-ssg settings', layout)
    event, values = window.read()
    if event != sg.WIN_CLOSED and event != 'cancel':
        save_settings(values)
    window.close()
    return values


def create_settings_window_layout() -> list:
    """Prepares the settings menu appearance and content."""
    settings = load_settings(fallback_option='default settings')

    sg.theme('DarkAmber')
    layout = [  
        [sg.Text('site title: '),
            sg.Input(key='site title',
                default_text=settings['site title'])],
        [sg.Text('site folder path: '),
            sg.FolderBrowse(target='site path'),
            sg.Input(key='site path',
                default_text=settings['site path'])],
        [sg.Text('zettelkasten folder path: '),
            sg.FolderBrowse(target='zettelkasten path'),
            sg.Input(key='zettelkasten path',
                default_text=settings['zettelkasten path'])],
        [sg.Text('copyright text: '),
            sg.Input(key='copyright text',
                default_text=settings['copyright text'])],
        [sg.Checkbox('hide tags',
            key='hide tags',
            default=settings['hide tags'])],
        [sg.Checkbox('hide dates in the chronological index',
            key='hide chrono index dates',
            default=settings['hide chrono index dates'])],
        [sg.HorizontalSeparator()],
        [sg.Button('save'), sg.Button('cancel')] ]

    return layout
