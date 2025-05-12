import os

import requests
from requests.exceptions import RequestException


def fetch_movie(title: str, year: str = "") -> dict:
    """
    Fetch detailed movie data from the OMDb API using a title and optional release year.

    This function requests data from the OMDb API and returns selected, normalized
    fields including director, year, genre, IMDb rating, and poster URL. It handles
    missing or malformed data gracefully and returns None where values are invalid.

    Args:
        title (str): The title of the movie to search for.
        year (str, optional): The release year to narrow the search (default is empty string).

    Returns:
        dict: A dictionary containing the movie data with keys:
              'title', 'director', 'year', 'genre', 'poster_url', 'imdb_rating'.
              If the API call fails or data is invalid, an empty dictionary is returned.
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
            "title": data.get("Title"),
            "director": data.get("Director") or "Unknown",
            "year": int(data["Year"]) if data.get("Year", "").isdigit() else None,
            "genre": data.get("Genre"),
            "poster_url": data.get("Poster"),
            "imdb_rating": float(data["imdbRating"]) if data.get("imdbRating", "").replace(".", "",
                                                                                           1).isdigit() else None,
        }

    return {}
