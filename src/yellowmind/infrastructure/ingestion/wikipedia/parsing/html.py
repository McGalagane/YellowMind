"""Generic helpers for reading Wikipedia's parsed-HTML tables.

Tables are located by their header signature rather than by document position,
because articles gain and lose surrounding tables as editors revise them.
"""

import re
from typing import Final
from urllib.parse import unquote

from bs4 import BeautifulSoup, Tag

# Wikipedia renders footnote links as bracketed markers, e.g. `[ 6 ]`, which
# appear inside data cells and must not be mistaken for content.
_REFERENCE_MARKER: Final[re.Pattern[str]] = re.compile(r"\[\s*[^\[\]]{1,20}\s*\]")

_WIKILINK_PREFIX: Final[str] = "./"


class TableNotFoundError(Exception):
    """Raised when no table in a document matches the expected headers."""


def parse_html(html: str) -> BeautifulSoup:
    """Parse an article's HTML into a navigable tree."""
    return BeautifulSoup(html, "lxml")


def clean_text(value: str) -> str:
    """Collapse whitespace and drop footnote markers from cell text."""
    without_refs = _REFERENCE_MARKER.sub(" ", value)
    return " ".join(without_refs.split())


def element_text(element: Tag | None) -> str:
    """Return an element's visible text, cleaned."""
    if element is None:
        return ""
    return clean_text(element.get_text(" ", strip=True))


def row_cells(row: Tag) -> list[Tag]:
    """Return a row's cells, header and data alike, in document order."""
    return row.find_all(["th", "td"])


def row_texts(row: Tag) -> list[str]:
    """Return a row's cleaned cell texts."""
    return [element_text(cell) for cell in row_cells(row)]


def find_table_by_headers(soup: BeautifulSoup, required_headers: set[str]) -> Tag:
    """Return the first table whose first row contains all `required_headers`.

    Raises:
        TableNotFoundError: If no table matches.
    """
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        if required_headers.issubset(set(row_texts(rows[0]))):
            return table

    msg = f"No table found with headers {sorted(required_headers)}"
    raise TableNotFoundError(msg)


def find_infobox(soup: BeautifulSoup) -> Tag:
    """Return the article's infobox table.

    Infoboxes are laid out vertically, one label-value row at a time, so they
    cannot be located by a header signature the way data tables are.

    Raises:
        TableNotFoundError: If the article has no infobox.
    """
    # A CSS class selector matches the `infobox` token wherever it sits among an
    # element's classes, which is what the articles need: every edition between
    # 2015 and 2024 renders `class="infobox vevent"`. The suppression covers an
    # untyped `namespaces` parameter in the bs4 stubs, not this call.
    infobox = soup.select_one("table.infobox")  # pyright: ignore[reportUnknownMemberType]
    if infobox is None:
        msg = "No infobox found in article"
        raise TableNotFoundError(msg)
    return infobox


def infobox_value(infobox: Tag, label: str) -> str:
    """Return the value paired with `label` in an infobox, or an empty string."""
    for row in infobox.find_all("tr"):
        cells = row_cells(row)
        if len(cells) == 2 and element_text(cells[0]) == label:
            return element_text(cells[1])
    return ""


def header_index(table: Tag, *names: str) -> int:
    """Return the column index of the first header matching any of `names`.

    Accepts several spellings because headers vary between editions, for
    instance ``Ref`` in 2015 and ``Ref.`` in later years.

    Raises:
        TableNotFoundError: If none of the names is present.
    """
    rows = table.find_all("tr")
    if not rows:
        msg = "Table has no rows"
        raise TableNotFoundError(msg)

    headers = row_texts(rows[0])
    for name in names:
        if name in headers:
            return headers.index(name)

    msg = f"None of the headers {list(names)} found in {headers}"
    raise TableNotFoundError(msg)


def wikilink_slug(cell: Tag | None) -> str:
    """Return the article slug of a cell's first wikilink, or an empty string.

    Slugs are percent-decoded so that non-ASCII titles read naturally and match
    across editions.
    """
    if cell is None:
        return ""

    anchor = cell.find("a", href=True)
    if not isinstance(anchor, Tag):
        return ""

    href = str(anchor.get("href", ""))
    if href.startswith(_WIKILINK_PREFIX):
        href = href[len(_WIKILINK_PREFIX) :]

    # Drop any section fragment; the article identity is what matters.
    slug = href.split("#", 1)[0]
    return unquote(slug)


def parse_optional_int(value: str) -> int | None:
    """Return `value` as an int, or None when it is absent or not numeric."""
    text = clean_text(value)
    return int(text) if text.isdigit() else None
