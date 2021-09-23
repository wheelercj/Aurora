import re


class patterns:
    """Compiled regex patterns."""
    tags = re.compile(r'(?<=\s)#[a-zA-Z0-9_-]+')
    h1_content = re.compile(r'(?<=#\s).+')
