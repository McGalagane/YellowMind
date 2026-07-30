"""Build weather observations from stage finishes and dates."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from typing import cast
from urllib.parse import quote

from yellowmind.application.dto import StageFinishRecord, WeatherRecord
from yellowmind.infrastructure.ingestion.http import HttpFetchError
from yellowmind.infrastructure.ingestion.open_meteo import (
    GeoLocation,
    OpenMeteoClient,
    OpenMeteoError,
)
from yellowmind.infrastructure.ingestion.wikipedia.client import WikipediaClient


@dataclass(frozen=True, slots=True)
class WeatherCollectSummary:
    """Outcome of resolving finishes to daily weather observations."""

    records: tuple[WeatherRecord, ...]
    #: Stage numbers whose finish could not be geocoded.
    unresolved_finishes: tuple[tuple[int, str], ...]
    #: Stage numbers where archive weather was missing after a successful geocode.
    missing_observations: tuple[int, ...]


class StageWeatherCollector:
    """Geocode each finish, then pull Open-Meteo daily weather for the stage date.

    Resolution order:

    1. Open-Meteo geocoding on the finish name and slug-derived variants
    2. Wikipedia page-summary coordinates
    3. Wikidata ``P625`` via the article's Wikibase item

    Failures are listed rather than skipped silently so a backfill can be audited.
    """

    def __init__(
        self,
        open_meteo: OpenMeteoClient,
        wikipedia: WikipediaClient,
    ) -> None:
        self._open_meteo = open_meteo
        self._wikipedia = wikipedia
        self._geo_cache: dict[tuple[str, str], GeoLocation | None] = {}

    def collect(
        self,
        finishes: Sequence[StageFinishRecord],
        stage_dates: Mapping[int, date],
    ) -> WeatherCollectSummary:
        """Resolve ``finishes`` against ``stage_dates`` into weather records."""
        records: list[WeatherRecord] = []
        unresolved: list[tuple[int, str]] = []
        missing: list[int] = []

        for finish in finishes:
            day = stage_dates.get(finish.stage_number)
            if day is None:
                unresolved.append((finish.stage_number, finish.finish_name))
                continue

            location = self._resolve_location(finish)
            if location is None:
                unresolved.append((finish.stage_number, finish.finish_name))
                continue

            try:
                observation = self._open_meteo.fetch_daily(
                    location.latitude, location.longitude, day
                )
            except OpenMeteoError:
                missing.append(finish.stage_number)
                continue

            records.append(
                WeatherRecord(
                    stage_number=finish.stage_number,
                    location_name=location.name,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    temperature_c=observation.temperature_c,
                    wind_speed_kmh=observation.wind_speed_kmh,
                    precipitation_mm=observation.precipitation_mm,
                )
            )

        return WeatherCollectSummary(
            records=tuple(records),
            unresolved_finishes=tuple(unresolved),
            missing_observations=tuple(missing),
        )

    def _resolve_location(self, finish: StageFinishRecord) -> GeoLocation | None:
        key = (finish.finish_name, finish.finish_slug)
        if key not in self._geo_cache:
            self._geo_cache[key] = self._geocode(finish)
        return self._geo_cache[key]

    def _geocode(self, finish: StageFinishRecord) -> GeoLocation | None:
        for name in _geocode_candidates(finish):
            location = self._open_meteo.geocode(name)
            if location is not None:
                return location

        title = finish.finish_slug or finish.finish_name.replace(" ", "_")
        coords = self._wikipedia_coordinates(title)
        source = "wikipedia"
        if coords is None:
            coords = self._wikidata_coordinates(title)
            source = "wikidata"
        if coords is None:
            return None
        latitude, longitude = coords
        return GeoLocation(
            name=finish.finish_name,
            latitude=latitude,
            longitude=longitude,
            country_code="",
            source=source,
        )

    def _wikipedia_coordinates(self, title: str) -> tuple[float, float] | None:
        """Read lat/lon from the page summary API, if the article has them."""
        path = f"/api/rest_v1/page/summary/{quote(title, safe='')}"
        try:
            raw: object = json.loads(self._wikipedia.fetch(path))
        except (HttpFetchError, json.JSONDecodeError, ValueError):
            return None
        payload = _object_map(raw)
        if payload is None:
            return None
        return _lat_lon(_object_map(payload.get("coordinates")))

    def _wikidata_coordinates(self, title: str) -> tuple[float, float] | None:
        """Read lat/lon from Wikidata ``P625`` via the article's Wikibase item."""
        query = (
            "/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item"
            f"&titles={quote(title, safe='')}&format=json"
        )
        try:
            raw: object = json.loads(self._wikipedia.fetch(query))
        except (HttpFetchError, json.JSONDecodeError, ValueError):
            return None

        qid = _wikibase_item(raw)
        if qid is None:
            return None

        entity_url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
        try:
            entity_raw: object = json.loads(self._wikipedia.fetch(entity_url))
        except (HttpFetchError, json.JSONDecodeError, ValueError):
            return None
        return _wikidata_p625(entity_raw, qid)


