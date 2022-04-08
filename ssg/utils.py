import os
import sys
import re
import shutil
from typing import List, Tuple
import PySimpleGUI as sg
import logging
from ssg.settings import settings


__log_path = os.path.join(os.path.dirname(__file__), "zk-ssg.log")
logging.basicConfig(
    filename=__log_path, encoding="utf-8", filemode="w", level=logging.INFO
)  # https://docs.python.org/3/howto/logging.html#logging-basic-tutorial


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
