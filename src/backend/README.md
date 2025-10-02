# Finance Sentiment Dashboard Backend

This is the backend service for the Finance Sentiment Dashboard project. It leverages state-of-the-art transformer-based NLP models (such as FinBERT) to analyze sentiment in financial texts. The backend exposes RESTful APIs to power a dashboard with real-time, ticker-specific sentiment insights from news, social media, and user-uploaded data.

## Key Features

- RESTful API for sentiment inference and data ingestion
- Integration with FinBERT and other transformer-based models
- Preprocessing pipeline for financial text
- Aggregation and explainability endpoints
- CORS enabled via `flask-cors`
- Robust code quality via Poetry, Ruff, Mypy, Pytest, pytest-cov, and pre-commit

## Project Structure

```
src/backend/
├── app/                        # Backend application code (Flask)
│   ├── __init__.py             # App factory, routes (e.g., /health)
│   └── config.py               # Settings loaded from .env
├── tests/                      # Test suite
│   ├── __init__.py
│   └── app_test.py
├── .env.example                # Example environment variables
├── poetry.lock                 # Poetry dependency lockfile
└── pyproject.toml              # Project metadata and dependencies
```

## Environment

Copy the example and edit values as needed:

```sh
cd src/backend
cp .env.example .env
```

Key variables (see `.env.example` for defaults):
- `FLASK_ENV` (default `development`)
- `API_PORT` (default `8000`)
- `CORS_ALLOWED_ORIGINS` (comma-separated, default `http://localhost:5173`)
- `ENABLE_SOURCES` (default `news,reddit`)
- `NEWS_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`

Settings are loaded via `python-dotenv` and `app/config.py` computes `enabled_sources` based on provided credentials.

## Installation (End Users)

```sh
cd src/backend
poetry install --no-dev
poetry run python -m app
```

By default the server runs on port 8000. Change with `API_PORT`.

Health check:
```sh
curl http://localhost:8000/health
```
Response JSON includes: `status`, `env`, `enabled_sources`, `default_window_hours`.

## Developer Setup

1. **Install dependencies:**

   ```sh
   poetry install
   ```

2. **Set up pre-commit hooks:**

   ```sh
   poetry run pre-commit install
   ```

3. **Run the development server:**

   ```sh
   poetry run flask --app app:create_app --debug run --port 8000
   ```

4. **Lint and type-check:**

   ```sh
   poetry run ruff check .
   poetry run mypy .
   ```

5. **Run tests:**

   ```sh
   poetry run pytest
   ```

6. **Code coverage:**

   ```sh
   poetry run pytest --cov=app --cov-report=term-missing --cov-report=html
   # View HTML report at htmlcov/index.html
   ```

## CORS

CORS is configured via `flask-cors` and allowed origins come from `CORS_ALLOWED_ORIGINS`. Use a comma-separated list for multiple origins.

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a pull request

## License

This project is for educational purposes as part of Anany Sachan’s independent study.

---

_Questions? Suggestions? Open an issue or contact [Anany Sachan](mailto:ananysachan2005@gmail.com)!_
