"""Tests for Pydantic models validation in app/ai/common/models.py."""

import pytest

from app.ai.common.models import QueryMetadata, VehicleQueryParams


class TestVehicleQueryParamsVehicleId:
    """Test vehicle_id parameter validation."""

    def test_vehicle_id_exact_match(self):
        """Exact vehicle ID should work."""
        params = VehicleQueryParams(vehicle_id='VIN0466HID25')
        assert params.vehicle_id == 'VIN0466HID25'

    def test_vehicle_id_with_hyphens(self):
        """Vehicle ID with hyphens should work."""
        params = VehicleQueryParams(vehicle_id='VIN-123-ABC')
        assert params.vehicle_id == 'VIN-123-ABC'

    def test_vehicle_id_with_underscores(self):
        """Vehicle ID with underscores should work."""
        params = VehicleQueryParams(vehicle_id='VIN_123_ABC')
        assert params.vehicle_id == 'VIN_123_ABC'

    def test_vehicle_id_starts_with_pattern(self):
        """Pattern 'VVA1*' should work."""
        params = VehicleQueryParams(vehicle_id='VVA1*')
        assert params.vehicle_id == 'VVA1*'

    def test_vehicle_id_ends_with_pattern(self):
        """Pattern '*78' should work."""
        params = VehicleQueryParams(vehicle_id='*78')
        assert params.vehicle_id == '*78'

    def test_vehicle_id_contains_pattern(self):
        """Pattern '*ABC*' should work."""
        params = VehicleQueryParams(vehicle_id='*ABC*')
        assert params.vehicle_id == '*ABC*'

    def test_vehicle_id_none_allowed(self):
        """None should be allowed (optional parameter)."""
        params = VehicleQueryParams(vehicle_id=None)
        assert params.vehicle_id is None

    def test_vehicle_id_empty_params(self):
        """Creating params without vehicle_id should work."""
        params = VehicleQueryParams()
        assert params.vehicle_id is None

    def test_vehicle_id_max_length_100(self):
        """Vehicle ID with exactly 100 characters should work."""
        params = VehicleQueryParams(vehicle_id='A' * 100)
        assert len(params.vehicle_id) == 100

    def test_vehicle_id_exceeds_length(self):
        """Vehicle ID over 100 characters should fail."""
        with pytest.raises(ValueError, match='cannot exceed 100 characters'):
            VehicleQueryParams(vehicle_id='A' * 101)

    def test_vehicle_id_special_chars_rejected(self):
        """Special regex characters should be rejected."""
        invalid_chars = ['.', '+', '?', '[', ']', '(', ')', '{', '}', '|', '^', '$', '\\']
        for char in invalid_chars:
            with pytest.raises(ValueError, match='can only contain'):
                VehicleQueryParams(vehicle_id=f'VIN{char}123')

    def test_vehicle_id_excessive_wildcards(self):
        """More than 2 wildcards should fail."""
        with pytest.raises(ValueError, match='cannot contain more than 2 wildcards'):
            VehicleQueryParams(vehicle_id='*A*B*C*')

    def test_vehicle_id_only_wildcards(self):
        """Only wildcards should fail."""
        with pytest.raises(ValueError, match='must contain at least one non-wildcard'):
            VehicleQueryParams(vehicle_id='*')

        with pytest.raises(ValueError, match='must contain at least one non-wildcard'):
            VehicleQueryParams(vehicle_id='**')


