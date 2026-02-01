"""Tests for Pydantic models validation in app/ai/common/models.py."""

import pytest

from app.ai.common.models import QueryMetadata, VehicleQueryParams


def test_vehicle_id_exact_match():
    """Exact vehicle ID should work."""
    params = VehicleQueryParams(vehicle_id='VIN0466HID25')
    assert params.vehicle_id == 'VIN0466HID25'


def test_vehicle_id_with_hyphens():
    """Vehicle ID with hyphens should work."""
    params = VehicleQueryParams(vehicle_id='VIN-123-ABC')
    assert params.vehicle_id == 'VIN-123-ABC'


def test_vehicle_id_with_underscores():
    """Vehicle ID with underscores should work."""
    params = VehicleQueryParams(vehicle_id='VIN_123_ABC')
    assert params.vehicle_id == 'VIN_123_ABC'


def test_vehicle_id_starts_with_pattern():
    """Pattern 'VVA1*' should work."""
    params = VehicleQueryParams(vehicle_id='VVA1*')
    assert params.vehicle_id == 'VVA1*'


def test_vehicle_id_ends_with_pattern():
    """Pattern '*78' should work."""
    params = VehicleQueryParams(vehicle_id='*78')
    assert params.vehicle_id == '*78'


def test_vehicle_id_contains_pattern():
    """Pattern '*ABC*' should work."""
    params = VehicleQueryParams(vehicle_id='*ABC*')
    assert params.vehicle_id == '*ABC*'


def test_vehicle_id_none_allowed():
    """None should be allowed (optional parameter)."""
    params = VehicleQueryParams(vehicle_id=None)
    assert params.vehicle_id is None


def test_vehicle_id_empty_params():
    """Creating params without vehicle_id should work."""
    params = VehicleQueryParams()
    assert params.vehicle_id is None


def test_vehicle_id_max_length_100():
    """Vehicle ID with exactly 100 characters should work."""
    params = VehicleQueryParams(vehicle_id='A' * 100)
    assert params.vehicle_id is not None
    assert len(params.vehicle_id) == 100


def test_vehicle_id_exceeds_length():
    """Vehicle ID over 100 characters should fail."""
    with pytest.raises(ValueError, match='cannot exceed 100 characters'):
        VehicleQueryParams(vehicle_id='A' * 101)


def test_vehicle_id_special_chars_rejected():
    """Special regex characters should be rejected."""
    invalid_chars = ['.', '+', '?', '[', ']', '(', ')', '{', '}', '|', '^', '$', '\\']
    for char in invalid_chars:
        with pytest.raises(ValueError, match='can only contain'):
            VehicleQueryParams(vehicle_id=f'VIN{char}123')


def test_vehicle_id_excessive_wildcards():
    """More than 2 wildcards should fail."""
    with pytest.raises(ValueError, match='cannot contain more than 2 wildcards'):
        VehicleQueryParams(vehicle_id='*A*B*C*')


def test_vehicle_id_only_wildcards():
    """Only wildcards should fail."""
    with pytest.raises(ValueError, match='must contain at least one non-wildcard'):
        VehicleQueryParams(vehicle_id='*')

    with pytest.raises(ValueError, match='must contain at least one non-wildcard'):
        VehicleQueryParams(vehicle_id='**')


def test_timestamp_start_valid_format():
    """Valid timestamp format should work."""
    params = VehicleQueryParams(timestamp_start='2024-11-21-15')
    assert params.timestamp_start == '2024-11-21-15'


def test_timestamp_end_valid_format():
    """Valid timestamp format should work."""
    params = VehicleQueryParams(timestamp_end='2024-11-21-23')
    assert params.timestamp_end == '2024-11-21-23'


def test_timestamp_both_start_and_end():
    """Both timestamps can be provided."""
    params = VehicleQueryParams(timestamp_start='2024-11-21-09', timestamp_end='2024-11-21-17')
    assert params.timestamp_start == '2024-11-21-09'
    assert params.timestamp_end == '2024-11-21-17'


def test_timestamp_none_allowed():
    """None timestamps should be allowed."""
    params = VehicleQueryParams(timestamp_start=None, timestamp_end=None)
    assert params.timestamp_start is None
    assert params.timestamp_end is None


