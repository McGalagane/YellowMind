"""Unit tests for the route table parser."""

from datetime import date
from pathlib import Path

import pytest

from yellowmind.domain.entities import StageType
from yellowmind.infrastructure.ingestion.wikipedia.parsing import StageParseError, parse_stages

_FIXTURE = Path(__file__).parents[5] / "fixtures" / "wikipedia" / "route_stages_sample.html"


def _stages(year: int = 2020):
    return parse_stages(_FIXTURE.read_text(), year)


def _route(rows: str) -> str:
    """Wrap route rows in a header whose `Type` spans two columns, as the real one does."""
    return f"""
    <table class="wikitable">
      <tbody>
        <tr><th>Stage</th><th>Date</th><th>Course</th><th>Distance</th>
            <th colspan="2">Type</th><th>Winner</th></tr>
        {rows}
      </tbody>
    </table>
    """


def _row(number: str, date_text: str, distance: str, type_label: str) -> str:
    return f"""
    <tr><th>{number}</th><td>{date_text}</td><td>A to B</td><td>{distance}</td>
        <td><span><img src="./icon.png" /></span></td><td>{type_label}</td>
        <td>Someone (FRA)</td></tr>
    """


def test_reads_every_stage_and_skips_the_rest() -> None:
    """The fixture holds 10 stages plus a rest day and a distance total."""
    stages = _stages()

    assert [s.number for s in stages] == list(range(1, 11))


def test_terrain_comes_from_the_label_not_the_icon_cell() -> None:
    """`Type` spans a pictogram and a label; reading the wrong one yields nothing."""
    stages = _stages()

    assert stages[0].stage_type is StageType.FLAT
    assert stages[3].stage_type is StageType.INDIVIDUAL_TT


@pytest.mark.parametrize(
    ("number", "expected"),
    [
        (1, StageType.FLAT),
        (2, StageType.HILLY),  # 'Medium mountain stage'
        (3, StageType.HILLY),  # 'Medium-mountain stage', hyphenated in 2023
        (4, StageType.INDIVIDUAL_TT),
        (5, StageType.TEAM_TT),
        (6, StageType.MOUNTAIN),  # 'High mountain stage'
        (7, StageType.MOUNTAIN_TT),
        (8, StageType.FLAT),  # bare 'Flat'
        (9, StageType.HILLY),  # 'Hilly stage'
        (10, StageType.MOUNTAIN),
    ],
)
def test_maps_every_terrain_spelling(number: int, expected: StageType) -> None:
    stage = next(s for s in _stages() if s.number == number)

    assert stage.stage_type is expected


def test_resolves_dates_against_the_edition_year() -> None:
    stages = _stages(2020)

    assert stages[0].date == date(2020, 8, 29)


def test_handles_a_route_crossing_two_months() -> None:
    """2020 ran from August into September."""
    stages = _stages(2020)

    assert stages[0].date == date(2020, 8, 29)
    assert stages[3].date == date(2020, 9, 1)


def test_reads_distances_including_decimals() -> None:
    stages = _stages()

    # Exact parses of decimal strings, so equality is safe here.
    assert stages[0].distance_km == 182.0
    assert stages[2].distance_km == 193.5
    assert stages[3].distance_km == 13.8


def test_skips_the_rest_day_row() -> None:
    """A rest day has no stage number and must not become a stage."""
    stages = _stages()

    assert all(s.date != date(2020, 9, 3) for s in stages)


def test_skips_the_distance_total_row() -> None:
    """The total carries a thousands separator that would parse as a distance."""
    stages = _stages()

    assert all(s.distance_km < 1000 for s in stages)


def test_accepts_the_2018_header_spelling() -> None:
    """2018 names the column `Stage type`."""
    html = """
    <table class="wikitable"><tbody>
      <tr><th>Stage</th><th>Date</th><th>Course</th><th>Distance</th>
          <th colspan="2">Stage type</th><th>Winner</th></tr>
      <tr><th>1</th><td>7 July</td><td>A to B</td><td>201 km (125 mi)</td>
          <td><span><img src="./i.png" /></span></td><td>Flat stage</td>
          <td>Someone (FRA)</td></tr>
    </tbody></table>
    """

    stages = parse_stages(html, 2018)

    assert stages[0].stage_type is StageType.FLAT


def test_rejects_an_unknown_terrain_label() -> None:
    """Guessing would mislabel terrain, which is a primary predictor of a winner."""
    html = _route(_row("1", "1 July", "100 km (62 mi)", "Gravel stage"))

    with pytest.raises(StageParseError, match="Unrecognised stage type"):
        parse_stages(html, 2023)


def test_rejects_an_unreadable_distance() -> None:
    html = _route(_row("1", "1 July", "quite far", "Flat stage"))

    with pytest.raises(StageParseError, match="Cannot read distance"):
        parse_stages(html, 2023)


def test_rejects_an_unreadable_date() -> None:
    html = _route(_row("1", "sometime", "100 km (62 mi)", "Flat stage"))

    with pytest.raises(StageParseError, match="Cannot read date"):
        parse_stages(html, 2023)


def test_rejects_an_unknown_month() -> None:
    html = _route(_row("1", "1 Jullet", "100 km (62 mi)", "Flat stage"))

    with pytest.raises(StageParseError, match="Unrecognised month"):
        parse_stages(html, 2023)


def test_rejects_an_impossible_date() -> None:
    html = _route(_row("1", "31 June", "100 km (62 mi)", "Flat stage"))

    with pytest.raises(StageParseError, match="Invalid date"):
        parse_stages(html, 2023)
