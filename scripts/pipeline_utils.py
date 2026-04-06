"""
Shared helpers for the metro data engineering pipeline.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
PUBLIC_DIR = PROJECT_DIR / "public"
GTFS_DIR = PUBLIC_DIR / "gtfs_hmrl"
OSM_PATH = PUBLIC_DIR / "export.geojson"
DATA_DIR = PROJECT_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"

NAME_ALIASES = {
    "hyderabad deccan nampally": "nampally",
    "parade grounds": "parade ground",
    "mahatma gandhi bus station": "mahatma gandhi bus station",
    "jbs parade ground": "jbs parade ground",
    "sr nagar": "s r nagar",
    "s r nagar": "s r nagar",
    "road no 5 jubilee hills": "road no 5 jubilee hills",
    "lb nagar": "l b nagar",
    "l b nagar": "l b nagar",
}


def normalize_name(name: str) -> str:
    if not isinstance(name, str):
        return ""
    cleaned = name.lower()
    cleaned = cleaned.replace("&", " and ")
    cleaned = re.sub(r"\(.*?\)", " ", cleaned)
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return NAME_ALIASES.get(cleaned, cleaned)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    return earth_radius_km * c


def gtfs_time_to_minutes(value: str) -> Optional[float]:
    if not isinstance(value, str) or value.count(":") != 2:
        return None
    hours, minutes, seconds = value.split(":")
    return int(hours) * 60 + int(minutes) + (int(seconds) / 60)


def parent_station_id(stop_id: str, parent_station: Optional[str]) -> str:
    if isinstance(parent_station, str) and parent_station.strip():
        return parent_station.strip()
    return re.sub(r"\d+$", "", str(stop_id).strip())


def load_gtfs_tables() -> Dict[str, pd.DataFrame]:
    tables = {}
    for name in ["stops", "routes", "trips", "stop_times", "transfers"]:
        path = GTFS_DIR / f"{name}.txt"
        if path.exists():
            tables[name] = pd.read_csv(path)
        else:
            tables[name] = pd.DataFrame()
    return tables


def load_osm_geojson() -> Dict:
    with open(OSM_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def _feature_name(properties: Dict) -> str:
    return (
        properties.get("name:en")
        or properties.get("official_name")
        or properties.get("name")
        or ""
    )


def load_osm_points() -> pd.DataFrame:
    data = load_osm_geojson()
    records: List[Dict] = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates")

        if geometry_type == "Point" and isinstance(coordinates, list) and len(coordinates) >= 2:
            lon, lat = coordinates[0], coordinates[1]
        else:
            continue

        records.append(
            {
                "name": _feature_name(properties),
                "name_normalized": normalize_name(_feature_name(properties)),
                "latitude": float(lat),
                "longitude": float(lon),
                "railway": properties.get("railway"),
                "public_transport": properties.get("public_transport"),
                "station": properties.get("station"),
                "amenity": properties.get("amenity"),
                "shop": properties.get("shop"),
                "office": properties.get("office"),
                "building": properties.get("building"),
                "landuse": properties.get("landuse"),
                "tourism": properties.get("tourism"),
                "leisure": properties.get("leisure"),
                "properties": properties,
            }
        )
    return pd.DataFrame(records)


def choose_representative_trips(
    stop_times: pd.DataFrame,
    trips: pd.DataFrame,
    routes: pd.DataFrame,
) -> pd.DataFrame:
    merged = stop_times.merge(
        trips[["trip_id", "route_id", "direction_id"]],
        on="trip_id",
        how="left",
    ).merge(
        routes[["route_id", "route_short_name"]],
        on="route_id",
        how="left",
    )
    merged["parent_id"] = merged.apply(
        lambda row: parent_station_id(row["stop_id"], row.get("parent_station")),
        axis=1,
    )
    lengths = (
        merged.groupby(["route_short_name", "direction_id", "trip_id"])
        .size()
        .reset_index(name="stop_count")
        .sort_values(
            ["route_short_name", "direction_id", "stop_count", "trip_id"],
            ascending=[True, True, False, True],
        )
    )
    return lengths.groupby(["route_short_name", "direction_id"]).head(1)


def build_route_sequences(
    stops: pd.DataFrame,
    routes: pd.DataFrame,
    trips: pd.DataFrame,
    stop_times: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    stops_lookup = stops[["stop_id", "stop_name", "location_type", "parent_station"]].copy()
    merged = stop_times.merge(stops_lookup, on="stop_id", how="left")
    merged["parent_id"] = merged.apply(
        lambda row: parent_station_id(row["stop_id"], row.get("parent_station")),
        axis=1,
    )
    merged = merged.merge(
        trips[["trip_id", "route_id", "direction_id"]],
        on="trip_id",
        how="left",
    ).merge(
        routes[["route_id", "route_short_name"]],
        on="route_id",
        how="left",
    )

    representative = choose_representative_trips(stop_times, trips, routes)
    route_sequences: List[Dict] = []
    route_edges: List[Dict] = []

    for row in representative.itertuples(index=False):
        trip_rows = merged[merged["trip_id"] == row.trip_id].sort_values("stop_sequence")
        trip_rows = trip_rows.drop_duplicates(subset=["parent_id"], keep="first")

        previous = None
        for stop in trip_rows.itertuples(index=False):
            route_sequences.append(
                {
                    "route_short_name": row.route_short_name,
                    "direction_id": int(row.direction_id),
                    "trip_id": row.trip_id,
                    "stop_sequence": int(stop.stop_sequence),
                    "station_id": stop.parent_id,
                    "station_name": stop.stop_name,
                    "arrival_time": stop.arrival_time,
                    "departure_time": stop.departure_time,
                }
            )

            if previous is not None:
                previous_departure = gtfs_time_to_minutes(previous.departure_time)
                current_arrival = gtfs_time_to_minutes(stop.arrival_time)
                scheduled_minutes = None
                if previous_departure is not None and current_arrival is not None:
                    scheduled_minutes = max(current_arrival - previous_departure, 0.5)

                route_edges.append(
                    {
                        "route_short_name": row.route_short_name,
                        "direction_id": int(row.direction_id),
                        "from_station_id": previous.parent_id,
                        "from_station_name": previous.stop_name,
                        "to_station_id": stop.parent_id,
                        "to_station_name": stop.stop_name,
                        "scheduled_minutes": scheduled_minutes,
                    }
                )
            previous = stop

    return pd.DataFrame(route_sequences), pd.DataFrame(route_edges)


def ensure_directories():
    DATA_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

