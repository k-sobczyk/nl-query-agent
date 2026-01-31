# Supabase Local Setup Guide

This guide shows how to set up a local Supabase instance using Docker Desktop to replace BigQuery.

## Prerequisites

- Docker Desktop installed and running
- Python 3.13+
- Gemini API key

## Step 1: Install Supabase CLI

```bash
# Using npm (if you have Node.js)
npm install -g supabase

# Or using Homebrew (macOS/Linux)
brew install supabase/tap/supabase

# Or download binary from: https://github.com/supabase/cli/releases
```

## Step 2: Start Supabase Locally

```bash
# Initialize Supabase in your project (first time only)
supabase init

# Start local Supabase services (PostgreSQL, Auth, Storage, etc.)
supabase start
```

This will start PostgreSQL on port **54322** (not the standard 5432).

You'll see output like:
```
API URL: http://localhost:54321
DB URL: postgresql://postgres:postgres@localhost:54322/postgres
Studio URL: http://localhost:54323
```

## Step 3: Create Database Table

1. Open Supabase Studio at http://localhost:54323
2. Go to SQL Editor
3. Run this SQL to create the telemetry table:

```sql
CREATE TABLE IF NOT EXISTS public.telemetry (
    vehicle_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    battery_health_percent DOUBLE PRECISION,
    odometer_km INTEGER,
    PRIMARY KEY (vehicle_id, timestamp)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_telemetry_battery
    ON public.telemetry(battery_health_percent);

CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp
    ON public.telemetry(timestamp);

CREATE INDEX IF NOT EXISTS idx_telemetry_vehicle_id
    ON public.telemetry(vehicle_id);
```

## Step 4: Load Sample Data

You can insert sample data directly via SQL:

```sql
INSERT INTO public.telemetry (vehicle_id, timestamp, battery_health_percent, odometer_km)
VALUES
    ('CAR001DPBHSA', '2024-11-20T09:00:00Z', 77.4, 115326),
    ('VEH010OC6UZH', '2024-11-15T23:00:00Z', 82.3, 49916),
    ('VVA1ABC123', '2024-11-21T10:30:00Z', 65.2, 200000),
    ('VVA1DEF456', '2024-11-21T14:00:00Z', 90.1, 45000);
```

Or import from your existing JSON file using a Python script.

## Step 5: Configure Environment Variables

Create a `.env` file in your project root:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
GEMINI_API_KEY=your_actual_gemini_api_key

# Supabase Local Connection
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
```

## Step 6: Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

## Step 7: Run the Agent

```bash
python -m app.main
```

## Supabase Commands Reference

```bash
# Start local Supabase
supabase start

# Stop local Supabase
supabase stop

# Check status
supabase status

# Access PostgreSQL directly
psql postgresql://postgres:postgres@localhost:54322/postgres

# View logs
supabase logs
```

## Accessing Supabase Studio

- **URL**: http://localhost:54323
- **Use Case**: Visual database management, SQL editor, table viewer
- **Features**:
  - Table editor (view/edit data)
  - SQL editor (run queries)
  - API documentation
  - Database schema viewer

## Connection Details

| Parameter | Value |
|-----------|-------|
| Host | localhost |
| Port | 54322 |
| Database | postgres |
| User | postgres |
| Password | postgres |

## Troubleshooting

### Port Already in Use
If port 54322 is already in use:
```bash
supabase stop
supabase start
```

### Can't Connect to Database
1. Ensure Docker Desktop is running
2. Check Supabase status: `supabase status`
3. Verify connection in Studio: http://localhost:54323

### Data Not Persisting
Supabase local data is stored in Docker volumes. To reset:
```bash
supabase db reset
```

## Production Deployment (Optional)

To deploy to Supabase Cloud (not needed for this POC):

```bash
# Link to your Supabase project
supabase link --project-ref your-project-ref

# Push migrations
supabase db push
```

Then update `DATABASE_URL` in `.env` to your production connection string.

## Performance Comparison

| Feature | BigQuery | Supabase Local |
|---------|----------|----------------|
| Setup | Complex (GCP account) | Simple (Docker) |
| Cost | Pay per query | Free locally |
| Speed | Very fast (cloud) | Fast (local) |
| Scalability | Petabyte | Gigabyte (local) |
| Development | Requires internet | Works offline |

For this POC with ~150 rows, Supabase local is perfect!
