"""Tests for composing geocoding with daily weather fetch."""

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

from yellowmind.application.dto import StageFinishRecord
from yellowmind.infrastructure.ingestion.open_meteo import (
    DailyWeatherObservation,
    GeoLocation,
    OpenMeteoClient,
)
from yellowmind.infrastructure.ingestion.weather import StageWeatherCollector


def test_uses_open_meteo_when_geocode_hits() -> None:
    open_meteo = MagicMock(spec=OpenMeteoClient)
    open_meteo.geocode.return_value = GeoLocation(
        name="Bilbao",
        latitude=43.26,
        longitude=-2.92,
        country_code="ES",
        source="open_meteo",
    )
    open_meteo.fetch_daily.return_value = DailyWeatherObservation(
        temperature_c=24.0,
        wind_speed_kmh=10.0,
        precipitation_mm=0.0,
    )
    wikipedia = MagicMock()

    summary = StageWeatherCollector(open_meteo, wikipedia).collect(
        [StageFinishRecord(1, "Bilbao", "Bilbao")],
        {1: date(2023, 7, 1)},
    )

    assert len(summary.records) == 1
    assert summary.records[0].temperature_c == 24.0
    assert summary.unresolved_finishes == ()
    wikipedia.fetch.assert_not_called()


def test_falls_back_to_wikipedia_coordinates() -> None:
    open_meteo = MagicMock(spec=OpenMeteoClient)
    open_meteo.geocode.return_value = None
    open_meteo.fetch_daily.return_value = DailyWeatherObservation(
        temperature_c=12.0,
        wind_speed_kmh=20.0,
        precipitation_mm=5.0,
    )
    wikipedia = MagicMock()
    wikipedia.fetch.return_value = json.dumps({"coordinates": {"lat": 42.725, "lon": 1.691}})

    summary = StageWeatherCollector(open_meteo, wikipedia).collect(
        [StageFinishRecord(15, "Plateau de Beille", "Plateau_de_Beille")],
        {15: date(2015, 7, 17)},
    )

    assert summary.records[0].latitude == 42.725
    assert summary.records[0].location_name == "Plateau de Beille"
    assert summary.unresolved_finishes == ()
    wikipedia.fetch.assert_called()


def test_falls_back_to_wikidata_coordinates() -> None:
    open_meteo = MagicMock(spec=OpenMeteoClient)
    open_meteo.geocode.return_value = None
    open_meteo.fetch_daily.return_value = DailyWeatherObservation(
        temperature_c=8.0,
        wind_speed_kmh=30.0,
        precipitation_mm=1.0,
    )
    wikipedia = MagicMock()

    def fetch(path: str) -> str:
        if path.startswith("/api/rest_v1/page/summary/"):
            return json.dumps({})
        if path.startswith("/w/api.php"):
            return json.dumps(
                {"query": {"pages": {"1": {"pageprops": {"wikibase_item": "Q933261"}}}}}
            )
        if "wikidata.org" in path:
            return json.dumps(
                {
                    "entities": {
                        "Q933261": {
                            "claims": {
                                "P625": [
                                    {
                                        "mainsnak": {
                                            "datavalue": {
                                                "value": {
                                                    "latitude": 45.2365,
                                                    "longitude": 6.29036,
                                                }
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    }
                }
            )
        msg = f"unexpected path {path}"
        raise AssertionError(msg)

    wikipedia.fetch.side_effect = fetch

    summary = StageWeatherCollector(open_meteo, wikipedia).collect(
        [StageFinishRecord(19, "Les Sybelles", "Les_Sybelles")],
        {19: date(2015, 7, 24)},
    )

    assert summary.records[0].latitude == 45.2365
    assert summary.records[0].longitude == 6.29036
    assert summary.unresolved_finishes == ()


def test_tries_slug_name_when_finish_name_misses() -> None:
    open_meteo = MagicMock(spec=OpenMeteoClient)
    open_meteo.geocode.side_effect = [
        None,
        GeoLocation(
            name="La Planche des Belles Filles",
            latitude=47.767,
            longitude=6.774,
            country_code="FR",
            source="open_meteo",
        ),
    ]
    open_meteo.fetch_daily.return_value = DailyWeatherObservation(
        temperature_c=18.0,
        wind_speed_kmh=8.0,
        precipitation_mm=0.0,
    )
    wikipedia = MagicMock()

    summary = StageWeatherCollector(open_meteo, wikipedia).collect(
        [
            StageFinishRecord(
                7,
                "La Super Planche des Belles Filles",
                "La_Planche_des_Belles_Filles",
            )
        ],
        {7: date(2022, 7, 8)},
    )

    assert summary.records[0].location_name == "La Planche des Belles Filles"
    assert open_meteo.geocode.call_count >= 2
    wikipedia.fetch.assert_not_called()


def test_lists_unresolved_finishes(tmp_path: Path) -> None:
    open_meteo = MagicMock(spec=OpenMeteoClient)
    open_meteo.geocode.return_value = None
    wikipedia = MagicMock()
    wikipedia.fetch.return_value = json.dumps({})

    summary = StageWeatherCollector(open_meteo, wikipedia).collect(
        [StageFinishRecord(3, "Nowhere", "Nowhere")],
        {3: date(2023, 7, 3)},
    )

    assert summary.records == ()
    assert summary.unresolved_finishes == ((3, "Nowhere"),)
