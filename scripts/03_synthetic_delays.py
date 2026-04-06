"""
Synthetic Realtime Delay Data Generator
Generates metro delay patterns with smoother, more realistic operational logic:
- Peak-hour crowding and interchange pressure
- Terminal dispatch dwell
- Commercial, college, and IT hub demand patterns
- Weather disruption with modest fog impact
- Rare moderate/severe incidents
"""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


class SyntheticDelayGenerator:
    def __init__(self, n_samples=50000, seed=42):
        self.n_samples = n_samples
        self.rng = np.random.default_rng(seed)
        self.data_dir = Path("../data")
        self.stations = pd.read_csv(self.data_dir / "station_metadata.csv")

    def generate_timestamps(self):
        """Generate timestamps across the last 30 days with realistic service hours."""
        print(f"Generating {self.n_samples} timestamps...")

        start_date = datetime.now() - timedelta(days=30)
        timestamps = []

        for _ in range(self.n_samples):
            random_days = int(self.rng.integers(0, 30))
            random_hour = int(self.rng.choice(range(5, 23), p=self._hour_probability()))
            random_minute = int(self.rng.integers(0, 60))

            timestamp = start_date + timedelta(
                days=random_days,
                hours=random_hour,
                minutes=random_minute,
            )
            timestamps.append(timestamp)

        return pd.Series(timestamps)

    def _hour_probability(self):
        """Weighted service demand by hour."""
        probs = np.array(
            [
                0.02,
                0.03,
                0.05,
                0.09,
                0.08,
                0.05,
                0.04,
                0.05,
                0.04,
                0.04,
                0.05,
                0.06,
                0.08,
                0.09,
                0.08,
                0.07,
                0.05,
                0.03,
            ]
        )
        return probs / probs.sum()

    def is_peak_hour(self, timestamp):
        hour = timestamp.hour
        return (8 <= hour <= 10) or (17 <= hour <= 20)

    def is_weekday(self, timestamp):
        return timestamp.weekday() < 5

    def generate_weather_factor(self):
        """Generate weather with mostly clear operating conditions."""
        roll = self.rng.random()
        if roll < 0.82:
            return "clear"
        if roll < 0.92:
            return "rain"
        if roll < 0.97:
            return "fog"
        return "storm"

    def calculate_operational_pressure(self, station, timestamp, weather):
        """Estimate crowding/load variables that drive delays."""
        hour = timestamp.hour
        weekday = self.is_weekday(timestamp)
        peak = self.is_peak_hour(timestamp)

        congestion = 22.0 + self.rng.normal(0, 4)
        if peak:
            congestion += 18
        if weekday:
            congestion += 3
        if station["is_interchange"]:
            congestion += 16
        if station["is_terminal"]:
            congestion += 5
        if station["commercial_area"] and (peak or 12 <= hour <= 15):
            congestion += 5
        if station["college_zone"] and weekday and (8 <= hour <= 10 or 16 <= hour <= 18):
            congestion += 4
        if station["near_it_hub"] and weekday and 17 <= hour <= 20:
            congestion += 8

        if weather == "rain":
            congestion += 5
        elif weather == "fog":
            congestion += 2
        elif weather == "storm":
            congestion += 9

        congestion = float(np.clip(congestion, 10, 98))

        if station["is_interchange"]:
            transfer_load = 12 + (24 if peak else 8) + self.rng.integers(-4, 5)
            if weather in {"rain", "storm"}:
                transfer_load += 4
            transfer_load = int(np.clip(transfer_load, 5, 110))
        else:
            transfer_load = 0

        platform_occupancy = float(
            np.clip(
                congestion * self.rng.uniform(0.85, 1.08) + (6 if station["is_terminal"] else 0),
                10,
                98,
            )
        )

        return congestion, transfer_load, platform_occupancy

    def calculate_delay(self, station, timestamp, weather, congestion, transfer_load, platform_occupancy):
        """Create a plausible delay value in minutes."""
        hour = timestamp.hour
        weekday = self.is_weekday(timestamp)
        peak = self.is_peak_hour(timestamp)

        delay = 0.35 + self.rng.normal(0, 0.12)

        if peak:
            delay += self.rng.uniform(0.6, 1.2)
        if not weekday:
            delay -= self.rng.uniform(0.1, 0.25)
        if station["is_interchange"]:
            delay += self.rng.uniform(0.55, 1.1 if peak else 0.75)
        if station["is_terminal"]:
            delay += self.rng.uniform(0.18, 0.55 if peak else 0.35)
        if station["commercial_area"] and (peak or 12 <= hour <= 15):
            delay += self.rng.uniform(0.15, 0.5)
        if station["college_zone"] and weekday and (8 <= hour <= 10 or 16 <= hour <= 18):
            delay += self.rng.uniform(0.15, 0.4)
        if station["near_it_hub"] and weekday and 17 <= hour <= 20:
            delay += self.rng.uniform(0.35, 0.8)

        if weather == "rain":
            delay += self.rng.uniform(0.4, 0.9)
        elif weather == "fog":
            delay += self.rng.uniform(0.15, 0.4)
        elif weather == "storm":
            delay += self.rng.uniform(0.9, 1.8)

        delay += max(0.0, congestion - 35.0) * 0.02
        delay += max(0.0, platform_occupancy - 60.0) * 0.01
        delay += transfer_load * 0.006

        moderate_incident = self.rng.random() < 0.018
        severe_incident = self.rng.random() < 0.004
        if moderate_incident:
            delay += self.rng.uniform(1.5, 4.0)
        if severe_incident:
            delay += self.rng.uniform(4.0, 9.0)

        return float(np.clip(delay, 0.0, 18.0))

    def generate_delay_data(self):
        """Generate the synthetic delay dataset."""
        print("Generating synthetic delay data...")

        records = []
        timestamps = self.generate_timestamps()

        for index, timestamp in enumerate(timestamps, start=1):
            station = self.stations.sample(1, random_state=int(self.rng.integers(0, 1_000_000))).iloc[0]
            weather = self.generate_weather_factor()
            congestion, transfer_load, platform_occupancy = self.calculate_operational_pressure(
                station,
                timestamp,
                weather,
            )
            delay = self.calculate_delay(
                station,
                timestamp,
                weather,
                congestion,
                transfer_load,
                platform_occupancy,
            )

            records.append(
                {
                    "station_id": station["station_id"],
                    "station_name": station["station_name"],
                    "timestamp": timestamp,
                    "delay_minutes": round(delay, 2),
                    "peak_hour": self.is_peak_hour(timestamp),
                    "weekday": self.is_weekday(timestamp),
                    "hour": timestamp.hour,
                    "weather_factor": weather,
                    "transfer_load": transfer_load,
                    "platform_occupancy": round(platform_occupancy, 1),
                    "congestion_score": round(congestion, 1),
                }
            )

            if index % 10000 == 0:
                print(f"  Generated {index}/{self.n_samples} records...")

        df = pd.DataFrame(records)

        print(f"Generated {len(df)} delay records")
        print(f"Average delay: {df['delay_minutes'].mean():.2f} minutes")
        print(f"95th percentile delay: {df['delay_minutes'].quantile(0.95):.2f} minutes")
        print(f"Peak-hour average delay: {df[df['peak_hour']]['delay_minutes'].mean():.2f} minutes")

        return df

    def save(self, df):
        output_path = self.data_dir / "synthetic_realtime_delays.csv"
        df.to_csv(output_path, index=False)
        print(f"Saved delay data to {output_path}")

    def run(self):
        print("=" * 60)
        print("SYNTHETIC DELAY DATA GENERATION")
        print("=" * 60)

        delay_data = self.generate_delay_data()
        self.save(delay_data)

        print("=" * 60)
        print("DELAY GENERATION COMPLETE")
        print("=" * 60)

        return delay_data


if __name__ == "__main__":
    generator = SyntheticDelayGenerator(n_samples=50000)
    generator.run()
