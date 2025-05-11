import os

import requests
from requests.exceptions import RequestException


def fetch_movie(title: str, year: str = "") -> dict:
    """Fetch movie data from the OMDb API based on title and optional year.

    Args:
        title (str): Movie title.
        year (str, optional): Release year.

    Returns:
        dict: Normalized movie data or empty dict on error.
    """
    api_key = os.getenv("OMDB_API_KEY")
    params = {"t": title, "apikey": api_key}
    if year:
        params["y"] = year

    try:
        response = requests.get("http://www.omdbapi.com/", params=params)
        data = response.json()
    except RequestException:
        return {}

    if data.get("Response") == "True":
        return {
            "title": data["Title"],
            "director": data.get("Director", "Unknown"),
            "year": data.get("Year"),
            "rating": data.get("imdbRating", "N/A"),
        }

    return {}
