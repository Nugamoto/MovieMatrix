> 🇬🇧 For the English version see [README.md](README.md)

# 🎬 MovieMatrix

Eine moderne Webanwendung zum Durchsuchen, Suchen und Bewerten von Filmen. Entwickelt als Lernprojekt, um Python, Flask und Best Practices der Branche zu meistern.

---

## 🚀 Übersicht

MovieMatrix ist eine Flask-basierte Web-App, die es Nutzern ermöglicht:

- 🔍 **Filme zu suchen** über die OMDb-API
- 📄 **Filmdetails** und Poster anzusehen
- ⭐️ **Bewertungen** und Rezensionen zu hinterlassen
- 📊 **Filmdaten** mit SQLite und SQLAlchemy zu verwalten

Dieses Projekt wurde erstellt, um folgende Konzepte zu festigen:

- Python-Programmierung und sauberen Code (PEP 8)
- Flask-Anwendungsdesign (Application Factory, Blueprints)
- RESTful-API-Nutzung
- Relationale Datenbanken mit SQLAlchemy & Migrationen
- Automatisiertes Testen mit Pytest
- Frontend-Templates mit Jinja2, HTML, CSS und JavaScript

---

## 📚 Was ich gelernt habe

1. **Pythonic Code & PEP 8**  
   Namenskonventionen, Type Hints und modulare Struktur für Wartbarkeit und Lesbarkeit angewendet.

2. **Flask Best Practices**  
   - Application Factory Pattern für flexible Konfiguration implementiert.  
   - Routen in Blueprints organisiert für bessere Modularität.  
   - Zentrale Fehlerbehandlung und Konfigurationsklassen.

3. **Datenmanagement**  
   - SQLAlchemy-Modelle entworfen und Sessions sauber verwaltet.  
   - Alembic-Migrationen (oder geplant) statt manueller Skripte.

4. **API-Integration**  
   - Wiederverwendbaren OMDb-Client für externe API-Aufrufe erstellt.  
   - API-Fehler mit benutzerdefinierten Ausnahmen abgefangen.

5. **Testing & CI**  
   - Unit- und Integrationstests mit Pytest geschrieben.  
   - Test-Fixtures konfiguriert und Test-Datenbank verwendet.

6. **Frontend-Fähigkeiten**  
   - Jinja2-Templates mit Vererbung (`base.html`) strukturiert.  
   - Bestätigungsdialoge mit vanilla JS hinzugefügt.  
   - Responsive CSS-Styles angewendet.

---

## 🛠️ Technologien & Tools

| Kategorie      | Tools & Bibliotheken             |
| -------------- | -------------------------------- |
| Backend        | Python 3.x, Flask, Flask-SQLAlchemy |
| Datenbank      | SQLite, SQLAlchemy               |
| API-Client     | Requests, OMDb API               |
| Testing        | Pytest, pytest-cov               |
| Frontend       | Jinja2, HTML5, CSS3, JavaScript  |
| Dev-Tools      | Git, pre-commit, Black, Flake8   |

---

## ⚙️ Installation

1. **Repository klonen**
   ```bash
   git clone https://github.com/Nugamoto/MovieMatrix.git
   cd MovieMatrix
   ```
2. **Virtuelle Umgebung erstellen & aktivieren**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```
4. **`.env`-Datei anlegen**
   ```env
   SECRET_KEY=dein_secret_key_hier
   OMDB_API_KEY=dein_api_key_hier
   ```
   Stelle sicher, dass diese Variablen gesetzt sind, bevor du die Datenbank initialisierst oder die App startest.

5. **Datenbank initialisieren**
   ```bash
   python init_db.py
   ```
   Dies erstellt alle notwendigen Tabellen. Du **musst** diesen Schritt ausführen, **bevor** du die Flask-Anwendung startest.

---

## 🏃 Nutzung

- **Entwicklungsserver starten**: `flask run`  
- **Tests ausführen**: `pytest --cov=.`  
- **Linting & Formatierung**: `flake8 . && black .`

---

## 🤝 Mitwirken

1. Forke das Repository  
2. Erstelle einen neuen Branch: `git checkout -b feature/DeinFeature`  
3. Committe deine Änderungen: `git commit -m "feat: tolle Funktion hinzufügen"`  
4. Push zum Branch: `git push origin feature/DeinFeature`  
5. Öffne einen Pull Request

Bitte nutze [Conventional Commits](https://www.conventionalcommits.org/) für deine Commit-Nachrichten.

---

## 📄 Lizenz

Veröffentlicht unter der MIT-Lizenz. Siehe `LICENSE` für Details.

---

_Last updated: 14. Mai 2025_
