"""Utilities for converting safe wildcard patterns to SQL patterns."""


def wildcard_to_sql_like(pattern: str | None) -> tuple[str, str] | None:
    """Convert wildcard pattern (* syntax) to SQL LIKE pattern."""
    if pattern is None:
        return None

    if '*' not in pattern:
        return ('=', pattern)

    return ('LIKE', pattern.replace('*', '%'))
