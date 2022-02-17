# Use `pyinstaller -wF generate_site.py` to create an .exe for Windows.

# external imports
import os
import sys
import re
import shutil
from pygments import highlight, lexers  # https://pygments.org/
from pygments.formatters import HtmlFormatter
import PySimpleGUI as sg  # https://pysimplegui.readthedocs.io/en/latest/
from typing import List, Tuple, Dict, Optional, Any
from functools import cache
import logging

logging.basicConfig(
    level=logging.WARNING
)  # https://docs.python.org/3/howto/logging.html#logging-basic-tutorial

# internal imports
from settings import show_settings_window, load_settings
from zettel import Zettel, get_zettel_by_file_name
import patterns
from convert_links import convert_links_from_zk_to_md


def show_main_menu() -> None:
    """Runs the main menu."""
    window = create_main_menu_window()
    settings = None
    while True:
        event, _ = window.read()
        if event == sg.WIN_CLOSED or event == "exit":
            window.close()
            return
        window.Hide()
        settings = respond_to_main_menu_event(event, settings)
        window.UnHide()


def create_main_menu_window() -> sg.Window:
    """Creates and displays the main menu."""
    sg.theme("DarkAmber")
    layout = [
        [sg.Button("generate site", size=(14, 1), pad=(40, 5))],
        [sg.Button("settings", size=(14, 1), pad=(40, 5))],
        [sg.Button("exit", size=(14, 1), pad=(40, 5))],
    ]
    return sg.Window("zk-ssg", layout)


def respond_to_main_menu_event(event, settings: Optional[dict]) -> Optional[dict]:
    """Handles main menu events."""
    if event == "generate site":
        generate_site(settings)
    elif event == "settings":
        settings = show_settings_window(settings)
    return settings


def show_progress(n):
    sg.one_line_progress_meter("generating the site", n, 100, "progress meter")


def generate_site(settings: Optional[dict]) -> None:
    """Generates all the site's files."""
    show_progress(0)
    logging.info("Getting the application settings.")
    if not settings:
        settings = load_settings("prompt user")
    site_path = settings["site path"]
    zettelkasten_path = settings["zettelkasten path"]

    this_dir, _ = os.path.split(__file__)
    if 3 > len({this_dir, site_path, zettelkasten_path}):
        error_message = (
            "Error: the zettelkasten, the website's files, "
            "and this program's files should probably be in different "
            "folders."
        )
        sg.popup(error_message)
        sys.exit(error_message)

    logging.info("Finding zettels that contain `#published`.")
    show_progress(2)
    zettels = get_zettels_to_publish(zettelkasten_path)
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
    create_index_files(zettels, site_path, settings["hide chrono index dates"])

    logging.info("Searching for any attachments that are linked to in the zettels.")
    show_progress(20)
    n = copy_attachments(zettels, site_pages_path)
    logging.info(f"Found {n} attachments and copied them to {site_pages_path}")

    reformat_zettels(zettels, settings)
    show_progress(25)
    new_html_paths = regenerate_html_files(zettels, site_path, site_pages_path)

    fix_image_links(new_html_paths)
    show_progress(50)
    n = convert_attachment_links(new_html_paths)
    logging.info(f"Converted {n} attachment links from the md to the html format.")

    logging.info("Adding syntax highlighting to code in codeblocks.")
    show_progress(60)
    syntax_highlight_code(new_html_paths)

    logging.info("Inserting the site header, footer, etc. into each file.")
    append_index_links(site_path)
    append_copyright_notice(site_path, settings["copyright text"])
    copy_template_html_files(site_path)
    wrap_template_html(site_path, new_html_paths, settings["site title"])
    show_progress(85)

    logging.info("Checking for style.css.")
    check_style(site_path, settings)
    show_progress(95)

    logging.info("\nGenerated HTML files:")
    for path in new_html_paths:
        logging.info(f"  {path}")

    print(f"Successfully generated {len(new_html_paths)} HTML files.")
    show_progress(100)


def append_copyright_notice(site_path, copyright_text) -> None:
    """Appends the site's coyright notice to the end of index.html."""
    index_path = os.path.join(site_path, "index.html")
    append_text(
        index_path,
        '<br><br><br><br><br><br><br><p style="text-align: '
        f'center">{copyright_text}</p>',
    )


