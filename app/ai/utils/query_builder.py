"""PostgreSQL/Supabase query construction and execution with parameterized queries."""

import csv
import os
import time
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from app.ai.common.constants import DATA_OUTPUT_DIR
from app.ai.common.models import QueryMetadata, VehicleQueryParams
from app.ai.utils.pattern_converter import wildcard_to_sql_like

DEFAULT_DB_SCHEMA = ''
DEFAULT_DB_TABLE = ''
MAX_QUERY_RESULTS = 100


def get_database_connection():
    """Create PostgreSQL/Supabase connection from DATABASE_URL or individual env vars."""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '54322'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
    )


def _parse_timestamp(timestamp_str: str) -> str:
    """Convert YYYY-MM-DD-HH format to YYYY-MM-DDTHH:00:00Z for SQL."""
    parts = timestamp_str.split('-')
    return f'{parts[0]}-{parts[1]}-{parts[2]}T{parts[3]}:00:00Z'


def _add_range_filter(
    clauses: list[str],
    params: dict,
    field: str,
    min_val: float | int | None,
    max_val: float | int | None,
    param_prefix: str,
):
    """Add min/max range filters to WHERE clauses."""
    if min_val is not None:
        clauses.append(f'{field} >= %({param_prefix}_min)s')
        params[f'{param_prefix}_min'] = min_val

    if max_val is not None:
        clauses.append(f'{field} <= %({param_prefix}_max)s')
        params[f'{param_prefix}_max'] = max_val


def _serialize_row(row: dict) -> dict:
    """Convert datetime objects to ISO strings for CSV compatibility."""
    return {k: v.isoformat() if isinstance(v, datetime) else v for k, v in row.items()}


def build_query(params: VehicleQueryParams) -> tuple[str, dict]:
    """Build parameterized PostgreSQL query from validated parameters."""
    where_clauses = []
    query_params = {}

    if params.vehicle_id is not None:
        pattern_result = wildcard_to_sql_like(params.vehicle_id)
        if pattern_result:
            operator, sql_pattern = pattern_result
            where_clauses.append(f'vehicle_id {operator} %(vehicle_id)s')
            query_params['vehicle_id'] = sql_pattern

    if params.timestamp_start is not None:
        where_clauses.append('timestamp >= %(timestamp_start)s')
        query_params['timestamp_start'] = _parse_timestamp(params.timestamp_start)

    if params.timestamp_end is not None:
        where_clauses.append('timestamp <= %(timestamp_end)s')
        query_params['timestamp_end'] = _parse_timestamp(params.timestamp_end)

    _add_range_filter(
        where_clauses,
        query_params,
        'battery_health_percent',
        params.battery_health_min,
        params.battery_health_max,
        'battery_health',
    )

    _add_range_filter(
        where_clauses,
        query_params,
        'odometer_km',
        params.odometer_km_min,
        params.odometer_km_max,
        'odometer_km',
    )

    where_sql = ' AND '.join(where_clauses) if where_clauses else 'TRUE'
    schema = os.getenv('DB_SCHEMA', DEFAULT_DB_SCHEMA)
    table = os.getenv('DB_TABLE', DEFAULT_DB_TABLE)
    full_table_name = f'{schema}.{table}'

    query = f"""
        SELECT *
        FROM {full_table_name}
        WHERE {where_sql}
        LIMIT {MAX_QUERY_RESULTS}
    """

    return query, query_params


def execute_query(params: VehicleQueryParams) -> QueryMetadata:
    """Execute query, save results to CSV, return metadata."""
    try:
        query, query_params = build_query(params)
        start_time = time.time()

        with get_database_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, query_params)
                rows = cursor.fetchall()

        execution_time_ms = (time.time() - start_time) * 1000
        rows_list = [dict(row) for row in rows]
        record_count = len(rows_list)

        output_file = _save_results_to_csv(rows_list) if record_count > 0 else None

        return QueryMetadata(
            record_count=record_count,
            execution_time_ms=execution_time_ms,
            success=True,
            error_message=None,
            output_file=output_file,
        )

    except Exception as e:
        return QueryMetadata(
            record_count=0,
            execution_time_ms=0.0,
            success=False,
            error_message=f'Query execution failed: {str(e)}',
            output_file=None,
        )


def _save_results_to_csv(rows: list[dict]) -> str:
    """Save query results to timestamped CSV file."""
    data_dir = Path(DATA_OUTPUT_DIR)
    data_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filepath = data_dir / f'query_results_{timestamp}.csv'

    if rows:
        rows_for_csv = [_serialize_row(row) for row in rows]
        fieldnames = rows_for_csv[0].keys()

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_for_csv)

    return str(filepath)
