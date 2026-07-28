"""Tests for Wikipedia URL and page-title helpers."""

import pytest

from yellowmind.infrastructure.ingestion.wikipedia import (
    edition_title,
    rest_html_path,
    stage_range_title,
    stage_range_titles,
)


def test_edition_title() -> None:
    assert edition_title(2023) == "2023_Tour_de_France"


def test_edition_title_rejects_year_before_first_tour() -> None:
    with pytest.raises(ValueError, match="1903"):
        edition_title(1902)


def test_stage_range_title() -> None:
    title = stage_range_title(2023, 1, 11)

    assert title == "2023_Tour_de_France,_Stage_1_to_Stage_11"


@pytest.mark.parametrize(("first", "last"), [(0, 11), (11, 11), (12, 5)])
def test_stage_range_title_rejects_invalid_range(first: int, last: int) -> None:
    with pytest.raises(ValueError, match="stage range"):
        stage_range_title(2023, first, last)


def test_stage_range_titles_covers_both_articles() -> None:
    first, second = stage_range_titles(2023)

    assert first == "2023_Tour_de_France,_Stage_1_to_Stage_11"
    assert second == "2023_Tour_de_France,_Stage_12_to_Stage_21"


def test_rest_html_path_preserves_readable_title() -> None:
    path = rest_html_path("2023_Tour_de_France,_Stage_1_to_Stage_11")

    assert path == "/api/rest_v1/page/html/2023_Tour_de_France,_Stage_1_to_Stage_11"


def test_rest_html_path_escapes_unsafe_characters() -> None:
    assert rest_html_path("Paris–Roubaix 2024") == (
        "/api/rest_v1/page/html/Paris%E2%80%93Roubaix%202024"
    )


def test_rest_html_path_rejects_empty_title() -> None:
    with pytest.raises(ValueError, match="cannot be empty"):
        rest_html_path("")
