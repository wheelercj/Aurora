# external imports
from typing import List, Optional, Callable
import logging

# internal imports
from zettel import Zettel, get_zettel_by_id
from patterns import patterns


md_linker_type = Callable[[Zettel, Zettel], str]


def convert_links_from_zk_to_md(
        zettels: List[Zettel] = [],
        zettel_paths: List[str] = [],
        md_linker: Optional[md_linker_type] = None) -> None:
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
    md_linker : Optional[Callable[[Zettel, Zettel], str]]
        A function that takes two zettels as arguments and returns a 
        markdown link from the first zettel to the second one. Only 
        needed for custom link formatting or if the zettels are not in 
        the same folder.
    """
    if zettel_paths:
        zettels.extend([Zettel(z) for z in zettel_paths])
    if md_linker is None:
        md_linker = lambda _, linked_z: \
            f'[{linked_z.title}]({linked_z.file_name})'
    for zettel in zettels:
        convert_zettel_links_from_zk_to_md(zettel, zettels, md_linker)


def convert_zettel_links_from_zk_to_md(
        zettel: Zettel,
        zettels: List[Zettel],
        md_linker: md_linker_type) -> None:
    """Converts links in one zettel from the zk to the md format.
    
    Logs warnings for links that have valid IDs but outdated titles.

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
    link_ids: List[str] = patterns.zettel_link_id.findall(contents)
    for link_id in set(link_ids):
        linked_z = get_zettel_by_id(link_id, zettels)
        if linked_z.link not in contents:
            logging.warning(f'`{zettel.title}` has a link with a valid ID ' \
                f'but an outdated title. It should be: {linked_z.link}')
        
        markdown_link = md_linker(zettel, linked_z)
        contents = contents.replace(linked_z.link, markdown_link)

    save_zettel(contents, zettel)


def save_zettel(contents: str, zettel: Zettel) -> None:
    """Overwrites a zettel with new contents."""
    with open(zettel.path, 'w', encoding='utf8') as file:
        file.write(contents)


def get_contents(zettel: Zettel) -> Optional[str]:
    """Gets the contents of a zettel.
    
    Logs a warning if attempting to open the zettel raises OSError.

    Returns
    -------
    str or None
        The zettel's contents, or None if attempting to open the zettel 
        raises OSError.
    """
    try:
        with open(zettel.path, 'r', encoding='utf8') as file:
            contents = file.read()
    except OSError:
        logging.warning(f'  Zettel not found: `{zettel.title}` at ' \
            f'{zettel.path}')
        return None
    else:
        return contents
