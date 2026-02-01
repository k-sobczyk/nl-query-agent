"""Data cleaning script to remove duplicates and resolve odometer rollbacks."""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


def load_data(data_path: Path) -> list[dict[str, Any]]:
    with open(data_path, encoding='utf-8') as f:
        return json.load(f)


def remove_exact_duplicates(data: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    seen = set()
    unique_records = []
    duplicates_removed = 0

    for record in data:
        record_key = (
            record['vehicle_id'],
            record['timestamp'],
            record['battery_health_percent'],
            record['odometer_km'],
        )
        if record_key not in seen:
            seen.add(record_key)
            unique_records.append(record)
        else:
            duplicates_removed += 1

    return unique_records, duplicates_removed


def resolve_odometer_rollbacks(data: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    vehicle_readings: dict[str, list[dict]] = defaultdict(list)

    for record in data:
        vehicle_readings[record['vehicle_id']].append(record)

    cleaned_records = []
    records_removed = 0

    for vehicle_id, readings in vehicle_readings.items():
        sorted_readings = sorted(readings, key=lambda r: datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')))

        if sorted_readings:
            kept_readings = [sorted_readings[0]]
            current_max_odometer = sorted_readings[0]['odometer_km']

            for record in sorted_readings[1:]:
                odometer = record['odometer_km']
                if odometer >= current_max_odometer:
                    kept_readings.append(record)
                    current_max_odometer = odometer
                else:
                    records_removed += 1

            cleaned_records.extend(kept_readings)

    return cleaned_records, records_removed


def validate_cleaned_data(data: list[dict[str, Any]]) -> bool:
    vehicle_readings: dict[str, list[tuple]] = defaultdict(list)

    for record in data:
        ts = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
        vehicle_readings[record['vehicle_id']].append((ts, record['odometer_km']))

    for readings in vehicle_readings.values():
        readings.sort(key=lambda x: x[0])
        for i in range(1, len(readings)):
            if readings[i][1] < readings[i - 1][1]:
                return False

    return True


def save_clean_data(data: list[dict[str, Any]], output_path: Path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def main():
    input_path = Path(__file__).parent.parent / 'data' / 'telemetry.json'
    output_path = Path(__file__).parent.parent / 'data' / 'clean_telemetry.json'

    raw_data = load_data(input_path)
    data_no_dupes, _ = remove_exact_duplicates(raw_data)
    cleaned_data, _ = resolve_odometer_rollbacks(data_no_dupes)

    if not validate_cleaned_data(cleaned_data):
        return 1

    save_clean_data(cleaned_data, output_path)
    return 0


if __name__ == '__main__':
    exit(main())