def append_index_links(site_path: str) -> None:
    """Appends links to the other index pages in each HTML index file."""
    index_path = os.path.join(site_path, "index.html")
    append_text(
        index_path,
        "<hr /><p>sort by: "
        '<a href="alphabetical-index.html">α</a> | '
        '<a href="chronological-index.html">🕑</a></p>',
    )
    index_path = os.path.join(site_path, "alphabetical-index.html")
    append_text(
        index_path,
        "<hr /><p>sort by: "
        '<a href="index.html">💡</a> | '
        '<a href="chronological-index.html">🕑</a></p>',
    )
    index_path = os.path.join(site_path, "chronological-index.html")
    append_text(
        index_path,
        "<hr /><p>sort by: "
        '<a href="alphabetical-index.html">α</a> | '
        '<a href="index.html">💡</a>',
    )


def create_index_files(
    zettels: List[Zettel], site_path: str, hide_chrono_index_dates: bool
) -> None:
    """Creates markdown files that list all the published zettels

    The files created are alphabetical-index.md and
    chronological-index.md. The file index.md is also edited, and must
    already exist.
    """
    edit_categorical_index_file(zettels)
    create_alphabetical_index_file(zettels, site_path)
    create_chronological_index_file(zettels, site_path, hide_chrono_index_dates)


def syntax_highlight_code(html_paths: List[str]) -> None:
    """Adds syntax highlighting to code inside all HTML codeblocks."""
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
    cb_contents_match: re.Match, lexer: Any, formatter, contents: str
) -> str:
    """Adds syntax highlighting to the code inside an HTML codeblock

    Assumes the given lexer is valid. Returns contents unchanged if
    cb_contents_match is None.
    """
    if cb_contents_match:
        plain_codeblock = revert_html(cb_contents_match[0])
        result = highlight(plain_codeblock, lexer, formatter)
        contents = contents.replace(cb_contents_match[0], result, 1)
    return contents


def get_lexer(language: str) -> Any:
    """Gets a pygments lexer by name

    Returns None if a valid language is not found.
    """
    if language.startswith("language-"):
        language = language[9:]
    if language == "cpp":
        language == "c++"
    return lexers.get_lexer_by_name(language)


