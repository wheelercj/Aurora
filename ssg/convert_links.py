from typing import Callable
from typing import List
from typing import Optional

import PySimpleGUI as sg

from ssg.settings import get_zk_link_contents_pattern
from ssg.settings import settings
from ssg.utils import logging
from ssg.zettel import get_zettel_by_id_or_file_name
from ssg.zettel import Zettel


md_linker_type = Callable[[Zettel, Zettel], str]


def convert_links_from_zk_to_md(
    zettels: List[Zettel] = [],
    zettel_paths: List[str] = [],
    md_linker: md_linker_type = None,
) -> None:
    """Converts links in multiple zettels from the zk to the md format.

    Logs warnings for links that have valid IDs but outdated titles.

    Parameters
    ----------
    zettels : List[Zettel]
        All of the zettels to convert links in. Only needed if
        zettel_paths is an empty list.
    zettel_paths : List[str]
        The paths of all the zettels to convert links in. Only needed if
        zettels is an empty list. If both zettels and zettel_paths are
        not empty, they will both be used.
    md_linker : Callable[[Zettel, Zettel], str], None
        A function that takes two zettels as arguments and returns a
        markdown link from the first zettel to the second one. Only
        needed for custom link formatting or if the zettels are not in
        the same folder.
    """
    if zettel_paths:
        zettels.extend([Zettel(z) for z in zettel_paths])
    if md_linker is None:
        md_linker = (
            lambda _, linked_z: f"[{linked_z.title}]({linked_z.file_name_and_ext})"
        )
    for zettel in zettels:
        convert_zettel_links_from_zk_to_md(zettel, zettels, md_linker)


def convert_zettel_links_from_zk_to_md(
    zettel: Zettel,
    zettels: List[Zettel],
    md_linker: md_linker_type,
) -> None:
    """Converts links in one zettel from the zk to the md format.

    Shows a warning message if any of the internal links are broken. Also logs
    warnings for links that are broken or have unexpected formats.

    Parameters
    ----------
    zettel : Zettel
        The zettel to convert links in.
    zettels : List[Zettel]
        All of the zettels that might be linked to.
    md_linker : Callable[[Zettel, Zettel], str]
        A function that takes two zettels as arguments and returns a
        markdown link from the first zettel to the second one.
    """
    contents = get_contents(zettel)
    if not contents:
        return
    links_content: List[str] = get_zk_link_contents_pattern().findall(contents)
    for link_content in set(links_content):
        link = f"{settings['zk link start']}{link_content}{settings['zk link end']}"
        linked_z = get_zettel_by_id_or_file_name(link_content, zettels)
        if linked_z is None:
            logging.warning(
                f'Broken link detected: "{link}" in "{zettel.title}" at {zettel.path}'
            )
            sg.popup(f'Warning: broken internal link in "{zettel.title}": {link}')
            continue
        if linked_z.link not in contents and linked_z.alt_link not in contents:
            logging.warning(
                f'Unexpected zettel link format: "{link}"\n'
                f'  Expected format: "{zettel.link}"\n'
                f'  in "{zettel.title}" at {zettel.path}'
            )
        markdown_link = md_linker(zettel, linked_z)
        contents = contents.replace(f"{link} {linked_z.title}", markdown_link)
        contents = contents.replace(link, markdown_link)
    with open(zettel.path, "w", encoding="utf8") as file:
        file.write(contents)


def get_contents(zettel: Zettel) -> Optional[str]:
    """Gets the contents of a zettel.

    Logs a warning if attempting to open the zettel raises OSError.

    Parameters
    ----------
    zettel : Zettel
        The zettel to get the contents of.

    Returns
    -------
    str or None
        The zettel's contents, or None if attempting to open the zettel
        raises OSError.
    """
    try:
        with open(zettel.path, "r", encoding="utf8") as file:
            contents = file.read()
    except OSError:
        logging.warning(f"  Zettel not found: `{zettel.title}` at {zettel.path}")
        return None
    else:
        return contents
