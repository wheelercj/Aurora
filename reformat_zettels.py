# external imports
from typing import List

# internal imports
from settings import settings
from zettel import Zettel
from utils import logging, replace_pattern
from convert_links import convert_links_from_zk_to_md


def reformat_zettels(zettels: List[Zettel]) -> None:
    """Convert file links and remove tags.

    Convert any file links to absolute markdown-style HTML links, and remove
    all tags from the files if the setting to hide tags is True.

    Parameters
    ----------
    zettels : List[Zettel]
        The list of zettels to reformat.
    """
    make_file_paths_relative(zettels)
    if settings["hide tags"]:
        remove_all_tags(zettels)
    logging.info(f"Converting internal links from the zk to the md format.")
    md_linker = md_linker_creator(settings)
    convert_links_from_zk_to_md(zettels, md_linker=md_linker)
    redirect_links_from_md_to_html(zettels)


def make_file_paths_relative(zettels: List[Zettel]) -> None:
    """Converts all absolute file paths to relative file paths.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to change the paths in.
    """
    zettel_paths = [z.path for z in zettels]
    n = replace_pattern(
        settings["patterns"]["absolute attachment link"],
        r"\1",
        zettel_paths,
        file_must_exist=True,
    )
    logging.info(f"Converted {n} absolute file paths to relative file paths.")


def remove_all_tags(zettels: List[Zettel]) -> None:
    """Removes all tags from the zettels.

    Logs a message saying how many tags were removed.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to remove the tags from.
    """
    zettel_paths = [z.path for z in zettels]
    n = replace_pattern(settings["patterns"]["tag"], "", zettel_paths)
    logging.info(f"Removed {n} tags.")


def md_linker_creator(settings: dict) -> str:
    """Creates an md linker creator for zettels in multiple folders.

    Parameters
    ----------
    settings : dict
        The settings to use.
    """

    def create_markdown_link(zettel: Zettel, linked_zettel: Zettel) -> str:
        """Creates a markdown link from one zettel to another.

        Prefixes the links with `[§] `, and points some of the links to
        the pages folder.

        Parameters
        ----------
        zettel : Zettel
            The zettel that the link is from.
        linked_zettel : Zettel
            The zettel that the link is to.
        """
        if linked_zettel.id.isnumeric() and not zettel.id.isnumeric():
            markdown_link = (
                f"[{settings['internal html link prefix']}{linked_zettel.title}]"
                f"({settings['site subfolder name']}/{linked_zettel.id}.md)"
            )
        else:
            markdown_link = (
                f"[{settings['internal html link prefix']}{linked_zettel.title}]"
                f"({linked_zettel.id}.md)"
            )
        return markdown_link

    return create_markdown_link


def redirect_links_from_md_to_html(zettels: List[Zettel]) -> None:
    """Changes links from pointing to markdown files to HTML files.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to change the links in.
    """
    zettel_paths = [z.path for z in zettels]
    n = replace_pattern(settings["patterns"]["md ext in link"], ".html", zettel_paths)
    logging.info(
        f"Converted {n} internal links from ending with `.md` to "
        "ending with `.html`."
    )
