import re


class patterns:
    """Compiled regex patterns."""
    tags = re.compile(r'(?<=\s)#[a-zA-Z0-9_-]+')
    h1_content = re.compile(r'(?<=#\s).+')
    zettel_link_id = re.compile(r'(?<=\[\[)\d{14}(?=\]\])')
    triple_codeblock = re.compile(r'(?<=\n)(`{3}(.|\n)*?(?<=\n)`{3})')
    single_codeblock = re.compile(r'(`[^`]+?`)')
