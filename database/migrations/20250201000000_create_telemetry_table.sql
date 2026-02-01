-- Create telemetry table for vehicle data
CREATE TABLE IF NOT EXISTS public.telemetry (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    battery_health_percent DOUBLE PRECISION NOT NULL,
    odometer_km INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for query performance
CREATE INDEX IF NOT EXISTS idx_telemetry_vehicle_id
    ON public.telemetry(vehicle_id);

CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
    ON public.telemetry(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_telemetry_battery_health
    ON public.telemetry(battery_health_percent);

CREATE INDEX IF NOT EXISTS idx_telemetry_vehicle_timestamp
    ON public.telemetry(vehicle_id, timestamp DESC);

-- Add constraints
ALTER TABLE public.telemetry
    ADD CONSTRAINT chk_battery_health
    CHECK (battery_health_percent >= 0 AND battery_health_percent <= 100);

ALTER TABLE public.telemetry
    ADD CONSTRAINT chk_odometer
    CHECK (odometer_km >= 0);

-- Prevent duplicate telemetry readings for same vehicle at same time
ALTER TABLE public.telemetry
    ADD CONSTRAINT uq_vehicle_timestamp
    UNIQUE (vehicle_id, timestamp);

-- Add comments for documentation
COMMENT ON TABLE public.telemetry IS 'Vehicle telemetry data including battery health and odometer readings';
COMMENT ON COLUMN public.telemetry.vehicle_id IS 'Unique vehicle identifier (e.g., CAR001DPBHSA, VIN0466HID25)';
COMMENT ON COLUMN public.telemetry.timestamp IS 'Timestamp of telemetry reading in UTC';
COMMENT ON COLUMN public.telemetry.battery_health_percent IS 'Battery health as percentage (0-100)';
COMMENT ON COLUMN public.telemetry.odometer_km IS 'Odometer reading in kilometers';