def test_timestamp_invalid_format_missing_parts():
    """Invalid format without all parts should fail."""
    with pytest.raises(ValueError, match='must be in format YYYY-MM-DD-HH'):
        VehicleQueryParams(timestamp_start='2024-11-21')


def test_timestamp_invalid_format_wrong_separators():
    """Invalid format with wrong separators should fail."""
    with pytest.raises(ValueError, match='must be in format YYYY-MM-DD-HH'):
        VehicleQueryParams(timestamp_start='2024/11/21/15')


def test_timestamp_invalid_month():
    """Invalid month value should fail."""
    with pytest.raises(ValueError, match='Invalid timestamp values'):
        VehicleQueryParams(timestamp_start='2024-13-21-15')


def test_timestamp_invalid_day():
    """Invalid day value should fail."""
    with pytest.raises(ValueError, match='Invalid timestamp values'):
        VehicleQueryParams(timestamp_start='2024-11-32-15')


def test_timestamp_invalid_hour():
    """Invalid hour value should fail."""
    with pytest.raises(ValueError, match='Invalid timestamp values'):
        VehicleQueryParams(timestamp_start='2024-11-21-24')


def test_timestamp_start_after_end():
    """Start timestamp after end timestamp should fail."""
    with pytest.raises(ValueError, match='cannot be after timestamp_end'):
        VehicleQueryParams(timestamp_start='2024-11-21-17', timestamp_end='2024-11-21-09')


def test_timestamp_edge_case_midnight():
    """Midnight hour (00) should work."""
    params = VehicleQueryParams(timestamp_start='2024-11-21-00')
    assert params.timestamp_start == '2024-11-21-00'


def test_timestamp_edge_case_last_hour():
    """Last hour of day (23) should work."""
    params = VehicleQueryParams(timestamp_end='2024-11-21-23')
    assert params.timestamp_end == '2024-11-21-23'


def test_battery_health_min_valid():
    """Valid min battery health should work."""
    params = VehicleQueryParams(battery_health_min=85.5)
    assert params.battery_health_min == 85.5


def test_battery_health_max_valid():
    """Valid max battery health should work."""
    params = VehicleQueryParams(battery_health_max=95.0)
    assert params.battery_health_max == 95.0


def test_battery_health_range():
    """Battery health range should work."""
    params = VehicleQueryParams(battery_health_min=80.0, battery_health_max=90.0)
    assert params.battery_health_min == 80.0
    assert params.battery_health_max == 90.0


def test_battery_health_none_allowed():
    """None battery health should be allowed."""
    params = VehicleQueryParams(battery_health_min=None, battery_health_max=None)
    assert params.battery_health_min is None
    assert params.battery_health_max is None


def test_battery_health_boundary_zero():
    """Boundary value 0.0 should work."""
    params = VehicleQueryParams(battery_health_min=0.0)
    assert params.battery_health_min == 0.0


def test_battery_health_boundary_hundred():
    """Boundary value 100.0 should work."""
    params = VehicleQueryParams(battery_health_max=100.0)
    assert params.battery_health_max == 100.0


def test_battery_health_min_negative():
    """Negative battery health should fail."""
    with pytest.raises(ValueError, match='must be between 0 and 100'):
        VehicleQueryParams(battery_health_min=-1.0)


def test_battery_health_max_over_hundred():
    """Battery health over 100 should fail."""
    with pytest.raises(ValueError, match='must be between 0 and 100'):
        VehicleQueryParams(battery_health_max=101.0)


def test_battery_health_min_greater_than_max():
    """Min greater than max should fail."""
    with pytest.raises(ValueError, match='cannot be greater than battery_health_max'):
        VehicleQueryParams(battery_health_min=90.0, battery_health_max=80.0)


def test_battery_health_integer_values():
    """Integer values should work (auto-converted to float)."""
    params = VehicleQueryParams(battery_health_min=80, battery_health_max=90)
    assert params.battery_health_min == 80.0
    assert params.battery_health_max == 90.0


def test_odometer_min_valid():
    """Valid min odometer should work."""
    params = VehicleQueryParams(odometer_km_min=50000)
    assert params.odometer_km_min == 50000


def test_odometer_max_valid():
    """Valid max odometer should work."""
    params = VehicleQueryParams(odometer_km_max=100000)
    assert params.odometer_km_max == 100000


def test_odometer_range():
    """Odometer range should work."""
    params = VehicleQueryParams(odometer_km_min=50000, odometer_km_max=100000)
    assert params.odometer_km_min == 50000
    assert params.odometer_km_max == 100000


