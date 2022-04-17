import os
from typing import List, Optional
from mistune import markdown as HTMLConverter  # https://github.com/lepture/mistune
from ssg.settings import settings, get_zk_id_not_in_link_pattern


class Zettel:
    def __init__(self, zettel_path: str):
        self.path: str = zettel_path
        self.folder_path: str = os.path.dirname(zettel_path)
        self.file_name_and_ext: str = os.path.split(self.path)[1]
        self.file_name: str = os.path.splitext(self.file_name_and_ext)[0]
        self.id: Optional[str] = self.__get_zettel_id(self.path, self.file_name)
        self.title: str = self.__get_zettel_title(self.path, self.file_name_and_ext)
        self.link: str = self.__get_zettel_link(self.file_name, self.id, self.title)
        self.alt_link: Optional[str] = self.__get_zettel_name_link(self.file_name)
        self.tags: List[str] = self.__get_zettel_tags(self.path)

    def __get_zettel_id(self, path: str, file_name: str) -> Optional[str]:
        """Gets the zettel's ID, if it has one.

        Checks the file's name for an ID first, and then checks the contents of
        the file if no ID is found in the file name. If no ID is found
        anywhere, the ID is None.
        """
        match = settings["patterns"]["zk id"].match(file_name)
        if match:
            return match[0]
        with open(path, "r", encoding="utf8") as file:
            contents = file.read()
        match = get_zk_id_not_in_link_pattern().search(contents)
        if match:
            return match[0]

    def __get_zettel_title(self, path: str, file_name_and_ext: str) -> str:
        """Gets the zettel's title.
        
        The title is the content of the first header level 1, or the file name
        including the extension if there is no header level 1.
        """
        if file_name_and_ext == "index.md":
            return "index"
        elif file_name_and_ext == "about.md":
            return "about"
        with open(path, "r", encoding="utf8") as file:
            contents = file.read()
        match = settings["patterns"]["h1 content"].search(contents)
        if match:
            return match[0]
        return file_name_and_ext

    def __get_zettel_link(self, file_name: str, id: Optional[str], title: str) -> str:
        """Gets the zettel's zettelkasten-style link.

        E.g. `[[20210919100142]] zettel title here` if the zettel has an ID.
        Otherwise, the zettel link will be in the format `[[file name]]`, which
        does not include the file extension.
        """
        if id is None:
            return f"[[{file_name}]]"
        return f"[[{id}]] {title}"

    def __get_zettel_name_link(self, file_name: str) -> Optional[str]:
        """Gets the zettel's zettelkasten-style link that uses the file's name.

        This does not include the file extension. This will be the same as what
        __get_zettel_link returns if the zettel has no ID.
        """
        return f"[[{file_name}]]"

    def __get_zettel_tags(self, path: str) -> List[str]:
        """Gets all the tags in the zettel."""
        with open(path, "r", encoding="utf8") as file:
            contents = file.read()
        tags: List[str] = settings["patterns"]["tag"].findall(contents)
        return tags

    def create_html_file(self) -> str:
        """Creates one HTML file from a markdown file in the same folder.

        Overwrites an HTML file if it happens to have the same name.
        Returns the new HTML file's path.
        """
        with open(self.path, "r", encoding="utf8") as file:
            md_text = file.read()
        html_text = HTMLConverter(md_text)
        html_path = self.create_html_path(self.path)
        with open(html_path, "w", encoding="utf8") as file:
            file.write(html_text)
        return html_path

    def create_html_path(self, path: str) -> str:
        """Creates an HTML file path from a corresponding md file path."""
        file_path_and_name, _ = os.path.splitext(path)
        new_html_path = file_path_and_name + ".html"
        return new_html_path


def get_zettel_by_id_or_file_name(
    identifier: str, zettels: List[Zettel]
) -> Optional[Zettel]:
    """Gets a zettel by its ID or file name.

    If the identifier matches the pattern of a zettel ID, this function will
    attempt to get the zettel by its ID. Otherwise, it will attempt to get the
    zettel by its file name. If this also does not succeed, it will attempt to
    get the zettel by its file name including the extension.

    Parameters
    ----------
    identifier : str
        The ID or file name of the zettel.
    zettels : List[Zettel]
        The list of zettels to search in.

    Returns
    -------
    Optional[Zettel]
        The zettel with the given ID or file name, if it exists.
    """
    if settings["patterns"]["zk id"].match(identifier):
        for zettel in zettels:
            if zettel.id == identifier:
                return zettel
    for zettel in zettels:
        if zettel.file_name == identifier:
            return zettel
    for zettel in zettels:
        if zettel.file_name_and_ext == identifier:
            return zettel
