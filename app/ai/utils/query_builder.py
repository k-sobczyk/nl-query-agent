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
    """Create and return a PostgreSQL database connection.

    Reads connection parameters from environment variables for Supabase.

    Environment Variables:
        DATABASE_URL: Full connection string (preferred), OR
        DB_HOST: Database host (default: localhost)
        DB_PORT: Database port (default: 54322 for Supabase local)
        DB_NAME: Database name (default: postgres)
        DB_USER: Database user (default: postgres)
        DB_PASSWORD: Database password (required)

    Returns:
        psycopg2 connection object.
    """
    # Try DATABASE_URL first (standard for Supabase)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)

    # Otherwise construct from individual parameters
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '54322'),  # Supabase local default
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
    )


def build_query(params: VehicleQueryParams) -> tuple[str, dict]:
    """Build parameterized PostgreSQL SQL query from validated parameters.

    This function constructs a safe SQL query using PostgreSQL's parameterized query system.
    No user input is directly interpolated into the SQL string.

    Args:
        params: Validated query parameters from Pydantic model.

    Returns:
        Tuple of (query_string, query_parameters_dict) ready for PostgreSQL execution.
    """
    where_clauses = []
    query_params = {}

    # Handle vehicle_id with pattern matching
    if params.vehicle_id is not None:
        pattern_result = wildcard_to_sql_like(params.vehicle_id)
        if pattern_result:
            operator, sql_pattern = pattern_result
            if operator == '=':
                where_clauses.append('vehicle_id = %(vehicle_id)s')
            else:  # LIKE
                where_clauses.append('vehicle_id LIKE %(vehicle_id)s')
            query_params['vehicle_id'] = sql_pattern

    # Handle timestamp range
    if params.timestamp_start is not None:
        # Convert YYYY-MM-DD-HH to YYYY-MM-DD HH:00:00 format
        parts = params.timestamp_start.split('-')
        timestamp_str = f'{parts[0]}-{parts[1]}-{parts[2]} {parts[3]}:00:00'
        where_clauses.append('timestamp >= %(timestamp_start)s')
        query_params['timestamp_start'] = timestamp_str

    if params.timestamp_end is not None:
        parts = params.timestamp_end.split('-')
        timestamp_str = f'{parts[0]}-{parts[1]}-{parts[2]} {parts[3]}:00:00'
        where_clauses.append('timestamp <= %(timestamp_end)s')
        query_params['timestamp_end'] = timestamp_str

    # Handle battery health range
    if params.battery_health_min is not None:
        where_clauses.append('battery_health_percent >= %(battery_health_min)s')
        query_params['battery_health_min'] = params.battery_health_min

    if params.battery_health_max is not None:
        where_clauses.append('battery_health_percent <= %(battery_health_max)s')
        query_params['battery_health_max'] = params.battery_health_max

    # Handle odometer range
    if params.odometer_km_min is not None:
        where_clauses.append('odometer_km >= %(odometer_km_min)s')
        query_params['odometer_km_min'] = params.odometer_km_min

    if params.odometer_km_max is not None:
        where_clauses.append('odometer_km <= %(odometer_km_max)s')
        query_params['odometer_km_max'] = params.odometer_km_max

    # Construct WHERE clause
    where_sql = ' AND '.join(where_clauses) if where_clauses else 'TRUE'

    # Get table name from environment
    schema = os.getenv('DB_SCHEMA', DEFAULT_DB_SCHEMA)
    table = os.getenv('DB_TABLE', DEFAULT_DB_TABLE)
    full_table_name = f'{schema}.{table}'

    # Build complete query with LIMIT as guardrail
    query = f"""
        SELECT *
        FROM {full_table_name}
        WHERE {where_sql}
        LIMIT {MAX_QUERY_RESULTS}
    """

    return query, query_params


def execute_query(params: VehicleQueryParams) -> QueryMetadata:
    """Execute PostgreSQL query, save results to CSV, and return metadata.

    This function executes the query against PostgreSQL/Supabase, saves the actual results
    to a CSV file in the data/ directory, and returns metadata (including file path).

    Args:
        params: Validated query parameters from Pydantic model.

    Returns:
        QueryMetadata with execution results and path to saved CSV file.
    """
    try:
        # Build parameterized query
        query, query_params = build_query(params)

        # Execute query and measure time
        start_time = time.time()

        with get_database_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, query_params)
                rows = cursor.fetchall()

        execution_time_ms = (time.time() - start_time) * 1000

        # Convert rows to list of dicts
        rows_list = [dict(row) for row in rows]
        record_count = len(rows_list)

        # Save results to CSV file if we have data
        output_file = None
        if record_count > 0:
            output_file = _save_results_to_csv(rows_list)

        return QueryMetadata(
            record_count=record_count,
            execution_time_ms=execution_time_ms,
            success=True,
            error_message=None,
            output_file=output_file,
        )

    except Exception as e:
        # Return error metadata without raising
        return QueryMetadata(
            record_count=0,
            execution_time_ms=0.0,
            success=False,
            error_message=f'Query execution failed: {str(e)}',
            output_file=None,
        )


def _save_results_to_csv(rows: list[dict]) -> str:
    """Save query results to CSV file in data/ directory.

    Args:
        rows: List of row dictionaries from PostgreSQL results.

    Returns:
        Path to the saved CSV file (relative to project root).
    """
    # Create data directory if it doesn't exist
    data_dir = Path(DATA_OUTPUT_DIR)
    data_dir.mkdir(exist_ok=True)

    # Generate timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'query_results_{timestamp}.csv'
    filepath = data_dir / filename

    # Write results to CSV
    if rows:
        # Convert datetime objects to strings for CSV compatibility
        rows_for_csv = []
        for row in rows:
            row_dict = {}
            for key, value in row.items():
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()
                else:
                    row_dict[key] = value
            rows_for_csv.append(row_dict)

        fieldnames = rows_for_csv[0].keys()
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_for_csv)

    return str(filepath)