def revert_html(codeblock: str) -> str:
    """Converts certain HTML strings back to plaintext

    For example, `&lt;` is converted back to `<`.
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
    """Shows a warning message if any zettel links are broken."""
    for zettel in zettels:
        with open(zettel.path, "r", encoding="utf8") as file:
            contents = file.read()
        ids = patterns.zettel_link_id.findall(contents)
        for id in ids:
            if id not in (z.id for z in zettels):
                sg.popup(
                    f"Warning: zettel with ID {id} cannot be found"
                    f" but has been linked to in {zettel.title}"
                )


def reformat_zettels(zettels: List[Zettel], settings: dict) -> None:
    """Convert any file links to absolute markdown-style HTML links

    Also, remove all tags from the files if hide_tags is True.
    """
    make_file_paths_absolute(zettels)
    if settings["hide tags"]:
        remove_all_tags(zettels)
    logging.info(f"Converting internal links from the zk to the md format.")
    md_linker = md_linker_creator(settings)
    convert_links_from_zk_to_md(zettels, md_linker=md_linker)
    redirect_links_from_md_to_html(zettels)


def md_linker_creator(settings: dict) -> str:
    """Creates an md linker creator for zettels in multiple folders."""

    def create_markdown_link(zettel: Zettel, linked_zettel: Zettel) -> str:
        """Creates a markdown link from one zettel to another.

        Prefixes the links with `[§] `, and points some of the links to
        the pages folder.
        """
        if linked_zettel.id.isnumeric() and not zettel.id.isnumeric():
            markdown_link = (
                f"[[§] {linked_zettel.title}]"
                f'({settings["site subfolder name"]}/{linked_zettel.id}.md)'
            )
        else:
            markdown_link = f"[[§] {linked_zettel.title}]({linked_zettel.id}.md)"
        return markdown_link

    return create_markdown_link


def regenerate_html_files(
    zettels: List[Zettel], site_path: str, site_pages_path: str
) -> List[str]:
    """Creates new and deletes old HTML files

    May overwrite some HTML files. Old HTML files that were listed in
    ssg-ignore.txt are saved and not changed at all.
    """
    old_html_paths = get_file_paths(site_path, ".html") + get_file_paths(
        site_pages_path, ".html"
    )
    logging.info("Creating html files from the md files.")
    new_html_paths = create_html_files(zettels)
    all_html_paths = get_file_paths(site_path, ".html") + get_file_paths(
        site_pages_path, ".html"
    )

    logging.info(
        "Deleting any HTML files that were not just generated and "
        "were not listed in ssg-ignore.txt."
    )
    delete_old_html_files(old_html_paths, all_html_paths, site_pages_path)

    return new_html_paths


def convert_attachment_links(all_html_paths: List[str]) -> int:
    """Converts any attachment links from the md to the html format

    Returns the number of links converted.
    """
    md_link_pattern = r"\[(.+)]\((.+)\)"
    n = replace_pattern(md_link_pattern, r'<a href="\2">\1</a>', all_html_paths)
    return n


def fix_image_links(all_html_paths: List[str]) -> None:
    """Fixes any image links that were not converted correctly

    For example, `.png" src="/images/` must be changed to `.png" src="images/`.
    """
    # This function might not be needed anymore. I originally wrote this
    # because I was using gh_md_to_html, which didn't convert some
    # things correctly (including image links).
    incorrect_link_pattern1 = r"\.png\" src=\".+images/"
    n = replace_pattern(incorrect_link_pattern1, '.png" src="images/', all_html_paths)
    incorrect_link_pattern2 = r"\.jpg\" src=\".+images/"
    n += replace_pattern(incorrect_link_pattern2, '.jpg" src="images/', all_html_paths)
    logging.info(f"Fixed the src path of {n} image links.")


def create_html_files(zettels: List[Zettel]) -> List[str]:
    """Creates HTML files from markdown files into the site folder

    Expects the zettels to already be in the site folder. Returns all
    the new HTML files' paths.
    """
    new_html_file_paths = []
    for zettel in zettels:
        new_html_file_path = zettel.create_html_file()
        new_html_file_paths.append(new_html_file_path)
    return new_html_file_paths


def redirect_links_from_md_to_html(zettels: List[Zettel]) -> None:
    """Changes links from pointing to markdown files to HTML files."""
    md_link_pattern = r"(?<=\S)\.md(?=\))"
    zettel_paths = [z.path for z in zettels]
    n = replace_pattern(md_link_pattern, ".html", zettel_paths)
    logging.info(
        f"Converted {n} internal links from ending with `.md` to "
        "ending with `.html`."
    )


def make_file_paths_absolute(zettels: List[Zettel]) -> None:
    """Converts all relative file paths to absolute file paths."""
    attachment_link_pattern = r"(?<=]\()C:[^\n]*?([^\\/\n]+\.(pdf|png|jpg))(?=\))"
    zettel_paths = [z.path for z in zettels]
    n = replace_pattern(attachment_link_pattern, r"\1", zettel_paths)
    logging.info(f"Converted {n} absolute file paths to relative file paths.")


def copy_attachments(zettels: List[Zettel], site_pages_path: str) -> int:
    """Copies files linked to in the zettels into the site folder."""
    attachment_paths = get_attachment_paths(zettels)
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
    """
    tag_pattern = r"(?<=\s)#[a-zA-Z0-9_-]+"
    zettel_paths = [z.path for z in zettels]
    n = replace_pattern(tag_pattern, "", zettel_paths)
    logging.info(f"Removed {n} tags.")


def append_text(file_path: str, text: str) -> None:
    """Appends to a file."""
    with open(file_path, "a", encoding="utf8") as file:
        file.write(text)


def copy_template_html_files(site_path: str) -> None:
    """Copies header and footer .html to the site folder iff they're'nt there."""
    copy_file_iff_not_present("header.html", site_path)
    copy_file_iff_not_present("footer.html", site_path)


