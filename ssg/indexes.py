import os
import sys
from typing import List, Dict
import PySimpleGUI as sg
from ssg.zettel import Zettel
from ssg.settings import settings


def edit_categorical_index_file(zettels: List[Zettel]) -> None:
    """Lists all the zettels categorically in index.md

    index.md must already exist and contain the `#published` tag and the
    other tags that will be replaced by the zettel links to the zettels
    that contain those tags.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to list.
    """
    index_zettel = None
    for zettel in zettels:
        if "index.md" == zettel.file_name_and_ext:
            index_zettel = zettel
    if index_zettel is None:
        sg.popup("index.md is required but was not found.")
        sys.exit("index.md is required but was not found.")
    with open(index_zettel.path, "r", encoding="utf8") as file:
        index_contents = file.read()
    index_tags: List[str] = settings["patterns"]["tag"].findall(index_contents)
    if "#published" not in index_tags:
        sg.popup("index.md must have the #published tag.")
        sys.exit("index.md must have the #published tag.")
    index_tags.remove("#published")
    categories: Dict[str, str] = create_categorical_indexes(zettels, index_tags)
    for tag, links in categories.items():
        index_contents = index_contents.replace(tag, links, 1)
    with open(index_zettel.path, "w", encoding="utf8") as file:
        file.write(index_contents)


def create_alphabetical_index_file(zettels: List[Zettel], site_path: str) -> None:
    """Lists all the zettels alphabetically in a new markdown file.

    The file will be created in the site folder.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to list.
    site_path : str
        The path to the site folder.
    """
    index = create_alphabetical_index(zettels)
    index_file_path = os.path.join(site_path, "alphabetical-index.md")
    with open(index_file_path, "w", encoding="utf8") as file:
        file.write(index)
    zettels.append(Zettel(index_file_path))


def create_chronological_index_file(
    zettels: List[Zettel], site_path: str, hide_chrono_index_dates: bool
) -> None:
    """Lists all the zettels chronologically in a new markdown file.

    The file will be created in the site folder.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to list.
    site_path : str
        The path to the site folder.
    hide_chrono_index_dates : bool
        Whether to hide the dates in the chronological index.
    """
    index = create_chronological_index(zettels, hide_chrono_index_dates)
    index_file_path = os.path.join(site_path, "chronological-index.md")
    with open(index_file_path, "w", encoding="utf8") as file:
        file.write(index)
    zettels.append(Zettel(index_file_path))


def create_categorical_indexes(
    zettels: List[Zettel], index_tags: List[str]
) -> Dict[str, str]:
    """Creates categorical markdown lists of all zettels' links

    The returned dict's keys are tags and its values are the link lists.
    Excludes zettels that have alpha characters in their IDs.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to list.
    index_tags : List[str]
        The tags to categorize.
    """
    categories: Dict[list] = dict()
    unlinked_zettels: List[Zettel] = list(zettels)
    for index_tag in index_tags:
        categories[index_tag] = []
        for zettel in zettels:
            if zettel.file_name not in settings["root pages"]:
                if index_tag in zettel.tags:
                    categories[index_tag].append("* " + zettel.link)
                    unlinked_zettels.remove(zettel)
    for zettel in unlinked_zettels:
        if zettel.file_name not in settings["root pages"]:
            if "#other" not in categories:
                categories["#other"] = []
            categories["#other"].append("* " + zettel.link)
    for key, value in categories.items():
        categories[key] = "\n".join(value)
    return categories


def create_alphabetical_index(zettels: List[Zettel]) -> str:
    """Creates an alphabetized markdown list of all zettels' links

    Excludes zettels that have alpha characters in their IDs.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to list.
    """
    numeric_links = []
    sorted_zettels = sorted(zettels, key=lambda z: z.title.lower())
    for zettel in sorted_zettels:
        if zettel.file_name not in settings["root pages"]:
            numeric_links.append("* " + zettel.link)
    zettel_index = "## alphabetical index\n\n" + "\n".join(numeric_links)
    return zettel_index


def create_chronological_index(
    zettels: List[Zettel], hide_chrono_index_dates: bool
) -> str:
    """Creates a chronologized markdown list of all zettels' links

    Excludes zettels that have alpha characters in their IDs.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to list.
    hide_chrono_index_dates : bool
        Whether to hide the dates in the chronological index.
    """
    z_with_id_links = []
    non_root_zettels = [
        zettel for zettel in zettels if zettel.file_name not in settings["root pages"]
    ]
    zettels_with_ids = [zettel for zettel in non_root_zettels if zettel.id is not None]
    zettels_with_ids = sorted(zettels_with_ids, key=lambda z: z.id, reverse=True)
    if hide_chrono_index_dates:
        for zettel in zettels_with_ids:
            z_with_id_links.append("* " + zettel.link)
    else:
        for zettel in zettels_with_ids:
            date = f"{zettel.id[0:4]}/{zettel.id[4:6]}/{zettel.id[6:8]}"
            z_with_id_links.append("* " + date + " " + zettel.link)
    zettel_index = "## chronological index\n\n"
    if not hide_chrono_index_dates:
        zettel_index += "_Dates shown here are the original file creation dates, not necessarily latest edit or post dates._\n\n"
    zettel_index += "\n".join(z_with_id_links)
    zettels_without_ids = [
        zettel for zettel in non_root_zettels if zettel.id is None
    ]
    z_without_id_links = []
    for zettel in zettels_without_ids:
        z_without_id_links.append("* " + zettel.link)
    if z_without_id_links:
        zettel_index += "\n\n### undated pages\n\n" + "\n".join(z_without_id_links)
    return zettel_index
