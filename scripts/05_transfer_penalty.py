"""
Transfer penalty matrix generation.
"""

from __future__ import annotations

from itertools import combinations

import pandas as pd

from pipeline_utils import DATA_DIR, haversine_km, load_gtfs_tables


class TransferPenaltyGenerator:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.stations = pd.read_csv(self.data_dir / "station_metadata.csv")
        self.route_edges = pd.read_csv(self.data_dir / "processed" / "route_edges.csv")
        self.transfers = load_gtfs_tables()["transfers"]

    def _is_direct_neighbor(self, station_a: str, station_b: str) -> bool:
        neighbors = self.route_edges[
            (
                (self.route_edges["from_station_id"] == station_a)
                & (self.route_edges["to_station_id"] == station_b)
            )
            | (
                (self.route_edges["from_station_id"] == station_b)
                & (self.route_edges["to_station_id"] == station_a)
            )
        ]
        return not neighbors.empty

    def _effective_cost(self, walking_minutes: float, crowd_penalty: float, platform_switch_penalty: float, escalator_penalty: float) -> float:
        return walking_minutes + crowd_penalty + platform_switch_penalty + escalator_penalty

    def generate_transfer_matrix(self):
        print("Generating transfer penalty matrix...")
        records = []

        for station in self.stations.itertuples(index=False):
            lines = [line.strip() for line in str(station.line).split(",") if line.strip()]
            if len(lines) < 2:
                continue

            for from_line, to_line in combinations(lines, 2):
                crowd_penalty = 3.5 + (0.02 * float(station.importance_score))
                platform_switch_penalty = 2.0 if station.platform_count >= 4 else 1.2
                escalator_penalty = 1.0 if station.platform_count >= 4 else 0.4
                walking_minutes = 2.5
                effective_cost = self._effective_cost(
                    walking_minutes,
                    crowd_penalty,
                    platform_switch_penalty,
                    escalator_penalty,
                )

                for start_line, end_line in [(from_line, to_line), (to_line, from_line)]:
                    records.append(
                        {
                            "from_station": station.station_name,
                            "to_station": station.station_name,
                            "walking_minutes": round(walking_minutes, 2),
                            "crowd_penalty": round(crowd_penalty, 2),
                            "platform_switch_penalty": round(platform_switch_penalty, 2),
                            "escalator_penalty": round(escalator_penalty, 2),
                            "effective_transfer_cost": round(effective_cost, 2),
                            "from_line": start_line,
                            "to_line": end_line,
                            "transfer_type": "in_station_interchange",
                        }
                    )

        station_rows = list(self.stations.itertuples(index=False))
        for index, station_a in enumerate(station_rows):
            for station_b in station_rows[index + 1 :]:
                if self._is_direct_neighbor(station_a.station_id, station_b.station_id):
                    continue

                distance_km = haversine_km(
                    float(station_a.latitude),
                    float(station_a.longitude),
                    float(station_b.latitude),
                    float(station_b.longitude),
                )
                if distance_km > 0.9:
                    continue

                walking_minutes = (distance_km / 4.8) * 60
                crowd_penalty = 0.02 * (float(station_a.importance_score) + float(station_b.importance_score))
                platform_switch_penalty = 0.8 if (station_a.is_interchange or station_b.is_interchange) else 0.4
                escalator_penalty = 0.5 if (station_a.platform_count > 2 or station_b.platform_count > 2) else 0.2
                effective_cost = self._effective_cost(
                    walking_minutes,
                    crowd_penalty,
                    platform_switch_penalty,
                    escalator_penalty,
                )

                for origin, destination in [(station_a, station_b), (station_b, station_a)]:
                    records.append(
                        {
                            "from_station": origin.station_name,
                            "to_station": destination.station_name,
                            "walking_minutes": round(walking_minutes, 2),
                            "crowd_penalty": round(crowd_penalty, 2),
                            "platform_switch_penalty": round(platform_switch_penalty, 2),
                            "escalator_penalty": round(escalator_penalty, 2),
                            "effective_transfer_cost": round(effective_cost, 2),
                            "from_line": origin.line,
                            "to_line": destination.line,
                            "transfer_type": "walking_link",
                        }
                    )

        transfer_matrix = pd.DataFrame(records).drop_duplicates(
            subset=["from_station", "to_station", "from_line", "to_line", "transfer_type"]
        )

        if not self.transfers.empty:
            transfer_matrix["gtfs_transfer_file_present"] = True
        else:
            transfer_matrix["gtfs_transfer_file_present"] = False

        return transfer_matrix.sort_values(
            ["effective_transfer_cost", "from_station", "to_station"]
        ).reset_index(drop=True)

    def save(self, df: pd.DataFrame):
        df.to_csv(self.data_dir / "transfer_penalty_matrix.csv", index=False)
        print(f"Saved transfer penalties to {self.data_dir / 'transfer_penalty_matrix.csv'}")

    def run(self):
        transfer_matrix = self.generate_transfer_matrix()
        self.save(transfer_matrix)
        print(f"Generated {len(transfer_matrix)} transfer penalty rows")
        return transfer_matrix


if __name__ == "__main__":
    TransferPenaltyGenerator().run()
