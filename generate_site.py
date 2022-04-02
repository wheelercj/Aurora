# external imports
import os
import sys
import re
import webbrowser
import shutil
from pygments import highlight, lexers  # https://pygments.org/
from pygments.formatters import HtmlFormatter
import PySimpleGUI as sg  # https://pysimplegui.readthedocs.io/en/latest/
import send2trash  # https://pypi.org/project/Send2Trash/
from typing import List, Tuple, Dict, Any
from functools import cache
import logging

# internal imports
from settings import Settings, settings, show_settings_window, validate_settings
from zettel import Zettel, get_zettel_by_file_name
from convert_links import convert_links_from_zk_to_md


log_path = os.path.join(os.path.dirname(__file__), "zk-ssg.log")
logging.basicConfig(
    filename=log_path, encoding="utf-8", filemode="w", level=logging.INFO
)  # https://docs.python.org/3/howto/logging.html#logging-basic-tutorial


def show_progress(n: int) -> None:
    """Shows a progress bar in a new window.

    Parameters
    ----------
    n : int
        The percentage of the progress bar to fill.
    """
    sg.one_line_progress_meter("generating the site", n, 100, "progress meter")


def generate_site(settings: Settings) -> None:
    """Generates all the site's files.

    Parameters
    ----------
    settings : Settings
        The settings dictionary. If not provided, the settings will be loaded
        from the settings.json file.
    """
    show_progress(0)
    logging.info("Getting the application settings.")
    if not validate_settings(settings):
        settings = show_settings_window(settings)
    site_path = settings["site folder path"]

    logging.info("Finding zettels that contain `#published`.")
    show_progress(2)
    zettels = get_zettels_to_publish(settings["zettelkasten path"])
    logging.info(f"Found {len(zettels)} zettels that contain `#published`.")
    show_progress(5)
    check_links(zettels)
    show_progress(10)

    logging.info("Creating the pages folder if it doesn't already exist.")
    site_pages_path = os.path.join(site_path, settings["site subfolder name"])
    try:
        os.mkdir(site_pages_path)
    except FileExistsError:
        pass

    logging.info("Deleting all markdown files currently in the pages folder.")
    delete_site_md_files(site_pages_path)

    logging.info(f"Copying the zettels to {site_path}")
    show_progress(12)
    zettels = copy_zettels_to_site_folder(zettels, site_path, site_pages_path)

    logging.info("Creating index files of all published zettels.")
    show_progress(15)
    create_md_index_files(zettels, site_path, settings["hide chrono index dates"])

    logging.info("Searching for any attachments that are linked to in the zettels.")
    show_progress(20)
    n = copy_attachments(zettels, site_pages_path)
    logging.info(f"Found {n} attachments and copied them to {site_pages_path}")

    reformat_zettels(zettels, settings)
    show_progress(25)
    new_html_paths = regenerate_html_files(zettels, site_path, site_pages_path)

    show_progress(50)
    n = convert_attachment_links(new_html_paths)
    logging.info(f"Converted {n} attachment links from the md to the html format.")

    logging.info("Adding syntax highlighting to code in codeblocks.")
    show_progress(60)
    syntax_highlight_code(new_html_paths)

    logging.info("Inserting the site header, footer, etc. into each file.")
    append_copyright_notice(site_path, settings["copyright text"])
    copy_template_html_files(site_path)
    wrap_template_html(site_path, new_html_paths, settings["site title"])
    insert_all_index_links(site_path)
    show_progress(85)

    logging.info("Checking for style.css.")
    check_style(site_path, settings)
    show_progress(95)

    logging.info("\nGenerated HTML files:")
    for path in new_html_paths:
        logging.info(f"  {path}")

    show_progress(100)
    print(f"Successfully generated {len(new_html_paths)} HTML files.")


def append_copyright_notice(site_path: str, copyright_text: str) -> None:
    """Appends the site's coyright notice to the end of index.html.

    Parameters
    ----------
    site_path : str
        The path to the site's folder.
    copyright_text : str
        The copyright notice to append.
    """
    index_path = os.path.join(site_path, "index.html")
    append_text(
        index_path,
        '<br><br><br><br><br><br><br><p style="text-align: '
        f'center">{copyright_text}</p>',
    )