def test_odometer_none_allowed():
    """None odometer should be allowed."""
    params = VehicleQueryParams(odometer_km_min=None, odometer_km_max=None)
    assert params.odometer_km_min is None
    assert params.odometer_km_max is None


def test_odometer_boundary_zero():
    """Boundary value 0 should work."""
    params = VehicleQueryParams(odometer_km_min=0)
    assert params.odometer_km_min == 0


def test_odometer_large_value():
    """Large odometer value should work."""
    params = VehicleQueryParams(odometer_km_max=999999)
    assert params.odometer_km_max == 999999


def test_odometer_max_boundary_10_million():
    """Boundary value 10,000,000 km should work."""
    params = VehicleQueryParams(odometer_km_max=10_000_000)
    assert params.odometer_km_max == 10_000_000


def test_odometer_exceeds_10_million():
    """Odometer over 10 million km should fail."""
    with pytest.raises(ValueError, match='less than or equal to 10000000'):
        VehicleQueryParams(odometer_km_min=10_000_001)


def test_odometer_absurd_value_rejected():
    """Absurdly high odometer value should fail."""
    with pytest.raises(ValueError, match='less than or equal to 10000000'):
        VehicleQueryParams(odometer_km_max=999_999_999)


def test_odometer_min_negative():
    """Negative odometer should fail."""
    with pytest.raises(ValueError, match='greater than or equal to 0'):
        VehicleQueryParams(odometer_km_min=-1)


def test_odometer_min_greater_than_max():
    """Min greater than max should fail."""
    with pytest.raises(ValueError, match='cannot be greater than odometer_km_max'):
        VehicleQueryParams(odometer_km_min=100000, odometer_km_max=50000)


def test_all_parameters_together():
    """All parameters can be used together."""
    params = VehicleQueryParams(
        vehicle_id='VVA1*',
        timestamp_start='2024-11-20-09',
        timestamp_end='2024-11-20-17',
        battery_health_min=80.0,
        battery_health_max=95.0,
        odometer_km_min=50000,
        odometer_km_max=100000,
    )
    assert params.vehicle_id == 'VVA1*'
    assert params.timestamp_start == '2024-11-20-09'
    assert params.timestamp_end == '2024-11-20-17'
    assert params.battery_health_min == 80.0
    assert params.battery_health_max == 95.0
    assert params.odometer_km_min == 50000
    assert params.odometer_km_max == 100000


def test_partial_parameters():
    """Partial parameters should work."""
    params = VehicleQueryParams(vehicle_id='*78', battery_health_min=85.0)
    assert params.vehicle_id == '*78'
    assert params.battery_health_min == 85.0
    assert params.timestamp_start is None
    assert params.odometer_km_max is None


def test_no_parameters():
    """No parameters should create valid empty query."""
    params = VehicleQueryParams()
    assert params.vehicle_id is None
    assert params.timestamp_start is None
    assert params.battery_health_min is None
    assert params.odometer_km_min is None


def test_query_metadata_success():
    """Successful query metadata should work."""
    metadata = QueryMetadata(record_count=42, execution_time_ms=123.45, success=True, error_message=None)
    assert metadata.record_count == 42
    assert metadata.execution_time_ms == 123.45
    assert metadata.success is True
    assert metadata.error_message is None


def test_query_metadata_failure():
    """Failed query metadata should work."""
    metadata = QueryMetadata(
        record_count=0, execution_time_ms=50.0, success=False, error_message='Database connection failed'
    )
    assert metadata.record_count == 0
    assert metadata.execution_time_ms == 50.0
    assert metadata.success is False
    assert metadata.error_message == 'Database connection failed'


def test_query_metadata_negative_count():
    """Negative record count should fail."""
    with pytest.raises(ValueError):
        QueryMetadata(record_count=-1, execution_time_ms=100.0, success=True)


def test_query_metadata_negative_time():
    """Negative execution time should fail."""
    with pytest.raises(ValueError):
        QueryMetadata(record_count=10, execution_time_ms=-1.0, success=True)


def test_query_metadata_zero_values():
    """Zero values should work."""
    metadata = QueryMetadata(record_count=0, execution_time_ms=0.0, success=True)
    assert metadata.record_count == 0
    assert metadata.execution_time_ms == 0.0
