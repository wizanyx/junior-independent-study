# Finance Sentiment Dashboard Frontend

This is the frontend for the Finance Sentiment Dashboard project, built with React, TypeScript, and Vite. It provides a modern dashboard to visualize real-time sentiment analysis results for financial assets, powered by the backend API.

## Getting Started (End Users)

1. **Install dependencies:**

   ```sh
   npm install --omit=dev
   ```

2. **Build for production:**

   ```sh
   npm run build
   ```

3. **Preview the production build:**
   ```sh
   npm run preview
   ```

## Developer Setup

1. **Install dependencies:**

   ```sh
   npm install
   ```

2. **Set up pre-commit hooks (Husky + lint-staged):**

   ```sh
   npm run prepare
   ```

3. **Run the development server:**

   ```sh
   npm run dev
   ```

4. **Lint and format code:**

   ```sh
   npm run lint
   npm run format
   ```

5. **Run tests:**

   ```sh
   npm run test
   # or interactive UI mode
   npm run test:ui
   ```

6. **Run code coverage:**

   ```sh
   npm run test:coverage      # or: vitest --coverage
   # HTML report will be available in coverage/ directory
   ```

## Project Structure

```
src/frontend/
├── src/           # React app source
├── public/        # Static files
├── package.json
├── tsconfig.json
├── vite.config.ts
└── ...
```

## License

This project is for educational purposes as part of Anany Sachan’s independent study.

---

_Questions? Suggestions? Open an issue or contact [Anany Sachan](mailto:ananysachan2005@gmail.com)!_