def insert_all_index_links(site_path: str) -> None:
    """Inserts links to index files into each of the other HTML index files.

    This function must not be called until after the template HTML has been
    wrapped around each HTML file.

    Parameters
    ----------
    site_path : str
        The path to the site's folder.
    """
    index_path = os.path.join(site_path, "index.html")
    insert_index_links(
        index_path,
        '<p>sort by: <a href="alphabetical-index.html">α</a> <a href="chronological-index.html">🕑</a></p>',
    )
    index_path = os.path.join(site_path, "alphabetical-index.html")
    insert_index_links(
        index_path,
        '<p>sort by: <a href="index.html">💡</a> <a href="chronological-index.html">🕑</a></p>',
    )
    index_path = os.path.join(site_path, "chronological-index.html")
    insert_index_links(
        index_path,
        '<p>sort by: <a href="alphabetical-index.html">α</a> <a href="index.html">💡</a>',
    )


def insert_index_links(file_path: str, links_to_insert: str) -> None:
    """Inserts links to index files into one HTML index file.

    Parameters
    ----------
    file_path : str
        The absolute path to the HTML index file.
    links_to_insert : str
        The links to insert into the HTML index file.
    """
    with open(file_path, "r+", encoding="utf8") as file:
        file_contents = file.read()
        file_contents = file_contents.replace("<main>", f"<main>\n{links_to_insert}")
        file.seek(0)
        file.write(file_contents)


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


def syntax_highlight_code(html_paths: List[str]) -> None:
    """Adds syntax highlighting to code inside all HTML codeblocks.

    Parameters
    ----------
    html_paths : List[str]
        The paths to the HTML files to add syntax highlighting to.
    """
    formatter = HtmlFormatter(linenos=False, cssclass="source")
    cb_pattern = re.compile(r"<code[^<]+</code>")
    cb_lang_pattern = re.compile(r'(?<=<code class=").+(?=">)')
    cb_contents_pattern = re.compile(r"(?<=>)[^<]+(?=</code>)")

    for html_path in html_paths:
        with open(html_path, "r+", encoding="utf8") as file:
            contents = file.read()
            codeblocks: List[str] = cb_pattern.findall(contents)
            for codeblock in codeblocks:
                language: re.Match = cb_lang_pattern.search(codeblock)
                lexer = None
                if language:
                    lexer = get_lexer(language[0])
                if lexer:
                    cb_contents_match = cb_contents_pattern.search(codeblock)
                    contents = highlight_codeblock(
                        cb_contents_match, lexer, formatter, contents
                    )

            if codeblocks:
                file.truncate(0)
                file.seek(0)
                file.write(contents)


def highlight_codeblock(
    cb_contents_match: re.Match, lexer: Any, formatter: Any, contents: str
) -> str:
    """Adds syntax highlighting to the code inside an HTML codeblock

    Assumes the given lexer is valid. Returns contents unchanged if
    cb_contents_match is None.

    Parameters
    ----------
    cb_contents_match : re.Match
        The match object for the code inside the codeblock.
    lexer : Any
        The lexer to use for syntax highlighting.
    formatter : Any
        The formatter to use for syntax highlighting.
    contents : str
        The contents of the HTML file.
    """
    if cb_contents_match:
        plain_codeblock = revert_html(cb_contents_match[0])
        result = highlight(plain_codeblock, lexer, formatter)
        contents = contents.replace(cb_contents_match[0], result, 1)
        # Remove empty line at the end of the code block.
        contents = contents.replace(
            "</span>\n</pre></div>\n</code></pre>\n", "</span></pre></div></code></pre>"
        )
        contents = contents.replace('<div class="source"><pre>', '<div class="source">')
        contents = contents.replace("</pre></div>", "</div>")
    return contents


def get_lexer(language: str) -> Any:
    """Gets a pygments lexer by name

    Returns None if a valid language is not found.

    Parameters
    ----------
    language : str
        The name of the language to get the lexer for.
    """
    if language.startswith("language-"):
        language = language[9:]
    if language == "cpp":
        language == "c++"
    return lexers.get_lexer_by_name(language)


