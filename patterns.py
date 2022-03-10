"""Regex patterns.

Attributes
----------
absolute_attachment_link : str
    The uncompiled pattern of a markdown link containing an absolute path to a file.
h1_content : re.Pattern
    The compiled pattern of a header of level 1.
single_codeblock : re.Pattern
    The compiled pattern of a codeblock delimited by single backticks (an inline 
    codeblock).
tags : re.Pattern
    The compiled pattern of a tag, including a #. Assumes the tag is not at the very
    beginning of the string.
triple_codeblock : re.Pattern
    The compiled pattern of a codeblock delimited by triple backticks.
zettel_link_id : re.Pattern
    The compiled pattern of a zettelkasten-style internal link that follows Zettlr's
    default settings (double square braces surrounding a 14-digit number).
"""
import re


absolute_attachment_link = (
    r"(?<=]\()(?:file://)?(?:[a-zA-Z]:|/)[^\n]*?([^\\/\n]+\.(pdf|png|jpg|jpeg))(?=\))"
)
h1_content = re.compile(r"(?<=#\s).+")
single_codeblock = re.compile(r"(`[^`]+?`)")
tags = re.compile(r"(?<=\s)#[a-zA-Z0-9_-]+")
triple_codeblock = re.compile(r"(?<=\n)(`{3}(.|\n)*?(?<=\n)`{3})")
zettel_link_id = re.compile(r"(?<=\[\[)\d{14}(?=\]\])")
