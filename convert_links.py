# external imports
import re
from typing import List, Tuple, Optional
import logging

# internal imports
from zettel import Zettel, get_zettel_by_id


def convert_links_from_zk_to_md(zettels: List[Zettel]) -> None:
    """Converts links in multiple zettels from the zk to the md format."""
    logging.info(f'Converting internal links from the zk to the md format.')
    link_id_pattern = re.compile(r'(?<=\[\[)\d{14}(?=\]\])')
    total_char_count = 0
    total_n_replaced = 0

    for zettel in zettels:
        contents = get_contents(zettel)
        if contents is None:
            continue

        char_count_1 = len(contents)
        n_replaced, contents = convert_links(link_id_pattern,
                                             contents,
                                             zettel,
                                             zettels)
        char_count_2 = len(contents)

        # Save contents back to the zettel.
        if n_replaced:
            with open(zettel.path, 'w', encoding='utf8') as file:
                file.write(contents)

        # Log character change stats.
        char_count = char_count_2 - char_count_1
        if n_replaced:
            logging.info(f'    Changed `{zettel.title}` by {char_count} ' \
                f'characters with {n_replaced} links converted.')
        total_char_count += char_count
        total_n_replaced += n_replaced

    logging.info(f'  Changed {len(zettels)} zettels by a total of ' \
        f'{total_char_count} characters with {total_n_replaced} links ' \
        'converted from the zk to the md format.')


def get_contents(zettel: Zettel) -> Optional[str]:
    """Gets the contents of a zettel
    
    Returns None and logs an error message if attempting to open the 
    zettel raised OSError.
    """
    try:
        with open(zettel.path, 'r', encoding='utf8') as file:
            contents = file.read()
            return contents
    except OSError:
        logging.warning(f'  Zettel not found: `{zettel.title}` at ' \
            f'{zettel.path}')
        return None


def convert_links(link_id_pattern: str,
                  contents: str,
                  zettel: Zettel,
                  zettels: List[Zettel]) -> Tuple[int, str]:
    """Converts links in one zettel from the zk to the md format
    
    Returns the number of links converted and the new contents with the 
    converted links.
    """
    link_ids: List[str] = link_id_pattern.findall(contents)
    for link_id in set(link_ids):
        linked_z = get_zettel_by_id(link_id, zettels)
        if not contents.count(linked_z.link):
            logging.warning(f'`{zettel.title}` has an outdated link' \
                f' title. It should be: {linked_z.link}')
        if linked_z.id.isnumeric() and not zettel.id.isnumeric():
            markdown_link = f'[[§] {linked_z.title}](posts/{linked_z.id}.md)'
        else:
            markdown_link = f'[[§] {linked_z.title}]({linked_z.id}.md)'
        contents = contents.replace(linked_z.link, markdown_link)

    return len(link_ids), contents
