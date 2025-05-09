from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    movies = relationship("Movie", back_populates="user", cascade="all, delete")
    reviews = relationship("Review", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}')>"


class Movie(Base):
    __tablename__ = 'movies'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    director = Column(String)
    year = Column(Integer)
    rating = Column(Float)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="movies")

    reviews = relationship("Review", back_populates="movie", cascade="all, delete")

    def __repr__(self):
        return f"<Movie(id={self.id}, title='{self.title}', user_id={self.user_id})>"


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
