"""Parsers turning Wikipedia article HTML into source-shaped records."""

from yellowmind.infrastructure.ingestion.wikipedia.parsing.edition import (
    EditionParseError,
    parse_edition,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing.html import (
    TableNotFoundError,
    data_columns,
    find_infobox,
    find_table_by_headers,
    header_span,
    infobox_value,
    parse_html,
    span_text,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing.results import (
    ResultsParseError,
    StageBoard,
    parse_stage_boards,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing.stages import (
    StageParseError,
    parse_stages,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing.startlist import (
    parse_abandonment,
    parse_startlist,
)
from yellowmind.infrastructure.ingestion.wikipedia.parsing.times import (
    TimeParseError,
    parse_gap_seconds,
    parse_time_cell,
)

__all__ = [
    "EditionParseError",
    "ResultsParseError",
    "StageBoard",
    "StageParseError",
    "TableNotFoundError",
    "TimeParseError",
    "data_columns",
    "find_infobox",
    "find_table_by_headers",
    "header_span",
    "infobox_value",
    "parse_abandonment",
    "parse_edition",
    "parse_gap_seconds",
    "parse_html",
    "parse_stage_boards",
    "parse_stages",
    "parse_startlist",
    "parse_time_cell",
    "span_text",
]
