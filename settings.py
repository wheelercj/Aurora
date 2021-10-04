from datetime import datetime
import json
from typing import Dict, Union, Optional
import PySimpleGUI as sg  # https://pysimplegui.readthedocs.io/en/latest/


def show_settings_window(settings: Optional[dict]) -> Dict[str, Union[str, bool]]:
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
        [sg.Text('body background color: '),
            sg.ColorChooserButton('choose',
                target='body background color'),
            sg.Input(key='body background color',
                default_text=settings['body background color'])],
        [sg.Text('header background color: '),
            sg.ColorChooserButton('choose',
                target='header background color'),
            sg.Input(key='header background color',
                default_text=settings['header background color'])],
        [sg.Text('header text color: '),
            sg.ColorChooserButton('choose',
                target='header text color'),
            sg.Input(key='header text color',
                default_text=settings['header text color'])],
        [sg.Text('header hover color: '),
            sg.ColorChooserButton('choose',
                target='header hover color'),
            sg.Input(key='header hover color',
                default_text=settings['header hover color'])],
        [sg.Text('body link color: '),
            sg.ColorChooserButton('choose',
                target='body link color'),
            sg.Input(key='body link color',
                default_text=settings['body link color'])],
        [sg.Text('body hover color: '),
            sg.ColorChooserButton('choose',
                target='body hover color'),
            sg.Input(key='body hover color',
                default_text=settings['body hover color'])],
        [sg.Checkbox('hide tags',
            key='hide tags',
            default=settings['hide tags'])],
        [sg.Checkbox('hide dates in the chronological index',
            key='hide chrono index dates',
            default=settings['hide chrono index dates'])],
        [sg.HorizontalSeparator()],
        [sg.Button('save'), sg.Button('cancel')] ]

    return sg.Window('zk-ssg settings', layout)

