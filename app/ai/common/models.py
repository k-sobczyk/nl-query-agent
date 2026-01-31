"""Pydantic models for function calling validation and structured data extraction."""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class VehicleQueryParams(BaseModel):
    """Parameters for querying vehicle telemetry data."""

    vehicle_id: str | None = Field(
        None,
        description=(
            'Vehicle ID filter. Supports: '
            'exact match (e.g., "VIN123"), '
            'prefix with * (e.g., "VVA1*"), '
            'suffix with * (e.g., "*78"), '
            'contains with * (e.g., "*ABC*")'
        ),
    )

    timestamp_start: str | None = Field(
        None,
        description='Start timestamp in format YYYY-MM-DD-HH (e.g., 2024-11-21-15)',
    )

    timestamp_end: str | None = Field(
        None,
        description='End timestamp in format YYYY-MM-DD-HH (e.g., 2024-11-21-23)',
    )

    battery_health_min: float | None = Field(
        None,
        description='Minimum battery health percentage (0-100)',
    )

    battery_health_max: float | None = Field(
        None,
        description='Maximum battery health percentage (0-100)',
    )

    odometer_km_min: int | None = Field(
        None,
        ge=0,
        le=10_000_000,
        description='Minimum odometer reading in kilometers (0-10,000,000)',
    )

    odometer_km_max: int | None = Field(
        None,
        ge=0,
        le=10_000_000,
        description='Maximum odometer reading in kilometers (0-10,000,000)',
    )

    @field_validator('vehicle_id')
    @classmethod
    def validate_vehicle_id(cls, value: str | None) -> str | None:
        """Validate vehicle_id is safe and within reasonable length.

        Supports safe wildcard patterns using * instead of arbitrary regex:
        - Exact match: "VIN123"
        - Starts with: "VVA1*"
        - Ends with: "*78"
        - Contains: "*ABC*"
        """
        if value is None:
            return value

        # Length limit to prevent ReDoS and resource exhaustion
        if len(value) > 100:
            raise ValueError('vehicle_id pattern cannot exceed 100 characters')

        # Only allow alphanumeric characters, hyphens, underscores, and wildcards
        # This prevents regex special characters that could cause ReDoS
        allowed_pattern = r'^[A-Za-z0-9\-_*]+$'
        if not re.match(allowed_pattern, value):
            raise ValueError('vehicle_id can only contain letters, numbers, hyphens, underscores, and wildcards (*)')

        # Limit wildcard usage to prevent abuse
        if value.count('*') > 2:
            raise ValueError('vehicle_id pattern cannot contain more than 2 wildcards')

        # Prevent patterns that are just wildcards (too broad)
        if value.strip('*') == '':
            raise ValueError('vehicle_id pattern must contain at least one non-wildcard character')

        return value

    @field_validator('timestamp_start', 'timestamp_end')
    @classmethod
    def validate_timestamp_format(cls, value: str | None) -> str | None:
        """Validate timestamp is in YYYY-MM-DD-HH format."""
        if value is None:
            return value

        pattern = r'^\d{4}-\d{2}-\d{2}-\d{2}$'
        if not re.match(pattern, value):
            raise ValueError(f'Timestamp must be in format YYYY-MM-DD-HH (e.g., 2024-11-21-15), got: {value}')

        # Validate that it's a valid date/time
        try:
            year, month, day, hour = value.split('-')
            datetime(int(year), int(month), int(day), int(hour))
        except ValueError as e:
            raise ValueError(f'Invalid timestamp values: {value}. Error: {e}') from e

        return value

    @field_validator('battery_health_min', 'battery_health_max')
    @classmethod
    def validate_battery_health(cls, value: float | None) -> float | None:
        """Validate battery health percentage is within valid range."""
        if value is not None and not 0.0 <= value <= 100.0:
            raise ValueError(f'Battery health must be between 0 and 100, got: {value}')
        return value

    @field_validator('odometer_km_min', 'odometer_km_max')
    @classmethod
    def validate_odometer(cls, value: int | None) -> int | None:
        """Validate odometer reading is within realistic range."""
        if value is None:
            return value

        if value < 0:
            raise ValueError(f'Odometer reading must be non-negative, got: {value}')

        if value > 10_000_000:
            raise ValueError(
                f'Odometer reading cannot exceed 10,000,000 km (got: {value:,}). '
                'This limit prevents data entry errors and unrealistic values.'
            )

        return value

    def model_post_init(self, __context) -> None:
        """Validate logical consistency of range parameters after model initialization."""
        # Validate battery health range
        if (
            self.battery_health_min is not None
            and self.battery_health_max is not None
            and self.battery_health_min > self.battery_health_max
        ):
            raise ValueError(
                f'battery_health_min ({self.battery_health_min}) '
                f'cannot be greater than battery_health_max ({self.battery_health_max})'
            )

        # Validate odometer range
        if (
            self.odometer_km_min is not None
            and self.odometer_km_max is not None
            and self.odometer_km_min > self.odometer_km_max
        ):
            raise ValueError(
                f'odometer_km_min ({self.odometer_km_min}) '
                f'cannot be greater than odometer_km_max ({self.odometer_km_max})'
            )

        # Validate timestamp range
        if self.timestamp_start is not None and self.timestamp_end is not None:
            start = datetime.strptime(self.timestamp_start, '%Y-%m-%d-%H')
            end = datetime.strptime(self.timestamp_end, '%Y-%m-%d-%H')
            if start > end:
                raise ValueError(
                    f'timestamp_start ({self.timestamp_start}) cannot be after timestamp_end ({self.timestamp_end})'
                )


class QueryMetadata(BaseModel):
    """Metadata about query execution results."""

    record_count: int = Field(..., ge=0, description='Number of matching records')
    execution_time_ms: float = Field(..., ge=0.0, description='Execution time in milliseconds')
    query_success: bool = Field(..., description='Query execution status')
    error_message: str | None = Field(None, description='Error message if query failed')
