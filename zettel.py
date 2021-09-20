import os
import re


class Zettel:
    def __init__(self, zettel_path: str):
        self.path: str = zettel_path
        self.file_name: str = self.get_zettel_file_name()
        self.id: str = self.get_zettel_id()
        self.title: str = self.get_zettel_title()
        self.link: str = self.get_zettel_link()


    def get_zettel_file_name(self) -> str:
        """Gets a zettel's file name including the extension."""
        _, name_and_extension = os.path.split(self.path)
        return name_and_extension


    def get_zettel_id(self) -> str:
        """Gets a zettel's ID from its path."""
        zettel_id, _ = os.path.splitext(self.file_name)
        return zettel_id


    def get_zettel_title(self) -> str:
        """Gets a zettel's title (its first header level 1)."""
        if self.path.endswith('index.md'):
            return 'index'
        elif self.path.endswith('about.md'):
            return 'about'

        with open(self.path, 'r', encoding='utf8') as file:
            contents = file.read()
        match = re.search(r'(?<=#\s).+', contents)
        if match:
            return match[0]
        raise ValueError(f'Zettel missing a title: {self.file_name}')


    def get_zettel_link(self) -> str:
        """Gets a zettel's zettelkasten-style link
        
        E.g. `[[20210919100142]] zettel title here`.
        """
        return f'[[{self.id}]] {self.title}'