class TestVehicleQueryParamsTimestamp:
    """Test timestamp parameter validation."""

    def test_timestamp_start_valid_format(self):
        """Valid timestamp format should work."""
        params = VehicleQueryParams(timestamp_start='2024-11-21-15')
        assert params.timestamp_start == '2024-11-21-15'

    def test_timestamp_end_valid_format(self):
        """Valid timestamp format should work."""
        params = VehicleQueryParams(timestamp_end='2024-11-21-23')
        assert params.timestamp_end == '2024-11-21-23'

    def test_timestamp_both_start_and_end(self):
        """Both timestamps can be provided."""
        params = VehicleQueryParams(timestamp_start='2024-11-21-09', timestamp_end='2024-11-21-17')
        assert params.timestamp_start == '2024-11-21-09'
        assert params.timestamp_end == '2024-11-21-17'

    def test_timestamp_none_allowed(self):
        """None timestamps should be allowed."""
        params = VehicleQueryParams(timestamp_start=None, timestamp_end=None)
        assert params.timestamp_start is None
        assert params.timestamp_end is None

    def test_timestamp_invalid_format_missing_parts(self):
        """Invalid format without all parts should fail."""
        with pytest.raises(ValueError, match='must be in format YYYY-MM-DD-HH'):
            VehicleQueryParams(timestamp_start='2024-11-21')

    def test_timestamp_invalid_format_wrong_separators(self):
        """Invalid format with wrong separators should fail."""
        with pytest.raises(ValueError, match='must be in format YYYY-MM-DD-HH'):
            VehicleQueryParams(timestamp_start='2024/11/21/15')

    def test_timestamp_invalid_month(self):
        """Invalid month value should fail."""
        with pytest.raises(ValueError, match='Invalid timestamp values'):
            VehicleQueryParams(timestamp_start='2024-13-21-15')

    def test_timestamp_invalid_day(self):
        """Invalid day value should fail."""
        with pytest.raises(ValueError, match='Invalid timestamp values'):
            VehicleQueryParams(timestamp_start='2024-11-32-15')

    def test_timestamp_invalid_hour(self):
        """Invalid hour value should fail."""
        with pytest.raises(ValueError, match='Invalid timestamp values'):
            VehicleQueryParams(timestamp_start='2024-11-21-24')

    def test_timestamp_start_after_end(self):
        """Start timestamp after end timestamp should fail."""
        with pytest.raises(ValueError, match='cannot be after timestamp_end'):
            VehicleQueryParams(timestamp_start='2024-11-21-17', timestamp_end='2024-11-21-09')

    def test_timestamp_edge_case_midnight(self):
        """Midnight hour (00) should work."""
        params = VehicleQueryParams(timestamp_start='2024-11-21-00')
        assert params.timestamp_start == '2024-11-21-00'

    def test_timestamp_edge_case_last_hour(self):
        """Last hour of day (23) should work."""
        params = VehicleQueryParams(timestamp_end='2024-11-21-23')
        assert params.timestamp_end == '2024-11-21-23'


class TestVehicleQueryParamsBatteryHealth:
    """Test battery_health parameter validation."""

    def test_battery_health_min_valid(self):
        """Valid min battery health should work."""
        params = VehicleQueryParams(battery_health_min=85.5)
        assert params.battery_health_min == 85.5

    def test_battery_health_max_valid(self):
        """Valid max battery health should work."""
        params = VehicleQueryParams(battery_health_max=95.0)
        assert params.battery_health_max == 95.0

    def test_battery_health_range(self):
        """Battery health range should work."""
        params = VehicleQueryParams(battery_health_min=80.0, battery_health_max=90.0)
        assert params.battery_health_min == 80.0
        assert params.battery_health_max == 90.0

    def test_battery_health_none_allowed(self):
        """None battery health should be allowed."""
        params = VehicleQueryParams(battery_health_min=None, battery_health_max=None)
        assert params.battery_health_min is None
        assert params.battery_health_max is None

    def test_battery_health_boundary_zero(self):
        """Boundary value 0.0 should work."""
        params = VehicleQueryParams(battery_health_min=0.0)
        assert params.battery_health_min == 0.0

    def test_battery_health_boundary_hundred(self):
        """Boundary value 100.0 should work."""
        params = VehicleQueryParams(battery_health_max=100.0)
        assert params.battery_health_max == 100.0

    def test_battery_health_min_negative(self):
        """Negative battery health should fail."""
        with pytest.raises(ValueError, match='must be between 0 and 100'):
            VehicleQueryParams(battery_health_min=-1.0)

    def test_battery_health_max_over_hundred(self):
        """Battery health over 100 should fail."""
        with pytest.raises(ValueError, match='must be between 0 and 100'):
            VehicleQueryParams(battery_health_max=101.0)

    def test_battery_health_min_greater_than_max(self):
        """Min greater than max should fail."""
        with pytest.raises(ValueError, match='cannot be greater than battery_health_max'):
            VehicleQueryParams(battery_health_min=90.0, battery_health_max=80.0)

    def test_battery_health_integer_values(self):
        """Integer values should work (auto-converted to float)."""
        params = VehicleQueryParams(battery_health_min=80, battery_health_max=90)
        assert params.battery_health_min == 80.0
        assert params.battery_health_max == 90.0


