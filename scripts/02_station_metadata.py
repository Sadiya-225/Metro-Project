"""
Station metadata and importance scoring generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

import networkx as nx
import pandas as pd

from pipeline_utils import DATA_DIR, PROCESSED_DIR, haversine_km, load_osm_points


class StationMetadataGenerator:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.processed_dir = PROCESSED_DIR
        self.parent_stations = pd.read_csv(self.processed_dir / "parent_stations.csv")
        self.interchanges = pd.read_csv(self.processed_dir / "interchanges.csv")
        self.terminals = pd.read_csv(self.processed_dir / "terminals.csv")
        self.route_edges = pd.read_csv(self.processed_dir / "route_edges.csv")
        self.osm_points = load_osm_points()

    def _poi_counts(self, station_row: pd.Series) -> Dict[str, int]:
        if self.osm_points.empty:
            return {
                "it_count": 0,
                "commercial_count": 0,
                "education_count": 0,
                "activity_count": 0,
            }

        def is_it_hub(row: pd.Series) -> bool:
            text = " ".join(
                str(row.get(column, "")).lower()
                for column in ["name", "office", "landuse", "building"]
            )
            return any(keyword in text for keyword in ["tech", "cyber", "hitec", "it", "software", "mindspace"])

        def is_commercial(row: pd.Series) -> bool:
            return any(
                str(row.get(column, "")).lower() not in ["", "nan", "none"]
                for column in ["shop", "office", "amenity"]
            ) or str(row.get("landuse", "")).lower() in {"commercial", "retail"}

        def is_education(row: pd.Series) -> bool:
            text = " ".join(
                str(row.get(column, "")).lower()
                for column in ["name", "amenity", "building"]
            )
            return any(keyword in text for keyword in ["college", "university", "school", "institute", "campus"])

        nearby = self.osm_points.copy()
        nearby["distance_km"] = nearby.apply(
            lambda row: haversine_km(
                float(station_row["latitude"]),
                float(station_row["longitude"]),
                float(row["latitude"]),
                float(row["longitude"]),
            ),
            axis=1,
        )
        nearby = nearby[nearby["distance_km"] <= 0.8]

        return {
            "it_count": int(nearby.apply(is_it_hub, axis=1).sum()),
            "commercial_count": int(nearby.apply(is_commercial, axis=1).sum()),
            "education_count": int(nearby.apply(is_education, axis=1).sum()),
            "activity_count": int(len(nearby)),
        }

    def _build_graph(self) -> nx.Graph:
        graph = nx.Graph()
        for station in self.parent_stations.itertuples(index=False):
            graph.add_node(station.station_id, station_name=station.station_name)

        for edge in self.route_edges.itertuples(index=False):
            graph.add_edge(
                edge.from_station_id,
                edge.to_station_id,
                distance_km=float(edge.distance_km),
                scheduled_minutes=float(edge.scheduled_minutes),
            )
        return graph

    def _zone_from_counts(self, row: pd.Series) -> str:
        if row["it_count"] >= max(row["commercial_count"], row["education_count"], 2):
            return "IT Hub"
        if row["commercial_count"] >= max(row["education_count"], 3):
            return "Commercial"
        if row["education_count"] >= 2:
            return "Educational"
        if row["is_interchange"]:
            return "Interchange"
        if row["is_terminal"]:
            return "Terminal"
        return "Residential"

    def generate_metadata(self):
        print("Generating station metadata...")
        metadata = self.parent_stations.copy()
        metadata["is_interchange"] = metadata["station_id"].isin(self.interchanges["station_id"])
        metadata["is_terminal"] = metadata["station_id"].isin(self.terminals["station_id"])
        metadata["platform_count"] = metadata["route_count"].apply(lambda route_count: 2 + (max(route_count - 1, 0) * 2))

        poi_counts = metadata.apply(self._poi_counts, axis=1, result_type="expand")
        metadata = pd.concat([metadata, poi_counts], axis=1)
        metadata["near_it_hub"] = metadata["it_count"] >= 2
        metadata["commercial_area"] = metadata["commercial_count"] >= 3
        metadata["college_zone"] = metadata["education_count"] >= 2
        metadata["zone"] = metadata.apply(self._zone_from_counts, axis=1)

        graph = self._build_graph()
        degree_centrality = nx.degree_centrality(graph)
        betweenness_centrality = nx.betweenness_centrality(graph, weight="scheduled_minutes")
        closeness_centrality = nx.closeness_centrality(graph, distance="scheduled_minutes")

        metadata["degree_centrality"] = metadata["station_id"].map(degree_centrality).fillna(0.0)
        metadata["betweenness_centrality"] = metadata["station_id"].map(betweenness_centrality).fillna(0.0)
        metadata["closeness_centrality"] = metadata["station_id"].map(closeness_centrality).fillna(0.0)

        metadata["activity_score"] = (
            metadata["activity_count"].rank(pct=True)
            + metadata["commercial_count"].rank(pct=True)
            + metadata["education_count"].rank(pct=True)
        ) / 3

        raw_score = (
            30
            + (metadata["route_count"] * 10)
            + (metadata["is_interchange"].astype(int) * 22)
            + (metadata["is_terminal"].astype(int) * 8)
            + (metadata["degree_centrality"] * 15)
            + (metadata["betweenness_centrality"] * 30)
            + (metadata["closeness_centrality"] * 12)
            + (metadata["activity_score"] * 12)
        )
        metadata["importance_score"] = raw_score.clip(0, 100).round().astype(int)
        threshold = metadata["importance_score"].quantile(0.8)
        metadata["smart_city_priority"] = metadata["importance_score"] >= threshold

        station_metadata = metadata[
            [
                "station_id",
                "station_name",
                "routes",
                "is_interchange",
                "is_terminal",
                "platform_count",
                "zone",
                "near_it_hub",
                "commercial_area",
                "college_zone",
                "importance_score",
                "smart_city_priority",
                "latitude",
                "longitude",
                "osm_name",
                "osm_distance_m",
            ]
        ].rename(columns={"routes": "line"})

        importance_scores = metadata[
            [
                "station_id",
                "station_name",
                "importance_score",
                "smart_city_priority",
                "route_count",
                "degree_centrality",
                "betweenness_centrality",
                "closeness_centrality",
                "activity_score",
            ]
        ].sort_values("importance_score", ascending=False)

        return station_metadata, importance_scores

    def save(self, station_metadata: pd.DataFrame, importance_scores: pd.DataFrame):
        station_metadata.to_csv(self.data_dir / "station_metadata.csv", index=False)
        importance_scores.to_csv(self.data_dir / "station_importance_scores.csv", index=False)
        print(f"Saved station metadata to {self.data_dir / 'station_metadata.csv'}")
        print(f"Saved importance scores to {self.data_dir / 'station_importance_scores.csv'}")

    def run(self):
        station_metadata, importance_scores = self.generate_metadata()
        self.save(station_metadata, importance_scores)
        print(f"Generated metadata for {len(station_metadata)} stations")
        return station_metadata


if __name__ == "__main__":
    StationMetadataGenerator().run()
