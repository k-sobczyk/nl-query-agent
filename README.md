**WRITTEN BY HUMAN**

# Project goal and assumtions.
Creating and natural language interface for vehicle telemetry data using LLM-powered query parsing.

This project implements a natural language interface for querying vehicle telemetry data using LLM-powered query parsing. Instead of writing SQL queries or manually filtering data, users can ask questions in plain English and receive structured results.

The system demonstrates a production-minded architecture within a POC scope, with focus on security and scalability.

Project design objectives:
- demonstrating AI/Backend engineering principles without over-engineering,
- this POC reflect production requirements, discussed in this README even when not fully implemented,
- dataset have 150 examples however we assume this is just an example and we build the solution that could handle milions of rows.
- Safety first - no LLM separated from data source, no raw company/customer data exposure to the LLM
- priorytet bezpieczeństwa i skalowności (symulowanie warunków produkcyjnych bez faktycznego ich wdrażania)

### Technology Stack

- Language: Python
- Libraries: Google ADK, Google GenAI, Pydantic
- LLM Model: gemini-2.5-flash
- Database: BigQuery
- Development tools: uv, ruff, pyright, pytest, pre-commit hooks

### Installation and how to run

git clone

gcloud auth application-default login (to access GCP servies like Gemini and Bigquery)

make install

docker compose -up d

uv run python scripts/load_data_to_supabase.py

make run

### Project Folder/Files Structure

TODO



### Architecture & Design Decisions

1) Przerzucenie wartości z jsona do bazy SQL.


2) Agent/Google ADK/Pydantic

Query Builder po walidacji z modelu Pydantica -> tutaj używać (np. %s w psycopg2 lub :value w SQLAlchemy), a nie podawać wartości w stringu.

LLM + Function Calling + Pydantic



**Pydantic for structured outputs** ensures:
- LLM responses match expected schema before database operations
- Early error detection and clear error messages
- Clean integration between LLM outputs and application logic
- Self-documenting code through type annotations

2) Gemini as a LLM

Model musi znać aktualną datę

Feedback Loop do modelu jeśli użytkownik zapytałby o coś innego lub podałby złe parametry.
- "No vehicles match your criteria. Try adjusting the battery health threshold."
- "I couldn't understand your query. Please try: 'Show vehicles with battery health below X%'"
- System asks clarifying questions via feedback loop

- **Cost-effectiveness**
- **Native ADK integration**
- **Good for fast development**
- **I just like it more than e.g Langchain**

3) BigQuery

Czemu relacyjna a nie NOSQL, czemu postgres a nie SQLLite?

Co jeśli baza nic nie zwróci?

Co jeśli baza zwróci 10 milionów rekordów? (hardcoded LIMIT)
- Limitowanie (Guardrails)
- Obsługa braku danych - brak wyników dla podanych filtrów. LLM wtedy grzecznie odpowie użytkownikowi, zamiast zmyślać (halucynować) dane.

Natomiast jeśli te dane są to ja nie chce ich wrzucać do LLM'a, dane nie powinny do niego trafiać ale informacja o tym jak przebiegło query, ile trawało ile rekordów zwróciło juz moze

natomiast same dane z bazy mają nie trafiać do LLM'a

Other:
- The LLM never generates SQL directly. Instead, it calls typed functions with validated parameters. The application then builds parameterized queries using safe methods (e.g., `%s` in psycopg2 or `:value` in SQLAlchemy).

- Separation:
  - LLM: Interprets user intent and extracts query parameters
  - Application: Builds and executes safe database queries
  - This clear boundary prevents the LLM from accessing or manipulating the database directly

- Only query metadata (execution time, result count, error status) is sent back to the LLM for response generation. Raw customer data never leaves the secure application boundary. (it will be shown in other way but i dont know which one yet)



### Security Principles

**LLM + Function Calling Pattern**:
The LLM receives the user's query and the current date context. It responds by calling a predefined function with typed parameters (e.g., `battery_health_threshold: float`). The application validates these parameters through Pydantic models before constructing database queries.

**Parameterized Query Construction**:
All database queries use BigQuery's parameterized query system (`@parameter_name` syntax with `QueryJobConfig`) rather than string interpolation. This prevents SQL injection even if the LLM were somehow compromised or manipulated.

