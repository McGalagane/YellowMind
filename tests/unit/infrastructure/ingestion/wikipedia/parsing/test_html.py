"""Tests for the generic Wikipedia table helpers."""

import pytest
from bs4 import Tag

from yellowmind.infrastructure.ingestion.wikipedia.parsing.html import (
    TableNotFoundError,
    clean_text,
    data_columns,
    find_table_by_headers,
    header_index,
    header_span,
    parse_html,
    parse_optional_int,
    row_cells,
    row_texts,
    span_text,
    wikilink_slug,
)

TWO_TABLES = """
<html><body>
  <table><tbody><tr><th>Legend</th><th>Meaning</th></tr></tbody></table>
  <table><tbody>
    <tr><th>Rank</th><th>Rider</th><th>Team</th><th>Time</th></tr>
    <tr><td>1</td><td><a href="./Adam_Yates">Adam Yates</a></td><td>UAE</td><td>4h</td></tr>
  </tbody></table>
</body></html>
"""


def first_cell(html: str) -> Tag:
    """Return a snippet's first table cell, narrowed for the type checker."""
    cell = parse_html(html).find("td")
    assert isinstance(cell, Tag)
    return cell


def test_clean_text_collapses_whitespace() -> None:
    assert clean_text("  Jonas   Vingegaard \n ") == "Jonas Vingegaard"


def test_clean_text_removes_footnote_markers() -> None:
    assert clean_text("DSQ-15 [ 6 ]") == "DSQ-15"
    assert clean_text("Rider[12]") == "Rider"


def test_clean_text_keeps_ordinary_content() -> None:
    assert clean_text("Team Jumbo\u2013Visma") == "Team Jumbo\u2013Visma"


def test_find_table_by_headers_skips_non_matching_tables() -> None:
    soup = parse_html(TWO_TABLES)

    table = find_table_by_headers(soup, {"Rank", "Rider", "Team"})

    assert row_texts(table.find_all("tr")[0]) == ["Rank", "Rider", "Team", "Time"]


def test_find_table_by_headers_raises_when_absent() -> None:
    soup = parse_html(TWO_TABLES)

    with pytest.raises(TableNotFoundError, match="No table found"):
        find_table_by_headers(soup, {"Stage", "Distance"})


def test_header_index_locates_columns() -> None:
    table = find_table_by_headers(parse_html(TWO_TABLES), {"Rank"})

    assert header_index(table, "Rank") == 0
    assert header_index(table, "Time") == 3


def test_header_index_accepts_alternative_spellings() -> None:
    # Headers drift between editions, e.g. "Ref" in 2015 versus "Ref." later.
    table = find_table_by_headers(parse_html(TWO_TABLES), {"Rank"})

    assert header_index(table, "Ref.", "Ref", "Time") == 3


def test_header_index_raises_when_no_spelling_matches() -> None:
    table = find_table_by_headers(parse_html(TWO_TABLES), {"Rank"})

    with pytest.raises(TableNotFoundError, match="None of the headers"):
        header_index(table, "Distance")


def test_wikilink_slug_extracts_article_title() -> None:
    cell = first_cell('<td><a href="./Adam_Yates">Adam Yates</a></td>')

    assert wikilink_slug(cell) == "Adam_Yates"


def test_wikilink_slug_decodes_percent_escapes() -> None:
    cell = first_cell('<td><a href="./Visma%E2%80%93Lease_a_Bike">x</a></td>')

    assert wikilink_slug(cell) == "Visma\u2013Lease_a_Bike"


def test_wikilink_slug_drops_section_fragment() -> None:
    cell = first_cell('<td><a href="./2023_Tour#General_classification">x</a></td>')

    assert wikilink_slug(cell) == "2023_Tour"


def test_wikilink_slug_is_empty_without_a_link() -> None:
    assert wikilink_slug(first_cell("<td>No link here</td>")) == ""


def test_wikilink_slug_handles_missing_cell() -> None:
    assert wikilink_slug(None) == ""


@pytest.mark.parametrize(
    ("value", "expected"),
    [("26", 26), ("", None), ("   ", None), ("DNF-8", None), ("+ 4'", None)],
)
def test_parse_optional_int(value: str, expected: int | None) -> None:
    assert parse_optional_int(value) == expected


SPANNING_HEADER = """
<table><tbody>
  <tr><th>Stage</th><th>Date</th><th colspan="2">Type</th><th>Winner</th></tr>
  <tr><td>1</td><td>1 July</td><td><img src="./icon.png" /></td><td>Flat stage</td>
      <td>Someone</td></tr>
</tbody></table>
"""


def _spanning_table() -> Tag:
    table = parse_html(SPANNING_HEADER).find("table")
    assert isinstance(table, Tag)
    return table


def test_data_columns_repeats_a_spanning_header() -> None:
    """One label per data column, so positions line up with a data row's cells."""
    assert data_columns(_spanning_table()) == [
        "Stage",
        "Date",
        "Type",
        "Type",
        "Winner",
    ]


def test_columns_after_a_span_are_not_shifted() -> None:
    """The bug this guards against is silent: `Winner` would otherwise read `Type`."""
    assert header_index(_spanning_table(), "Winner") == 4


def test_header_span_reports_width() -> None:
    assert header_span(_spanning_table(), "Type") == (2, 2)
    assert header_span(_spanning_table(), "Stage") == (0, 1)


def test_header_span_accepts_alternative_spellings() -> None:
    assert header_span(_spanning_table(), "Stage type", "Type") == (2, 2)


def test_span_text_skips_an_empty_pictogram_cell() -> None:
    rows = _spanning_table().find_all("tr")
    cells = row_cells(rows[1])

    assert span_text(cells, 2, 2) == "Flat stage"


def test_span_text_is_empty_when_the_span_holds_nothing() -> None:
    rows = _spanning_table().find_all("tr")
    cells = row_cells(rows[1])

    assert span_text(cells, 99, 2) == ""
