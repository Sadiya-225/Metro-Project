"""
Origin-destination benchmark generation.
"""

from __future__ import annotations

from itertools import combinations

import networkx as nx
import pandas as pd

from pipeline_utils import DATA_DIR


class ODBenchmarkGenerator:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.stations = pd.read_csv(self.data_dir / "station_metadata.csv")
        self.delays = pd.read_csv(self.data_dir / "synthetic_realtime_delays.csv")
        self.route_edges = pd.read_csv(self.data_dir / "processed" / "route_edges.csv")

    def _build_graph(self) -> nx.Graph:
        graph = nx.Graph()
        for station in self.stations.itertuples(index=False):
            graph.add_node(
                station.station_name,
                station_id=station.station_id,
                line=station.line,
            )

        for edge in self.route_edges.itertuples(index=False):
            graph.add_edge(
                edge.from_station_name,
                edge.to_station_name,
                scheduled_minutes=float(edge.scheduled_minutes),
                distance_km=float(edge.distance_km),
                line=edge.line,
            )
        return graph

    def _path_transfer_count(self, graph: nx.Graph, path: list[str]) -> int:
        if len(path) < 2:
            return 0

        previous_line = None
        transfer_count = 0
        for start, end in zip(path[:-1], path[1:]):
            current_lines = set(str(graph[start][end]["line"]).split(","))
            chosen_line = next(iter(current_lines)) if not previous_line else None
            if previous_line:
                overlapping = current_lines.intersection({previous_line})
                if overlapping:
                    chosen_line = next(iter(overlapping))
                else:
                    transfer_count += 1
                    chosen_line = next(iter(current_lines))
            previous_line = chosen_line
        return transfer_count

    def generate_od_pairs(self):
        print("Generating OD pair benchmarks...")
        graph = self._build_graph()
        station_delay_lookup = (
            self.delays.groupby("station_name")["delay_minutes"].mean().to_dict()
        )
        records = []

        station_pairs = list(combinations(sorted(graph.nodes()), 2))
        for source, destination in station_pairs:
            try:
                path = nx.shortest_path(
                    graph,
                    source,
                    destination,
                    weight="scheduled_minutes",
                )
            except nx.NetworkXNoPath:
                continue

            shortest_path_time = sum(
                float(graph[start][end]["scheduled_minutes"])
                for start, end in zip(path[:-1], path[1:])
            )
            scheduled_time = shortest_path_time * 1.08
            path_station_delay = sum(
                float(station_delay_lookup.get(station, 0.0))
                for station in path
            )
            actual_delay_time = scheduled_time + path_station_delay
            inefficiency_ratio = actual_delay_time / max(shortest_path_time, 0.1)

            bottleneck_station = max(
                path,
                key=lambda station: station_delay_lookup.get(station, 0.0),
            )
            transfer_count = self._path_transfer_count(graph, path)

            records.append(
                {
                    "source": source,
                    "destination": destination,
                    "shortest_path_time": round(shortest_path_time, 2),
                    "scheduled_time": round(scheduled_time, 2),
                    "actual_delay_time": round(actual_delay_time, 2),
                    "inefficiency_ratio": round(inefficiency_ratio, 3),
                    "bottleneck_station": bottleneck_station,
                    "transfer_count": transfer_count,
                    "path": " -> ".join(path),
                }
            )

        return pd.DataFrame(records).sort_values(
            ["inefficiency_ratio", "actual_delay_time"],
            ascending=[False, False],
        )

    def save(self, df: pd.DataFrame):
        df.to_csv(self.data_dir / "od_pair_benchmarks.csv", index=False)
        print(f"Saved OD benchmarks to {self.data_dir / 'od_pair_benchmarks.csv'}")

    def run(self):
        benchmarks = self.generate_od_pairs()
        self.save(benchmarks)
        print(f"Generated {len(benchmarks)} OD benchmark rows")
        return benchmarks


if __name__ == "__main__":
    ODBenchmarkGenerator().run()
