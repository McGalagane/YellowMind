"""Unit tests for the stage results and GC standings parser."""

from pathlib import Path

from yellowmind.infrastructure.ingestion.wikipedia.parsing import parse_stage_boards

_FIXTURE = Path(__file__).parents[5] / "fixtures" / "wikipedia" / "stage_results_sample.html"
_HEADING_FIXTURE = """
<html><body>
  <h3>Stage 1</h3>
  <table>
    <tr><th>Rank</th><th>Rider</th><th>Team</th><th>Time</th></tr>
    <tr><td>1</td><td><a href="./Rohan_Dennis">Rohan Dennis ( AUS )</a></td>
        <td>BMC</td><td>14' 56"</td></tr>
    <tr><td>2</td><td><a href="./Tony_Martin_(cyclist)">Tony Martin ( GER )</a></td>
        <td>EQS</td><td>+ 5"</td></tr>
  </table>
  <h3>Stage 2</h3>
  <table>
    <tr><th>Rank</th><th>Rider</th><th>Team</th><th>Time</th></tr>
    <tr><td>1</td><td><a href="./Andre_Greipel">Andre Greipel ( GER )</a></td>
        <td>Lotto</td><td>3h 29' 03"</td></tr>
    <tr><td>2</td><td><a href="./Peter_Sagan">Peter Sagan ( SVK )</a></td>
        <td>Tinkoff</td><td>+ 0"</td></tr>
  </table>
  <table>
    <tr><th>Rank</th><th>Rider</th><th>Team</th><th>Time</th></tr>
    <tr><td>1</td><td><a href="./Fabian_Cancellara">Fabian Cancellara ( SUI )</a></td>
        <td>Trek</td><td>3h 44' 01"</td></tr>
    <tr><td>2</td><td><a href="./Tony_Martin_(cyclist)">Tony Martin ( GER )</a></td>
        <td>EQS</td><td>+ 3"</td></tr>
  </table>
</body></html>
"""


def test_reads_stage_result_and_gc_from_captions() -> None:
    boards = {b.stage_number: b for b in parse_stage_boards(_FIXTURE.read_text())}

    assert set(boards) == {1, 2}
    assert [r.rider_slug for r in boards[1].results] == [
        "Adam_Yates",
        "Simon_Yates_(cyclist)",
        "Tadej_Pogačar",
    ]
    assert boards[1].gc[0].rider_slug == "Adam_Yates"
    assert boards[1].gc[0].time_gap_seconds == 0
    assert boards[1].gc[1].time_gap_seconds == 8


def test_same_time_inherits_previous_gap() -> None:
    boards = {b.stage_number: b for b in parse_stage_boards(_FIXTURE.read_text())}

    assert boards[1].results[1].time_gap_seconds == 4
    assert boards[1].results[2].time == "s.t."
    assert boards[1].results[2].time_gap_seconds == 4


def test_strips_nationality_from_rider_name() -> None:
    boards = {b.stage_number: b for b in parse_stage_boards(_FIXTURE.read_text())}

    assert boards[1].results[0].rider_name == "Adam Yates"


def test_skips_team_time_trial_stage_results() -> None:
    boards = {b.stage_number: b for b in parse_stage_boards(_FIXTURE.read_text())}

    assert boards[2].results_skipped == "team_time_trial"
    assert boards[2].results == ()
    assert boards[2].gc[0].rider_slug == "Mike_Teunissen"


def test_heading_fallback_treats_lone_table_as_both() -> None:
    """Stage 1 ITT under a heading has one table that is result and GC."""
    boards = {b.stage_number: b for b in parse_stage_boards(_HEADING_FIXTURE)}

    assert boards[1].results[0].rider_slug == "Rohan_Dennis"
    assert boards[1].gc[0].rider_slug == "Rohan_Dennis"
    assert boards[1].gc[1].time_gap_seconds == 5


def test_heading_fallback_uses_second_table_as_gc() -> None:
    boards = {b.stage_number: b for b in parse_stage_boards(_HEADING_FIXTURE)}

    assert boards[2].results[0].rider_slug == "Andre_Greipel"
    assert boards[2].gc[0].rider_slug == "Fabian_Cancellara"


def test_ignores_outer_wrapper_tables() -> None:
    """The fixture's wrappers would yield duplicate ranks if read."""
    boards = parse_stage_boards(_FIXTURE.read_text())
    stage_one = next(b for b in boards if b.stage_number == 1)

    assert len(stage_one.results) == 3
