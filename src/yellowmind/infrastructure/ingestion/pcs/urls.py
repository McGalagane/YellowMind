"""URL helpers for ProCyclingStats paths."""


def tour_stage_path(race_slug: str, year: int, stage_number: int) -> str:
    """Build a PCS path for a Tour stage result page."""
    return f"/race/{race_slug}/{year}/stage-{stage_number}"
