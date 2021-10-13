# external imports
import os
from typing import List, Optional

# internal imports
import patterns


class Zettel:
    def __init__(self, zettel_path: str):
        self.path: str = zettel_path
        self.file_name: str = self.get_zettel_file_name()  # includes extension
        self.id: str = self.get_zettel_id()
        self.title: str = self.get_zettel_title()
        self.link: str = self.get_zettel_link()
        self.tags: List[str] = self.get_zettel_tags()


    def get_zettel_file_name(self) -> str:
        """Gets a zettel's file name including the extension."""
        _, name_and_extension = os.path.split(self.path)
        return name_and_extension


    def get_zettel_id(self) -> str:
        """Gets a zettel's ID from its path."""
        zettel_id, _ = os.path.splitext(self.file_name)
        return zettel_id


    def get_zettel_title(self) -> str:
        """Gets the zettel's title (its first header level 1)."""
        if self.file_name == 'index.md':
            return 'index'
        elif self.file_name == 'about.md':
            return 'about'

        with open(self.path, 'r', encoding='utf8') as file:
            contents = file.read()
        match = patterns.h1_content.search(contents)
        if match:
            return match[0]
        raise ValueError(f'Zettel missing a title: {self.file_name}')


    def get_zettel_link(self) -> str:
        """Gets the zettel's zettelkasten-style link
        
        E.g. `[[20210919100142]] zettel title here`.
        """
        return f'[[{self.id}]] {self.title}'

    
    def get_zettel_tags(self) -> List[str]:
        """Gets all the tags in the zettel."""
        with open(self.path, 'r', encoding='utf8') as file:
            contents = file.read()
        tags: List[str] = patterns.tags.findall(contents)
        return tags


def get_zettel_by_id(link_id: str, zettels: List[Zettel]) -> Zettel:
    """Gets a zettel by its zettel ID."""
    for zettel in zettels:
        if zettel.id == link_id:
            return zettel


def get_zettel_by_file_name(file_name: str,
                            zettels: List[Zettel]) -> Optional[Zettel]:
    """Gets a zettel by its file name, not including the extension."""
    for zettel in zettels:
        if file_name + '.md' == zettel.file_name:
            return zettel