def copy_file_iff_not_present(file_name: str, site_path: str) -> str:
    """Copies a file from this dir to the site dir iff it's not there.

    Returns the file's path whether it was already there or newly copied.
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
    """
    for path in all_html_paths:
        with open(path, "r+", encoding="utf8") as file:
            contents = file.read()
            file.truncate(0)
            file.seek(0)  # Without this, \x00 would be inserted into
            # the front of the file.
            if file_name_is_numeric(path):
                header_html = get_header_html(site_title, site_path, "../")
            else:
                header_html = get_header_html(site_title, site_path)
            footer_html = get_footer_html(site_path)
            file.write(header_html + contents + footer_html)


def file_name_is_numeric(path: str) -> bool:
    """Determines if the file the path is for has a numeric name."""
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
    """Retrieves the site's footer HTML from footer.html."""
    footer_file_path = os.path.join(site_path, "footer.html")
    with open(footer_file_path, "r", encoding="utf8") as file:
        footer_html = file.read()
    footer_html = footer_html.replace("{{footer_text}}", footer_text)
    return footer_html


def replace_pattern(
    uncompiled_pattern: str,
    replacement: str,
    file_paths: List[str],
    encoding: str = "utf8",
) -> int:
    """Replaces a regex pattern with a string in multiple files

    Returns the total number of replacements.
    """
    total_replaced = 0
    chosen_pattern = re.compile(uncompiled_pattern)

    for file_path in file_paths:
        contents = get_file_contents(file_path, encoding)

        # Temporarily remove any code blocks from contents.
        triple_codeblocks = patterns.triple_codeblock.findall(contents)
        if len(triple_codeblocks):
            contents = patterns.triple_codeblock.sub("␝", contents)

        single_codeblocks = patterns.single_codeblock.findall(contents)
        if len(single_codeblocks):
            contents = patterns.single_codeblock.sub("␞", contents)

        # Replace the pattern.
        new_contents, n_replaced = chosen_pattern.subn(replacement, contents)
        total_replaced += n_replaced

        # Put back the code blocks.
        for single_codeblock in single_codeblocks:
            new_contents = re.sub(
                r"␞", single_codeblock.replace("\\", r"\\"), new_contents, count=1
            )
        for triple_codeblock in triple_codeblocks:
            new_contents = re.sub(
                r"␝", triple_codeblock[0].replace("\\", r"\\"), new_contents, count=1
            )

        # Save changes.
        if n_replaced > 0:
            with open(file_path, "w", encoding=encoding) as file:
                file.write(new_contents)

    return total_replaced


def get_zettels_to_publish(zettelkasten_path: str) -> List[Zettel]:
    """Gets all the zettels that contain '#published'."""
    zettel_paths = get_paths_of_zettels_to_publish(zettelkasten_path)
    zettels = []
    for path in zettel_paths:
        zettels.append(Zettel(path))
    return zettels


def get_paths_of_zettels_to_publish(zettelkasten_path: str) -> List[str]:
    """Gets the paths of all zettels that contain '#published'."""
    zettel_paths = get_file_paths(zettelkasten_path, ".md")
    zettels_to_publish = []
    published_tag_pattern = re.compile(r"(?<=\s)#published(?=\s)")

    for zettel_path in zettel_paths:
        contents = get_file_contents(zettel_path, "utf8")
        match = published_tag_pattern.search(contents)
        if match:
            zettels_to_publish.append(zettel_path)

    return zettels_to_publish


def get_file_contents(absolute_path: str, encoding: str) -> str:
    """Gets a file's contents.

    If UnicodeDecodeError is raised, this function will log and show an
    error message and make the program exit.
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
    """
    index_zettel = get_zettel_by_file_name("index", zettels)
    with open(index_zettel.path, "r", encoding="utf8") as file:
        index_contents = file.read()
    index_tags: List[str] = patterns.tags.findall(index_contents)
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
    """Lists all the zettels alphabetically in a new markdown file."""
    index = create_alphabetical_index(zettels)
    index_file_path = os.path.join(site_path, "alphabetical-index.md")
    with open(index_file_path, "w", encoding="utf8") as file:
        file.write(index)
    zettels.append(Zettel(index_file_path))


