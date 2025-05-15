import pytest

from utils.helpers import (
    is_valid_username,
    is_valid_email,
    is_valid_name,
    passwords_match,
    is_valid_year,
    is_valid_rating,
    normalize_rating,
)


@pytest.mark.parametrize("username,expected", [
    ("JohnDoe", True),
    ("", False),
    ("___", True),
    ("a", False),
    ("veryveryverylongusername_exceeding_limit", False),
])
def test_is_valid_username(username: str, expected: bool):
    """
    Test is_valid_username behavior for various username inputs.

    Verifies that valid usernames (correct length and allowed characters)
    return True, and invalid usernames (empty, too short, too long) return False.
    """
    assert is_valid_username(username) is expected


@pytest.mark.parametrize("email,expected", [
    ("user@example.com", True),
    ("john.doe@mail.co.uk", True),
    ("invalid@", False),
    ("@invalid.com", False),
    ("", False),
])
def test_is_valid_email(email: str, expected: bool):
    """
    Test is_valid_email validation across different email formats.

    Ensures standard emails pass, and malformed or empty strings fail.
    """
    assert is_valid_email(email) is expected


@pytest.mark.parametrize("name,expected", [
    ("Anna", True),
    ("O'Neill", True),
    ("Jean-Luc", True),
    ("", False),
    ("X", False),
    ("$pecial", False),
])
def test_is_valid_name(name: str, expected: bool):
    """
    Test is_valid_name acceptance of valid personal names.

    Checks names with letters, hyphens, apostrophes are accepted,
    and empty, too short, or containing invalid characters are rejected.
    """
    assert is_valid_name(name) is expected


@pytest.mark.parametrize("pw1,pw2,expected", [
    ("secret", "secret", True),
    ("", "", False),
    ("password", "different", False),
    ("123456", "123456", True),
])
def test_passwords_match(pw1: str, pw2: str, expected: bool):
    """
    Test passwords_match for equality of two password strings.

    Confirms matching non-empty passwords return True,
    identical empty passwords are considered invalid (False),
    and different passwords return False.
    """
    assert passwords_match(pw1, pw2) is expected


@pytest.mark.parametrize("year_str,expected", [
    ("1999", True),
    ("2025", True),
    ("1877", False),
    ("2101", False),
    ("abcd", False),
    ("", False),
])
def test_is_valid_year(year_str: str, expected: bool):
    """
    Test is_valid_year for numeric year string validation.

    Verifies years within acceptable range (e.g., 1900-2100) pass,
    out-of-range, non-numeric, or empty inputs fail.
    """
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
def test_is_valid_rating(value: str, expected: bool):
    """
    Test is_valid_rating for rating string boundaries.

    Ensures numeric ratings between 0 and 10 inclusive are valid,
    and out-of-bounds, non-numeric, or empty strings are invalid.
    """
    assert is_valid_rating(value) is expected


@pytest.mark.parametrize("value,expected", [
    ("5.567", 5.567),
    ("8.94", 8.94),
    ("0", 0.0),
    ("10", 10.0),
    ("15", 10.0),
    ("-5", 0.0),
    ("abc", 0.0),
])
def test_normalize_rating(value: str, expected: float):
    """
    Test normalize_rating conversion and clamping behavior.

    Confirms valid numeric strings convert to floats,
    values above 10 clamp to 10.0, below 0 clamp to 0.0,
    and non-numeric inputs return 0.0.
    """
    assert normalize_rating(value) == expected
