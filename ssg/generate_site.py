import os
import re
import webbrowser
import shutil
import PySimpleGUI as sg  # https://pysimplegui.readthedocs.io/en/latest/
import send2trash  # https://pypi.org/project/Send2Trash/
from typing import List
from ssg.settings import (
    settings,
    show_settings_window,
    validate_settings,
)
from ssg.zettel import Zettel
from ssg.reformat_zettels import reformat_zettels
from ssg.reformat_html import reformat_html_files
from ssg.indexes import (
    edit_categorical_index_file,
    create_alphabetical_index_file,
    create_chronological_index_file,
)
from ssg.utils import (
    logging,
    show_progress,
    get_file_contents,
    copy_file_iff_not_present,
)

# TODO: add a way to control the size of individual images on the site.

def generate_site() -> None:
    """Generates all the site's files."""
    global settings
    show_progress(0)
    logging.info("Getting the application settings.")
    if not validate_settings(settings.data):
        settings = show_settings_window(settings)
    site_path = settings["site folder path"]

    logging.info("Finding zettels that contain `#published`.")
    show_progress(2)
    zettels = get_zettels_to_publish(settings["zettelkasten path"])
    logging.info(f"Found {len(zettels)} zettels that contain `#published`.")
    show_progress(50)

    logging.info("Creating the pages folder if it doesn't already exist.")
    site_pages_path = os.path.join(site_path, settings["site subfolder name"])
    try:
        os.mkdir(site_pages_path)
    except FileExistsError:
        pass

    logging.info("Deleting all markdown files currently in the pages folder.")
    delete_site_md_files(site_pages_path)

    logging.info(f"Copying the zettels to {site_path}")
    show_progress(55)
    zettels: List[Zettel] = copy_zettels_to_site_folder(
        zettels, site_path, site_pages_path
    )

    logging.info("Creating index files of all published zettels.")
    show_progress(60)
    create_md_index_files(zettels, site_path, settings["hide chrono index dates"])

    logging.info("Searching for any attachments that are linked to in the zettels.")
    show_progress(65)
    n: int = copy_attachments(zettels, site_pages_path)
    logging.info(f"Found {n} attachments and copied them to {site_pages_path}")

    reformat_zettels(zettels)
    show_progress(70)
    new_html_paths: List[str] = regenerate_html_files(
        zettels, site_path, site_pages_path
    )
    show_progress(75)
    reformat_html_files(site_path, new_html_paths)
    show_progress(85)

    logging.info("Checking for style.css.")
    check_style(site_path)
    show_progress(95)

    logging.info("\nGenerated HTML files:")
    for path in new_html_paths:
        logging.info(f"  {path}")

    show_progress(100)
    print(f"Successfully generated {len(new_html_paths)} HTML files.")


def create_md_index_files(
    zettels: List[Zettel], site_path: str, hide_chrono_index_dates: bool
) -> None:
    """Creates markdown files that list all the published zettels

    The files created are alphabetical-index.md and
    chronological-index.md. The file index.md is also edited, and must
    already exist.

    Parameters
    ----------
    zettels : List[Zettel]
        The list of zettels to create the index files for.
    site_path : str
        The path to the site's folder.
    hide_chrono_index_dates : bool
        Whether to hide the dates in the chronological index.
    """
    edit_categorical_index_file(zettels)
    create_alphabetical_index_file(zettels, site_path)
    create_chronological_index_file(zettels, site_path, hide_chrono_index_dates)


def regenerate_html_files(
    zettels: List[Zettel], site_path: str, site_pages_path: str
) -> List[str]:
    """Creates new and deletes old HTML files

    May overwrite some HTML files. Old HTML files that were listed in
    ssg-ignore.txt are saved and not changed at all.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to generate HTML files from.
    site_path : str
        The path to the site folder.
    site_pages_path : str
        The path to the pages folder within the site folder.
    """
    old_html_paths = get_file_paths(site_path, [".html"]) + get_file_paths(
        site_pages_path, [".html"]
    )
    logging.info("Creating html files from the md files.")
    new_html_paths = create_html_files(zettels)
    for i, path in enumerate(new_html_paths):
        new_html_paths[i] = os.path.normpath(path)

    logging.info(
        "Deleting any HTML files that were not just generated and "
        "were not listed in ssg-ignore.txt."
    )
    delete_old_html_files(old_html_paths, new_html_paths, site_pages_path)

    return new_html_paths


