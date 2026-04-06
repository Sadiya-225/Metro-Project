"""
Peak-hour label generation.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from pipeline_utils import DATA_DIR


class PeakHourGenerator:
    def __init__(self, days: int = 30):
        self.data_dir = DATA_DIR
        self.days = days

    def _label_hour(self, hour: int, weekday: bool):
        is_peak = False
        peak_type = "normal"
        zone_pressure = 1.0
        expected_wait_multiplier = 1.0

        if weekday and 8 <= hour < 10:
            is_peak = True
            peak_type = "morning_office"
            zone_pressure = 3.3
            expected_wait_multiplier = 2.4
        elif weekday and 17 <= hour < 20:
            is_peak = True
            peak_type = "evening_return"
            zone_pressure = 3.8
            expected_wait_multiplier = 2.8
        elif weekday and (7 <= hour < 8 or 16 <= hour < 17):
            peak_type = "student_rush"
            zone_pressure = 2.1
            expected_wait_multiplier = 1.6
        elif (not weekday) and 11 <= hour < 15:
            peak_type = "weekend_market"
            zone_pressure = 1.8
            expected_wait_multiplier = 1.35

        return is_peak, peak_type, zone_pressure, expected_wait_multiplier

    def generate_peak_hour_labels(self):
        print("Generating peak-hour labels...")
        records = []
        start_date = datetime.now() - timedelta(days=self.days)

        for offset in range(self.days):
            current_date = start_date + timedelta(days=offset)
            weekday = current_date.weekday() < 5

            for hour in range(24):
                timestamp = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                is_peak, peak_type, zone_pressure, expected_wait_multiplier = self._label_hour(hour, weekday)
                records.append(
                    {
                        "timestamp": timestamp,
                        "hour": hour,
                        "is_peak": is_peak,
                        "peak_type": peak_type,
                        "zone_pressure": zone_pressure,
                        "expected_wait_multiplier": expected_wait_multiplier,
                        "weekday": weekday,
                    }
                )

        return pd.DataFrame(records)

    def save(self, df: pd.DataFrame):
        df.to_csv(self.data_dir / "peak_hour_labels.csv", index=False)
        print(f"Saved peak-hour labels to {self.data_dir / 'peak_hour_labels.csv'}")

    def run(self):
        labels = self.generate_peak_hour_labels()
        self.save(labels)
        print(f"Generated {len(labels)} peak-hour records")
        return labels


if __name__ == "__main__":
    PeakHourGenerator().run()
