"""Compiled regex patterns.

Attributes
----------
absolute_attachment_link : str
    The pattern of a markdown link containing an absolute path to a file.
h1_content : re.Pattern
    The pattern of a header of level 1.
link_path : str
    The pattern of a markdown link containing a path to a file or website,
    and the path may be either relative or absolute.
md_ext_in_link : re.Pattern
    The pattern of a markdown file path extension in a markdown link.
md_link : re.Pattern
    The pattern of a markdown link.
published_tag : re.Pattern
    The pattern of the ``#published`` tag.
single_codeblock : re.Pattern
    The pattern of a codeblock delimited by single backticks (an inline 
    codeblock).
tag : re.Pattern
    The pattern of a tag, including a #. Assumes the tag is not at the very
    beginning of the string.
triple_codeblock : re.Pattern
    The pattern of a codeblock delimited by triple backticks.
zettel_link_id : re.Pattern
    The pattern of a zettelkasten-style internal link that follows Zettlr's
    default settings (double square braces surrounding a 14-digit number).
"""
import os
import re
from typing import List


absolute_attachment_link = re.compile(
    r"(?<=]\()(?:file://)?(?:[a-zA-Z]:|/)[^\n]*?([^\\/\n]+\.(pdf|png|jpg|jpeg))(?=\))"
)
link_path = re.compile(r"(?<=]\().+(?=\))")
h1_content = re.compile(r"(?<=#\s).+")
md_ext_in_link = re.compile(r"(?<=\S)\.md(?=\))")
md_link = re.compile(r"\[(.+)]\((.+)\)")
published_tag = re.compile(r"(?<=\s)#published(?=\s)")
single_codeblock = re.compile(r"(`[^`]+?`)")
tag = re.compile(r"(?<=\s)#[a-zA-Z0-9_-]+")
triple_codeblock = re.compile(r"(?<=\n)(`{3}(.|\n)*?(?<=\n)`{3})")
zettel_link_id = re.compile(r"(?<=\[\[)\d{14}(?=\]\])")


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
    paths: List[str] = link_path.findall(contents)
    for path in paths:
        file_path = os.path.join(folder_path, path)
        file_path = os.path.normpath(file_path)
        if os.path.exists(file_path):
            file_paths.append(file_path)
    return file_paths