def create_chronological_index_file(
    zettels: List[Zettel], site_path: str, hide_chrono_index_dates: bool
) -> None:
    """Lists all the zettels chronologically in a new markdown file."""
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
    """
    categories = dict()
    linked_zettels: List[Zettel] = []
    for index_tag in index_tags:
        categories[index_tag] = ""
        for zettel in zettels:
            if zettel.id.isnumeric():
                if index_tag in zettel.tags:
                    categories[index_tag] += "* " + zettel.link + "\n"
                    linked_zettels.append(zettel)

    for zettel in zettels:
        if zettel not in linked_zettels and zettel.title not in ("index", "about"):
            logging.warning(" zettel not listed in index.md: `{zettel.title}`")

    return categories


def create_alphabetical_index(zettels: List[Zettel]) -> str:
    """Creates an alphabetized markdown list of all zettels' links

    Excludes zettels that have alpha characters in their IDs.
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
    """Permanently deletes all the markdown files in the site folder."""
    md_paths = get_file_paths(site_pages_path, ".md")
    for path in md_paths:
        os.remove(path)


def get_file_paths(dir_path: str, file_extension: str) -> List[str]:
    """Gets the paths of files in a directory

    Only paths of files with the given file extension are included.
    """
    file_names = os.listdir(dir_path)
    file_paths = []

    for file_name in file_names:
        if file_name.endswith(file_extension):
            file_path = os.path.join(dir_path, file_name)
            file_paths.append(file_path)

    return file_paths


def get_attachment_paths(zettels: List[Zettel]) -> List[str]:
    """Gets the file attachment links in multiple zettels."""
    all_attachment_paths = []
    file_attachment_groups: List[Tuple[str]] = []

    attachment_pattern = re.compile(r"(?<=]\()(.+\S\.(pdf|png|jpg))(?=\))")
    for zettel in zettels:
        with open(zettel.path, "r", encoding="utf8") as file:
            contents = file.read()
        file_attachment_groups: List[Tuple[str]] = attachment_pattern.findall(contents)
        for group in file_attachment_groups:
            if not group[0].startswith("http"):
                all_attachment_paths.append(group[0])

    return all_attachment_paths


def check_style(site_path: str, settings: dict) -> None:
    """Copies style.css into the site folder and settings into style.css.

    If style.css is already there, this function only tries to update
    the file.
    """
    site_style_path = copy_file_iff_not_present("style.css", site_path)
    try:
        update_css(site_style_path, settings)
    except ValueError:
        logging.error("  style.css cannot be parsed.")


def update_css(site_style_path: str, settings: dict) -> None:
    """Updates the site's copy of style.css with the user's settings.

    Raises ValueError if the file cannot be parsed.
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
    old_html_paths: List[str], all_html_paths: List[str], site_pages_path: str
) -> None:
    """Deletes HTML files that are not being generated or saved

    old_html_paths is the paths to HTML files present before the
    #published zettels were converted to HTML. all_html_paths is the
    ones present after. A file can be marked to be saved by putting its
    absolute path on a new line in ssg-ignore.txt.
    """
    file_name = os.path.join(site_pages_path, "ssg-ignore.txt")
    try:
        with open(file_name, "r", encoding="utf8") as file:
            ignored_html_paths = file.read().split("\n")
    except FileNotFoundError:
        logging.info("  ssg-ignore.txt not found")
        ignored_html_paths = []

    # Make sure all the slashes in all the paths are the same.
    for path in ignored_html_paths:
        path = path.replace("/", "\\")

    old_count = 0
    for old_path in old_html_paths:
        if old_path not in all_html_paths:
            if old_path not in ignored_html_paths:
                old_count += 1
                print(f"  Ready to delete {old_path}.")
                answer = input("  Confirm (y/n): ").lower()
                if answer == "y":
                    os.remove(old_path)
                    print("    File deleted.")
                else:
                    print("    File saved.")
    if not old_count:
        print("No old HTML files found.")
    else:
        print(f"  Deleted {old_count} files.")


if __name__ == "__main__":
    show_main_menu()
