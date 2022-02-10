"""Compiled regex patterns.

Attributes
----------
tags : re.Pattern
    The pattern of a tag, including a #. Assumes the tag is not at the 
    very beginning of the string.
h1_content : re.Pattern
    The pattern of a header of level 1.
zettel_link_id : re.Pattern
    The pattern of a zettelkasten-style internal link that follows 
    Zettlr's default settings (double square braces surrounding a 
    14-digit number).
triple_codeblock : re.Pattern
    The pattern of a codeblock delimited by triple backticks.
single_codeblock : re.Pattern
    The pattern of a codeblock delimited by single backticks (an inline 
    codeblock).
"""
import re


tags = re.compile(r"(?<=\s)#[a-zA-Z0-9_-]+")
h1_content = re.compile(r"(?<=#\s).+")
zettel_link_id = re.compile(r"(?<=\[\[)\d{14}(?=\]\])")
triple_codeblock = re.compile(r"(?<=\n)(`{3}(.|\n)*?(?<=\n)`{3})")
single_codeblock = re.compile(r"(`[^`]+?`)")
