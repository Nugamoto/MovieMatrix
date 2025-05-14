from unittest.mock import patch

from requests.exceptions import RequestException

from clients.omdb_client import fetch_movie


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_success(mock_get):
    """Should return fully normalized movie data on valid OMDb response."""
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
    """Should return empty dict if OMDb response indicates movie not found."""
    mock_get.return_value.json.return_value = {
        "Response": "False",
        "Error": "Movie not found!"
    }

    result = fetch_movie("NonExistentMovie")
    assert result == {}


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_with_missing_fields(mock_get):
    """Should fill missing fields with defaults like None or 'Unknown'."""
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
    """Should convert non-numeric year and rating to None."""
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
    """Should return empty dict if network error occurs."""
    mock_get.side_effect = RequestException("Network failure")

    result = fetch_movie("AnyMovie")
    assert result == {}
