# Finance Sentiment Dashboard – Source Code

[![CI](https://github.com/wizanyx/junior-independent-study/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/wizanyx/junior-independent-study/actions/workflows/ci.yml)
[![codecov](https://codecov.io/github/wizanyx/junior-independent-study/graph/badge.svg)](https://codecov.io/github/wizanyx/junior-independent-study)
[![Node.js Version](https://img.shields.io/badge/node-%3E=20.0.0-brightgreen.svg)](https://nodejs.org/)
[![Frontend: React](https://img.shields.io/badge/frontend-react-61DAFB)](https://reactjs.org/)
[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Backend: Flask](https://img.shields.io/badge/backend-flask-blue)](https://flask.palletsprojects.com/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://pre-commit.com/)

This directory contains the source code for the Finance Sentiment Dashboard, a full-stack application for real-time, ticker-specific sentiment analysis of financial texts. The project consists of a Flask backend for data processing and a React + Vite frontend for visualization.

## Repository Structure

- `backend/` — Flask backend ([see details](backend/README.md))
- `frontend/` — React + Vite frontend ([see details](frontend/README.md))

---

## 📝 Prerequisites

You will need the following tools installed on your machine:

- **Node.js** (>= 20.x) and **npm** (>= 9.x) — for frontend development ([Download node.js (including npm)](https://nodejs.org/en/download/))
- **Python** (>= 3.11) — for backend development ([Download python](https://www.python.org/downloads/))
- **Poetry** (>= 2.0) — for Python dependency management ([Install instructions](https://python-poetry.org/docs/#installation))

---

## 🛠 Installation (For End Users)

### Clone the repo:

```sh
git clone https://github.com/wizanyx/junior-independent-study.git
cd junior-independent-study/
```

### Backend

```sh
cd src/backend
poetry install --no-dev
poetry run flask run
```

### Frontend

```sh
cd src/frontend
npm install --omit=dev
npm run build
npm run preview
```

---

## 👩‍💻 Development Setup (For Contributors)

### 1. Install Dependencies

```sh
# Frontend
cd src/frontend
npm install

# Backend
cd src/backend
poetry install
```

### 2. Set Up Pre-commit Hooks

Pre-commit hooks enforce code quality for both backend and frontend:

```sh
# Frontend (Husky + lint-staged)
cd src/frontend
npm run prepare

# Backend (pre-commit)
cd src/backend
poetry run pre-commit install
```

### 3. Run Development Servers

```sh
# Frontend
cd src/frontend
npm run dev

# Backend
cd src/backend
poetry run flask run
```

### 4. Lint, Format, and Test

```sh
# Frontend
cd src/frontend
npm run lint
npm run format
npm run test

# Backend
cd src/backend
poetry run ruff check .
poetry run mypy .
poetry run pytest
```

### 5. Code Coverage

#### Frontend (React + Vite + Vitest + v8)

```sh
cd src/frontend
npm run test:coverage
```

#### Backend (Flask + Pytest + pytest-cov)

```sh
cd src/backend
poetry run pytest --cov=app
```

---

## 📁 Additional Information

- Each subdirectory (`backend/` and `frontend/`) contains its own `README.md` with more detailed setup, usage, and contribution instructions.
- For environment variable configuration or advanced deployment, refer to the respective subproject’s README.

---

## 📝 License

This project is for educational purposes as part of Anany Sachan’s independent study.

---

_Questions? Suggestions? Open an issue or contact [Anany Sachan](mailto:ananysachan2005@gmail.com)!_
