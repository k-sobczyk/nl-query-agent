"""Tool for querying vehicle telemetry data with LLM function calling."""

from pydantic import ValidationError

from app.ai.common.models import VehicleQueryParams
from app.ai.utils.query_builder import execute_query


def _error_response(message: str) -> dict:
    """Build standardized error response."""
    return {
        'success': False,
        'record_count': 0,
        'execution_time_ms': 0.0,
        'error_message': message,
        'output_file': None,
    }


def query_vehicle_data(
    vehicle_id: str | None = None,
    timestamp_start: str | None = None,
    timestamp_end: str | None = None,
    battery_health_min: float | None = None,
    battery_health_max: float | None = None,
    odometer_km_min: int | None = None,
    odometer_km_max: int | None = None,
) -> dict:
    """Query vehicle telemetry data with optional filters."""
    try:
        params = VehicleQueryParams(
            vehicle_id=vehicle_id,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            battery_health_min=battery_health_min,
            battery_health_max=battery_health_max,
            odometer_km_min=odometer_km_min,
            odometer_km_max=odometer_km_max,
        )
        metadata = execute_query(params)
        return metadata.model_dump()

    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = ' -> '.join(str(loc) for loc in error['loc'])
            error_messages.append(f'{field}: {error["msg"]}')
        return _error_response(f'Validation error: {"; ".join(error_messages)}')

    except Exception as e:
        return _error_response(f'Unexpected error: {str(e)}')