def create_html_files(zettels: List[Zettel]) -> List[str]:
    """Creates HTML files from markdown files into the site folder

    Expects the zettels to already be in the site folder. Returns all
    the new HTML files' paths.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to create HTML files from.
    """
    new_html_file_paths = []
    for zettel in zettels:
        new_html_file_path = zettel.create_html_file()
        new_html_file_paths.append(new_html_file_path)
    return new_html_file_paths


def copy_attachments(zettels: List[Zettel], site_pages_path: str) -> int:
    """Copies files linked to in the zettels into the site folder.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to copy the attachments from.
    site_pages_path : str
        The path to the pages folder within the site folder.
    """
    attachment_paths = get_all_attachment_paths(zettels)
    for path in attachment_paths:
        try:
            shutil.copy(path, site_pages_path)
        except shutil.SameFileError:
            _, file_name = os.path.split(path)
            logging.info(f"  Did not copy {file_name} because it is already there.")
    # TODO: find and request to delete unused attachments

    return len(attachment_paths)


def copy_zettels_to_site_folder(
    zettels: List[Zettel], site_path: str, site_pages_path: str
) -> List[Zettel]:
    """Copies zettels to the site folder

    Returns the zettels with their new paths.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to copy.
    site_path : str
        The path to the site folder.
    site_pages_path : str
        The path to the pages folder within the site folder.
    """
    for i, zettel in enumerate(zettels):
        if zettel.file_name not in settings["root pages"]:
            new_path = shutil.copy(zettel.path, site_pages_path)
            zettels[i].path = new_path
        else:
            new_path = shutil.copy(zettel.path, site_path)
            zettels[i].path = new_path
    return zettels


def get_zettels_to_publish(zettelkasten_path: str) -> List[Zettel]:
    """Gets all the zettels that contain '#published'.

    Parameters
    ----------
    zettelkasten_path : str
        The path to the zettelkasten folder."""
    zettel_paths = get_paths_of_zettels_to_publish(zettelkasten_path)
    zettels = []
    for path in zettel_paths:
        zettels.append(Zettel(path))
    return zettels


def get_paths_of_zettels_to_publish(zettelkasten_path: str) -> List[str]:
    """Gets the paths of all zettels that contain '#published'.

    Parameters
    ----------
    zettelkasten_path : str
        The path to the zettelkasten folder.
    """
    zettel_paths = get_file_paths(zettelkasten_path, settings["zettel file types"])
    zettels_to_publish = []
    progress_conversion_ratio = 39 / len(zettel_paths)
    iter_count = 0
    for i, zettel_path in enumerate(zettel_paths):
        contents = get_file_contents(zettel_path, "utf8")
        match = settings["patterns"]["published tag"].search(contents)
        if match:
            zettels_to_publish.append(zettel_path)
        if iter_count == 500:
            iter_count = 0
            show_progress(10 + i * progress_conversion_ratio)  # range: 10 to <= 49
        else:
            iter_count += 1
    return zettels_to_publish


def delete_site_md_files(site_pages_path: str) -> None:
    """Permanently deletes all the markdown files in the site folder.

    Parameters
    ----------
    site_pages_path : str
        The path to the site folder.
    """
    md_paths = get_file_paths(site_pages_path, settings["zettel file types"])
    for path in md_paths:
        os.remove(path)


def get_file_paths(dir_path: str, file_extensions: List[str]) -> List[str]:
    """Gets the paths of files in a directory

    Only paths of files with the given file extension are included.

    Parameters
    ----------
    dir_path : str
        The path to the directory to get the file paths of.
    file_extensions : List[str]
        The file extensions to filter by. All letters must be lowercase.
        Including the extension's leading period is recommended.
    """
    file_names = os.listdir(dir_path)
    file_paths = []
    for file_name in file_names:
        for extension in file_extensions:
            if file_name.lower().endswith(extension):
                file_path = os.path.join(dir_path, file_name)
                file_paths.append(file_path)
    return file_paths


def get_attachment_paths(contents: str, folder_path: str) -> List[str]:
    """Gets all absolute and relative paths to files and folders in markdown links.

    Parameters
    ----------
    contents : str
        The contents of the markdown file to search in.
    folder_path : str
        The absolute path to the folder containing the markdown file.

    Returns
    -------
    List[str]
        A list of paths to files and/or folders.
    """
    file_paths: List[str] = []
    paths: List[str] = settings["patterns"]["link path"].findall(contents)
    for path in paths:
        file_path = os.path.join(folder_path, path)
        file_path = os.path.normpath(file_path)
        if os.path.exists(file_path):
            file_paths.append(file_path)
    return file_paths


