"""Tests for pattern_converter utilities."""

from app.ai.utils.pattern_converter import wildcard_to_sql_like


def test_none_pattern_returns_none():
    """None input returns None."""
    assert wildcard_to_sql_like(None) is None


def test_exact_match_no_wildcards():
    """Pattern without wildcards uses exact match operator."""
    result = wildcard_to_sql_like('VIN123')
    assert result is not None
    operator, pattern = result
    assert operator == '='
    assert pattern == 'VIN123'


def test_starts_with_pattern():
    """Pattern ending with * uses LIKE with trailing %."""
    result = wildcard_to_sql_like('VVA1*')
    assert result is not None
    operator, pattern = result
    assert operator == 'LIKE'
    assert pattern == 'VVA1%'


def test_ends_with_pattern():
    """Pattern starting with * uses LIKE with leading %."""
    result = wildcard_to_sql_like('*78')
    assert result is not None
    operator, pattern = result
    assert operator == 'LIKE'
    assert pattern == '%78'


def test_contains_pattern():
    """Pattern with wildcards on both sides uses LIKE with % on both sides."""
    result = wildcard_to_sql_like('*ABC*')
    assert result is not None
    operator, pattern = result
    assert operator == 'LIKE'
    assert pattern == '%ABC%'


def test_multiple_wildcards():
    """Pattern with multiple * converts all to %."""
    result = wildcard_to_sql_like('A*B*C')
    assert result is not None
    operator, pattern = result
    assert operator == 'LIKE'
    assert pattern == 'A%B%C'


def test_alphanumeric_with_hyphens():
    """Pattern with hyphens is preserved."""
    result = wildcard_to_sql_like('VIN-123-*')
    assert result is not None
    operator, pattern = result
    assert operator == 'LIKE'
    assert pattern == 'VIN-123-%'


def test_alphanumeric_with_underscores():
    """Pattern with underscores is preserved."""
    result = wildcard_to_sql_like('VIN_123_*')
    assert result is not None
    operator, pattern = result
    assert operator == 'LIKE'
    assert pattern == 'VIN_123_%'


def test_single_character_exact():
    """Single character without wildcard uses exact match."""
    result = wildcard_to_sql_like('A')
    assert result is not None
    operator, pattern = result
    assert operator == '='
    assert pattern == 'A'


def test_single_character_with_wildcard():
    """Single character with wildcard uses LIKE."""
    result = wildcard_to_sql_like('A*')
    assert result is not None
    operator, pattern = result
    assert operator == 'LIKE'
    assert pattern == 'A%'
