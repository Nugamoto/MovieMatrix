"""
Tests for the OMDb client `fetch_movie` function.

This module contains pytest unit tests that verify the behavior of the
`fetch_movie` function under various scenarios, including successful
responses, missing data, errors, and edge cases.
"""

from unittest.mock import patch

from requests.exceptions import RequestException

from clients.omdb_client import fetch_movie


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_success(mock_get):
    """
    Return normalized movie data on valid OMDb response.

    Given a successful OMDb API response with all expected fields,
    `fetch_movie` should parse and convert the data to the correct types
    and keys.
    """
    mock_get.return_value.json.return_value = {
        "Response": "True",
        "Title": "Inception",
        "Director": "Christopher Nolan",
        "Year": "2010",
        "Genre": "Sci-Fi",
        "Poster": "http://poster.url",
        "imdbRating": "8.8"
    }

    result = fetch_movie("Inception", "2010")
    assert result == {
        "title": "Inception",
        "director": "Christopher Nolan",
        "year": 2010,
        "genre": "Sci-Fi",
        "poster_url": "http://poster.url",
        "imdb_rating": 8.8
    }


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_not_found(mock_get):
    """
    Return empty dict when movie is not found.

    If the OMDb API indicates `Response: False`, `fetch_movie` should
    return an empty dictionary.
    """
    mock_get.return_value.json.return_value = {
        "Response": "False",
        "Error": "Movie not found!"
    }

    result = fetch_movie("NonExistentMovie")
    assert result == {}


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_with_missing_fields(mock_get):
    """
    Fill missing fields with defaults.

    When certain fields are absent in the OMDb response, `fetch_movie`
    should supply sensible defaults such as None or 'Unknown'.
    """
    mock_get.return_value.json.return_value = {
        "Response": "True",
        "Title": "Minimal Movie"
        # Director, Year, Genre, Poster, imdbRating missing
    }

    result = fetch_movie("Minimal Movie")
    assert result == {
        "title": "Minimal Movie",
        "director": "Unknown",
        "year": None,
        "genre": None,
        "poster_url": None,
        "imdb_rating": None
    }


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_with_invalid_year_and_rating(mock_get):
    """
    Convert non-numeric year and rating to None.

    If the OMDb response contains non-numeric values for Year or
    imdbRating (e.g., 'N/A'), `fetch_movie` should return None for these fields.
    """
    mock_get.return_value.json.return_value = {
        "Response": "True",
        "Title": "Strange Data",
        "Director": "Unknown",
        "Year": "N/A",
        "Genre": "Mystery",
        "Poster": "",
        "imdbRating": "N/A"
    }

    result = fetch_movie("Strange Data")
    assert result == {
        "title": "Strange Data",
        "director": "Unknown",
        "year": None,
        "genre": "Mystery",
        "poster_url": "",
        "imdb_rating": None
    }


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_network_error(mock_get):
    """
    Return empty dict on network error.

    If a `RequestException` occurs during the HTTP request,
    `fetch_movie` should handle it gracefully and return an empty dict.
    """
    mock_get.side_effect = RequestException("Network failure")

    result = fetch_movie("AnyMovie")
    assert result == {}
