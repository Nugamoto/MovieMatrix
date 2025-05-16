> 🇩🇪 Für die deutsche Version siehe [README.de.md](README.de.md)

# 🎬 MovieMatrix

A sleek, modern web application for browsing, searching, and reviewing movies. Built as a learning project to master Python, Flask, and industry best practices.

---

## 🚀 Overview

MovieMatrix is a Flask-based web app that lets users:

- 🔍 **Search** movies via the OMDb API
- 📄 **View** movie details and posters
- ⭐️ **Leave reviews** and ratings
- 📊 **Manage** movie data with SQLite and SQLAlchemy

This project was created to solidify concepts in:

- Python programming and clean code (PEP 8)
- Flask application design (application factory, Blueprints)
- RESTful API consumption
- Relational databases with SQLAlchemy & migrations
- Automated testing with Pytest
- Frontend templating with Jinja2, HTML, CSS, and JavaScript

---

## 📚 What I Learned

1. **Pythonic Code & PEP 8**  
   Applied naming conventions, type hints, and structured modules to keep the codebase readable and maintainable.

2. **Flask Best Practices**  
   - Implemented an *application factory* pattern for flexible configuration.  
   - Organized routes into *Blueprints* for modularity.  
   - Centralized error handling and configuration classes.

3. **Data Management**  
   - Designed SQLAlchemy models and managed sessions gracefully.  
   - Used Alembic migrations (or plan to integrate) instead of manual scripts.

4. **API Integration**  
   - Created a reusable OMDb client for external API calls.  
   - Handled API errors gracefully with custom exceptions.

5. **Testing & CI**  
   - Wrote unit and integration tests with Pytest.  
   - Configured test fixtures and used a test database.

6. **Frontend Skills**  
   - Structured Jinja2 templates with inheritance (`base.html`).  
   - Added confirmation prompts with vanilla JS.  
   - Styled pages with responsive CSS.

---

## 🛠️ Technologies & Tools

| Category       | Tools & Libraries                  |
| -------------- | ---------------------------------- |
| Backend        | Python 3.x, Flask, Flask-SQLAlchemy |
| Database       | SQLite, SQLAlchemy                 |
| API Client     | Requests, OMDb API                 |
| Testing        | Pytest, pytest-cov                 |
| Frontend       | Jinja2, HTML5, CSS3, JavaScript    |
| Dev Tools      | Git, pre-commit, Black, Flake8     |

---

## ⚙️ Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/Nugamoto/MovieMatrix.git
   cd MovieMatrix
   ```
2. **Create & activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Create a `.env` file**
   ```env
   SECRET_KEY=your_secret_key_here
   OMDB_API_KEY=your_api_key_here
   ```
   Ensure these variables are set before initializing the database or running the app.

5. **Initialize the database**
   ```bash
   python -m utils.init_db
   ```
   This will create all necessary tables. You must run this **before** starting the Flask application.

---

## 🏃 Usage

- **Run development server**: `flask run`  
- **Run tests**: `pytest --cov=.`  
- **Lint & format**: `flake8 . && black .`

---

## 🤝 Contributing

1. Fork the repository  
2. Create a new branch: `git checkout -b feature/YourFeature`  
3. Commit your changes: `git commit -m "feat: add awesome feature"`  
4. Push to the branch: `git push origin feature/YourFeature`  
5. Open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

_Last updated: May 14, 2025_
