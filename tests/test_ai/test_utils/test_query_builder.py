"""Tests for query_builder utilities."""

from datetime import datetime

from app.ai.common.models import VehicleQueryParams
from app.ai.utils.query_builder import (
    _add_range_filter,
    _parse_timestamp,
    _serialize_row,
    build_query,
)


def test_parse_timestamp_converts_format():
    """Converts YYYY-MM-DD-HH to YYYY-MM-DD HH:00:00."""
    result = _parse_timestamp('2024-11-21-15')
    assert result == '2024-11-21 15:00:00'


def test_parse_timestamp_different_values():
    """Handles different date and time values."""
    result = _parse_timestamp('2025-01-05-23')
    assert result == '2025-01-05 23:00:00'


def test_parse_timestamp_midnight():
    """Handles midnight hour."""
    result = _parse_timestamp('2024-12-31-00')
    assert result == '2024-12-31 00:00:00'


def test_add_range_filter_both_min_max():
    """Adds both min and max filters when both provided."""
    clauses = []
    params = {}
    _add_range_filter(clauses, params, 'odometer_km', 1000, 5000, 'odometer_km')

    assert len(clauses) == 2
    assert 'odometer_km >= %(odometer_km_min)s' in clauses
    assert 'odometer_km <= %(odometer_km_max)s' in clauses
    assert params['odometer_km_min'] == 1000
    assert params['odometer_km_max'] == 5000


def test_add_range_filter_only_min():
    """Adds only min filter when max is None."""
    clauses = []
    params = {}
    _add_range_filter(clauses, params, 'battery_health_percent', 50.0, None, 'battery_health')

    assert len(clauses) == 1
    assert 'battery_health_percent >= %(battery_health_min)s' in clauses
    assert params['battery_health_min'] == 50.0
    assert 'battery_health_max' not in params


def test_add_range_filter_only_max():
    """Adds only max filter when min is None."""
    clauses = []
    params = {}
    _add_range_filter(clauses, params, 'odometer_km', None, 10000, 'odometer_km')

    assert len(clauses) == 1
    assert 'odometer_km <= %(odometer_km_max)s' in clauses
    assert params['odometer_km_max'] == 10000
    assert 'odometer_km_min' not in params


def test_add_range_filter_both_none():
    """Adds no filters when both are None."""
    clauses = []
    params = {}
    _add_range_filter(clauses, params, 'odometer_km', None, None, 'odometer_km')

    assert len(clauses) == 0
    assert len(params) == 0


def test_serialize_row_converts_datetime():
    """Converts datetime objects to ISO format strings."""
    row = {'id': 1, 'timestamp': datetime(2024, 11, 21, 15, 30, 45), 'value': 100}

    result = _serialize_row(row)

    assert result['id'] == 1
    assert result['timestamp'] == '2024-11-21T15:30:45'
    assert result['value'] == 100


def test_serialize_row_preserves_non_datetime():
    """Preserves non-datetime values as-is."""
    row = {'vehicle_id': 'VIN123', 'odometer': 50000, 'battery': 85.5, 'active': True}

    result = _serialize_row(row)

    assert result == row


def test_serialize_row_empty_dict():
    """Handles empty dictionary."""
    result = _serialize_row({})
    assert result == {}


def test_build_query_no_filters():
    """Generates query with no WHERE filters when params are empty."""
    params = VehicleQueryParams()
    query, query_params = build_query(params)

    assert 'WHERE TRUE' in query
    assert 'SELECT *' in query
    assert 'LIMIT 100' in query
    assert len(query_params) == 0


def test_build_query_vehicle_id_exact_match():
    """Uses = operator for exact vehicle_id match."""
    params = VehicleQueryParams(vehicle_id='VIN123')
    query, query_params = build_query(params)

    assert 'vehicle_id = %(vehicle_id)s' in query
    assert query_params['vehicle_id'] == 'VIN123'


def test_build_query_vehicle_id_wildcard():
    """Uses LIKE operator for wildcard vehicle_id."""
    params = VehicleQueryParams(vehicle_id='VVA1*')
    query, query_params = build_query(params)

    assert 'vehicle_id LIKE %(vehicle_id)s' in query
    assert query_params['vehicle_id'] == 'VVA1%'


def test_build_query_timestamp_range():
    """Includes timestamp filters when provided."""
    params = VehicleQueryParams(timestamp_start='2024-11-21-15', timestamp_end='2024-11-21-23')
    query, query_params = build_query(params)

    assert 'timestamp >= %(timestamp_start)s' in query
    assert 'timestamp <= %(timestamp_end)s' in query
    assert query_params['timestamp_start'] == '2024-11-21 15:00:00'
    assert query_params['timestamp_end'] == '2024-11-21 23:00:00'


def test_build_query_battery_health_range():
    """Includes battery health filters."""
    params = VehicleQueryParams(battery_health_min=70.0, battery_health_max=90.0)
    query, query_params = build_query(params)

    assert 'battery_health_percent >= %(battery_health_min)s' in query
    assert 'battery_health_percent <= %(battery_health_max)s' in query
    assert query_params['battery_health_min'] == 70.0
    assert query_params['battery_health_max'] == 90.0


def test_build_query_odometer_range():
    """Includes odometer filters."""
    params = VehicleQueryParams(odometer_km_min=10000, odometer_km_max=50000)
    query, query_params = build_query(params)

    assert 'odometer_km >= %(odometer_km_min)s' in query
    assert 'odometer_km <= %(odometer_km_max)s' in query
    assert query_params['odometer_km_min'] == 10000
    assert query_params['odometer_km_max'] == 50000


def test_build_query_all_filters_combined():
    """Combines all filters with AND."""
    params = VehicleQueryParams(
        vehicle_id='VVA*',
        timestamp_start='2024-11-21-15',
        timestamp_end='2024-11-21-23',
        battery_health_min=70.0,
        battery_health_max=90.0,
        odometer_km_min=10000,
        odometer_km_max=50000,
    )
    query, query_params = build_query(params)

    assert 'vehicle_id LIKE %(vehicle_id)s' in query
    assert 'timestamp >= %(timestamp_start)s' in query
    assert 'timestamp <= %(timestamp_end)s' in query
    assert 'battery_health_percent >= %(battery_health_min)s' in query
    assert 'battery_health_percent <= %(battery_health_max)s' in query
    assert 'odometer_km >= %(odometer_km_min)s' in query
    assert 'odometer_km <= %(odometer_km_max)s' in query
    assert ' AND ' in query
    assert len(query_params) == 7


def test_build_query_partial_filters():
    """Handles partial filter combinations."""
    params = VehicleQueryParams(vehicle_id='VIN*', battery_health_min=80.0)
    query, query_params = build_query(params)

    assert 'vehicle_id LIKE %(vehicle_id)s' in query
    assert 'battery_health_percent >= %(battery_health_min)s' in query
    assert 'timestamp' not in query
    assert 'odometer_km' not in query
    assert len(query_params) == 2
