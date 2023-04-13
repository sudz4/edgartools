import re

from markdownify import markdownify
from rich import box
from rich.console import Group
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from edgar._rich import repr_rich

__all__ = [
    'convert_table',
    'MarkdownContent',
    'markdown_to_rich',
    "fix_markdown"
]


def _empty(row):
    if not row:
        return True
    chars = set(re.sub(r"\s", "", row.strip()))
    return chars == {'|'} or chars == {'-', '|'}


def convert_table(table_markdown: str):
    """Convert the markdown to a rich Table"""
    all_rows = table_markdown.replace("| |", "|\n|").split("\n")

    # Just output a simple table with no headers
    table = Table(" " * all_rows[0].count("|"), box=box.SIMPLE)
    for row in all_rows:
        if not _empty(row):
            row = [cell.strip() for cell in row[1:-1].strip().split("|")]
            table.add_row(*row)
    return table


skip_tags = ["<DOCUMENT>", "<TYPE>", "<SEQUENCE>", "<FILENAME>", "<DESCRIPTION>", "<TEXT>"]


def markdown_to_rich(md: str, title: str = "") -> Markdown:
    """Convert the markdown to rich .. handling tables better than rich"""
    content = []
    buf = ""
    table_buf = ""
    is_table = False
    for line in md.split("\n"):
        if is_table:
            if not line.strip():
                table = convert_table(table_buf)
                content.append(table)
                is_table = False
                table_buf = ""
            else:
                table_buf += line + "\n"
        else:
            if "|  |" in line:
                markdown = Markdown(buf)
                buf = ""
                table_buf = line + "\n"
                content.append(markdown)
                is_table = True
            else:
                buf += line + "\n"
    if buf:
        content.append(Markdown(buf))
    return Panel(Group(*content), title=title, subtitle=title, box=box.ROUNDED)


def fix_markdown(md: str):

    # Clean up issues with not spaces between sentences like "Condition.On"
    md = re.sub(r"([a-z]\.)([A-Z])", r"\1 \2", md)

    # And fix split Item numbers e.g. "Item\n5.02"
    md = re.sub(r"(Item)\n\s?(\d.\d{,2})", r"\1 \2", md)

    # Fix items not on newlines e.g. ". Item 5.02"
    md = re.sub(r"\. (Item)\s?(\d.\d{,2})", r".\n \1 \2", md)
    return md


def html_to_markdown(html: str) -> str:
    return fix_markdown(markdownify(html))


class MarkdownContent:

    def __init__(self,
                 html: str,
                 title: str = ""):
        if "<DOCUMENT>" in html[:500]:
            html = "\n".join(line for line in html.split("\n")
                             if not any(line.startswith(tag) for tag in skip_tags))

        self.md = re.sub(r'(\n\s*)+\n', '\n\n', markdownify(html))
        self.title = title

    def __rich__(self):
        return markdown_to_rich(self.md, title=self.title)

    def __repr__(self):
        return repr_rich(self.__rich__())