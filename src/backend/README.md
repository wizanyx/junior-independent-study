# Finance Sentiment Dashboard Backend

This is the backend service for the Finance Sentiment Dashboard project. It leverages state-of-the-art transformer-based NLP models (such as FinBERT) to analyze sentiment in financial texts. The backend exposes RESTful APIs to power a dashboard with real-time, ticker-specific sentiment insights from news, social media, and user-uploaded data.

## Key Features

- RESTful API for sentiment inference and data ingestion
- Integration with FinBERT and other transformer-based models
- Preprocessing pipeline for financial text
- Aggregation and explainability endpoints
- Robust code quality via Poetry, Ruff, Mypy, Pytest, pytest-cov, and pre-commit

## Project Structure

```
src/backend/
├── app/                        # Backend application code (Flask)
│   └── __init__.py
├── tests/                      # Test suite
│   ├── __init__.py
│   └── app_test.py
├── .gitignore                  # Gitignore
├── .pre-commit-config.yaml     # Pre-commit hooks for code quality
├── poetry.lock                 # Poetry dependency lockfile
├── pyproject.toml              # Project metadata and dependencies
├── README.md                   # This file
├── requirements-dev.txt        # Dev dependency list
└── requirements.txt            # Dependency list
```

## Installation (End Users)

```sh
cd src/backend
poetry install --no-dev
poetry run flask run
```

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
   poetry run flask run
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
   # View the HTML report by opening htmlcov/index.html in your browser
   ```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a pull request

## License

This project is for educational purposes as part of Anany Sachan’s independent study.

---

_Questions? Suggestions? Open an issue or contact [Anany Sachan](mailto:ananysachan2005@gmail.com)!_
