# FinSight

A software application that ingests financial text data (news headlines, social media posts, or discussion forum content) and outputs sentiment classifications and visualizations in near real-time. The system leverages transformer-based models like FinBERT to provide ticker-specific sentiment scores and trends via an interactive dashboard. Users can analyze sentiment for specific stocks using recent news and social data, upload their own text or CSVs for analysis, and view clear sentiment metrics, trend charts, and top posts. This project demonstrates the practical application of state-of-the-art NLP to financial market analysis.

## Feature Calendar

| **Issue** | **Due Date**        | **Notes** |
| --------- | ------------------ | --------- |
| [Initialize project environment (backend/frontend, tests, CI)](https://github.com/wizanyx/junior-independent-study/issues/1) | 9/21/25 |  |
| [Configure environment variables and secrets](https://github.com/wizanyx/junior-independent-study/issues/2) | 9/21/25 |  |
| [Standardize document schema for texts](https://github.com/wizanyx/junior-independent-study/issues/3) | 9/25/25 |  |
| [Build text preprocessing pipeline](https://github.com/wizanyx/junior-independent-study/issues/4) | 9/29/25 |  |
| [Integrate FinBERT sentiment model](https://github.com/wizanyx/junior-independent-study/issues/5) | 10/3/25 |  |
| [Backend endpoint: paste-text analysis](https://github.com/wizanyx/junior-independent-study/issues/6) | 10/5/25 |  |
| [Backend endpoint: CSV upload analysis](https://github.com/wizanyx/junior-independent-study/issues/7) | 10/7/25 |  |
| [News ingestion adapter](https://github.com/wizanyx/junior-independent-study/issues/8) | 10/10/25 |  |
| [Reddit/StockTwits ingestion adapter](https://github.com/wizanyx/junior-independent-study/issues/9) | 10/13/25 |  |
| [Aggregation module for sentiment metrics](https://github.com/wizanyx/junior-independent-study/issues/10) | 10/16/25 |  |
| [Explainability endpoint (token-level highlights)](https://github.com/wizanyx/junior-independent-study/issues/11) | 10/19/25 |  |
| [REST API endpoints for metrics, posts, explanations, health](https://github.com/wizanyx/junior-independent-study/issues/12) | 10/23/25 | Integration milestone |
| [Core React dashboard (ticker input, KPIs, chart, posts)](https://github.com/wizanyx/junior-independent-study/issues/13) | 10/30/25 | Demo milestone |
| [Frontend: paste-text and file upload flows](https://github.com/wizanyx/junior-independent-study/issues/14) | 11/2/25 |  |
| [Frontend: error handling and UX states](https://github.com/wizanyx/junior-independent-study/issues/15) | 11/5/25 |  |
| [Containerize backend/frontend with Docker Compose](https://github.com/wizanyx/junior-independent-study/issues/16) | 11/10/25 | Integration milestone |

| **Stretch Goals** | **Due Date**        | **Notes** |
| ----------------- | ------------------ | --------- |
| [Add scheduler and caching for in-memory refresh](https://github.com/wizanyx/junior-independent-study/issues/17) | If time permits | Stretch goal |
| [Persistent storage for texts, scores, and aggregates](https://github.com/wizanyx/junior-independent-study/issues/18) | If time permits | Stretch goal |
| [Live stock price overlay in dashboard](https://github.com/wizanyx/junior-independent-study/issues/19) | If time permits | Stretch goal |
| [Prototype predictive model using sentiment features](https://github.com/wizanyx/junior-independent-study/issues/20) | If time permits | Stretch goal; depends on sufficient data gathered |
