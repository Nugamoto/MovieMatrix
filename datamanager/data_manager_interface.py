from abc import ABC, abstractmethod


class DataManagerInterface(ABC):
    # === USER ===
    @abstractmethod
    def get_all_users(self) -> list:
        """Return all user objects."""
        raise NotImplementedError

    @abstractmethod
    def add_user(
            self,
            username: str,
            email: str,
            first_name: str,
            password_hash: str,
            last_name: str | None = None,
            age: int | None = None,
    ):
        """Create a user with the required fields and return it."""
        raise NotImplementedError

    @abstractmethod
    def update_user(self, user_id: int, new_name: str):
        """Rename a user and return the updated object or None."""
        raise NotImplementedError

    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        """Remove a user and cascade deletes; return True on success."""
        raise NotImplementedError

    # === MOVIE ===
    @abstractmethod
    def get_all_movies(self) -> list:
        """Return all movie objects, regardless of user."""
        raise NotImplementedError

    @abstractmethod
    def get_movies_by_user(self, user_id: int) -> list:
        """Return all movies linked to a user via user_movies."""
        raise NotImplementedError

    @abstractmethod
    def add_movie(
            self,
            user_id: int,
            movie_data: dict,
            planned: bool = True,
            watched: bool = False,
            favorite: bool = False,
    ):
        """Insert (or link) a movie and return the Movie object."""
        raise NotImplementedError

    @abstractmethod
    def update_movie(self, movie_id: int, updated_data: dict):
        """Update given fields of a movie; return updated object or None."""
        raise NotImplementedError

    @abstractmethod
    def delete_movie(self, movie_id: int) -> bool:
        """Delete a movie record and return success status."""
        raise NotImplementedError

    # === REVIEW ===
    @abstractmethod
    def add_review(self, user_id: int, movie_id: int, review_data: dict):
        """Create a review and return it, or None on failure."""
        raise NotImplementedError

    @abstractmethod
    def get_reviews_for_movie(self, movie_id: int) -> list:
        """Return all reviews for a specific movie."""
        raise NotImplementedError

    @abstractmethod
    def get_reviews_by_user(self, user_id: int) -> list:
        """Return all reviews written by a user."""
        raise NotImplementedError

    @abstractmethod
    def update_review(self, review_id: int, updated_data: dict):
        """Modify review text or rating; return updated review or None."""
        raise NotImplementedError

    @abstractmethod
    def delete_review(self, review_id: int) -> bool:
        """Delete a review and return success status."""
        raise NotImplementedError
