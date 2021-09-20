# Converts zettel links from the zettelkasten style to markdown's style,
# or vice versa. Currently, this only works with links that are 14-digit
# zettel IDs, and with double square brackets for the zettelkasten-style
# links. E.g. [[20201221140928]] gets changed to [§](20201221140928.md)
# or vice-versa.


# external imports
import re
from typing import List

# internal imports
from zettel import Zettel


def convert_links_from_zk_to_md(zettels: List[Zettel]) -> None:
    print(f'Converting internal links from the zk to the md format.')
    n = convert(r'\[\[(\d{14})\]\]', r'[[§]](\1.md)', zettels)
    print(f'Converted {n} internal links from the zk to the md format.')


def convert_links_from_md_to_zk(zettels: List[Zettel]) -> None:
    convert(r'\[\[§\]\]\((\d{14})\.md\)', r'[[\1]]', zettels)


def convert(current_link_pattern: str,
            new_link: str,
            zettels: List[Zettel]) -> int:
    """Converts file links in multiple zettels from a pattern to a string
    
    The new_link string can contain references to pattern groups in
    current_link_pattern.
    """
    zettel_count = len(zettels)
    total_char_count = 0
    total_n_replaced = 0

    for zettel in zettels:
        try:
            with open(zettel.path, 'r', encoding='utf8') as file:
                contents = file.read()
            char_count_1 = len(contents)

            # Use regex to find the links, and then convert them.
            new_contents, n_replaced = re.subn(current_link_pattern,
                                               new_link,
                                               contents)
            char_count_2 = len(new_contents)

            # Save contents back to the zettel.
            if n_replaced > 0:
                with open(zettel.path, 'w', encoding='utf8') as file:
                    file.write(new_contents)

            # Print character change stats.
            char_count = char_count_2 - char_count_1
            if n_replaced:
                print(f'    Changed `{zettel.title}` by {char_count} ' \
                    f'characters with {n_replaced} links converted.')
            total_char_count += char_count
            total_n_replaced += n_replaced

        except OSError:
            print(f'Zettel not found: {zettel.path}')

    print(f'  Changed {zettel_count} zettels by a total of',
        end='',
        flush=True)
    print(f' {total_char_count} characters with {total_n_replaced} links ' \
        'converted.')
    return total_n_replaced