def revert_html(codeblock: str) -> str:
    """Converts certain HTML strings back to plaintext

    For example, `&lt;` is converted back to `<`.

    Parameters
    ----------
    codeblock : str
        The codeblock to revert.
    """
    replacements = [
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&quot;", '"'),
        ("&#39;", "'"),
        ("&amp;", "&"),
    ]
    for replacement in replacements:
        codeblock = codeblock.replace(replacement[0], replacement[1])
    return codeblock


def check_links(zettels: List[Zettel]) -> None:
    """Shows a warning message if any zettel links are broken.

    Parameters
    ----------
    zettels : List[Zettel]
        The list of zettels to check.
    """
    pattern = re.compile(
        re.escape(settings["zk link start"])
        + settings["patterns"]["zk link id"].pattern
        + re.escape(settings["zk link end"])
    )
    for zettel in zettels:
        with open(zettel.path, "r", encoding="utf8") as file:
            contents = file.read()
        ids = pattern.findall(contents)
        for id in ids:
            if id not in (z.id for z in zettels):
                sg.popup(
                    f"Warning: zettel with ID {id} cannot be found"
                    f" but has been linked to in {zettel.title}"
                )


def reformat_zettels(zettels: List[Zettel], settings: dict) -> None:
    """Convert any file links to absolute markdown-style HTML links

    Also, remove all tags from the files if hide_tags is True.

    Parameters
    ----------
    zettels : List[Zettel]
        The list of zettels to reformat.
    settings : dict
        The settings to use.
    """
    make_file_paths_relative(zettels)
    if settings["hide tags"]:
        remove_all_tags(zettels)
    logging.info(f"Converting internal links from the zk to the md format.")
    md_linker = md_linker_creator(settings)
    convert_links_from_zk_to_md(zettels, md_linker=md_linker)
    redirect_links_from_md_to_html(zettels)


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
    old_html_paths = get_file_paths(site_path, ".html") + get_file_paths(
        site_pages_path, ".html"
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


def convert_attachment_links(all_html_paths: List[str]) -> int:
    """Converts any attachment links from the md to the html format

    Returns the number of links converted.

    Parameters
    ----------
    all_html_paths : List[str]
        The list of all HTML files to convert links in.
    """
    n = replace_pattern(
        settings["patterns"]["md link"], r'<a href="\2">\1</a>', all_html_paths
    )
    return n


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
        if zettel.id.isnumeric():
            new_path = shutil.copy(zettel.path, site_pages_path)
            zettels[i].path = new_path
        else:
            new_path = shutil.copy(zettel.path, site_path)
            zettels[i].path = new_path
    return zettels


def remove_all_tags(zettels: List[Zettel]) -> None:
    """Removes all tags from the zettels

    Logs a message saying how many tags were removed.

    Parameters
    ----------
    zettels : List[Zettel]
        The zettels to remove the tags from.
    """
    zettel_paths = [z.path for z in zettels]
    n = replace_pattern(settings["patterns"]["tag"], "", zettel_paths)
    logging.info(f"Removed {n} tags.")


def append_text(file_path: str, text: str) -> None:
    """Appends to a file.

    Parameters
    ----------
    file_path : str
        The path to the file to append to.
    text : str
        The text to append to the file.
    """
    with open(file_path, "a", encoding="utf8") as file:
        file.write(text)


def copy_template_html_files(site_path: str) -> None:
    """Copies header and footer .html to the site folder iff they're'nt there.

    Parameters
    ----------
    site_path : str
        The path to the site folder.
    """
    copy_file_iff_not_present("header.html", site_path)
    copy_file_iff_not_present("footer.html", site_path)


def copy_file_iff_not_present(file_name: str, site_path: str) -> str:
    """Copies a file from this dir to the site dir iff it's not there.

    Returns the file's path whether it was already there or newly copied.

    Parameters
    ----------
    file_name : str
        The name of the file to copy.
    site_path : str
        The path to the site folder.
    """
    site_file_path = os.path.join(site_path, file_name)
    if os.path.isfile(site_file_path):
        logging.info(f"  {file_name} already exists. The file will not be replaced.")
    else:
        logging.info(f"  {file_name} was not found. Providing a new copy.")
        shutil.copy(file_name, site_path)
    return site_file_path


def wrap_template_html(
    site_path: str, all_html_paths: List[str], site_title: str
) -> None:
    """Wraps each HTML file's contents with a header and footer.

    The header and footer used are retrieved from the copies of
    header.html and footer.html that are in the site folder.

    Parameters
    ----------
    site_path : str
        The path to the site folder.
    all_html_paths : List[str]
        The paths to the HTML files to wrap.
    site_title : str
        The title of the site.
    """
    for path in all_html_paths:
        with open(path, "r+", encoding="utf8") as file:
            contents = file.read()
            file.truncate(0)
            file.seek(0)  # Without this, \x00 would be inserted into the front
            # of the file.
            if file_name_is_numeric(path):
                header_html = get_header_html(site_title, site_path, "../")
            else:
                header_html = get_header_html(site_title, site_path)
            footer_html = get_footer_html(site_path)
            file.write(header_html + contents + footer_html)


def file_name_is_numeric(path: str) -> bool:
    """Determines if the file the path is for has a numeric name.

    Parameters
    ----------
    path : str
        The path to the file.
    """
    _, name_and_extension = os.path.split(path)
    name, _ = os.path.splitext(name_and_extension)
    return name.isnumeric()


@cache
def get_header_html(
    site_title: str, site_path: str, relative_site_path: str = ""
) -> str:
    """Retrieves the site's header HTML from header.html.

    Parameters
    ----------
    site_title : str
        The title that will appear on the site.
    site_path : str
        The absolute path to the site's root folder.
    relative_site_path : str
        The relative path to the site's root folder from the HTML file
        that this function is being called for.
    """
    header_file_path = os.path.join(site_path, "header.html")
    with open(header_file_path, "r", encoding="utf8") as file:
        header_html = file.read()
    header_html = header_html.replace("{{site_title}}", site_title)
    header_html = header_html.replace("{{folder}}", relative_site_path)
    return header_html


@cache
def get_footer_html(site_path: str, footer_text: str = "") -> str:
    """Retrieves the site's footer HTML from footer.html.

    Parameters
    ----------
    site_path : str
        The absolute path to the site's root folder.
    footer_text : str
        The text that will appear in the footer.
    """
    footer_file_path = os.path.join(site_path, "footer.html")
    with open(footer_file_path, "r", encoding="utf8") as file:
        footer_html = file.read()
    footer_html = footer_html.replace("{{footer_text}}", footer_text)
    return footer_html


def replace_pattern(
    compiled_pattern: str,
    replacement: str,
    file_paths: List[str],
    encoding: str = "utf8",
    file_must_exist: bool = False,
) -> int:
    """Replaces a regex pattern with a string in multiple files

    Returns the total number of replacements.

    Parameters
    ----------
    compiled_pattern : str
        The regex pattern to search for.
    replacement : str
        The string to replace the pattern with. This can be a regex group
        reference.
    file_paths : List[str]
        The paths to the files to search in.
    encoding : str
        The encoding of the files.
    file_must_exist : bool
        Whether any file paths matched by the compiled pattern must exist.
        Assumes the compiled pattern is for searching for file paths but will
        sometimes match other things too.
    """
    total_replaced = 0

    for file_path in file_paths:
        contents = get_file_contents(file_path, encoding)

        # Temporarily remove any code blocks from contents.
        triple_codeblocks = settings["patterns"]["triple codeblock"].findall(contents)
        if len(triple_codeblocks):
            contents = settings["patterns"]["triple codeblock"].sub("␝", contents)

        single_codeblocks = settings["patterns"]["single codeblock"].findall(contents)
        if len(single_codeblocks):
            contents = settings["patterns"]["single codeblock"].sub("␞", contents)

        # Replace the pattern.
        if not file_must_exist:
            contents, n_replaced = compiled_pattern.subn(replacement, contents)
        else:
            contents, n_replaced = replace_file_paths(
                compiled_pattern, replacement, contents
            )
        total_replaced += n_replaced

        # Put back the code blocks.
        for single_codeblock in single_codeblocks:
            contents = re.sub(
                r"␞", single_codeblock.replace("\\", r"\\"), contents, count=1
            )
        for triple_codeblock in triple_codeblocks:
            contents = re.sub(
                r"␝", triple_codeblock[0].replace("\\", r"\\"), contents, count=1
            )

        # Save changes.
        if n_replaced > 0:
            with open(file_path, "w", encoding=encoding) as file:
                file.write(contents)

    return total_replaced


def replace_file_paths(
    path_pattern: re.Pattern, replacement: str, contents: str
) -> Tuple[str, int]:
    """Replaces all file paths in the contents with the correct relative path.

    Parameters
    ----------
    path_pattern : re.Pattern
        The compiled regex pattern to search for.
    replacement : str
        The string to replace the pattern with. This can be a regex group
        reference.
    contents : str
        The contents to replace the file links in.

    Returns
    -------
    str
        The contents with the file links replaced.
    int
        The number of replacements made.
    """
    start = 0
    n_replaced = 0
    while True:
        match = path_pattern.search(contents, start)
        if not match:
            return contents, n_replaced
        if os.path.isfile(match[0]):
            contents = path_pattern.sub(replacement, contents, count=1)
            n_replaced += 1
        start = match.end()


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
    zettel_paths = get_file_paths(zettelkasten_path, ".md")
    zettels_to_publish = []

    for zettel_path in zettel_paths:
        contents = get_file_contents(zettel_path, "utf8")
        match = settings["patterns"]["published tag"].search(contents)
        if match:
            zettels_to_publish.append(zettel_path)

    return zettels_to_publish


def get_file_contents(absolute_path: str, encoding: str) -> str:
    """Gets a file's contents.

    If UnicodeDecodeError is raised, this function will log and show an
    error message and make the program exit.

    Parameters
    ----------
    absolute_path : str
        The absolute path to the file.
    encoding : str
        The encoding of the file.
    """
    with open(absolute_path, "r", encoding=encoding) as file:
        try:
            contents = file.read()
        except UnicodeDecodeError as e:
            logging.error(f"UnicodeDecodeError: {e}")
            sg.popup(
                "Error: one or more symbols cannot not be decoded "
                f"as unicode in file {absolute_path}"
            )
            sys.exit(f"UnicodeDecodeError: {e}")
        else:
            return contents


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
    index_zettel = get_zettel_by_file_name("index", zettels)
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
            if zettel.id.isnumeric():
                if index_tag in zettel.tags:
                    categories[index_tag].append("* " + zettel.link)
                    unlinked_zettels.remove(zettel)

    for zettel in unlinked_zettels:
        if zettel.title not in ("index", "about"):
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
        if zettel.id.isnumeric():
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
    numeric_links = []
    sorted_zettels = sorted(zettels, key=lambda z: z.id, reverse=True)
    for zettel in sorted_zettels:
        if zettel.id.isnumeric():
            if hide_chrono_index_dates:
                numeric_links.append("* " + zettel.link)
            else:
                date = f"{zettel.id[0:4]}/{zettel.id[4:6]}/{zettel.id[6:8]}"
                numeric_links.append("* " + date + " " + zettel.link)
    zettel_index = "## chronological index\n\n" + "\n".join(numeric_links)
    return zettel_index


def delete_site_md_files(site_pages_path: str) -> None:
    """Permanently deletes all the markdown files in the site folder.

    Parameters
    ----------
    site_pages_path : str
        The path to the site folder.
    """
    md_paths = get_file_paths(site_pages_path, ".md")
    for path in md_paths:
        os.remove(path)


def get_file_paths(dir_path: str, file_extension: str) -> List[str]:
    """Gets the paths of files in a directory

    Only paths of files with the given file extension are included.

    Parameters
    ----------
    dir_path : str
        The path to the directory to get the file paths of.
    file_extension : str
        The file extension to filter by.
    """
    file_names = os.listdir(dir_path)
    file_paths = []
    for file_name in file_names:
        if file_name.endswith(file_extension):
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


def check_style(site_path: str, settings: dict) -> None:
    """Copies style.css into the site folder and settings into style.css.

    If style.css is already there, this function only tries to update
    the file.

    Parameters
    ----------
    site_path : str
        The path to the site folder.
    settings : dict
        The settings to write to style.css.
    """
    site_style_path = copy_file_iff_not_present("style.css", site_path)
    try:
        update_css(site_style_path, settings)
    except ValueError:
        logging.error("  style.css cannot be parsed.")


def update_css(site_style_path: str, settings: dict) -> None:
    """Updates the site's copy of style.css with the user's settings.

    Raises ValueError if the file cannot be parsed.

    Parameters
    ----------
    site_style_path : str
        The path to the site's style.css.
    settings : dict
        The settings to write to style.css.
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