```python
from google.cloud import bigquery

query = """
    SELECT * FROM `project.dataset.telemetry`
    WHERE battery_health_percent < @threshold
"""
job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("threshold", "FLOAT64", 85.0)
    ]
)
```

**No Raw SQL from LLM**:
The LLM never sees SQL syntax or generates SQL code. It only extracts structured parameters from natural language, which the application then uses with predefined query templates.

**Data Privacy Boundary**:
Raw vehicle data never reaches the LLM. After query execution, only metadata (record count, execution status, aggregate statistics if applicable) is sent to the LLM for response formatting. This protects customer privacy and reduces token costs.

### Scalability Considerations

**BigQuery Rationale**:
BigQuery is purpose-built for analytical queries at scale:
- Serverless architecture eliminates infrastructure management (no servers, no clusters, no capacity planning)
- Petabyte-scale capabilities: same queries work on 150 rows or 150 billion rows
- Columnar storage optimized for analytical workloads (filtering, aggregations, analytics)
- Automatic query optimization and execution planning
- Built-in partitioning and clustering for performance

**Cloud-Native Benefits**:
- Pay-per-query pricing aligns costs with actual usage (free tier covers POC needs)
- Auto-scaling handles concurrent queries without manual configuration
- Native integration with Google ADK ecosystem
- No connection pooling needed - BigQuery manages resources automatically

**Designed for Production Scale**:
The code leverages BigQuery's native scalability. Queries include LIMIT clauses for result management, but BigQuery efficiently handles filtering billions of rows before returning results. Pagination and result streaming are built into the BigQuery client library.

### User Experience

**Current Date Context**:
The LLM receives the current date with each request, enabling temporal queries like "vehicles from the last 30 days" without requiring users to calculate dates.

**Feedback Loop**:
When the LLM cannot confidently parse a query, it asks clarifying questions:
- "Did you mean battery health below 85%?"
- "Should I filter by the last 30 calendar days or 30 days from today?"

**Query Variation Handling**:
Prompt engineering enables the LLM to handle natural variations:
- "low battery" → battery_health_percent < 85
- "battery under 80%" → battery_health_percent < 80
- "bad battery health" → battery_health_percent < 85

### Guardrails & Safety

**Hard LIMIT on Results**:
All queries include a hard-coded LIMIT (e.g., 1000 rows) to prevent accidental massive data transfers. Pagination is required for larger result sets.

**Empty Result Handling**:
When the database returns no rows, the application explicitly tells the LLM "0 results found" rather than letting it hallucinate data. The LLM then generates helpful messages like "No vehicles match your criteria."

**Error Handling**:
Database errors (connection failures, syntax errors in constructed queries, constraint violations) are caught and logged. The LLM receives generic error status, not technical details that could leak schema information.


### Road to Production

- Rate Limited
- Circuit Breaker
- Kolejka (?)
- Logowanie danych i zapis użytkowania aplikacji
- Cacheowanie (Redis)


**Rate Limiting**:
Protects against abuse and controls LLM API costs. Implemented per-user or per-IP, with different tiers for authenticated vs anonymous users. Prevents runaway costs from automated query attacks.

**Circuit Breaker**:
Handles LLM API failures gracefully. When Gemini API returns errors above a threshold (e.g., 50% error rate over 1 minute), the circuit opens and requests fail fast with cached responses or degraded service rather than cascading failures.

**Health Checks & Monitoring**:
Endpoints for readiness and liveness probes. Monitors database connection health, LLM API availability, and query performance. Integrates with orchestration platforms (Kubernetes, ECS) for automatic recovery.

### Performance & Scaling

**Caching Layer (Redis)**:
Caches LLM responses for identical or semantically similar queries. Reduces API calls for common questions like "show low battery vehicles", cutting costs by 60-80%. Cache invalidation on data updates ensures freshness.

**Query Result Pagination**:
Large result sets are paginated using BigQuery's built-in pagination support. The BigQuery client library handles result streaming efficiently, preventing memory exhaustion even for queries returning millions of rows.

