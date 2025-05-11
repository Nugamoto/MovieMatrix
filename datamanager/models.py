from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String)  # nullable=True ist Standard
    age = Column(Integer)

    reviews = relationship("Review", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Movie(Base):
    __tablename__ = 'movies'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    director = Column(String)
    year = Column(Integer)
    genre = Column(String)
    poster_url = Column(String)
    imdb_rating = Column(Float)

    reviews = relationship("Review", back_populates="movie", cascade="all, delete")

    __table_args__ = (UniqueConstraint('title', 'year', name='uix_title_year'),)

    def __repr__(self):
        return f"<Movie(id={self.id}, title='{self.title}', year={self.year})>"


class Review(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False)

    text = Column(Text)
    user_rating = Column(Float)

    user = relationship("User", back_populates="reviews")
    movie = relationship("Movie", back_populates="reviews")

    def __repr__(self):
        return f"<Review(user_id={self.user_id}, movie_id={self.movie_id}, rating={self.user_rating})>"


class UserMovie(Base):
    __tablename__ = 'user_movies'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    movie_id = Column(Integer, ForeignKey('movies.id'), nullable=False)
    is_watched = Column(Integer, default=0)
    is_planned = Column(Integer, default=0)
    is_favorite = Column(Integer, default=0)

    user = relationship("User", back_populates="user_movies")
    movie = relationship("Movie", back_populates="user_movies")

    __table_args__ = (UniqueConstraint('user_id', 'movie_id', name='uix_user_movie'),)

    def __repr__(self):
        return (
            f"<UserMovie(user_id={self.user_id}, movie_id={self.movie_id}, "
            f"watched={self.is_watched}, planned={self.is_planned}, favorite={self.is_favorite})>"
        )


User.user_movies = relationship("UserMovie", back_populates="user", cascade="all, delete")
Movie.user_movies = relationship("UserMovie", back_populates="movie", cascade="all, delete")
