# Converts zettel links from the zettelkasten style to markdown's style,
# or vice versa. Currently, this only works with links that are 14-digit
# zettel IDs, and with double square brackets for the zettelkasten-style
# links. E.g. [[20201221140928]] gets changed to [§§](20201221140928.md)
# or vice-versa.


# External imports.
import re
import sys


def zk_to_md(zettel_paths):
    return convert(r'\[\[(\d{14})\]\]', r'[§§](\1.md)', zettel_paths)


def md_to_zk(zettel_paths):
    return convert(r'\[§§\]\((\d{14})\.md\)', r'[[\1]]', zettel_paths)


# Parameters:
# old_link_pattern is the regex pattern of the current links.
# new_link_name is the string that all the links will be changed to,
#   which can contain references to groups in old_link_pattern.
# zettel_paths is a list of paths to all the zettels to convert links in.
def convert(old_link_pattern, new_link_name, zettel_paths):
    zettel_count = len(zettel_paths)
    total_char_count = 0
    total_n_replaced = 0

    for zettel_path in zettel_paths:
        try:
            with open(zettel_path, 'r', encoding='utf8') as zettel:
                contents = zettel.read()
            char_count_1 = len(contents)

            # Use regex to find the links, and then convert them.
            new_contents, n_replaced = re.subn(old_link_pattern, new_link_name, contents)
            char_count_2 = len(new_contents)

            # Save contents back to the zettel.
            if n_replaced > 0:
                with open(zettel_path, 'w', encoding='utf8') as zettel:
                    zettel.write(new_contents)

            # Print character change stats.
            char_count = char_count_2 - char_count_1
            if n_replaced:
                print(f'    Changed {zettel.name} by {char_count} characters with {n_replaced} links converted.')
            total_char_count += char_count
            total_n_replaced += n_replaced

        except OSError:
            print(f'Zettel not found: {zettel_path}')

    print(f'  Changed {zettel_count} zettels by a total of', end='', flush=True)
    print(f' {total_char_count} characters with {total_n_replaced} links converted.')
    return total_n_replaced
