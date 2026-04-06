"""
GTFS + OSM ingestion pipeline.
Builds a processed station topology directly from GTFS trips/stop times and
matches parent stations to OSM point features when possible.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from pipeline_utils import (
    GTFS_DIR,
    OSM_PATH,
    PROCESSED_DIR,
    build_route_sequences,
    ensure_directories,
    haversine_km,
    load_gtfs_tables,
    load_osm_points,
    normalize_name,
    parent_station_id,
)


class GTFSIngestion:
    def __init__(self):
        self.gtfs_path = GTFS_DIR
        self.osm_path = OSM_PATH
        self.tables = load_gtfs_tables()
        self.osm_points = load_osm_points()
        self.parent_stations = pd.DataFrame()
        self.station_routes = pd.DataFrame()
        self.interchanges = pd.DataFrame()
        self.terminals = pd.DataFrame()
        self.route_sequences = pd.DataFrame()
        self.route_edges = pd.DataFrame()

    def _extract_parent_stations(self) -> pd.DataFrame:
        stops = self.tables["stops"].copy()
        parent_candidates = stops[stops["location_type"] == 1].copy()
        parent_candidates["station_id"] = parent_candidates["stop_id"].astype(str).str.strip()
        parent_candidates["station_name"] = parent_candidates["stop_name"].astype(str).str.strip()
        parent_candidates["name_normalized"] = parent_candidates["station_name"].map(normalize_name)
        parent_candidates["latitude"] = parent_candidates["stop_lat"].astype(float)
        parent_candidates["longitude"] = parent_candidates["stop_lon"].astype(float)
        return parent_candidates[
            [
                "station_id",
                "station_name",
                "name_normalized",
                "latitude",
                "longitude",
                "zone_id",
            ]
        ].drop_duplicates(subset=["station_id"])

    def _best_osm_match(self, station_row: pd.Series) -> Dict[str, Optional[float]]:
        if self.osm_points.empty:
            return {
                "osm_name": None,
                "osm_distance_m": None,
                "osm_match_rule": "no_osm_points",
                "latitude": float(station_row["latitude"]),
                "longitude": float(station_row["longitude"]),
            }

        station_name = station_row["name_normalized"]
        station_lat = float(station_row["latitude"])
        station_lon = float(station_row["longitude"])

        candidates = self.osm_points.copy()
        candidates["distance_m"] = candidates.apply(
            lambda row: haversine_km(station_lat, station_lon, row["latitude"], row["longitude"]) * 1000,
            axis=1,
        )

        exact_name = candidates[candidates["name_normalized"] == station_name]
        if not exact_name.empty:
            best = exact_name.sort_values("distance_m").iloc[0]
            return {
                "osm_name": best["name"],
                "osm_distance_m": round(float(best["distance_m"]), 2),
                "osm_match_rule": "exact_name",
                "latitude": station_lat if float(best["distance_m"]) > 250 else float(best["latitude"]),
                "longitude": station_lon if float(best["distance_m"]) > 250 else float(best["longitude"]),
            }

        token_candidates = candidates[
            candidates["name_normalized"].fillna("").str.contains(station_name, na=False)
            | candidates["name_normalized"].fillna("").apply(lambda value: value in station_name if value else False)
        ]
        if not token_candidates.empty:
            best = token_candidates.sort_values("distance_m").iloc[0]
            return {
                "osm_name": best["name"],
                "osm_distance_m": round(float(best["distance_m"]), 2),
                "osm_match_rule": "token_match",
                "latitude": station_lat if float(best["distance_m"]) > 250 else float(best["latitude"]),
                "longitude": station_lon if float(best["distance_m"]) > 250 else float(best["longitude"]),
            }

        nearby_stationish = candidates[
            (
                candidates["railway"].isin(["station", "halt", "subway"])
                | candidates["public_transport"].isin(["station", "stop_position"])
                | candidates["station"].notna()
            )
            & (candidates["distance_m"] <= 250)
        ]
        if not nearby_stationish.empty:
            best = nearby_stationish.sort_values("distance_m").iloc[0]
            return {
                "osm_name": best["name"],
                "osm_distance_m": round(float(best["distance_m"]), 2),
                "osm_match_rule": "nearest_station_feature",
                "latitude": float(best["latitude"]),
                "longitude": float(best["longitude"]),
            }

        return {
            "osm_name": None,
            "osm_distance_m": None,
            "osm_match_rule": "gtfs_only",
            "latitude": station_lat,
            "longitude": station_lon,
        }

    def _station_route_mapping(self) -> pd.DataFrame:
        stops = self.tables["stops"][["stop_id", "parent_station"]].copy()
        stop_times = self.tables["stop_times"].merge(stops, on="stop_id", how="left")
        stop_times["station_id"] = stop_times.apply(
            lambda row: parent_station_id(row["stop_id"], row.get("parent_station")),
            axis=1,
        )

        merged = stop_times.merge(
            self.tables["trips"][["trip_id", "route_id"]],
            on="trip_id",
            how="left",
        ).merge(
            self.tables["routes"][["route_id", "route_short_name"]],
            on="route_id",
            how="left",
        )

        route_map = (
            merged.groupby("station_id")["route_short_name"]
            .apply(lambda values: ",".join(sorted({value for value in values if isinstance(value, str)})))
            .reset_index(name="routes")
        )
        route_map["route_count"] = route_map["routes"].apply(lambda value: len(value.split(",")) if value else 0)
        return route_map

    def _interchange_detection(self) -> pd.DataFrame:
        platforms = self.tables["stops"][self.tables["stops"]["location_type"] == 0].copy()
        platforms["station_id"] = platforms.apply(
            lambda row: parent_station_id(row["stop_id"], row.get("parent_station")),
            axis=1,
        )
        zone_counts = (
            platforms.groupby("station_id")["zone_id"]
            .nunique(dropna=True)
            .reset_index(name="zone_count")
        )
        merged = self.station_routes.merge(zone_counts, on="station_id", how="left").fillna({"zone_count": 0})
        merged["is_interchange"] = (merged["route_count"] > 1) | (merged["zone_count"] > 1)
        return merged[merged["is_interchange"]][["station_id"]].drop_duplicates()

    def _terminal_detection(self) -> pd.DataFrame:
        terminal_ids = set()
        for _, group in self.route_sequences.groupby(["route_short_name", "direction_id"]):
            ordered = group.sort_values("stop_sequence")
            if not ordered.empty:
                terminal_ids.add(ordered.iloc[0]["station_id"])
                terminal_ids.add(ordered.iloc[-1]["station_id"])
        return pd.DataFrame({"station_id": sorted(terminal_ids)})

    def _finalize_route_edges(self) -> pd.DataFrame:
        station_lookup = self.parent_stations.set_index("station_id")
        edges = self.route_edges.copy()
        distance_values: List[float] = []
        line_groups: List[str] = []
        for edge in edges.itertuples(index=False):
            from_station = station_lookup.loc[edge.from_station_id]
            to_station = station_lookup.loc[edge.to_station_id]
            distance_km = haversine_km(
                float(from_station["latitude"]),
                float(from_station["longitude"]),
                float(to_station["latitude"]),
                float(to_station["longitude"]),
            )
            distance_values.append(round(distance_km, 4))
            line_groups.append(edge.route_short_name)

        edges["distance_km"] = distance_values
        edges["line"] = line_groups
        edges["scheduled_minutes"] = edges["scheduled_minutes"].fillna(
            edges["distance_km"].apply(lambda distance: max((distance / 34) * 60 + 0.8, 1.0))
        )

        aggregated = (
            edges.groupby(
                [
                    "from_station_id",
                    "from_station_name",
                    "to_station_id",
                    "to_station_name",
                ],
                as_index=False,
            )
            .agg(
                line=("line", lambda values: ",".join(sorted(set(values)))),
                distance_km=("distance_km", "mean"),
                scheduled_minutes=("scheduled_minutes", "median"),
            )
        )
        return aggregated

    def save_processed_data(self):
        ensure_directories()
        self.parent_stations.to_csv(PROCESSED_DIR / "parent_stations.csv", index=False)
        self.station_routes.to_csv(PROCESSED_DIR / "station_routes.csv", index=False)
        self.interchanges.to_csv(PROCESSED_DIR / "interchanges.csv", index=False)
        self.terminals.to_csv(PROCESSED_DIR / "terminals.csv", index=False)
        self.route_sequences.to_csv(PROCESSED_DIR / "route_sequences.csv", index=False)
        self.route_edges.to_csv(PROCESSED_DIR / "route_edges.csv", index=False)
        print(f"Saved processed outputs to {PROCESSED_DIR}")

    def run(self) -> Dict[str, pd.DataFrame]:
        print("=" * 60)
        print("HYDERABAD METRO - GTFS INGESTION PIPELINE")
        print("=" * 60)
        print(f"Reading GTFS from {self.gtfs_path}")
        print(f"Reading OSM from {self.osm_path}")

        self.parent_stations = self._extract_parent_stations()
        self.station_routes = self._station_route_mapping()
        self.route_sequences, self.route_edges = build_route_sequences(
            self.tables["stops"],
            self.tables["routes"],
            self.tables["trips"],
            self.tables["stop_times"],
        )

        osm_matches = self.parent_stations.apply(self._best_osm_match, axis=1)
        self.parent_stations["osm_name"] = [match["osm_name"] for match in osm_matches]
        self.parent_stations["osm_distance_m"] = [match["osm_distance_m"] for match in osm_matches]
        self.parent_stations["osm_match_rule"] = [match["osm_match_rule"] for match in osm_matches]
        self.parent_stations["latitude"] = [match["latitude"] for match in osm_matches]
        self.parent_stations["longitude"] = [match["longitude"] for match in osm_matches]

        self.parent_stations = self.parent_stations.merge(self.station_routes, on="station_id", how="left")
        self.parent_stations["routes"] = self.parent_stations["routes"].fillna("")
        self.parent_stations["route_count"] = self.parent_stations["route_count"].fillna(0).astype(int)

        self.interchanges = self._interchange_detection()
        self.terminals = self._terminal_detection()
        self.route_edges = self._finalize_route_edges()

        self.save_processed_data()

        print(f"Parent stations: {len(self.parent_stations)}")
        print(f"Interchanges: {len(self.interchanges)}")
        print(f"Terminals: {len(self.terminals)}")
        print(f"Route edges: {len(self.route_edges)}")

        return {
            "parent_stations": self.parent_stations,
            "station_routes": self.station_routes,
            "interchanges": self.interchanges,
            "terminals": self.terminals,
            "route_sequences": self.route_sequences,
            "route_edges": self.route_edges,
        }


if __name__ == "__main__":
    GTFSIngestion().run()
