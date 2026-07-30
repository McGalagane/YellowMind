"""Unit tests for the edition overview parser."""

from datetime import date
from pathlib import Path

import pytest

from yellowmind.infrastructure.ingestion.wikipedia.parsing import (
    EditionParseError,
    parse_edition,
)

_FIXTURE = Path(__file__).parents[5] / "fixtures" / "wikipedia" / "edition_overview_sample.html"


def _infobox(dates: str) -> str:
    """Wrap a `Dates` value in the minimum infobox the parser needs."""
    return f"""
    <table class="infobox vevent">
      <tbody>
        <tr><th>Dates</th><td>{dates}</td></tr>
        <tr><th>Stages</th><td>21</td></tr>
      </tbody>
    </table>
    """


def test_parses_the_sample_overview() -> None:
    record = parse_edition(_FIXTURE.read_text())

    assert record.year == 2023
    assert record.start_date == date(2023, 7, 1)
    assert record.end_date == date(2023, 7, 23)


# Every value below was taken from the live article for that edition, so these
# are the real variations rather than invented ones.
@pytest.mark.parametrize(
    ("dates", "expected_start", "expected_end"),
    [
        # Start day carries no month; both dates share July.
        ("4\u201326 July 2015", date(2015, 7, 4), date(2015, 7, 26)),
        ("2\u201324 July 2016", date(2016, 7, 2), date(2016, 7, 24)),
        ("7\u201329 July 2018", date(2018, 7, 7), date(2018, 7, 29)),
        # Crosses two months using an em dash, unlike every other edition.
        (
            "29 August \u2014 20 September 2020",
            date(2020, 8, 29),
            date(2020, 9, 20),
        ),
        # Crosses two months using an en dash.
        ("26 June \u2013 18 July 2021", date(2021, 6, 26), date(2021, 7, 18)),
        ("29 June \u2013 21 July 2024", date(2024, 6, 29), date(2024, 7, 21)),
    ],
)
def test_parses_real_date_variants(dates: str, expected_start: date, expected_end: date) -> None:
    record = parse_edition(_infobox(dates))

    assert record.start_date == expected_start
    assert record.end_date == expected_end
    assert record.year == expected_end.year


def test_ignores_footnote_markers() -> None:
    """The 2020 article appends a reference to its date range."""
    record = parse_edition(_infobox("29 August \u2014 20 September 2020 [ 1 ]"))

    assert record.start_date == date(2020, 8, 29)
    assert record.end_date == date(2020, 9, 20)


def test_accepts_a_plain_hyphen() -> None:
    """Editors sometimes use a hyphen where the house style wants a dash."""
    record = parse_edition(_infobox("1-23 July 2023"))

    assert record.start_date == date(2023, 7, 1)


def test_year_comes_from_the_article_not_the_caller() -> None:
    """A misfetched article must not be stored against the requested year."""
    record = parse_edition(_infobox("1\u201323 July 2019"))

    assert record.year == 2019


def test_rejects_article_without_infobox() -> None:
    with pytest.raises(EditionParseError, match="no infobox"):
        parse_edition("<html><body><p>No infobox here.</p></body></html>")


def test_rejects_infobox_without_dates_row() -> None:
    html = """
    <table class="infobox"><tbody>
      <tr><th>Stages</th><td>21</td></tr>
    </tbody></table>
    """

    with pytest.raises(EditionParseError, match="no 'Dates' row"):
        parse_edition(html)


def test_rejects_single_date() -> None:
    with pytest.raises(EditionParseError, match="Expected a date range"):
        parse_edition(_infobox("23 July 2023"))


def test_rejects_unreadable_closing_date() -> None:
    with pytest.raises(EditionParseError, match="Cannot read closing date"):
        parse_edition(_infobox("1 \u2013 sometime in July"))


def test_rejects_unknown_month() -> None:
    with pytest.raises(EditionParseError, match="Unrecognised month"):
        parse_edition(_infobox("1\u201323 Jullet 2023"))


def test_rejects_impossible_day() -> None:
    with pytest.raises(EditionParseError, match="Invalid date"):
        parse_edition(_infobox("1\u201332 July 2023"))
