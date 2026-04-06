"""
Metro route optimization and analytics engine.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import networkx as nx
import numpy as np
import pandas as pd


class MetroRouteEngine:
    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.graph = nx.Graph()
        self.stations = None
        self.delays = None
        self.od_pairs = None
        self.transfer_penalties = None
        self.route_edges = None
        self.peak_labels = None
        self.station_delay_profiles = {}

    def load_data(self):
        print("Loading backend route data...")
        self.stations = pd.read_csv(self.data_dir / "station_metadata.csv")
        self.delays = pd.read_csv(self.data_dir / "synthetic_realtime_delays.csv")
        self.od_pairs = pd.read_csv(self.data_dir / "od_pair_benchmarks.csv")
        self.transfer_penalties = pd.read_csv(self.data_dir / "transfer_penalty_matrix.csv")
        self.route_edges = pd.read_csv(self.data_dir / "processed" / "route_edges.csv")
        self.peak_labels = pd.read_csv(self.data_dir / "peak_hour_labels.csv")
        self._build_station_delay_profiles()
        print(f"Loaded {len(self.stations)} stations and {len(self.route_edges)} route edges")

    def _build_station_delay_profiles(self):
        grouped = (
            self.delays.groupby(["station_name", "hour", "weekday"])["delay_minutes"]
            .mean()
            .reset_index()
        )
        self.station_delay_profiles = {
            (row.station_name, int(row.hour), bool(row.weekday)): float(row.delay_minutes)
            for row in grouped.itertuples(index=False)
        }

    def build_graph(self):
        self.load_data()
        self.graph = nx.Graph()

        for station in self.stations.itertuples(index=False):
            self.graph.add_node(
                station.station_name,
                station_id=station.station_id,
                line=station.line,
                lat=float(station.latitude),
                lon=float(station.longitude),
                importance=float(station.importance_score),
                is_interchange=bool(station.is_interchange),
                is_terminal=bool(station.is_terminal),
                zone=station.zone,
            )

        for edge in self.route_edges.itertuples(index=False):
            self.graph.add_edge(
                edge.from_station_name,
                edge.to_station_name,
                distance_km=float(edge.distance_km),
                scheduled_minutes=float(edge.scheduled_minutes),
                line=edge.line,
                is_transfer=False,
            )

        if self.transfer_penalties is not None and not self.transfer_penalties.empty:
            walking_links = self.transfer_penalties[
                self.transfer_penalties["transfer_type"] == "walking_link"
            ]
            for transfer in walking_links.itertuples(index=False):
                if transfer.from_station == transfer.to_station:
                    continue
                if not self.graph.has_node(transfer.from_station) or not self.graph.has_node(transfer.to_station):
                    continue
                transfer_cost = float(transfer.effective_transfer_cost)
                if transfer_cost > 5.5:
                    continue
                if self.graph.has_edge(transfer.from_station, transfer.to_station):
                    continue
                self.graph.add_edge(
                    transfer.from_station,
                    transfer.to_station,
                    distance_km=0.0,
                    scheduled_minutes=transfer_cost,
                    line="TRANSFER",
                    is_transfer=True,
                )

        print(
            f"Graph built with {self.graph.number_of_nodes()} nodes and "
            f"{self.graph.number_of_edges()} edges"
        )

    def _haversine(self, lat1, lon1, lat2, lon2):
        earth_radius_km = 6371
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arcsin(np.sqrt(a))
        return earth_radius_km * c

    def _estimate_station_delay(self, station_name: str, hour: int, weekday: bool) -> float:
        profile = self.station_delay_profiles.get((station_name, hour, weekday))
        if profile is not None:
            return float(profile)
        fallback = self.delays[self.delays["station_name"] == station_name]["delay_minutes"].mean()
        if pd.isna(fallback):
            return 0.5
        return float(fallback)

    def _current_context(self) -> Tuple[int, bool]:
        now = datetime.now()
        return now.hour, now.weekday() < 5

    def _edge_delayed_weight(self, start: str, end: str, hour: int, weekday: bool) -> float:
        edge = self.graph[start][end]
        destination_delay = self._estimate_station_delay(end, hour, weekday)
        origin_delay = self._estimate_station_delay(start, hour, weekday)
        delay_penalty = (origin_delay + destination_delay) / 2
        if edge.get("is_transfer"):
            delay_penalty += 1.0
        return float(edge["scheduled_minutes"] + delay_penalty)

    def _path_distance(self, path: List[str]) -> float:
        return float(
            sum(self.graph[start][end]["distance_km"] for start, end in zip(path[:-1], path[1:]))
        )

    def _path_lines(self, path: List[str]) -> List[str]:
        lines = []
        previous_line = None
        for start, end in zip(path[:-1], path[1:]):
            available = [line.strip() for line in str(self.graph[start][end]["line"]).split(",") if line.strip()]
            line = available[0] if available else "UNKNOWN"
            if previous_line and previous_line in available:
                line = previous_line
            lines.append(line)
            previous_line = line
        return lines

    def _path_transfer_segments(self, path: List[str]) -> List[Dict]:
        lines = self._path_lines(path)
        transfer_segments = []
        for index, (start, end) in enumerate(zip(path[:-1], path[1:])):
            current_line = lines[index]
            previous_line = lines[index - 1] if index > 0 else current_line
            edge = self.graph[start][end]
            if edge.get("is_transfer") or current_line != previous_line:
                transfer_segments.append(
                    {
                        "from_station": start,
                        "to_station": end,
                        "line": current_line,
                        "is_walking_transfer": bool(edge.get("is_transfer")),
                    }
                )
        return transfer_segments

    def _route_divergence_score(self, shortest_path: List[str], actual_path: List[str]) -> float:
        shortest_set = set(shortest_path)
        actual_set = set(actual_path)
        union = shortest_set.union(actual_set)
        if not union:
            return 0.0
        overlap = shortest_set.intersection(actual_set)
        return round(1 - (len(overlap) / len(union)), 3)

    def _bottlenecks_for_path(self, path: List[str], hour: int, weekday: bool) -> List[str]:
        scored = []
        for station in path:
            node = self.graph.nodes[station]
            score = self._estimate_station_delay(station, hour, weekday)
            if node.get("is_interchange"):
                score += 0.75
            if node.get("importance", 0) >= 70:
                score += 0.4
            scored.append((station, score))

        if not scored:
            return []

        threshold = np.percentile([score for _, score in scored], 75)
        bottlenecks = [station for station, score in scored if score >= threshold and score > 1.0]
        return bottlenecks

    def _path_time(self, path: List[str], delayed: bool = False, hour: Optional[int] = None, weekday: Optional[bool] = None) -> float:
        if len(path) < 2:
            return 0.0

        if delayed:
            assert hour is not None and weekday is not None
            return float(
                sum(
                    self._edge_delayed_weight(start, end, hour, weekday)
                    for start, end in zip(path[:-1], path[1:])
                )
            )

        return float(
            sum(
                self.graph[start][end]["scheduled_minutes"]
                for start, end in zip(path[:-1], path[1:])
            )
        )

    def _shortest_path_by_algorithm(self, source: str, destination: str, algorithm: str, weight_fn):
        if algorithm == "dijkstra":
            path = nx.shortest_path(self.graph, source, destination, weight=weight_fn)
            cost = nx.shortest_path_length(self.graph, source, destination, weight=weight_fn)
            return path, float(cost)

        if algorithm == "astar":
            def heuristic(node: str, target: str):
                node_data = self.graph.nodes[node]
                target_data = self.graph.nodes[target]
                km = self._haversine(
                    node_data["lat"],
                    node_data["lon"],
                    target_data["lat"],
                    target_data["lon"],
                )
                return float((km / 34) * 60)

            path = nx.astar_path(self.graph, source, destination, heuristic=heuristic, weight=weight_fn)
            cost = nx.astar_path_length(self.graph, source, destination, heuristic=heuristic, weight=weight_fn)
            return path, float(cost)

        if algorithm == "yen":
            paths = self.find_k_shortest_paths(source, destination, k=1, weight=weight_fn)
            return paths[0] if paths else ([], float("inf"))

        raise ValueError(f"Unknown algorithm: {algorithm}")

    def find_shortest_path(self, source: str, destination: str, algorithm: str = "dijkstra"):
        return self._shortest_path_by_algorithm(source, destination, algorithm, "scheduled_minutes")

    def find_actual_path(self, source: str, destination: str, algorithm: str = "dijkstra", hour: Optional[int] = None, weekday: Optional[bool] = None):
        hour = self._current_context()[0] if hour is None else hour
        weekday = self._current_context()[1] if weekday is None else weekday

        def delayed_weight(start: str, end: str, edge_data: Dict):
            return self._edge_delayed_weight(start, end, hour, weekday)

        return self._shortest_path_by_algorithm(source, destination, algorithm, delayed_weight)

    def find_k_shortest_paths(self, source: str, destination: str, k: int = 3, weight="scheduled_minutes"):
        paths = list(nx.shortest_simple_paths(self.graph, source, destination, weight=weight))
        results = []
        for path in paths[:k]:
            if callable(weight):
                distance = sum(
                    weight(start, end, self.graph[start][end])
                    for start, end in zip(path[:-1], path[1:])
                )
            else:
                distance = sum(self.graph[start][end][weight] for start, end in zip(path[:-1], path[1:]))
            results.append((path, float(distance)))
        return results

    def calculate_travel_time(self, path: List[str], distance: float | None = None):
        if not path:
            return 0.0
        return self._path_time(path, delayed=False)

    def calculate_actual_time_with_delays(self, path: List[str], distance: float | None = None, hour: Optional[int] = None, weekday: Optional[bool] = None):
        if not path:
            return 0.0, 0.0
        hour, weekday = self._current_context() if hour is None or weekday is None else (hour, weekday)
        estimated_time = self._path_time(path, delayed=False)
        actual_time = self._path_time(path, delayed=True, hour=hour, weekday=weekday)
        return float(actual_time), float(actual_time - estimated_time)

    def identify_bottlenecks(self, path: List[str]) -> List[str]:
        hour, weekday = self._current_context()
        return self._bottlenecks_for_path(path, hour, weekday)

    def get_route_analysis(self, source: str, destination: str, algorithm: str = "dijkstra", k_paths: int = 3):
        hour, weekday = self._current_context()
        shortest_path, _ = self.find_shortest_path(source, destination, algorithm)
        actual_path, _ = self.find_actual_path(source, destination, algorithm, hour=hour, weekday=weekday)

        shortest_distance = self._path_distance(shortest_path)
        actual_distance = self._path_distance(actual_path)
        estimated_time = self._path_time(shortest_path, delayed=False)
        actual_time = self._path_time(actual_path, delayed=True, hour=hour, weekday=weekday)
        delay_minutes = actual_time - estimated_time

        bottleneck_stations = self._bottlenecks_for_path(actual_path, hour, weekday)
        transfer_segments = self._path_transfer_segments(actual_path)
        alternative_routes = []
        for path, cost in self.find_k_shortest_paths(source, destination, k=k_paths, weight="scheduled_minutes")[1:]:
            alternative_routes.append(
                {
                    "path": path,
                    "distance": round(self._path_distance(path), 2),
                    "time": round(self._path_time(path, delayed=False), 2),
                    "transfer_count": len(self._path_transfer_segments(path)),
                }
            )

        station_congestion = [
            {
                "station_name": station,
                "congestion_score": round(
                    float(
                        self.delays[
                            (self.delays["station_name"] == station)
                            & (self.delays["hour"] == hour)
                            & (self.delays["weekday"] == weekday)
                        ]["congestion_score"].mean()
                    )
                    if not self.delays[
                        (self.delays["station_name"] == station)
                        & (self.delays["hour"] == hour)
                        & (self.delays["weekday"] == weekday)
                    ].empty
                    else float(self.delays[self.delays["station_name"] == station]["congestion_score"].mean()),
                    2,
                ),
            }
            for station in actual_path
        ]

        return {
            "source": source,
            "destination": destination,
            "shortest_path": shortest_path,
            "actual_path": actual_path,
            "distance": round(shortest_distance, 2),
            "actual_distance": round(actual_distance, 2),
            "estimated_time": round(estimated_time, 2),
            "actual_time": round(actual_time, 2),
            "delay": round(delay_minutes, 2),
            "eta_deviation": round(delay_minutes, 2),
            "route_divergence_score": self._route_divergence_score(shortest_path, actual_path),
            "bottleneck_stations": bottleneck_stations,
            "transfer_segments": transfer_segments,
            "transfer_count": len(transfer_segments),
            "station_congestion": station_congestion,
            "alternative_routes": alternative_routes,
        }

    def get_top_bottlenecks(self, limit: int = 10) -> List[Dict]:
        grouped = (
            self.delays.groupby("station_name")
            .agg(
                avg_delay=("delay_minutes", "mean"),
                congestion_score=("congestion_score", "mean"),
            )
            .reset_index()
        )
        metadata = self.stations[["station_name", "importance_score", "is_interchange", "zone", "line"]]
        merged = grouped.merge(metadata, on="station_name", how="left")
        merged["risk_score"] = (
            merged["avg_delay"] * 0.6
            + merged["congestion_score"] * 0.03
            + merged["importance_score"] * 0.02
        )
        return (
            merged.sort_values("risk_score", ascending=False)
            .head(limit)
            .assign(
                avg_delay=lambda frame: frame["avg_delay"].round(2),
                congestion_score=lambda frame: frame["congestion_score"].round(2),
                importance_score=lambda frame: frame["importance_score"].round(2),
                risk_score=lambda frame: frame["risk_score"].round(2),
            )
            .to_dict(orient="records")
        )

    def get_dashboard_analytics(self) -> Dict:
        line_delay_comparison = (
            self.delays.merge(self.stations[["station_name", "line", "zone", "is_interchange"]], on="station_name", how="left")
            .assign(line=lambda frame: frame["line"].str.split(","))
            .explode("line")
            .groupby("line")["delay_minutes"]
            .mean()
            .round(2)
            .reset_index(name="avg_delay")
            .to_dict(orient="records")
        )

        zone_congestion = (
            self.delays.merge(self.stations[["station_name", "zone"]], on="station_name", how="left")
            .groupby("zone")["congestion_score"]
            .mean()
            .round(2)
            .reset_index(name="avg_congestion")
            .to_dict(orient="records")
        )

        hourly_delay_profile = (
            self.delays.groupby("hour")
            .agg(
                avg_delay=("delay_minutes", "mean"),
                avg_congestion=("congestion_score", "mean"),
            )
            .round(2)
            .reset_index()
            .to_dict(orient="records")
        )

        interchange_risk = (
            pd.DataFrame(self.get_top_bottlenecks(limit=20))
            .query("is_interchange == True")
            .head(10)
            .to_dict(orient="records")
        )

        return {
            "line_delay_comparison": line_delay_comparison,
            "zone_congestion": zone_congestion,
            "hourly_delay_profile": hourly_delay_profile,
            "interchange_risk": interchange_risk,
        }
