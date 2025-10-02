# Finance Sentiment Dashboard Frontend

This is the frontend for the Finance Sentiment Dashboard project, built with React, TypeScript, and Vite. It provides a modern dashboard to visualize real-time sentiment analysis results for financial assets, powered by the backend API.

## Getting Started (End Users)

1. **Environment variables:**

   Create your env file from the example and adjust the API base:

   ```sh
   cp .env.example .env
   # ensure VITE_API_BASE_URL points to your backend (default: http://localhost:8000)
   ```

2. **Install dependencies:**

   ```sh
   npm install --omit=dev
   ```

3. **Build for production:**

   ```sh
   npm run build
   ```

4. **Preview the production build:**
   ```sh
   npm run preview
   ```

## Developer Setup

1. **Environment variables:**

   ```sh
   cp .env.example .env
   # set VITE_API_BASE_URL (e.g., http://localhost:8000)
   ```

2. **Install dependencies:**

   ```sh
   npm install
   ```

3. **Set up pre-commit hooks (Husky + lint-staged):**

   ```sh
   npm run prepare
   ```

4. **Run the development server:**

   ```sh
   npm run dev
   ```

5. **Lint and format code:**

   ```sh
   npm run lint
   npm run format
   ```

6. **Run tests:**

   ```sh
   npm run test
   # or interactive UI mode
   npm run test:ui
   ```

7. **Run code coverage:**

   ```sh
   npm run test:coverage      # or: vitest --coverage
   # HTML report will be available in coverage/ directory
   ```

## Project Structure

```
src/frontend/
├── src/           # React app source
│   └── lib/api.ts # API client using VITE_API_BASE_URL
├── public/        # Static files
├── package.json
├── tsconfig.json
├── vite.config.ts
└── ...
```

## Notes

- The app expects the backend running on the URL specified by `VITE_API_BASE_URL`. Default backend port is `8000`.

## License

This project is for educational purposes as part of Anany Sachan’s independent study.

---

_Questions? Suggestions? Open an issue or contact [Anany Sachan](mailto:ananysachan2005@gmail.com)!_
