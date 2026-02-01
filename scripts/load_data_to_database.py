"""Load cleaned telemetry data into PostgreSQL database."""

import json
import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_batch

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_database_url() -> str:
    """Get database URL from environment or use default."""
    return os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:54322/postgres',
    )


def load_json_data(file_path: Path) -> list[dict]:
    """Load data from JSON file."""
    with open(file_path, encoding='utf-8') as f:
        return json.load(f)


def insert_telemetry_data(
    conn: psycopg2.extensions.connection,
    records: list[dict],
) -> None:
    """Insert telemetry records into database using batch insert."""
    insert_query = """
        INSERT INTO public.telemetry (
            vehicle_id,
            timestamp,
            battery_health_percent,
            odometer_km
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """

    data_tuples = [
        (
            record['vehicle_id'],
            record['timestamp'],
            record['battery_health_percent'],
            record['odometer_km'],
        )
        for record in records
    ]

    with conn.cursor() as cursor:
        execute_batch(cursor, insert_query, data_tuples, page_size=100)
        conn.commit()


def verify_data_load(conn: psycopg2.extensions.connection) -> dict:
    """Verify data was loaded successfully."""
    with conn.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM public.telemetry')
        total_count = cursor.fetchone()[0]  # type: ignore

        return {
            'total_records': total_count,
        }


def main() -> None:
    """Main execution function."""
    data_file = project_root / 'data' / 'clean_telemetry.json'

    try:
        records = load_json_data(data_file)
    except FileNotFoundError:
        print(f'Error: File not found: {data_file}')
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f'Error: Invalid JSON format: {e}')
        sys.exit(1)

    database_url = get_database_url()

    try:
        conn = psycopg2.connect(database_url)
    except psycopg2.Error as e:
        print(f'Database connection failed: {e}')
        sys.exit(1)

    try:
        insert_telemetry_data(conn, records)
        stats = verify_data_load(conn)
        print(f'Loaded {stats["total_records"]} records successfully')

    except psycopg2.Error as e:
        print(f'Database error: {e}')
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
