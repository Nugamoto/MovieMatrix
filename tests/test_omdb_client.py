from unittest.mock import patch

from requests.exceptions import RequestException

from clients.omdb_client import fetch_movie


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_success(mock_get):
    """Should return normalized movie data when OMDb returns valid response."""
    mock_get.return_value.json.return_value = {
        "Response": "True",
        "Title": "Inception",
        "Director": "Christopher Nolan",
        "Year": "2010",
        "imdbRating": "8.8"
    }

    result = fetch_movie("Inception", "2010")
    assert result == {
        "title": "Inception",
        "director": "Christopher Nolan",
        "year": "2010",
        "rating": "8.8"
    }


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_not_found(mock_get):
    """Should return empty dict if movie is not found."""
    mock_get.return_value.json.return_value = {
        "Response": "False",
        "Error": "Movie not found!"
    }

    result = fetch_movie("NonExistentMovie")
    assert result == {}


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_missing_fields(mock_get):
    """Should return empty dict if critical fields are missing."""
    mock_get.return_value.json.return_value = {
        "Response": "True",
        "Title": "No Director"
        # Missing Director, Year, Rating
    }

    result = fetch_movie("No Director")
    assert result == {
        "title": "No Director",
        "director": "Unknown",
        "year": None,
        "rating": "N/A"
    }


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_invalid_rating(mock_get):
    """Should still return data with 'N/A' rating if rating is not a number."""
    mock_get.return_value.json.return_value = {
        "Response": "True",
        "Title": "Fake",
        "Director": "Nobody",
        "Year": "2015",
        "imdbRating": "N/A"
    }

    result = fetch_movie("Fake", "2015")
    assert result == {
        "title": "Fake",
        "director": "Nobody",
        "year": "2015",
        "rating": "N/A"
    }


@patch("clients.omdb_client.requests.get")
def test_fetch_movie_network_exception(mock_get):
    """Should return empty dict if a network exception occurs."""
    mock_get.side_effect = RequestException("Network error")

    result = fetch_movie("AnyMovie")
    assert result == {}
