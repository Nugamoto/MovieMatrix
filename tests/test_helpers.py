import pytest

from helpers import (
    is_valid_username,
    is_valid_year,
    is_valid_rating,
    normalize_rating,
)


@pytest.mark.parametrize("name,expected", [
    ("JohnDoe", True),
    ("", False),
    ("   ", False),
    ("###", False),
    ("1234", False),
    ("valid_user123", True),
])
def test_is_valid_username(name, expected):
    """Test is_valid_username with various valid and invalid inputs."""
    assert is_valid_username(name) is expected


@pytest.mark.parametrize("year_str,expected", [
    ("1999", True),
    ("2025", True),
    ("1877", False),
    ("2101", False),
    ("abcd", False),
    ("", False),
])
def test_is_valid_year(year_str, expected):
    """Test is_valid_year for valid format and reasonable range."""
    assert is_valid_year(year_str) is expected


@pytest.mark.parametrize("value,expected", [
    ("0", True),
    ("5", True),
    ("9.9", True),
    ("10.0", True),
    ("10.1", False),
    ("-1", False),
    ("abc", False),
    ("", False),
])
def test_is_valid_rating(value, expected):
    """Test is_valid_rating for numeric input and allowed range."""
    assert is_valid_rating(value) is expected


@pytest.mark.parametrize("value,expected", [
    ("5.567", 5.6),
    ("8.94", 8.9),
    ("0", 0.0),
    ("10", 10.0),
])
def test_normalize_rating(value, expected):
    """Test normalize_rating rounds input to 1 decimal place as float."""
    assert normalize_rating(value) == expected
