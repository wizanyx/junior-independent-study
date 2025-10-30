# Finance Sentiment Dashboard Backend

This is the backend service for the Finance Sentiment Dashboard project. It leverages state-of-the-art transformer-based NLP models (such as FinBERT) to analyze sentiment in financial texts. The backend exposes RESTful APIs to power a dashboard with real-time, ticker-specific sentiment insights from news, social media, and user-uploaded data.

## Key Features

- RESTful API for sentiment inference and data ingestion
- Integration with FinBERT and other transformer-based models
- Preprocessing pipeline for financial text
- Aggregation and explainability endpoints
- CORS enabled via `flask-cors`
- Robust code quality via Poetry, Ruff, Mypy, Pytest, pytest-cov, and pre-commit

## Project structure (key files)

This is an illustrative, non-exhaustive view to orient contributors:

```
src/backend/
├── app/                        # Flask app code
│   ├── __init__.py             # App factory and routes (e.g., /health)
│   ├── __main__.py             # CLI entrypoint: `python -m app`
│   ├── config.py               # Settings loaded from .env
│   └── schema.py               # Canonical Document schema and (de)serialization
├── tests/                      # Test suite
│   ├── app_test.py
│   ├── config_test.py
│   └── main_test.py
├── .pre-commit-config.yaml     # Lint/format/type hooks
├── .env.example                # Example environment variables
├── pyproject.toml              # Project metadata and dependencies
├── poetry.lock                 # Poetry lockfile
└── requirements.txt            # Exported deps for non-Poetry installs
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
   poetry install --with dev
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

## Data model: Document

We use a single canonical `Document` schema (see `app/schema.py`) to represent all ingested and uploaded text documents. This ensures adapters and the preprocessing pipeline operate on a predictable structure.

- id (str): unique identifier for the document. UUID4 Auto-generated if omitted or falsy.
- source (str): origin of the document (e.g., `news`, `reddit`, `upload`).
- ticker (str | null): optional ticker symbol (stored uppercase) associated with the document.
- created_at (datetime): internally stored as a timezone-aware UTC datetime and serialized as an ISO8601 UTC string with `Z` suffix like `2025-01-01T12:00:00.000000Z`.
- text (str): the text body to be analyzed (required).
- permalink (str | null): optional URL linking back to the original item.

Example JSON representation returned by the API or `Document.to_dict()`:

```json
{
   "id": "550e8400-e29b-41d4-a716-446655440000",
   "source": "news",
   "ticker": "AAPL",
   "created_at": "2025-01-01T12:00:00.000000Z",
   "text": "Apple shares rallied after earnings beat...",
   "permalink": "https://example.com/article/123"
}
```

Notes
- Input parsing accepts `created_at` as either an ISO8601 string (with `Z` or offset) or a `datetime`. Values are normalized to UTC.
- If `id` is provided but empty, a new UUID will be generated during initialization.
- Missing or empty `source`/`text` will raise `ValueError` at validation time.

Implementation:
- The canonical dataclass lives at `app/schema.py` as `Document`.
- Adapters should return data in their native format and then convert to `Document` via `Document.from_adapter(adapter_name, payload)` or construct via `Document.from_dict(...)` before handing data to the preprocessing and inference pipelines.

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
