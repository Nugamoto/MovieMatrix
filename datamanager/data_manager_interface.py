from abc import ABC, abstractmethod


class DataManagerInterface(ABC):
    # === USER ===
    @abstractmethod
    def get_all_users(self):
        """Return a list of all users."""
        pass

    @abstractmethod
    def add_user(self, name: str):
        """Add a new user to the database."""
        pass

    @abstractmethod
    def update_user(self, user_id: int, new_name: str):
        """Update a user's name."""
        pass

    @abstractmethod
    def delete_user(self, user_id: int):
        """Delete a user and optionally their movies and reviews."""
        pass

    # === MOVIE ===
    @abstractmethod
    def get_all_movies(self):
        """Return a list of all movies."""
        pass

    @abstractmethod
    def get_user_movies(self, user_id: int):
        """Return a list of movies for the given user."""
        pass

    @abstractmethod
    def add_movie(self, user_id: int, movie_data: dict):
        """Add a movie to the user's list."""
        pass

    @abstractmethod
    def update_movie(self, movie_id: int, updated_data: dict):
        """Update a movie's details."""
        pass

    @abstractmethod
    def delete_movie(self, movie_id: int):
        """Delete a movie from the database."""
        pass

    # === REVIEW ===
    @abstractmethod
    def add_review(self, user_id: int, movie_id: int, review_data: dict):
        """Add a review for a movie by a user."""
        pass

    @abstractmethod
    def get_reviews_for_movie(self, movie_id: int):
        """Return all reviews for a given movie."""
        pass

    @abstractmethod
    def get_reviews_by_user(self, user_id: int):
        """Return all reviews written by a given user."""
        pass

    @abstractmethod
    def update_review(self, review_id: int, updated_data: dict):
        """Update the content or rating of a review."""
        pass

    @abstractmethod
    def delete_review(self, review_id: int):
        """Delete a review from the database."""
        pass