def _geocode_candidates(finish: StageFinishRecord) -> tuple[str, ...]:
    """Names to try against Open-Meteo, most specific first."""
    names: list[str] = [finish.finish_name]
    if finish.finish_slug:
        slug_name = finish.finish_slug.replace("_", " ")
        if slug_name not in names:
            names.append(slug_name)
    # Marketing prefixes like `La Super Planche…` hide the place Open-Meteo knows.
    if finish.finish_name.startswith("La Super "):
        stripped = finish.finish_name.removeprefix("La Super ")
        if stripped not in names:
            names.append(stripped)
    return tuple(names)


def _wikibase_item(payload: object) -> str | None:
    root = _object_map(payload)
    if root is None:
        return None
    query = _object_map(root.get("query"))
    if query is None:
        return None
    pages = query.get("pages")
    if not isinstance(pages, dict):
        return None
    for page in cast(dict[object, object], pages).values():
        mapped = _object_map(page)
        if mapped is None:
            continue
        props = _object_map(mapped.get("pageprops"))
        if props is None:
            continue
        item = props.get("wikibase_item")
        if isinstance(item, str) and item:
            return item
    return None


def _wikidata_p625(payload: object, qid: str) -> tuple[float, float] | None:
    root = _object_map(payload)
    if root is None:
        return None
    entities = _object_map(root.get("entities"))
    if entities is None:
        return None
    entity = _object_map(entities.get(qid))
    if entity is None:
        return None
    claims = _object_map(entity.get("claims"))
    if claims is None:
        return None
    p625 = claims.get("P625")
    if not isinstance(p625, list) or not p625:
        return None
    claim = _object_map(cast(list[object], p625)[0])
    if claim is None:
        return None
    mainsnak = _object_map(claim.get("mainsnak"))
    if mainsnak is None:
        return None
    datavalue = _object_map(mainsnak.get("datavalue"))
    if datavalue is None:
        return None
    value = _object_map(datavalue.get("value"))
    if value is None:
        return None
    return _lat_lon(value, lat_key="latitude", lon_key="longitude")


def _lat_lon(
    coordinates: dict[str, object] | None,
    *,
    lat_key: str = "lat",
    lon_key: str = "lon",
) -> tuple[float, float] | None:
    if coordinates is None:
        return None
    lat = coordinates.get(lat_key)
    lon = coordinates.get(lon_key)
    if isinstance(lat, bool) or isinstance(lon, bool):
        return None
    if not isinstance(lat, int | float) or not isinstance(lon, int | float):
        return None
    return float(lat), float(lon)


def _object_map(value: object) -> dict[str, object] | None:
    """Narrow a JSON value to a string-keyed object map."""
    if not isinstance(value, dict):
        return None
    typed = cast(dict[object, object], value)
    return {str(key): item for key, item in typed.items()}
