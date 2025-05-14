import pytest

from helpers import (
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
    assert is_valid_username(username) is expected


@pytest.mark.parametrize("email,expected", [
    ("user@example.com", True),
    ("john.doe@mail.co.uk", True),
    ("invalid@", False),
    ("@invalid.com", False),
    ("", False),
])
def test_is_valid_email(email: str, expected: bool):
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
    assert is_valid_name(name) is expected


@pytest.mark.parametrize("pw1,pw2,expected", [
    ("secret", "secret", True),
    ("", "", False),
    ("password", "different", False),
    ("123456", "123456", True),
])
def test_passwords_match(pw1: str, pw2: str, expected: bool):
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
    assert normalize_rating(value) == expected
