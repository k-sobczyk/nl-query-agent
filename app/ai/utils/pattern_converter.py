"""Utilities for converting safe wildcard patterns to SQL patterns."""


def wildcard_to_sql_like(pattern: str | None) -> tuple[str, str] | None:
    """Convert safe wildcard pattern to SQL LIKE pattern and operator.

    Converts user-friendly wildcard patterns (* for wildcard) into safe SQL LIKE patterns.
    This prevents ReDoS attacks while supporting common use cases.

    Supported patterns:
        - Exact match: "VIN123" → ("=", "VIN123")
        - Starts with: "VVA1*" → ("LIKE", "VVA1%")
        - Ends with: "*78" → ("LIKE", "%78")
        - Contains: "*ABC*" → ("LIKE", "%ABC%")

    Args:
        pattern: User pattern with * wildcards (already validated by Pydantic).

    Returns:
        Tuple of (operator, sql_pattern) for SQL query, or None if pattern is None.
        operator: Either "=" for exact match or "LIKE" for pattern matching.
        sql_pattern: Pattern string with SQL wildcards (%) instead of *.

    Examples:
        >>> wildcard_to_sql_like('VIN123')
        ("=", "VIN123")

        >>> wildcard_to_sql_like('VVA1*')
        ("LIKE", "VVA1%")

        >>> wildcard_to_sql_like('*78')
        ("LIKE", "%78")

        >>> wildcard_to_sql_like('*ABC*')
        ("LIKE", "%ABC%")

        >>> wildcard_to_sql_like(None)
        None
    """
    if pattern is None:
        return None

    # If no wildcards, use exact match
    if '*' not in pattern:
        return ('=', pattern)

    # Convert * to SQL % wildcard
    sql_pattern = pattern.replace('*', '%')

    return ('LIKE', sql_pattern)


def wildcard_to_bigquery_regexp(pattern: str | None) -> str | None:
    """Convert safe wildcard pattern to BigQuery REGEXP pattern.

    Alternative to LIKE for BigQuery if needed. Uses anchored regex for safety.

    Args:
        pattern: User pattern with * wildcards (already validated by Pydantic).

    Returns:
        BigQuery REGEXP pattern string, or None if pattern is None.

    Examples:
        >>> wildcard_to_bigquery_regexp('VIN123')
        "^VIN123$"

        >>> wildcard_to_bigquery_regexp('VVA1*')
        "^VVA1.*$"

        >>> wildcard_to_bigquery_regexp('*78')
        "^.*78$"
    """
    if pattern is None:
        return None

    # Escape special regex characters (except *)
    # Since we already validated only alphanumeric + * + - + _, we just need to escape -
    escaped = pattern.replace('-', r'\-')

    # Convert * to .* (match any characters)
    regexp = escaped.replace('*', '.*')

    # Anchor to prevent catastrophic backtracking
    return f'^{regexp}$'
