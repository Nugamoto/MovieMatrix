import os

import requests


def fetch_movie(title: str, year: str = "") -> dict:
    api_key = os.getenv("OMDB_API_KEY")
    params = {"t": title, "apikey": api_key}
    if year:
        params["y"] = year

    response = requests.get("http://www.omdbapi.com/", params=params)
    data = response.json()

    if data.get("Response") == "True":
        return {
            "title": data["Title"],
            "director": data.get("Director", "Unknown"),
            "year": data.get("Year"),
            "rating": data.get("imdbRating", "N/A")
        }

    return {}