def get_all_attachment_paths(zettels: List[Zettel]) -> List[str]:
    """Gets the file and folder attachment paths in multiple zettels.

    Both absolute and relative paths are included.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels from which to get the file and folder attachment paths.
    """
    all_attachment_paths = []
    for zettel in zettels:
        with open(zettel.path, "r", encoding="utf8") as file:
            contents = file.read()
        all_attachment_paths.extend(get_attachment_paths(contents, zettel.folder_path))
    return all_attachment_paths


def check_style(site_path: str) -> None:
    """Copies style.css into the site folder and settings into style.css.

    If style.css is already there, this function only tries to update
    the file.

    Parameters
    ----------
    site_path : str
        The path to the site folder.
    """
    site_style_path = copy_file_iff_not_present("style.css", site_path)
    try:
        update_css(site_style_path)
    except ValueError:
        logging.error("  style.css cannot be parsed.")


def update_css(site_style_path: str) -> None:
    """Updates the site's copy of style.css with the user's settings.

    Raises ValueError if the file cannot be parsed.

    Parameters
    ----------
    site_style_path : str
        The path to the site's style.css.
    """
    with open(site_style_path, "r", encoding="utf8") as file:
        contents = file.read()

    body_color_pattern = re.compile(
        r"(?<=html body {\n    background-color: ).+(?=;\n)"
    )
    header_color_pattern = re.compile(r"(?<=header {\n    background-color: ).+(?=;\n)")
    header_text_color_pattern = re.compile(r"(?<=nav a {\n    color: ).+(?=;\n)")
    header_hover_color_pattern = re.compile(r"(?<=nav a:hover {\n    color: ).+(?=;\n)")
    body_link_color_pattern = re.compile(r"(?<=main a {\n    color: ).+(?=;\n)")
    body_hover_color_pattern = re.compile(r"(?<=main a:hover {\n    color: ).+(?=;\n)")

    color_patterns = [
        (body_color_pattern, settings["body background color"]),
        (header_color_pattern, settings["header background color"]),
        (header_text_color_pattern, settings["header text color"]),
        (header_hover_color_pattern, settings["header hover color"]),
        (body_link_color_pattern, settings["body link color"]),
        (body_hover_color_pattern, settings["body hover color"]),
    ]

    for p, s in color_patterns:
        contents, n = p.subn(s, contents, 1)
        if not n:
            raise ValueError

    with open(site_style_path, "w", encoding="utf8") as file:
        file.write(contents)


def delete_old_html_files(
    old_html_paths: List[str], new_html_paths: List[str], site_pages_path: str
) -> None:
    """Deletes HTML files that are not being generated or saved

    A file can be marked to be saved by putting its absolute path on a new line
    in ssg-ignore.txt.

    Parameters
    ----------
    old_html_paths : List[str]
        The paths of HTML files present before the #published zettels were
        converted to HTML.
    new_html_paths : List[str]
        The paths of the new HTML files created from the #published zettels.
    site_pages_path : str
        The path to the site's pages folder.
    """
    file_name = os.path.join(site_pages_path, "ssg-ignore.txt")
    try:
        with open(file_name, "r", encoding="utf8") as file:
            ignored_html_paths = file.read().split("\n")
    except FileNotFoundError:
        logging.info("  ssg-ignore.txt not found")
        ignored_html_paths = []

    for i, path in enumerate(ignored_html_paths):
        ignored_html_paths[i] = os.path.normpath(path)

    old_count = 0
    for old_path in old_html_paths:
        old_path = os.path.normpath(old_path)
        if (
            old_path not in new_html_paths
            and not old_path.endswith("footer.html")
            and not old_path.endswith("header.html")
        ):
            if old_path not in ignored_html_paths:
                old_count += 1
                show_delete_confirmation_menu(old_path)
    if not old_count:
        logging.info("No old HTML files found.")
    else:
        logging.info(f"  Deleted {old_count} files.")


def show_delete_confirmation_menu(old_path: str) -> None:
    """Requests to open, delete, or save an HTML file and handles those events."""
    layout = [
        [sg.Text(f"Old HTML file found: {old_path}.\nReady to move to trash.")],
        [sg.Open(), sg.Button("Delete"), sg.Cancel()],
    ]
    window = sg.Window(title="Delete?", layout=layout, disable_close=True)
    while True:
        event, _ = window.read()
        if event == "Open":
            webbrowser.open(old_path, new=2)
        elif event == "Delete":
            send2trash.send2trash(old_path)
            sg.popup(f"Moved file to trash: {old_path}.")
            window.close()
            return
        else:
            sg.popup(f"Saved {old_path}.")
            window.close()
            return
