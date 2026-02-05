# Natural Language Query Agent

**Privacy-first AI-to-database interface using Claude function calling**

Convert natural language questions into safe database queries without exposing customer data to LLMs. This project demonstrates a production-ready architecture for integrating AI with databases through structured function calling rather than SQL generation.

```bash
You: "Show vehicles with battery below 85%"
Agent: Found 12 vehicles matching your criteria
       Results saved to: data/query_results_20240215_143022.csv
```

**Tech Stack:** Claude Sonnet 4.5 • PostgreSQL • Pydantic

**Key Innovation:** The LLM never sees customer data or generates SQL—only structured parameters pass through validation layers to build safe parameterized queries.

## Use Cases

This architecture is adaptable to any domain requiring natural language data access:

- **Vehicle Telemetry** (implemented): Battery health, odometer readings, maintenance schedules
- **E-commerce Analytics**: Order history, customer behavior, inventory queries
- **Healthcare Records**: Patient data, appointment scheduling, medical history (HIPAA-compliant with proper access controls)
- **Financial Data**: Transaction history, account balances, fraud detection
- **IoT Monitoring**: Sensor readings, device status, anomaly detection

The pattern is the same: define your Pydantic models → build safe queries → keep customer data isolated from the LLM.

---

## Table of Contents

- [Use Cases](#use-cases)
- [Quick Start](#quick-start)
- [Architecture & Design Decisions](#architecture--design-decisions)
  - [LLM Function Calling](#llm-function-calling)
  - [Technology Choices](#technology-choices)
  - [Data Privacy Boundary](#data-privacy-boundary)
- [Key Features (Implemented)](#key-features-implemented)
- [Production Considerations](#production-considerations)
  - [Security](#security)
  - [Scalability](#scalability)
  - [Reliability](#reliability)
  - [Observability](#observability)
- [Technical Stack](#technical-stack)
- [Development Commands](#development-commands)
- [Why This Architecture?](#why-this-architecture)
- [Future Enhancements](#future-enhancements)

---

## Quick Start

**Prerequisites:** Docker, Python 3.13+, Anthropic API key

```bash
# 1. Clone and configure
git clone <repository-url>
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# 2. Install dependencies
make install

# 3. Start database
docker compose up -d

# 4. Load sample data
uv run python scripts/load_data_to_database.py

# 5. Run the agent
make run
```

---

## Architecture & Design Decisions

### LLM Function Calling

The LLM **never generates SQL** or sees customer data. Instead:

1. **LLM Role:** Extracts structured parameters from natural language
2. **Application Role:** Builds safe parameterized queries using validated parameters
3. **Data Boundary:** Only query metadata (count, execution time) returns to LLM


### Technology Choices

| Choice | Rationale |
|--------|-----------|
| **Claude Sonnet 4.5** | Superior function calling |
| **PostgreSQL** | Production-scale database with indexes, constraints, and query optimization (designed for millions of rows, not just 150 examples as per data sample) |
| **Pydantic** | Type-safe validation layer between LLM outputs and database operations, catches errors before query execution |
| **Parameterized Queries** | SQL injection prevention through psycopg2's `%(param)s` syntax, never string interpolation |

### Data Privacy Boundary

**Raw vehicle data never reaches the LLM:**
- Query results export to timestamped CSV files (`data/query_results_*.csv`)
- LLM receives only metadata for response generation
- Protects customer privacy and reduces token costs
- Prevents LLM hallucination on actual data values

---

## Key Features (Implemented)

### Natural Language Understanding
- **Query variations:** "low battery", "battery under 80%", "bad battery health" all work
- **Temporal queries:** "last 30 days", "vehicles from November 2024"
- **Wildcard patterns:** "vehicles starting with VVA1", "IDs ending in 78"
- **Range filters:** "battery between 85% and 95%", "odometer over 50000 km" etc.

### Robust Validation (72 Pydantic Tests)
- Vehicle ID: alphanumeric + patterns, max 2 wildcards, 100 char limit
- Timestamps: format validation (`YYYY-MM-DD-HH`) + datetime parsing
- Battery health: 0-100% range enforcement
- Odometer: 0-10M km range with non-negative constraint
- Range consistency: min ≤ max validation

### Safe Query Execution (16 Query Builder Tests)
- Parameterized PostgreSQL queries via psycopg2
- Hard LIMIT 100 rows (configurable guardrail)
- Wildcard → SQL LIKE pattern conversion (10 pattern tests)
- Comprehensive error handling with generic messages to LLM

### Database Schema
```sql
telemetry (
  id BIGSERIAL PRIMARY KEY,
  vehicle_id TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL,
  battery_health_percent DOUBLE PRECISION CHECK (0-100),
  odometer_km INTEGER CHECK (>=0),
  created_at TIMESTAMPTZ DEFAULT NOW()
)

Indexes: vehicle_id, timestamp DESC, battery_health_percent, (vehicle_id, timestamp) UNIQUE
```

---

## Production Considerations

While this is a POC, the architecture is designed for production scale:

### Security
- **SQL Injection Prevention:** Parameterized queries with type validation
- **Data Privacy:** Customer data isolation from LLM (only metadata exposure)
- **Input Sanitization:** Defense-in-depth validation layers

### Scalability
- **Query Limits:** Hardcoded LIMIT prevents memory exhaustion, enforces pagination pattern
- **Database Indexes:** Optimized for vehicle_id, timestamp, battery_health queries
- **Stateless Design:** Agent can be horizontally scaled across instances
- **Migration Path:** PostgreSQL → BigQuery for petabyte-scale analytics

### Reliability
- **Circuit Breaker:** Graceful LLM API failure handling (fail fast vs cascading failures)
- **Rate Limiting:** Per-user/IP protection against abuse and cost control
- **Health Checks:** Readiness/liveness probes for orchestration platforms
- **Error Recovery:** Generic error messages prevent schema information leakage

### Observability
- **Structured Logging:** JSON logs for query patterns, timings, LLM token usage
- **Usage Tracking:** Per-query metrics (execution time, result count, cache hit/miss)
- **Error Tracking:** Integration points for Sentry/Rollbar monitoring
- **Performance Metrics:** Identify optimization targets (expensive queries to cache)

---

## Technical Stack

**Core Dependencies:**
- Python 3.13+
- Anthropic SDK 0.77.0 (Claude Sonnet 4.5, temperature 0.5)
- psycopg2 2.9.11 (PostgreSQL client)
- Pydantic 2.12.5 (validation)
- PostgreSQL 15-alpine (Docker)

**Development Tools:**
- `uv` - Fast Python package manager
- `ruff` - Format & lint (line-length: 120)
- `pyright` - Type checking
- `pytest` + `coverage` - Testing (98 tests: 72 validation + 16 query builder + 10 pattern)
- `pre-commit` - Git hooks for quality gates

**Project Structure:**
```
app/
├── main.py                      # CLI entry point
└── ai/
    ├── agent/agent.py           # VehicleQueryAgent (Claude + function calling)
    ├── common/
    │   ├── constants.py         # Model config, paths
    │   ├── models.py            # Pydantic validation models
    │   └── prompts.py           # System instructions
    ├── tools/query_tool.py      # query_vehicle_data function
    └── utils/
        ├── pattern_converter.py # Wildcard → SQL LIKE
        └── query_builder.py     # Safe query construction

database/migrations/             # SQL schema
tests/test_ai/                   # Comprehensive test suite
```

Full schema: [database/migrations/20250201000000_create_telemetry_table.sql](database/migrations/20250201000000_create_telemetry_table.sql)

---

## Development Commands

```bash
make install    # Install dependencies via uv
make run        # Start interactive CLI
make test       # Run test suite
make testcov    # Test with coverage report (htmlcov/)
make format     # Format code with ruff
make lint       # Check code style
make typecheck  # Type check with pyright
make all        # Run all checks (format + lint + typecheck + testcov)
```

---

## Why This Architecture?

This design prioritizes production-readiness over prototyping shortcuts:

1. **Security First:** Separating LLM logic from data access prevents SQL injection, data leakage, and prompt injection attacks while maintaining full query capabilities.

2. **Production Patterns:** Parameterized queries, validation layers, error handling, and query limits translate directly to systems handling millions of records—not just proof-of-concepts.

3. **Testability:** Clear separation (LLM → Pydantic → Query Builder → Database) enables comprehensive unit testing (98 tests) without mocking the LLM for every scenario.

4. **Extensibility:** Adding new data sources or query types requires only new Pydantic models and query builders—no architectural changes needed.

---

## Future Enhancements

### Multi-Source Data Integration
- **Structured data sources:** Maintenance records, driver behavior, route history, warranty claims
- **Multimodal data integration:** Vehicle camera images (damage detection), diagnostic audio (engine sounds), sensor time-series (vibration patterns). Claude's native vision capabilities enable queries like: "Show vehicles with battery below 85% AND visible exterior damage from last inspection photos"
- **Cross-source queries:** "Show vehicles with low battery AND high maintenance costs last quarter"
- **Federated queries:** PostgreSQL foreign data wrappers or BigQuery external tables for seamless multi-source joins

### Advanced Analytics
- **Aggregations:** "Average battery health by vehicle age"
- **Trend analysis:** "Battery degradation over last 6 months"
- **Predictive modeling:** BigQuery ML for failure prediction

### UX & Architecture Improvements
- **UI or MCP Server:** Claude Desktop integration for conversational data exploration and nice UI
- **API design:** Sync/async endpoints depending on scale and latency requirements
- **Streaming responses:** Real-time token streaming for better chat-like UX

### Performance & Cost Optimization
- **Caching layer:** Redis for LLM response caching
- **Prompt caching:** Reduce latency and costs for repeated system instructions

### Production Hardening
- **Comprehensive integration tests:** Full LLM call testing with recorded fixtures
- **Rate limiting:** Per-user/IP protection against abuse and cost control
- **Retry strategy:** Exponential backoff with jitter for transient LLM API failures (429 rate limits, 5xx errors)
- **Circuit breaker patterns:** Graceful LLM API failure handling with fast-fail and recovery states
- **Structured logging:** JSON logs with metrics export (query patterns, timings, token usage)
- **Observability stack:** error tracking, monitoring dashboards