**BigQuery Quota Management**:
Monitor and manage BigQuery quotas (concurrent queries, slots allocation) to prevent throttling under high load. Use reservation-based pricing for predictable costs at scale. Implement query complexity limits to prevent runaway resource consumption.

### Operations & Observability

**Structured Logging**:
JSON-formatted logs capture query patterns, LLM response times, database query performance, and error conditions. Enables analysis of popular query types, optimization opportunities, and user behavior patterns.

**Usage Tracking**:
Records per-query metrics: LLM tokens consumed, database query time, cache hit/miss, result count. Enables cost attribution by user/team and identifies optimization targets (e.g., expensive queries to cache).

**Error Tracking & Alerting**:
Integrates with error tracking services (Sentry, Rollbar). Alerts on elevated error rates, slow queries, or LLM API degradation. Proactive issue detection before users experience widespread failures.

### Security Hardening

**API Authentication & Authorization**:
JWT-based authentication for API access. Role-based access control (RBAC) for different user types. Some users may only query certain vehicle fleets or time ranges.

**Input Validation & Sanitization**:
While the current architecture already prevents SQL injection, production systems add defense-in-depth: maximum query length limits, rate limiting per user, content filtering for abusive queries.

**Audit Logging**:
Immutable audit trail of all queries: who asked what, when, and what data was accessed. Supports compliance requirements (GDPR, SOC2) and forensic investigation of data breaches or misuse.


### Future improvements ideas

1) Możliwość analizy danych.

2) FrondEnd / MCP server (aby korzystac z funkcjonalności claude desktop jako frontu)

**Multi-Source Data Integration**:
Extend beyond vehicle telemetry to maintenance records, driver behavior data, and route history. BigQuery's native support for federated queries and external data sources enables seamless integration with Cloud Storage, Google Sheets, or other BigQuery datasets. Natural language interface: "Show vehicles with low battery health that also have high maintenance costs in the last quarter."

**Advanced Query Capabilities**:
Support aggregations and analytics through natural language: "What's the average battery health by vehicle age?" or "Show battery degradation trends over the last 6 months." BigQuery's analytical SQL capabilities (window functions, aggregations, statistical functions) enable complex analyses while maintaining natural language simplicity.

**BigQuery ML Integration**:
Leverage BigQuery ML for predictive analytics without moving data. Train models directly in BigQuery: "Predict which vehicles will need battery replacement in the next 6 months." Enable natural language queries that trigger ML predictions: "Show vehicles at high risk of battery failure." This transforms the system from reactive querying to proactive intelligence.

**Enhanced User Experience**:
Implement query suggestions based on BigQuery INFORMATION_SCHEMA for schema awareness. Add result visualization: charts for trends, graphs for distributions, maps for geospatial data. Provide query history and saved queries. Export capabilities leveraging BigQuery's native export to CSV, JSON, or Google Sheets.

**Intelligence Layer**:
Learn from query patterns to optimize performance. Implement proactive alerts using BigQuery scheduled queries: "Alert me when battery health drops below 80% for any vehicle." Use BigQuery's materialized views to pre-compute common aggregations. Natural language explanations of results and trends transform raw data into actionable insights.

**Integration Possibilities**:
MCP server for Claude Desktop enabling conversational data exploration. REST API leveraging Cloud Functions with BigQuery backend. Webhook support using Cloud Pub/Sub for automated reporting workflows triggered by data events or scheduled queries.

Switch To OpenRouter


Application level caching (lru_cache?)
Prompt caching to speed it up?

Subapase instead of bigquery?
Test coverage
unit tests
etc.
docs strings
Data and loggs from the app
create a sync/async api or even MCP for it


===

**AI GENERATED SUMMARY OF THE WORK THAT WAS DONE (verified by human)**

**Example Query:**
```
"Show me all vehicles with battery health below 85%"
```

**Example data:**
```json
{
  "vehicle_id": "CAR001DPBHSA",
  "timestamp": "2024-11-20T09:00:00Z",
  "battery_health_percent": 77.4,
  "odometer_km": 115326
},
{
  "vehicle_id": "VEH010OC6UZH",
  "timestamp": "2024-11-15T23:00:00Z",
  "battery_health_percent": 82.3,
  "odometer_km": 49916
}
```
