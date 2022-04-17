import os
import re
from typing import List, Any
from functools import cache
from pygments import highlight, lexers  # https://pygments.org/
from pygments.formatters import HtmlFormatter
from ssg.settings import settings
from ssg.utils import logging, replace_pattern, copy_file_iff_not_present


def reformat_html_files(site_path: str, html_paths: List[str]) -> None:
    """Reformats the HTML files.

    Parameters
    ----------
    site_path : str
        The path to the site's folder.
    html_paths : List[str]
        The absolute paths to the HTML files.
    """
    n = convert_attachment_links(html_paths)
    logging.info(f"Converted {n} attachment links from the md to the html format.")
    logging.info("Adding syntax highlighting to code in codeblocks.")
    syntax_highlight_code(html_paths)

    logging.info("Inserting the site header, footer, etc. into each file.")
    append_copyright_notice(site_path, settings["copyright text"])
    copy_template_html_files(site_path)
    wrap_template_html(site_path, html_paths, settings["site title"])
    insert_all_index_links(site_path)


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
        plain_codeblock = revert_html_ampersand_char_codes(cb_contents_match[0])
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


def revert_html_ampersand_char_codes(codeblock: str) -> str:
    """Converts HTML ampersand character codes back to plaintext.

    For example, `&lt;` is converted back to `<`.

    Parameters
    ----------
    codeblock : str
        The codeblock content to revert.
    """
    replacements = [
        ("&#39;", "'"),
        ("&acute;", "´"),
        ("&aelig;", "æ"),
        ("&AElig;", "Æ"),
        ("&amp;", "&"),
        ("&Aring;", "Å"),
        ("&brvbar;", "¦"),
        ("&ccedil;", "ç"),
        ("&Ccedil;", "Ç"),
        ("&cedil;", "¸"),
        ("&cent;", "¢"),
        ("&copy;", "©"),
        ("&curren;", "¤"),
        ("&deg;", "°"),
        ("&divide;", "÷"),
        ("&eth;", "ð"),
        ("&ETH;", "Ð"),
        ("&frac12;", "½"),
        ("&frac14;", "¼"),
        ("&frac34;", "¾"),
        ("&gt;", ">"),
        ("&iexcl;", "¡"),
        ("&iquest;", "¿"),
        ("&laquo;", "«"),
        ("&lt;", "<"),
        ("&macr;", "¯"),
        ("&micro;", "µ"),
        ("&middot;", "·"),
        ("&nbsp;", "u"),
        ("&not;", "¬"),
        ("&ntilde;", "ñ"),
        ("&Ntilde;", "Ñ"),
        ("&oelig;", "œ"),
        ("&OElig;", "Œ"),
        ("&ordf;", "ª"),
        ("&ordm;", "º"),
        ("&Oslash;", "Ø"),
        ("&para;", "¶"),
        ("&plusmn;", "±"),
        ("&pound;", "£"),
        ("&quot;", '"'),
        ("&raquo;", "»"),
        ("&reg;", "®"),
        ("&sect;", "§"),
        ("&shy;", "­"),
        ("&sup1;", "¹"),
        ("&sup2;", "²"),
        ("&sup3;", "³"),
        ("&szlig;", "ß"),
        ("&thorn;", "þ"),
        ("&THORN;", "Þ"),
        ("&times;", "×"),
        ("&uml;", "¨"),
        ("&yen;", "¥"),
    ]
    for replacement in replacements:
        codeblock = codeblock.replace(replacement[0], replacement[1])
    return codeblock


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
    with open(index_path, "a", encoding="utf8") as file:
        file.write(
            '<br><br><br><br><br><br><br><p style="text-align: '
            f'center">{copyright_text}</p>'
        )


def copy_template_html_files(site_path: str) -> None:
    """Copies header and footer .html to the site folder iff they're'nt there.

    Parameters
    ----------
    site_path : str
        The path to the site folder.
    """
    copy_file_iff_not_present("header.html", site_path)
    copy_file_iff_not_present("footer.html", site_path)


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
            if os.path.splitext(os.path.split(path)[1])[0] not in settings["root pages"]:
                header_html = get_header_html(site_title, site_path, "../")
            else:
                header_html = get_header_html(site_title, site_path)
            footer_html = get_footer_html(site_path)
            file.write(header_html + contents + footer_html)


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