class TestVehicleQueryParamsOdometer:
    """Test odometer_km parameter validation."""

    def test_odometer_min_valid(self):
        """Valid min odometer should work."""
        params = VehicleQueryParams(odometer_km_min=50000)
        assert params.odometer_km_min == 50000

    def test_odometer_max_valid(self):
        """Valid max odometer should work."""
        params = VehicleQueryParams(odometer_km_max=100000)
        assert params.odometer_km_max == 100000

    def test_odometer_range(self):
        """Odometer range should work."""
        params = VehicleQueryParams(odometer_km_min=50000, odometer_km_max=100000)
        assert params.odometer_km_min == 50000
        assert params.odometer_km_max == 100000

    def test_odometer_none_allowed(self):
        """None odometer should be allowed."""
        params = VehicleQueryParams(odometer_km_min=None, odometer_km_max=None)
        assert params.odometer_km_min is None
        assert params.odometer_km_max is None

    def test_odometer_boundary_zero(self):
        """Boundary value 0 should work."""
        params = VehicleQueryParams(odometer_km_min=0)
        assert params.odometer_km_min == 0

    def test_odometer_large_value(self):
        """Large odometer value should work."""
        params = VehicleQueryParams(odometer_km_max=999999)
        assert params.odometer_km_max == 999999

    def test_odometer_max_boundary_10_million(self):
        """Boundary value 10,000,000 km should work."""
        params = VehicleQueryParams(odometer_km_max=10_000_000)
        assert params.odometer_km_max == 10_000_000

    def test_odometer_exceeds_10_million(self):
        """Odometer over 10 million km should fail."""
        with pytest.raises(ValueError, match='less than or equal to 10000000'):
            VehicleQueryParams(odometer_km_min=10_000_001)

    def test_odometer_absurd_value_rejected(self):
        """Absurdly high odometer value should fail."""
        with pytest.raises(ValueError, match='less than or equal to 10000000'):
            VehicleQueryParams(odometer_km_max=999_999_999)

    def test_odometer_min_negative(self):
        """Negative odometer should fail."""
        with pytest.raises(ValueError, match='greater than or equal to 0'):
            VehicleQueryParams(odometer_km_min=-1)

    def test_odometer_min_greater_than_max(self):
        """Min greater than max should fail."""
        with pytest.raises(ValueError, match='cannot be greater than odometer_km_max'):
            VehicleQueryParams(odometer_km_min=100000, odometer_km_max=50000)


class TestVehicleQueryParamsCombinations:
    """Test combinations of multiple parameters."""

    def test_all_parameters_together(self):
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

    def test_partial_parameters(self):
        """Partial parameters should work."""
        params = VehicleQueryParams(vehicle_id='*78', battery_health_min=85.0)
        assert params.vehicle_id == '*78'
        assert params.battery_health_min == 85.0
        assert params.timestamp_start is None
        assert params.odometer_km_max is None

    def test_no_parameters(self):
        """No parameters should create valid empty query."""
        params = VehicleQueryParams()
        assert params.vehicle_id is None
        assert params.timestamp_start is None
        assert params.battery_health_min is None
        assert params.odometer_km_min is None


class TestQueryMetadata:
    """Test QueryMetadata model."""

    def test_query_metadata_success(self):
        """Successful query metadata should work."""
        metadata = QueryMetadata(record_count=42, execution_time_ms=123.45, query_success=True, error_message=None)
        assert metadata.record_count == 42
        assert metadata.execution_time_ms == 123.45
        assert metadata.query_success is True
        assert metadata.error_message is None

    def test_query_metadata_failure(self):
        """Failed query metadata should work."""
        metadata = QueryMetadata(
            record_count=0, execution_time_ms=50.0, query_success=False, error_message='Database connection failed'
        )
        assert metadata.record_count == 0
        assert metadata.execution_time_ms == 50.0
        assert metadata.query_success is False
        assert metadata.error_message == 'Database connection failed'

    def test_query_metadata_negative_count(self):
        """Negative record count should fail."""
        with pytest.raises(ValueError):
            QueryMetadata(record_count=-1, execution_time_ms=100.0, query_success=True)

    def test_query_metadata_negative_time(self):
        """Negative execution time should fail."""
        with pytest.raises(ValueError):
            QueryMetadata(record_count=10, execution_time_ms=-1.0, query_success=True)

    def test_query_metadata_zero_values(self):
        """Zero values should work."""
        metadata = QueryMetadata(record_count=0, execution_time_ms=0.0, query_success=True)
        assert metadata.record_count == 0
        assert metadata.execution_time_ms == 0.0
